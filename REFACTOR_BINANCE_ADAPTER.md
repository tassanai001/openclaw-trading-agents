# 🔄 Refactor Plan: Exchange Adapter Pattern

**เป้าหมาย:** ย้ายจาก Hyperliquid Testnet → Binance Demo (Spot Testnet)  
**Pattern:** Adapter Pattern  
**เวลาโดยประมาณ:** 4-6 ชั่วโมง  
**ความเสี่ยง:** ต่ำ

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Execution Agent                           │
│  (ไม่แก้ logic หลัก - เรียกผ่าน Interface เท่านั้น)           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Exchange Interface                           │
│  (Abstract Base Class - กำหนด contract กลาง)                 │
│                                                              │
│  - place_order(symbol, side, quantity, price) → OrderResult │
│  - cancel_order(order_id) → bool                            │
│  - get_balance() → Balance                                  │
│  - get_positions() → List[Position]                         │
│  - get_ticker_price(symbol) → float                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
┌───────────────────┐   ┌─────────────────────┐
│ HyperliquidAdapter│   │  BinanceAdapter     │
│ (เดิม - เก็บไว้)   │   │  (ใหม่ - Binance)   │
└───────────────────┘   └─────────────────────┘
```

---

## 📁 New File Structure

```
openclaw-trading-agents/
├── agents/
│   └── execution/
│       ├── execution_agent.py      ← แก้ไข (ใช้ interface)
│       ├── exchange_interface.py   ← ใหม่ (abstract base)
│       ├── adapters/               ← ใหม่ (folder)
│       │   ├── __init__.py
│       │   ├── base.py             ← ใหม่ (interface implementation)
│       │   ├── hyperliquid.py      ← ย้ายจาก execution_agent.py เดิม
│       │   └── binance.py          ← ใหม่ (Binance implementation)
│       └── models/                 ← ใหม่ (data models)
│           ├── __init__.py
│           ├── order.py            ← ใหม่ (Order, OrderResult)
│           ├── position.py         ← ใหม่ (Position, Balance)
│           └── common.py           ← ใหม่ (enums, types)
│
├── config/
│   ├── exchange_config.py          ← แก้ไข (เลือก adapter)
│   └── .env.example                ← แก้ไข (Binance credentials)
│
├── tests/
│   └── adapters/                   ← ใหม่
│       ├── test_binance_adapter.py
│       └── test_hyperliquid_adapter.py
│
├── requirements.txt                ← แก้ไข (เพิ่ม python-binance)
└── REFACTOR_BINANCE_ADAPTER.md     ← ไฟล์นี้
```

---

## 🔧 Implementation Details

### 1. Data Models (`agents/execution/models/`)

#### `common.py`
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass
class ExchangeCredentials:
    api_key: str
    api_secret: str
    testnet: bool = True
    endpoint: Optional[str] = None
```

#### `order.py`
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .common import OrderSide, OrderType, OrderStatus

@dataclass
class Order:
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # GTC, IOC, FOK
    client_order_id: Optional[str] = None

@dataclass
class OrderResult:
    success: bool
    order_id: Optional[str] = None
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    fee: float = 0.0
    fee_currency: str = "USDT"
    status: OrderStatus = OrderStatus.PENDING
    message: str = ""
    raw_response: Optional[dict] = None
    
    @classmethod
    def success_result(cls, order_id: str, filled_qty: float = 0.0, 
                       filled_price: float = 0.0, fee: float = 0.0,
                       raw_response: dict = None):
        return cls(
            success=True,
            order_id=order_id,
            filled_quantity=filled_qty,
            filled_price=filled_price,
            fee=fee,
            status=OrderStatus.FILLED if filled_qty > 0 else OrderStatus.PENDING,
            raw_response=raw_response
        )
    
    @classmethod
    def error_result(cls, message: str, raw_response: dict = None):
        return cls(
            success=False,
            message=message,
            status=OrderStatus.REJECTED,
            raw_response=raw_response
        )
```

#### `position.py`
```python
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Position:
    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    side: str = "LONG"  # LONG, SHORT, NONE
    
    def update_price(self, price: float):
        self.current_price = price
        if self.side == "LONG":
            self.unrealized_pnl = (price - self.avg_entry_price) * self.quantity
        elif self.side == "SHORT":
            self.unrealized_pnl = (self.avg_entry_price - price) * self.quantity
    
    @property
    def market_value(self) -> float:
        return self.current_price * abs(self.quantity)

@dataclass
class Balance:
    total_balance: float  # ในหน่วย USDT
    available_balance: float
    locked_balance: float
    currency: str = "USDT"
    balances: dict = field(default_factory=dict)  # { "BTC": 0.5, "USDT": 10000 }
    
    @classmethod
    def from_dict(cls, data: dict, currency: str = "USDT"):
        return cls(
            total_balance=data.get("total", 0.0),
            available_balance=data.get("available", 0.0),
            locked_balance=data.get("locked", 0.0),
            currency=currency,
            balances=data.get("balances", {})
        )
```

---

### 2. Exchange Interface (`agents/execution/adapters/base.py`)

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.order import Order, OrderResult
from ..models.position import Position, Balance
from ..models.common import ExchangeCredentials

class ExchangeAdapter(ABC):
    """
    Abstract Base Class สำหรับ Exchange Adapter
    ทุก adapter ต้อง implement methods เหล่านี้
    """
    
    def __init__(self, credentials: ExchangeCredentials):
        self.credentials = credentials
        self.testnet = credentials.testnet
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize connection to exchange"""
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> OrderResult:
        """Place an order and return result"""
        pass
    
    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get list of open orders"""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all positions"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> Balance:
        """Get account balance"""
        pass
    
    @abstractmethod
    async def get_ticker_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        pass
    
    @abstractmethod
    def get_symbol_info(self, symbol: str) -> dict:
        """Get symbol info (precision, min qty, etc.)"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Exchange name"""
        pass
```

---

### 3. Binance Adapter (`agents/execution/adapters/binance.py`)

```python
import asyncio
from typing import List, Optional
from binance import AsyncClient
from ..adapters.base import ExchangeAdapter
from ..models.order import Order, OrderResult
from ..models.position import Position, Balance
from ..models.common import ExchangeCredentials, OrderSide, OrderStatus

class BinanceAdapter(ExchangeAdapter):
    """
    Binance Spot Testnet Adapter
    
    Testnet: https://testnet.binance.vision
    API Docs: https://binance-docs.github.io/apidocs/spot/en/
    """
    
    TESTNET_URL = "https://testnet.binance.vision"
    MAINNET_URL = "https://api.binance.com"
    
    def __init__(self, credentials: ExchangeCredentials):
        super().__init__(credentials)
        self.client: Optional[AsyncClient] = None
        self._symbol_info_cache = {}
    
    @property
    def name(self) -> str:
        return "Binance"
    
    async def initialize(self) -> bool:
        """Initialize Binance client"""
        try:
            base_url = self.TESTNET_URL if self.testnet else self.MAINNET_URL
            self.client = await AsyncClient.create(
                api_key=self.credentials.api_key,
                api_secret=self.credentials.api_secret,
                base_url=base_url
            )
            self._initialized = True
            print(f"✅ Binance Adapter initialized (testnet={self.testnet})")
            return True
        except Exception as e:
            print(f"❌ Binance Adapter initialization failed: {e}")
            return False
    
    async def place_order(self, order: Order) -> OrderResult:
        """Place order on Binance"""
        if not self._initialized:
            return OrderResult.error_result("Adapter not initialized")
        
        try:
            # Convert order to Binance format
            params = {
                "symbol": order.symbol.upper(),  # BTCUSDT
                "side": order.side.value,        # BUY/SELL
                "type": order.type.value,        # MARKET/LIMIT
                "quantity": self._format_quantity(order.symbol, order.quantity),
            }
            
            if order.type == OrderType.LIMIT:
                params["price"] = self._format_price(order.symbol, order.price)
                params["timeInForce"] = order.time_in_force
            
            if order.client_order_id:
                params["newClientOrderId"] = order.client_order_id
            
            # Place order
            response = await self.client.create_order(**params)
            
            # Parse response
            filled_qty = float(response.get("executedQty", 0))
            filled_price = float(response.get("price", 0))
            order_id = response.get("orderId")
            status = response.get("status", "NEW")
            
            # Calculate fee (Binance: 0.1% spot, 0.075% with BNB)
            fee = float(response.get("cummulativeQuoteQty", 0)) * 0.001
            
            return OrderResult.success_result(
                order_id=str(order_id),
                filled_qty=filled_qty,
                filled_price=filled_price,
                fee=fee,
                raw_response=response
            )
            
        except Exception as e:
            return OrderResult.error_result(f"Binance order failed: {str(e)}")
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel order"""
        try:
            await self.client.cancel_order(
                symbol=symbol.upper(),
                orderId=int(order_id)
            )
            return True
        except Exception as e:
            print(f"Cancel order failed: {e}")
            return False
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        try:
            if symbol:
                orders = await self.client.get_open_orders(symbol=symbol.upper())
            else:
                orders = await self.client.get_open_orders()
            
            return [self._parse_order(o) for o in orders]
        except Exception as e:
            print(f"Get open orders failed: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol (spot = balance)"""
        try:
            # For spot, position = balance of base asset
            base_asset = symbol.replace("USDT", "")
            account = await self.client.get_account()
            
            for balance in account["balances"]:
                if balance["asset"] == base_asset:
                    qty = float(balance["free"]) + float(balance["locked"])
                    if qty > 0:
                        # Get current price
                        ticker = await self.client.get_symbol_ticker(symbol=symbol)
                        price = float(ticker["price"])
                        return Position(
                            symbol=symbol,
                            quantity=qty,
                            avg_entry_price=price,  # Spot doesn't track avg entry
                            current_price=price,
                            side="LONG"
                        )
            return None
        except Exception as e:
            print(f"Get position failed: {e}")
            return None
    
    async def get_positions(self) -> List[Position]:
        """Get all positions (non-zero balances)"""
        positions = []
        try:
            account = await self.client.get_account()
            
            # Get prices for all symbols
            tickers = await self.client.get_symbol_ticker()
            price_map = {t["symbol"]: float(t["price"]) for t in tickers}
            
            for balance in account["balances"]:
                qty = float(balance["free"]) + float(balance["locked"])
                if qty > 0 and balance["asset"] != "USDT":
                    symbol = f"{balance['asset']}USDT"
                    price = price_map.get(symbol, 0)
                    if price > 0:
                        positions.append(Position(
                            symbol=symbol,
                            quantity=qty,
                            avg_entry_price=price,
                            current_price=price,
                            side="LONG"
                        ))
        except Exception as e:
            print(f"Get positions failed: {e}")
        
        return positions
    
    async def get_balance(self) -> Balance:
        """Get account balance"""
        try:
            account = await self.client.get_account()
            balances = {}
            
            for bal in account["balances"]:
                asset = bal["asset"]
                free = float(bal["free"])
                locked = float(bal["locked"])
                if free > 0 or locked > 0:
                    balances[asset] = {
                        "free": free,
                        "locked": locked,
                        "total": free + locked
                    }
            
            # Calculate total in USDT
            usdt_balance = balances.get("USDT", {"total": 0})
            total = usdt_balance["total"]
            
            # Add value of other assets in USDT
            tickers = await self.client.get_symbol_ticker()
            price_map = {t["symbol"]: float(t["price"]) for t in tickers}
            
            for asset, bal in balances.items():
                if asset != "USDT":
                    symbol = f"{asset}USDT"
                    if symbol in price_map:
                        total += bal["total"] * price_map[symbol]
            
            return Balance(
                total_balance=total,
                available_balance=usdt_balance.get("free", 0),
                locked_balance=usdt_balance.get("locked", 0),
                currency="USDT",
                balances=balances
            )
        except Exception as e:
            print(f"Get balance failed: {e}")
            return Balance(total_balance=0, available_balance=0, locked_balance=0)
    
    async def get_ticker_price(self, symbol: str) -> float:
        """Get current price"""
        try:
            ticker = await self.client.get_symbol_ticker(symbol=symbol.upper())
            return float(ticker["price"])
        except Exception as e:
            print(f"Get ticker failed: {e}")
            return 0.0
    
    def get_symbol_info(self, symbol: str) -> dict:
        """Get symbol precision info"""
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        
        # Default precision for most pairs
        info = {
            "base_asset_precision": 8,
            "quote_precision": 8,
            "base_asset_step_size": 0.00001,
            "quote_asset_step_size": 0.01,
            "min_quantity": 0.00001,
            "min_notional": 10.0  # Minimum $10 order
        }
        
        self._symbol_info_cache[symbol] = info
        return info
    
    def _format_quantity(self, symbol: str, quantity: float) -> float:
        """Format quantity according to symbol precision"""
        info = self.get_symbol_info(symbol)
        step = info["base_asset_step_size"]
        return round(quantity / step) * step
    
    def _format_price(self, symbol: str, price: float) -> float:
        """Format price according to symbol precision"""
        info = self.get_symbol_info(symbol)
        step = info["quote_asset_step_size"]
        return round(price / step) * step
    
    def _parse_order(self, data: dict) -> Order:
        """Parse Binance order dict to Order object"""
        return Order(
            symbol=data["symbol"],
            side=OrderSide(data["side"]),
            type=OrderType(data["type"]),
            quantity=float(data["origQty"]),
            price=float(data.get("price", 0)) or None,
            time_in_force=data.get("timeInForce", "GTC"),
            client_order_id=data.get("clientOrderId")
        )
    
    async def close(self):
        """Close client connection"""
        if self.client:
            await self.client.close_connection()
```

---

### 4. Hyperliquid Adapter (`agents/execution/adapters/hyperliquid.py`)

```python
# ย้าย code เดิมจาก execution_agent.py มาที่นี่
# ปรับให้ inherit จาก ExchangeAdapter และ implement ทุก method

from ..adapters.base import ExchangeAdapter
from ..models.order import Order, OrderResult
from ..models.position import Position, Balance
from ..models.common import ExchangeCredentials

class HyperliquidAdapter(ExchangeAdapter):
    """Hyperliquid Testnet Adapter (เดิม)"""
    
    @property
    def name(self) -> str:
        return "Hyperliquid"
    
    async def initialize(self) -> bool:
        # Implementation เดิม
        pass
    
    async def place_order(self, order: Order) -> OrderResult:
        # Implementation เดิม
        pass
    
    # ... implement methods อื่นๆ ทั้งหมด
```

---

### 5. Update Execution Agent (`agents/execution/execution_agent.py`)

```python
import os
from typing import Optional
from .adapters.base import ExchangeAdapter
from .adapters.binance import BinanceAdapter
from .adapters.hyperliquid import HyperliquidAdapter
from .models.order import Order, OrderResult
from .models.common import ExchangeCredentials, OrderSide, OrderType
from .models.position import Position

class ExecutionAgent:
    def __init__(self, exchange: str = "binance"):
        self.exchange = exchange.lower()
        self.adapter: Optional[ExchangeAdapter] = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from .env"""
        if self.exchange == "binance":
            self.credentials = ExchangeCredentials(
                api_key=os.getenv("BINANCE_API_KEY"),
                api_secret=os.getenv("BINANCE_API_SECRET"),
                testnet=os.getenv("BINANCE_TESTNET", "true").lower() == "true"
            )
        elif self.exchange == "hyperliquid":
            self.credentials = ExchangeCredentials(
                api_key=os.getenv("HYPERLIQUID_API_KEY"),
                api_secret=os.getenv("HYPERLIQUID_API_SECRET"),
                testnet=True
            )
        else:
            raise ValueError(f"Unknown exchange: {self.exchange}")
    
    async def initialize(self) -> bool:
        """Initialize exchange adapter"""
        if self.exchange == "binance":
            self.adapter = BinanceAdapter(self.credentials)
        elif self.exchange == "hyperliquid":
            self.adapter = HyperliquidAdapter(self.credentials)
        else:
            return False
        
        return await self.adapter.initialize()
    
    async def execute_signal(self, signal: dict) -> OrderResult:
        """Execute trading signal"""
        # Logic เดิม保持不变，แค่เรียกผ่าน adapter
        symbol = signal.get("symbol", "BTCUSDT")
        side = OrderSide.BUY if signal.get("decision") == "LONG" else OrderSide.SELL
        quantity = signal.get("position_size", 0.001)
        
        order = Order(
            symbol=symbol,
            side=side,
            type=OrderType.MARKET,
            quantity=quantity
        )
        
        return await self.adapter.place_order(order)
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        return await self.adapter.get_position(symbol)
    
    async def get_balance(self):
        return await self.adapter.get_balance()
```

---

### 6. Configuration (`config/exchange_config.py`)

```python
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExchangeConfig:
    name: str
    testnet: bool
    api_key: str
    api_secret: str
    endpoint: Optional[str] = None
    
    @classmethod
    def from_env(cls, exchange: str = "binance"):
        if exchange.lower() == "binance":
            return cls(
                name="binance",
                testnet=os.getenv("BINANCE_TESTNET", "true").lower() == "true",
                api_key=os.getenv("BINANCE_API_KEY", ""),
                api_secret=os.getenv("BINANCE_API_SECRET", ""),
                endpoint=os.getenv("BINANCE_ENDPOINT")
            )
        elif exchange.lower() == "hyperliquid":
            return cls(
                name="hyperliquid",
                testnet=True,
                api_key=os.getenv("HYPERLIQUID_API_KEY", ""),
                api_secret=os.getenv("HYPERLIQUID_API_SECRET", ""),
                endpoint="https://api.hyperliquid-testnet.xyz"
            )
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

# Global config
EXCHANGE = os.getenv("ACTIVE_EXCHANGE", "binance")
config = ExchangeConfig.from_env(EXCHANGE)
```

---

## 📝 Configuration Files

### `.env` (Updated)
```bash
# Active Exchange
ACTIVE_EXCHANGE=binance

# Binance Spot Testnet
# Get credentials from: https://testnet.binance.vision/
BINANCE_TESTNET=true
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_secret
# BINANCE_ENDPOINT=https://testnet.binance.vision  # Optional

# Hyperliquid Testnet (เก็บไว้สำหรับสลับกลับ)
HYPERLIQUID_API_KEY=your_hyperliquid_key
HYPERLIQUID_API_SECRET=your_hyperliquid_secret

# Trading Config (เดิม)
TRADING_PAIRS=BTCUSDT,ETHUSDT,BNBUSDT
RISK_PER_TRADE=0.02
DAILY_LOSS_LIMIT=0.05
```

### `requirements.txt` (Updated)
```txt
# Existing
python-dotenv==1.0.0
aiohttp==3.9.1
aiosqlite==0.19.0

# Remove
# hyperliquid-python-sdk

# Add
python-binance==1.0.19  # Binance SDK
websockets==12.0        # For Binance WebSocket
```

---

## 🚀 Migration Steps

### Phase 1: Setup (30 นาที)
```bash
# 1. สร้าง folder structure
cd /Users/nunamzza/projects/trading/openclaw-trading-agents
mkdir -p agents/execution/adapters
mkdir -p agents/execution/models
mkdir -p tests/adapters

# 2. ติดตั้ง dependencies
pip uninstall hyperliquid-python-sdk
pip install python-binance==1.0.19 websockets==12.0

# 3. สร้าง Binance Testnet Account
# ไปที่: https://testnet.binance.vision/
# กด "Generate HMAC_SHA256 Key"
# เก็บ API Key & Secret
```

### Phase 2: Implement Core (2-3 ชั่วโมง)
```bash
# 1. สร้าง models
touch agents/execution/models/{__init__,common,order,position}.py

# 2. สร้าง interface
touch agents/execution/adapters/{__init__,base}.py

# 3. สร้าง Binance adapter
touch agents/execution/adapters/binance.py

# 4. ย้าย Hyperliquid code
# copy execution_agent.py เดิม → adapters/hyperliquid.py
# ปรับให้ inherit จาก ExchangeAdapter
```

### Phase 3: Integration (1-2 ชั่วโมง)
```bash
# 1. แก้ execution_agent.py ให้ใช้ adapter
# 2. แก้ config/exchange_config.py
# 3. อัพเดท .env ด้วย Binance credentials
# 4. ทดสอบ connection
python -c "from agents.execution.execution_agent import ExecutionAgent; import asyncio; asyncio.run(ExecutionAgent('binance').initialize())"
```

### Phase 4: Testing (1 ชั่วโมง)
```bash
# 1. ทดสอบ balance
python -c "from agents.execution.execution_agent import ExecutionAgent; import asyncio; agent = ExecutionAgent('binance'); asyncio.run(agent.initialize()); print(asyncio.run(agent.get_balance()))"

# 2. ทดสอบ price feed
python -c "from agents.execution.execution_agent import ExecutionAgent; import asyncio; agent = ExecutionAgent('binance'); asyncio.run(agent.initialize()); print(asyncio.run(agent.adapter.get_ticker_price('BTCUSDT')))"

# 3. ทดสอบ order (เล็กๆ)
# ใช้ order size น้อยมาก (0.0001 BTC) เพื่อ test
```

### Phase 5: Deploy (30 นาที)
```bash
# 1. Commit changes
git add -A
git commit -m "Refactor: Implement Exchange Adapter Pattern with Binance support"

# 2. Update orchestrator
# แก้ orchestrator.py ให้ส่ง exchange parameter

# 3. Restart bot
# ถ้าใช้ systemd หรือ supervisor ให้ restart service
# หรือถ้าใช้ cron ให้รอ cycle ถัดไป
```

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/adapters/test_binance_adapter.py
import pytest
from agents.execution.adapters.binance import BinanceAdapter
from agents.execution.models.common import ExchangeCredentials
from agents.execution.models.order import Order, OrderSide, OrderType

@pytest.fixture
def adapter():
    creds = ExchangeCredentials(
        api_key="test_key",
        api_secret="test_secret",
        testnet=True
    )
    return BinanceAdapter(creds)

@pytest.mark.asyncio
async def test_get_balance(adapter):
    await adapter.initialize()
    balance = await adapter.get_balance()
    assert balance.total_balance >= 0

@pytest.mark.asyncio
async def test_get_ticker(adapter):
    await adapter.initialize()
    price = await adapter.get_ticker_price("BTCUSDT")
    assert price > 0
```

### Integration Tests
```bash
# ทดสอบ end-to-end cycle
python tests/integration/test_full_cycle.py

# ทดสอบ failover (สลับ exchange)
python tests/integration/test_exchange_failover.py
```

---

## ⚠️ Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| API Rate Limits | Medium | Implement retry logic + exponential backoff |
| Order Rejection | Medium | Validate order params before sending |
| Network Issues | Low | Add connection pooling + auto-reconnect |
| Wrong Credentials | High | Test with small order first |
| Symbol Format | Low | Add symbol normalization layer |

---

## 📊 Success Criteria

- ✅ All 6 agents运行ปกติ
- ✅ Can place/cancel orders on Binance Testnet
- ✅ Balance & position tracking works
- ✅ Can switch between Binance/Hyperliquid via config
- ✅ All existing tests pass
- ✅ No data loss in migration

---

## 🎯 Next Actions

1. **ยืนยัน:** ต้องการเริ่มทำเลยไหม?
2. **Binance Credentials:** ได้สร้าง testnet account แล้วหรือยัง?
3. **Timeline:** ต้องการเสร็จเมื่อไหร่?

พร้อมเริ่มครับ! 🚀

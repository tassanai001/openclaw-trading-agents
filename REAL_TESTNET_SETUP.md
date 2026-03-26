# 🚀 Real Testnet Trading Setup Guide

## ✅ สถานะปัจจุบัน

| รายการ | สถานะ |
|--------|--------|
| **API Wallet Configured** | ✅ Done |
| **Wallet Address** | `0x6f3286917229781d7e1314b0e66b7d6e8d56b951` |
| **SDK Integration** | ✅ hyperliquid-python-sdk v0.22.0 |
| **DRY_RUN** | `false` (Real Trading Mode) |
| **Account Balance** | ⚠️ **$0.00** (ต้อง claim USDC) |

---

## ⚠️ สิ่งที่ต้องทำก่อนเริ่มเทรด

### Wallet ของคุณยังไม่มีเงิน! ต้อง Claim Testnet USDC ก่อน

**ขั้นตอนที่ 1: Claim Testnet USDC**

1. เข้าลิงก์: https://app.hyperliquid-testnet.xyz/drip
2. Connect Wallet ด้วย Address: `0x6f3286917229781d7e1314b0e66b7d6e8d56b951`
3. Claim **1,000 USDC** (ฟรี สำหรับ testnet)

**ขั้นตอนที่ 2: ตรวจสอบ Balance**

หลังจาก claim แล้ว ตรวจสอบได้ที่:
- https://app.hyperliquid-testnet.xyz
- หรือรันคำสั่ง:
```bash
cd /Users/nunamzza/projects/trading/openclaw-trading-agents
python3 -c "
from hyperliquid.info import Info
info = Info(base_url='https://api.hyperliquid-testnet.xyz')
data = info.user_state('0x6f3286917229781d7e1314b0e66b7d6e8d56b951')
print('Balance:', data['marginSummary']['accountValue'])
"
```

---

## 📋 การตั้งค่า .env (เสร็จแล้ว)

```bash
# Hyperliquid API (Testnet)
HYPERLIQUID_API_KEY=0x6f3286917229781d7e1314b0e66b7d6e8d56b951
HYPERLIQUID_API_SECRET=0x076019d7e771ca0460e300ef27956de000b4b9d59876f78dc889d681b5e77deb
HYPERLIQUID_WALLET_ADDRESS=0x6f3286917229781d7e1314b0e66b7d6e8d56b951

# Trading Mode
TRADING_MODE=testnet
DRY_RUN=false  # Real trading enabled!
```

---

## 🎯 วิธีเริ่ม Bot

```bash
cd /Users/nunamzza/projects/trading/openclaw-trading-agents
python3 orchestrator.py
```

Bot จะ:
- ✅ สแกนตลาดทุก 5 นาที
- ✅ วิเคราะห์ Sentiment
- ✅ ตัดสินใจเทรดตาม Supertrend + Sentiment
- ✅ เปิด/ปิด Order อัตโนมัติ (เมื่อมี signal)

---

## 📊 ตรวจสอบสถานะ

### ดู Balance
```bash
python3 -c "
from hyperliquid.info import Info
info = Info(base_url='https://api.hyperliquid-testnet.xyz')
data = info.user_state('0x6f3286917229781d7e1314b0e66b7d6e8d56b951')
print('Account Value:', data['marginSummary']['accountValue'])
print('Available USDC:', data['marginSummary']['totalRawUsd'])
"
```

### ดู Positions
```bash
python3 -c "
from hyperliquid.info import Info
info = Info(base_url='https://api.hyperliquid-testnet.xyz')
data = info.user_state('0x6f3286917229781d7e1314b0e66b7d6e8d56b951')
for pos in data.get('assetPositions', []):
    print(pos)
"
```

### ดู Trades ใน Database
```bash
sqlite3 trading.db "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;"
```

---

## ⚠️ หมายเหตุสำคัญ

1. **นี่คือ Testnet** - ใช้เงินจำลอง ไม่ใช่เงินจริง
2. **ต้อง Claim USDC ก่อน** - Bot จะไม่เทรดถ้าไม่มีเงิน
3. **Bot รันทุก 5 นาที** - จะสแกนและตัดสินใจอัตโนมัติ
4. **Risk Management** - 2% ต่อ trade, 5% daily loss limit

---

## 🔧 Troubleshooting

### Bot ไม่เทรด
- ✅ ตรวจสอบ Balance: ต้องมี USDC ใน wallet
- ✅ ตรวจสอบ Signal: ต้องแรงกว่า ±0.2 ถึงจะเทรด
- ✅ ดู Log: `tail -f logs/*.log`

### Order ไม่ผ่าน
- ✅ ตรวจสอบ Balance: ต้องมีเงินพอ
- ✅ ตรวจสอบ Min Order Size: อย่างน้อย $10
- ✅ ดู Error Log: `logs/paper_trades.log` หรือ `logs/*.log`

### SDK Error
ถ้าเจอ error แบบ `IndexError: list index out of range`:
- นี่เป็น known issue กับ testnet metadata
- Bot จะ fallback ไปใช้ paper trading อัตโนมัติ
- เมื่อมี balance แล้วจะทำงานปกติ

---

## 📞 ติดต่อ/ช่วยเหลือ

- 📚 Hyperliquid Docs: https://hyperliquid.gitbook.io
- 💬 Discord: https://discord.gg/hyperliquid
- 🚰 Testnet Faucet: https://app.hyperliquid-testnet.xyz/drip

---

**Last Updated:** 2026-03-26 17:11 GMT+7

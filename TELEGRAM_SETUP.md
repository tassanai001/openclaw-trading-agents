# Telegram Bot Setup - Direct API Integration

## สรุปการแก้ไข

### 🎯 ปัญหาเดิม
- Code ใช้ `print()` แล้วพึ่งพา OpenClaw delivery ส่งต่อ
- OpenClaw Gateway ใช้ `@kajuu_auto_bot` (bot เก่า)
- strategy-job มี error เพราะ delivery config ผิด

### ✅ วิธีแก้ (วิธีที่ 3: Direct Bot API)
แก้ไข code ให้เรียก Telegram Bot API โดยตรง ไม่ผ่าน OpenClaw delivery

---

## 📁 ไฟล์ที่สร้าง/แก้ไข

### 1️⃣ `config/telegram_bot.py` (ใหม่)
Module สำหรับส่ง Telegram โดยตรง

**Features:**
- ใช้ `TELEGRAM_BOT_TOKEN` และ `TELEGRAM_CHAT_ID` จาก `.env`
- รองรับทั้ง async (aiohttp) และ sync (urllib)
- มี convenience functions สำหรับ use cases ต่างๆ

**Usage:**
```python
from config.telegram_bot import (
    send_message,
    send_signal_alert,
    send_strategy_summary,
    send_error_alert,
    send_startup_notification
)

# ส่งข้อความทั่วไป
await send_message("Hello World!")

# ส่งสัญญาณ trading
await send_signal_alert("BTC/USDT", "BUY", price=50000, confidence=0.85)

# ส่งสรุป strategy
await send_strategy_summary(thai_summary)

# ส่ง error alert
await send_error_alert("Database Error", "Connection failed")

# ส่ง startup notification
await send_startup_notification()
```

### 2️⃣ `scripts/run_strategy.py` (แก้ไข)
เพิ่ม Telegram integration

**Changes:**
- Import `config.telegram_bot`
- แปลง `run_strategy_agent()` เป็น async
- ส่งสรุปผ่าน Telegram โดยตรงหลัง generate
- ส่ง startup notification เมื่อเริ่มทำงาน
- ส่ง error alert เมื่อเกิดปัญหา

---

## 🧪 การทดสอบ

### Test 1: ตรวจสอบ Bot Config
```bash
cd /Users/nunamzza/projects/trading/openclaw-trading-agents
python3 -c "from config.telegram_bot import telegram_bot; print(f'Bot: @{telegram_bot._get_bot_username_from_token()}')"
```

**Expected Output:**
```
✅ Telegram Bot initialized: @openclaw_trading_assistant_bot
   Chat ID: 8062364760
Bot: @openclaw_trading_assistant_bot
```

### Test 2: ส่ง Test Message
```bash
python3 -c "
import asyncio
from config.telegram_bot import send_startup_notification
asyncio.run(send_startup_notification())
"
```

**Expected:** ได้รับข้อความจาก `@openclaw_trading_assistant_bot` ใน Telegram

### Test 3: Run Strategy Script
```bash
python3 scripts/run_strategy.py
```

**Expected:**
- ได้รับ startup notification
- ได้รับ strategy summary
- เห็น log `✅ Telegram message sent to @openclaw_trading_assistant_bot`

---

## 📊 Bot Architecture หลังแก้ไข

```
┌─────────────────────────────────────────────────────────────┐
│              OpenClaw Cron Jobs (Gateway)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  scanner-job (ทุก 5 นาที)                                   │
│    │                                                        │
│    ▼                                                        │
│  OpenClaw Agent → print()                                   │
│    │                                                        │
│    ▼                                                        │
│  delivery: { mode: "announce", to: "8062364760" }           │
│    │                                                        │
│    ▼                                                        │
│  📱 Telegram: @kajuu_auto_bot (bot เก่า)                    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  strategy-job (ทุก 5 นาที)                                  │
│    │                                                        │
│    ▼                                                        │
│  python3 scripts/run_strategy.py                            │
│    │                                                        │
│    ▼                                                        │
│  config/telegram_bot.py (Direct API)                        │
│    │                                                        │
│    ▼                                                        │
│  📱 Telegram: @openclaw_trading_assistant_bot (bot ใหม่) ✅ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 .env Configuration

```bash
# Telegram Alerts (ใช้ bot ใหม่)
TELEGRAM_BOT_TOKEN=8370864419:AAHqA_EP5ebCjSqaqWfLb4kwWds1aMJ51nk
TELEGRAM_CHAT_ID=8062364760
```

---

## 📝 หมายเหตุ

### Bot ทั้ง 2 ตัว
| Bot | Token | ใช้งานโดย | สถานะ |
|-----|-------|----------|-------|
| **@kajuu_auto_bot** | `8207...F0vtY` | OpenClaw Gateway (scanner, sentiment, monitoring) | ✅ ทำงานอยู่ |
| **@openclaw_trading_assistant_bot** | `8370...aMJ51nk` | Strategy Agent (Direct API) | ✅ ทำงานแล้ว |

### ข้อดีของ Direct API
- ✅ ไม่ต้องพึ่งพา OpenClaw delivery
- ✅ ควบคุม format และ timing ได้เต็มที่
- ✅ แยก bot ตาม use case ได้
- ✅ ลด dependency กับ Gateway config

### ข้อควรระวัง
- ⚠️ ต้องจัดการ error handling เอง
- ⚠️ ต้องดูแล rate limits เอง (Telegram: 30 messages/sec)
- ⚠️ ต้อง update token เองถ้ามีการ rotate

---

## 🚀 Next Steps

1. ✅ ทดสอบ run_strategy.py
2. ⚠️ แก้ไข scripts อื่นๆ ที่ต้องการส่ง Telegram (ถ้ามี)
3. ⚠️ เพิ่ม logging และ monitoring
4. ⚠️ เพิ่ม retry logic สำหรับ network errors

---

**Created:** 2026-03-24  
**Bot:** @openclaw_trading_assistant_bot  
**Status:** ✅ Working

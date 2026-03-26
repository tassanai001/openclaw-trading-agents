# Migration to Direct Telegram API

## สรุปการย้ายจาก OpenClaw Delivery → Direct Bot API

### 📅 วันที่: 2026-03-24

---

## ✅ สิ่งที่ทำเสร็จแล้ว

### 1️⃣ ปิด Cron Jobs เก่า (OpenClaw Delivery)

| Job ID | Name | สถานะเดิม | สถานะใหม่ |
|--------|------|----------|----------|
| `aaae910c-706d-4c82-9ca0-6e2a9c619454` | scanner-job | ✅ Enabled | ❌ **Disabled** |
| `f711e4b2-d8f3-4528-a335-853fbc552cb4` | sentiment-job | ✅ Enabled | ❌ **Disabled** |

**เหตุผล:** ใช้ OpenClaw delivery → @kajuu_auto_bot (bot เก่า)

---

### 2️⃣ สร้าง Scripts ใหม่ (Direct API)

#### `scripts/run_scanner.py` (ใหม่)
- สแกนตลาดทุก 5 นาที
- ส่งสรุปผ่าน Telegram โดยตรง
- ส่ง BUY signals แยกแต่ละคู่
- ใช้ bot: **@openclaw_trading_assistant_bot**

**Features:**
- ✅ Startup notification
- ✅ Summary พร้อมสัญญาณทั้งหมด
- ✅ Individual BUY alerts
- ✅ Error handling
- ✅ Logging to JSONL

#### `scripts/run_sentiment.py` (ใหม่)
- วิเคราะห์ sentiment ทุก 5 นาที
- Fetch Fear & Greed Index
- ส่งสรุปผ่าน Telegram โดยตรง
- ใช้ bot: **@openclaw_trading_assistant_bot**

**Features:**
- ✅ Startup notification
- ✅ F&G Index summary
- ✅ Combined sentiment score
- ✅ Error handling
- ✅ Logging to JSONL
- ✅ Save Markdown report

#### `scripts/run_strategy.py` (แก้ไข)
- เพิ่ม Direct API integration
- ส่ง strategy summary ผ่าน Telegram
- ใช้ bot: **@openclaw_trading_assistant_bot**

---

### 3️⃣ สร้าง Module กลาง

#### `config/telegram_bot.py` (ใหม่)
Telegram Bot wrapper สำหรับส่งข้อความโดยตรง

**Functions:**
```python
await send_message(message)                    # ส่งข้อความทั่วไป
await send_signal_alert(pair, signal, ...)     # ส่งสัญญาณ trading
await send_strategy_summary(summary)           # ส่งสรุป strategy
await send_error_alert(type, message)          # ส่ง error alert
await send_startup_notification()              # ส่ง startup msg
```

**Config:**
```bash
TELEGRAM_BOT_TOKEN=8370864419:AAHqA_EP5ebCjSqaqWfLb4kwWds1aMJ51nk
TELEGRAM_CHAT_ID=8062364760
```

---

### 4️⃣ สร้าง Cron Jobs ใหม่

| Job ID | Name | Schedule | Delivery | Bot |
|--------|------|----------|----------|-----|
| `a36e977e-e938-4de9-bd34-108e1cc37dd8` | scanner-direct | */5 * * * * | none (Direct API) | @openclaw_trading_assistant_bot |
| `cf08c102-b08e-4e9a-b74f-d58eb1f7d9b7` | sentiment-direct | */5 * * * * | none (Direct API) | @openclaw_trading_assistant_bot |
| (existing) | strategy-job | */5 * * * * | none (Direct API) | @openclaw_trading_assistant_bot |

**Note:** `delivery.mode: "none"` เพราะ scripts ส่ง Telegram เอง

---

## 📊 Architecture หลัง Migration

```
┌─────────────────────────────────────────────────────────────┐
│              OpenClaw Cron Jobs (Gateway)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  scanner-direct (ทุก 5 นาที)                                │
│    │                                                        │
│    ▼                                                        │
│  python3 scripts/run_scanner.py                             │
│    │                                                        │
│    ▼                                                        │
│  config/telegram_bot.py (Direct API)                        │
│    │                                                        │
│    ▼                                                        │
│  📱 Telegram: @openclaw_trading_assistant_bot ✅            │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  sentiment-direct (ทุก 5 นาที)                              │
│    │                                                        │
│    ▼                                                        │
│  python3 scripts/run_sentiment.py                           │
│    │                                                        │
│    ▼                                                        │
│  config/telegram_bot.py (Direct API)                        │
│    │                                                        │
│    ▼                                                        │
│  📱 Telegram: @openclaw_trading_assistant_bot ✅            │
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
│  📱 Telegram: @openclaw_trading_assistant_bot ✅            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 การทดสอบ

### Test 1: Scanner
```bash
cd /Users/nunamzza/projects/trading/openclaw-trading-agents
python3 scripts/run_scanner.py
```

**Result:** ✅ ส่งข้อความสำเร็จ (เห็น `✅ Telegram message sent`)

### Test 2: Sentiment
```bash
python3 scripts/run_sentiment.py
```

**Result:** ✅ ส่งข้อความสำเร็จ

### Test 3: Strategy
```bash
python3 scripts/run_strategy.py
```

**Result:** ✅ ส่งข้อความสำเร็จ

---

## 📱 ตัวอย่างข้อความที่ส่ง

### Scanner Summary
```
🔍 Scanner Agent Summary (19:40)

สถานะ: ✅ สำเร็จ

สัญญาณที่พบ:
• 🟢 BUY: 8
• 🔴 SELL: 0
• ⚪ HOLD: 7
• ❌ Error: 0

รายละเอียด:
• BTC/USDT: 5m: 🟢 | 15m: 🟢 | 1h: ⚪ | 4h: 🟢 | 1d: 🟢
• ETH/USDT: 5m: 🟢 | 15m: 🟢 | 1h: ⚪ | 4h: ⚪ | 1d: ⚪
• BNB/USDT: 5m: 🟢 | 15m: ⚪ | 1h: 🟢 | 4h: 🟢 | 1d: ⚪

รอบถัดไป: อีก 5 นาที
```

### Sentiment Summary
```
🐦 Sentiment Agent Summary (19:40)

สถานะ: ✅ สำเร็จ

Fear & Greed Index:
• Score: 11/100 (Extreme Fear 🔴)

Combined Sentiment:
• Score: -0.390
• Signal: ลบแข็ง (Bearish) 🔴

รอบถัดไป: อีก 5 นาที
```

---

## 📝 Logs

### Scanner Logs
`logs/scanner_runs.jsonl`

```json
{"timestamp": "2026-03-24T19:40:44.123456", "job": "scanner-job", "status": "completed", "results_summary": {"pairs_scanned": 3, "buy_signals": 8}}
```

### Sentiment Logs
`logs/sentiment_runs.jsonl`

```json
{"timestamp": "2026-03-24T19:40:36.123456", "job": "sentiment-job", "status": "completed", "sentiment_score": -0.39, "fng_value": 11}
```

---

## ⚠️ หมายเหตุ

### Bot ที่ใช้
| Bot | Token | ใช้งานโดย |
|-----|-------|----------|
| **@openclaw_trading_assistant_bot** | `8370...aMJ51nk` | Scanner, Sentiment, Strategy (Direct API) ✅ |
| **@kajuu_auto_bot** | `8207...F0vtY` | OpenClaw Gateway (monitoring-job) ⚠️ |

### ข้อดีของ Direct API
- ✅ ควบคุม bot ได้เต็มที่ (ใช้ bot ใหม่)
- ✅ ไม่ต้องพึ่งพา OpenClaw delivery
- ✅ Format ข้อความ customize ได้
- ✅ ส่ง multiple messages ได้ (เช่น แยก BUY alerts)
- ✅ Error handling ดีกว่า

### ข้อควรระวัง
- ⚠️ ต้องจัดการ rate limits เอง (Telegram: 30 msg/sec)
- ⚠️ ต้องดูแล error handling เอง
- ⚠️ Token rotation ต้อง update เอง

---

## 🚀 Next Steps

### Done ✅
- [x] สร้าง `config/telegram_bot.py`
- [x] แก้ไข `scripts/run_strategy.py`
- [x] สร้าง `scripts/run_scanner.py`
- [x] สร้าง `scripts/run_sentiment.py`
- [x] ปิด cron jobs เก่า
- [x] สร้าง cron jobs ใหม่
- [x] ทดสอบการทำงาน

### TODO ⏳
- [ ] แก้ไข `scripts/run_strategy.py` ให้ใช้ agents จริง (ไม่ใช่ mock)
- [ ] เพิ่ม retry logic สำหรับ network errors
- [ ] เพิ่ม monitoring และ alerting
- [ ] ปิด @kajuu_auto_bot ถ้าไม่ใช้แล้ว

---

## 📞 Support

ถ้ามีปัญหา:
1. ตรวจสอบ `.env` config
2. ดู logs: `logs/*.jsonl`
3. ทดสอบ manual: `python3 scripts/run_*.py`
4. ตรวจสอบ Telegram Bot API status

---

**Migration Completed:** 2026-03-24 07:40 ICT  
**Status:** ✅ SUCCESS  
**Bot:** @openclaw_trading_assistant_bot

"""
Telegram Bot - Direct API Integration
ส่งการแจ้งเตือนผ่าน Telegram Bot API โดยตรง
ไม่พึ่งพา OpenClaw delivery
"""

import os
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TelegramBot:
    """Telegram Bot สำหรับส่งการแจ้งเตือน"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if self.enabled:
            # ตรวจสอบว่าเป็น bot ไหน
            bot_username = self._get_bot_username_from_token()
            print(f"✅ Telegram Bot initialized: @{bot_username}")
            print(f"   Chat ID: {self.chat_id}")
        else:
            print("⚠️  Telegram Bot not configured (missing token or chat_id)")

    def _get_bot_username_from_token(self) -> str:
        """ดึง username จาก token (ส่วนก่อนหน้า : คือ bot ID)"""
        if not self.bot_token:
            return "unknown"
        
        bot_id = self.bot_token.split(":")[0]
        
        # Mapping bot IDs to usernames
        bot_mapping = {
            "8207420751": "kajuu_auto_bot",
            "8370864419": "openclaw_trading_assistant_bot",
        }
        
        return bot_mapping.get(bot_id, f"bot_{bot_id}")

    async def send_message(
        self,
        message: str,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        ส่งข้อความไปยัง Telegram
        
        Args:
            message: ข้อความที่จะส่ง (รองรับ HTML/Markdown)
            parse_mode: "HTML" หรือ "Markdown"
            
        Returns:
            True ถ้าส่งสำเร็จ, False ถ้าล้มเหลว
        """
        
        if not self.enabled:
            print(f"[Telegram] {message}")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get("ok"):
                        print(f"✅ Telegram message sent to @{self._get_bot_username_from_token()}")
                        return True
                    else:
                        error = result.get("description", "Unknown error")
                        print(f"❌ Telegram API Error: {error}")
                        return False
                        
        except ImportError:
            # Fallback ใช้ urllib ถ้าไม่มี aiohttp
            return self._send_message_sync(message, parse_mode)
        except Exception as e:
            print(f"❌ Telegram Error: {e}")
            return False

    def _send_message_sync(
        self,
        message: str,
        parse_mode: str = "HTML"
    ) -> bool:
        """ส่งข้อความแบบ synchronous (fallback)"""
        
        import urllib.request
        import urllib.error
        import json
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get("ok"):
                    print(f"✅ Telegram message sent to @{self._get_bot_username_from_token()}")
                    return True
                else:
                    error = result.get("description", "Unknown error")
                    print(f"❌ Telegram API Error: {error}")
                    return False
                    
        except urllib.error.HTTPError as e:
            print(f"❌ Telegram HTTP Error: {e.code} - {e.reason}")
            return False
        except Exception as e:
            print(f"❌ Telegram Error: {e}")
            return False

    async def send_signal_alert(
        self,
        pair: str,
        signal: str,
        price: Optional[float] = None,
        confidence: Optional[float] = None
    ) -> bool:
        """ส่งการแจ้งเตือนสัญญาณ trading"""
        
        emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"
        
        message = f"""{emoji} <b>TRADING SIGNAL</b>

<b>Pair:</b> {pair}
<b>Signal:</b> {signal}
"""
        
        if price:
            message += f"<b>Price:</b> ${price:,.2f}\n"
        
        if confidence:
            message += f"<b>Confidence:</b> {confidence:.1f}%\n"
        
        message += f"\n<b>Time:</b> {asyncio.get_event_loop().time()}"
        
        return await self.send_message(message)

    async def send_strategy_summary(
        self,
        summary: str
    ) -> bool:
        """ส่งสรุป Strategy Agent"""
        return await self.send_message(summary)

    async def send_error_alert(
        self,
        error_type: str,
        message: str
    ) -> bool:
        """ส่งการแจ้งเตือน error"""
        
        msg = f"""❌ <b>ERROR ALERT</b>

<b>Type:</b> {error_type}
<b>Message:</b> {message}

<b>Time:</b> {asyncio.get_event_loop().time()}"""
        
        return await self.send_message(msg)

    async def send_startup_notification(self) -> bool:
        """ส่งการแจ้งเตือนเมื่อ bot เริ่มทำงาน"""
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        message = f"""🤖 <b>Trading Agents Online</b>

<b>Bot:</b> @{self._get_bot_username_from_token()}
<b>Time:</b> {timestamp}
<b>Status:</b> ✅ Ready

รอบสแกนถัดไป: อีก 5 นาที
"""
        
        return await self.send_message(message)


# Global instance
telegram_bot = TelegramBot()


# Convenience functions
async def send_message(message: str, parse_mode: str = "HTML") -> bool:
    """ส่งข้อความ (convenience function)"""
    return await telegram_bot.send_message(message, parse_mode)


async def send_signal_alert(pair: str, signal: str, **kwargs) -> bool:
    """ส่งสัญญาณ trading (convenience function)"""
    return await telegram_bot.send_signal_alert(pair, signal, **kwargs)


async def send_strategy_summary(summary: str) -> bool:
    """ส่งสรุป strategy (convenience function)"""
    return await telegram_bot.send_strategy_summary(summary)


async def send_error_alert(error_type: str, message: str) -> bool:
    """ส่ง error alert (convenience function)"""
    return await telegram_bot.send_error_alert(error_type, message)


async def send_startup_notification() -> bool:
    """ส่ง startup notification (convenience function)"""
    return await telegram_bot.send_startup_notification()


if __name__ == "__main__":
    # Test
    async def test():
        print("Testing Telegram Bot...")
        await telegram_bot.send_startup_notification()
        
    asyncio.run(test())

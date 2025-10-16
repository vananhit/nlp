import httpx
from backend.core.config import settings
import traceback

async def send_telegram_message(message: str):
    """
    Gửi tin nhắn thông báo đến một chat Telegram cụ thể thông qua Bot.

    Args:
        message (str): Nội dung tin nhắn cần gửi.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        print("Telegram token hoặc chat ID chưa được cấu hình. Bỏ qua việc gửi thông báo.")
        return

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"  # Hỗ trợ định dạng Markdown
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=payload)
            response.raise_for_status()  # Ném exception nếu request không thành công (status code 4xx hoặc 5xx)
        except httpx.RequestError as e:
            print(f"Lỗi khi gửi yêu cầu đến Telegram: {e}")
        except httpx.HTTPStatusError as e:
            print(f"Lỗi HTTP từ Telegram: {e.response.status_code} - {e.response.text}")

async def notify_exception(e: Exception, context: str = "Không có context cụ thể"):
    """
    Định dạng và gửi thông báo lỗi chi tiết đến Telegram.

    Args:
        e (Exception): Đối tượng exception đã bắt được.
        context (str): Mô tả ngữ cảnh nơi lỗi xảy ra.
    """
    # Lấy traceback chi tiết
    tb_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    
    # Giới hạn độ dài của traceback để tránh tin nhắn quá dài
    max_tb_length = 3000
    if len(tb_str) > max_tb_length:
        tb_str = tb_str[-max_tb_length:]
        tb_str = f"... (traceback bị cắt bớt)\n{tb_str}"

    message = (
        f"*🚨 Đã xảy ra lỗi trong ứng dụng SEO Tool 🚨*\n\n"
        f"*Ngữ cảnh:*\n`{context}`\n\n"
        f"*Loại lỗi:*\n`{type(e).__name__}`\n\n"
        f"*Thông điệp lỗi:*\n`{str(e)}`\n\n"
        f"*Traceback:*\n```\n{tb_str}\n```"
    )
    
    await send_telegram_message(message)

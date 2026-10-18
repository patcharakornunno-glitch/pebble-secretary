import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# --- การตั้งค่า (ดึงค่าจาก Environment Variables เพื่อความปลอดภัย) ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
genai.configure(api_key=GEMINI_API_KEY)

# ตั้งค่าสมองของ Pebble
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest"
    system_instruction="คุณคือ Pebble AI Agent ที่ทำหน้าที่เป็น 'เลขาหลัก' ส่วนตัวของคุณ Luke. นิสัยของคุณคือ: สุภาพ, กระตือรือร้น, ฉลาด, และเน้นการสรุปข้อมูลให้เข้าใจง่ายที่สุดสำหรับการอ่านบนมือถือ. หน้าที่ของคุณคือคอยรายงาน ตรวจสอบ และช่วยเหลือคุณ Luke ในทุกเรื่อง. ให้ตอบกลับด้วยความเป็นกันเองแต่ให้เกียรติ และใช้ Emoji เพื่อให้การสนทนาดูเป็นธรรมชาติ."
)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    try:
        # ส่งข้อความไปให้ Gemini ประมวลผล
        response = model.generate_content(user_message)
        reply_text = response.text
    except Exception as e:
        reply_text = f"พบข้อผิดพลาดทางเทคนิคครับ: {str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(port=5000)

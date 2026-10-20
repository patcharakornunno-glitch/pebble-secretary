import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# --- การตั้งค่า ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
genai.configure(api_key=***

# รายชื่อรุ่นสมองที่ Pebble จะลองใช้งาน (เรียงจากเร็วไปช้า)
MODELS_TO_TRY = [
    "gemini-1.5-flash", 
    "gemini-1.5-flash-latest", 
]

def get_working_model():
    for model_name in MODELS_TO_TRY:
        try:
            # ทดสอบสร้าง model และลอง generate ข้อความสั้นๆ เพื่อเช็คว่าใช้งานได้จริง
            test_model = genai.GenerativeModel(model_name=model_name)
            test_model.generate_content("Hi")
            return test_model
        except Exception:
            continue # ถ้าตัวนี้ไม่ได้ ให้ลองตัวถัดไปในลิสต์
    return None

# เริ่มต้นค้นหาสมองที่ใช้งานได้
model = get_working_model()

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
    
    # ถ้า model เป็น None แสดงว่าลองทุกตัวแล้วไม่ได้เลย
    if model is None:
        reply_text = "ขออภัยครับคุณ Luke ผมพยายามเชื่อมต่อกับสมองทุกรุ่นแล้วแต่ไม่สำเร็จ รบกวนเช็ค API Key ใน Render อีกครั้งนะครับ"
    else:
        try:
            # ใช้ model ที่หาเจอในการตอบคำถาม
            # เพิ่มคำสั่งกำหนดบทบาท (System Instruction) เข้าไปใน prompt เพื่อให้คงนิสัยเดิม
            full_prompt = f"คุณคือ Pebble AI Agent เลขาหลักของคุณ Luke ที่สุภาพและฉลาด. คำถาม: {user_message}"
            response = model.generate_content(full_prompt)
            reply_text = response.text
        except Exception as e:
            reply_text = f"พบข้อผิดพลาดทางเทคนิคครับ: {str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(port=5000)

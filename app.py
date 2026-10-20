import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import google.generativeai as genai
import PIL.Image
import io

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('models/gemini-3.5-flash')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# HANDLE TEXT MESSAGES
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    try:
        response = model.generate_content(event.message.text)
        reply_text = response.text if response.text else "I'm not sure how to respond to that."
    except Exception as e:
        reply_text = "My brain is lagging! Please try again."
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# HANDLE IMAGE MESSAGES
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    try:
        # 1. Download image from LINE
        message_content = line_bot_api.get_message_content(event.message.id)
        image_bytes = message_content.content
        
        # 2. Convert bytes to an image Gemini can read
        img = PIL.Image.open(io.BytesIO(image_bytes))
        
        # 3. Ask Gemini to summarize the image
        response = model.generate_content(["Please summarize this image in detail.", img])
        reply_text = response.text if response.text else "I see the image, but I can't describe it."
    except Exception as e:
        print(f"Image Error: {e}")
        reply_text = "I couldn't read that image. Please try again!"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(port=5000)

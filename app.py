import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import google.generativeai as genai
import google.api_core.exceptions
import PIL.Image
import io

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Using the EXACT format from your logs
# 'models/gemini-flash-latest' is the safest choice for your account
model = genai.GenerativeModel('models/gemini-flash-latest')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def get_ai_response(prompt, img=None):
    try:
        if img:
            response = model.generate_content([prompt, img])
        else:
            response = model.generate_content(prompt)
        return response.text if response.text else "I can't describe this."

    except google.api_core.exceptions.ResourceExhausted:
        return "⚠️ Free limit reached! Try again later."
    except Exception as e:
        print(f"Internal Error: {e}")
        return "🧠 My brain is lagging! Please try again."

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    reply_text = get_ai_response(event.message.text)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    try:
        message_content = line_bot_api.get_message_content(event.message.id)
        img = PIL.Image.open(io.BytesIO(message_content.content))
        reply_text = get_ai_response("Please summarize this image in detail.", img)
    except Exception as e:
        reply_text = "I couldn't read that image. Please try again!"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(port=5000)

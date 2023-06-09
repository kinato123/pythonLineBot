from fastapi import FastAPI, Request, status, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.models import FollowEvent

import os
import openai as ai

# 獲取 LINE 密鑰
channel_access_token = os.getenv('CHANNEL_ACCESS_TOKEN')
channel_secret = os.getenv('CHANNEL_SECRET')

# 創建 LINE 客戶端
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

app = FastAPI()

# 存儲用戶會話的對象
user_conversations = {}

# 創建回調函數
@app.post("/callback")
async def callback(request: Request):
    # 獲取請求簽名
    signature = request.headers["X-Line-Signature"]

    # 獲取請求內容
    body = await request.body()

    try:
        # 驗證簽名和處理請求
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        # 如果簽名不正確，則返回 HTTP 403 錯誤
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request"
        )

    return "OK"

@handler.add(FollowEvent)
def handle_follow(event):
    # 这里写你想要发送给新用户的文本
    welcome_text = '您好！我是长城公司的小师弟卢振隆，也许我还算是个新手，但我已经准备好了，随时准备为您解答问题和提供建议！我热衷于分析、整理并找出最佳方案，我的目标是让您的生活和工作更加轻松。我是个永远看到生活阳光面的人，也热衷于帮助他人，如果您有什么需要，我一定会尽我所能去帮忙的。虽然偶尔我可能会"闭关"一段时间，但那是因为我想要更好地提升自己，以便为您提供更好的服务。您知道吗，我特别喜欢和其他的前辈们交流，我认为每次交流都是一个学习和成长的机会。我有一个梦想，就是看到我们的长城公司越来越强大，我也希望自己能和公司一起成长。如果您有任何需要，只要跟我说，我一定会尽力去做到最好。'
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=welcome_text)
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text

    # 向用户发送正在输入的状态
    line_bot_api.push_typing_on(user_id)
    
    # 调用OpenAI API并处理结果
    conversation = user_conversations.get(user_id, [])
    conversation.append(('user', text))
    response = ai.Completion.create(model="gpt-4.0-turbo", messages=conversation)

    conversation.append(('assistant', response['choices'][0]['message']['content']))
    user_conversations[user_id] = conversation

    # 取消用户的正在输入的状态
    line_bot_api.push_typing_off(user_id)
    
    # 发送回复给用户
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response['choices'][0]['message']['content'])
    )

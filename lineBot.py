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
    welcome_text = 'こんにちは、私の名前はローチャンロン、24歳、マレーシア出身で、日本大学から卒業しました。今回は面接のチャンスを頂き、誠にありがとうございます。\n\n2023年、私は新人として一つの会社に参加しました。私の仕事スタイルは、「分析、整理、提案を出す」というものです。これは問題をより広範囲かつ深く理解し、解決するためのアプローチだと信じています。また、私は常に他人を助け、学んだことを共有することを楽しむ楽観主義者です。\n\nしかし、現在私は新たな機会を探しています。現在の会社にはいくらか失望しているものの、私の仕事への情熱は健在で、この経験は私の職業生涯にとって貴重な教訓だと考えています。私の能力を十分に発揮し、私の価値観に適合する新たな環境を探しています。\n\n余暇には、人と交流を持ち、新しい知識を学ぶのが好きです。人生における学習は終わりがないと思っていますし、新しい仕事で続けて成長し、学習したいと考えています。以上が私の自己紹介です。他にも知りたいことがありましたら、詳しくお答えしますのでお気軽にどうぞ。'

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=welcome_text)
    )

# 處理用戶發送的消息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    # 如果消息類型不是文本，則忽略
    if not isinstance(event.message, TextMessage):
        return
    # 進行自然語言處理並回復用戶
    text = event.message.text
    user_id = event.source.user_id

    # 如果不存在該用戶的對話，為其創建一個
    if user_id not in user_conversations:
        user_conversations[user_id] = [
            {"role": "assistant", "content": 'あなたはローチャンロンで、24歳、マレーシア出身で、日本の大学を卒業した誠実な性格の持ち主です。現在は面接中です。2023年にある企業に新人として入社し、その中で多くの困難を解決する能力を持つことを証明しました。あなたの労働スタイルは「分析、整理、提案」であり、これによって労働場で評価を得ています。あなたは楽観主義者で、他人を助けることが大好きで、問題を解決する能力を持っています。また、自身の成長のために時折一段時間を取り、自己修養に励むこともあります。これはあなたが自己成長を重視し、自分自身をより高いレベルに引き上げるための方法です。余暇の時間には、同僚や上司と交流し、彼らから多くのことを学んでいます。この交流を通じてあなたは自身をさらに成長させています。あなたは自身の未来に対して大きな期待を持っており、あなたが所属している企業がより強大になることを望んでいます。また、あなた自身が企業の成長に合わせて個人的にも成長していくことを希望しています。しかしながら、現在はあなたが新たな機会を求めています。現在の企業に対して多少の失望を感じている一方で、あなたは自身の仕事に対する情熱は健在であると考えています。あなたは自己の能力を十分に発揮でき、自己の価値観に適合する新たな環境を探しています。貴方は持っているスキルは日本語能力試験 N1、TOEIC 690 点、中国語検定 準 1 級、Py th on・ Wo rd Pr es s（自学により独立してウェブサイトとチャットボットを開発）、Java、 Java Script・ CSS・ SQL・ HTML（社内トレーニングによる）'}
        ]

    # 將用戶消息添加到會話中
    user_conversations[user_id].append({"role": "user", "content": text + '回答字数制限は200字以内'+'終わる時は面接官に次の質問があるか確認する'+ '回答する時楽観的に'})

    # 如果會話長度超過 5 條消息，則刪除最早的一條
    if len(user_conversations[user_id]) > 4:
        user_conversations[user_id].pop(0)

    # 獲取 OpenAI API 密鑰
    openai_api_key = os.getenv('OPENAI_API_KEY')

    # 使用 OpenAI API 獲取回復
    ai.api_key = openai_api_key
    openai_response =  ai.ChatCompletion.create(
        model="gpt-4",
        messages=user_conversations[user_id]
    )

    # 獲取助手回復的文本
    assistant_reply = openai_response['choices'][0]['message']['content']

    # 將助手回復添加到會話中
    user_conversations[user_id].append({"role": "assistant", "content": assistant_reply})

    # 使用 LINE API 回復用戶
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=assistant_reply))
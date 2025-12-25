import os
import logging
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import google.generativeai as genai
from threading import Thread

# ロギング設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask アプリケーション初期化
flask_app = Flask(__name__)

# Slack Bolt アプリケーション初期化
slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Google Gemini API 初期化
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# Flask リクエストハンドラー
handler = SlackRequestHandler(slack_app)


def generate_reply_suggestions(message_text: str) -> str:
    """
    Google Gemini APIを使用して返信案を生成する
    
    Args:
        message_text: Slackメッセージのテキスト
        
    Returns:
        生成された返信案
    """
    try:
        prompt = f"""
以下のSlackメッセージに対して、3つの異なるトーンの返信案を提案してください。
各返信案は簡潔に（1-2文程度）してください。

メッセージ: {message_text}

以下の形式で返信案を提示してください：
1. プロフェッショナル：[返信案]
2. カジュアル：[返信案]
3. サポーティブ：[返信案]
"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating reply suggestions: {e}")
        return "申し訳ありません。返信案の生成に失敗しました。"


@slack_app.message("")
def handle_message(message, say, client):
    """
    すべてのメッセージを処理し、返信案をスレッドで提示する
    """
    # ボット自身のメッセージは無視
    if message.get("bot_id"):
        return
    
    # メッセージテキストを取得
    message_text = message.get("text", "")
    if not message_text:
        return
    
    # 返信案を生成（スレッドで実行して応答を遅延させない）
    def post_suggestions():
        try:
            suggestions = generate_reply_suggestions(message_text)
            
            # スレッドに返信案を投稿
            client.chat_postMessage(
                channel=message["channel"],
                thread_ts=message["ts"],
                text=f"💡 *返信案*\n\n{suggestions}"
            )
        except Exception as e:
            logger.error(f"Error posting suggestions: {e}")
    
    thread = Thread(target=post_suggestions)
    thread.daemon = True
    thread.start()


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """
    Slackイベント受信エンドポイント
    """
    return handler.handle(request)


@flask_app.route("/health", methods=["GET"])
def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return {"status": "ok"}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port, debug=False)

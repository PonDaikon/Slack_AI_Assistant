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


def create_reply_suggestions_blocks(suggestions_text: str) -> list:
    """
    Block Kitを使用して返信案ブロックを作成
    
    Args:
        suggestions_text: 生成された返信案のテキスト
        
    Returns:
        Block Kitブロックのリスト
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "💡 返信案",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": suggestions_text
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "閉じる",
                        "emoji": True
                    },
                    "value": "close_suggestions",
                    "action_id": "close_suggestions_button"
                }
            ]
        }
    ]
    return blocks


@slack_app.shortcut("generate_reply_suggestions")
def handle_message_action(ack, body, client):
    """
    Message Shortcutで「AI返信生成」がクリックされた時の処理
    
    @slack_app.shortcut() を使用してMessage Shortcutを処理
    スレッド内での使用に対応し、Block Kitで返信案を表示
    """
    ack()
    
    try:
        # メッセージ情報を取得
        message_text = body.get("message", {}).get("text", "")
        channel_id = body.get("channel", {}).get("id", "")
        user_id = body.get("user", {}).get("id", "")
        thread_ts = body.get("message", {}).get("thread_ts")  # スレッドのタイムスタンプ
        message_ts = body.get("message", {}).get("ts")  # メッセージのタイムスタンプ
        
        logger.info(f"Message shortcut triggered - Text: {message_text}, Channel: {channel_id}, User: {user_id}, Thread: {thread_ts}")
        
        if not message_text or not channel_id or not user_id:
            logger.error("Missing required fields in shortcut body")
            return
        
        # 返信案を生成（スレッドで実行）
        def post_suggestions():
            try:
                logger.info("Generating reply suggestions...")
                suggestions = generate_reply_suggestions(message_text)
                
                # Block Kitブロックを作成
                blocks = create_reply_suggestions_blocks(suggestions)
                
                logger.info("Posting ephemeral message...")
                
                # Ephemeral Messageで返信案を投稿
                # スレッド内の場合はthread_tsを指定
                if thread_ts:
                    logger.info(f"Posting to thread: {thread_ts}")
                    client.chat_postEphemeral(
                        channel=channel_id,
                        user=user_id,
                        thread_ts=thread_ts,
                        blocks=blocks
                    )
                else:
                    logger.info("Posting to channel")
                    client.chat_postEphemeral(
                        channel=channel_id,
                        user=user_id,
                        blocks=blocks
                    )
                
                logger.info("Ephemeral message posted successfully")
            except Exception as e:
                logger.error(f"Error posting suggestions: {e}")
                try:
                    if thread_ts:
                        client.chat_postEphemeral(
                            channel=channel_id,
                            user=user_id,
                            thread_ts=thread_ts,
                            text="申し訳ありません。返信案の生成に失敗しました。"
                        )
                    else:
                        client.chat_postEphemeral(
                            channel=channel_id,
                            user=user_id,
                            text="申し訳ありません。返信案の生成に失敗しました。"
                        )
                except Exception as inner_e:
                    logger.error(f"Error posting error message: {inner_e}")
        
        thread = Thread(target=post_suggestions)
        thread.daemon = True
        thread.start()
    except Exception as e:
        logger.error(f"Error in handle_message_action: {e}")


@slack_app.action("close_suggestions_button")
def handle_close_button(ack, body, client):
    """
    「閉じる」ボタンがクリックされた時の処理
    
    Ephemeral Messageは自動的に削除されるため、
    ここではユーザーへの確認メッセージを表示
    """
    ack()
    
    try:
        logger.info("Close button clicked")
        # Ephemeral Messageなので、自動的に削除される
        # 必要に応じてここでログを記録したり、追加処理を実行
    except Exception as e:
        logger.error(f"Error in handle_close_button: {e}")


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

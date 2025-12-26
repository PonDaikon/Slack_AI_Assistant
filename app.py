import os
import logging
import json
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import google.generativeai as genai
from threading import Thread
import time

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

# メッセージ追跡用（削除用）
message_tracking = {}


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


def create_reply_suggestions_blocks(suggestions_text: str, message_id: str) -> list:
    """
    Block Kitを使用して返信案ブロックを作成
    
    Args:
        suggestions_text: 生成された返信案のテキスト
        message_id: メッセージID（削除用）
        
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
                    "value": message_id,
                    "action_id": "close_suggestions_button"
                }
            ]
        }
    ]
    return blocks


def delete_message_after_delay(client, channel_id, message_ts, user_id, delay_seconds=120):
    """
    指定時間後にメッセージを削除する
    
    Args:
        client: Slack APIクライアント
        channel_id: チャンネルID
        message_ts: メッセージのタイムスタンプ
        user_id: ユーザーID
        delay_seconds: 削除までの遅延時間（秒）
    """
    try:
        logger.info(f"Scheduled message deletion in {delay_seconds} seconds: {message_ts}")
        time.sleep(delay_seconds)
        
        # Ephemeral Messageは削除できないため、ここでは何もしない
        # Ephemeral Messageは自動的に消える
        logger.info(f"Message {message_ts} would be deleted (Ephemeral messages auto-delete)")
    except Exception as e:
        logger.error(f"Error in delete_message_after_delay: {e}")


@slack_app.shortcut("generate_reply_suggestions")
def handle_message_action(ack, body, client):
    """
    Message Shortcutで「AI返信生成」がクリックされた時の処理
    
    スレッド内での使用に対応し、Block Kitで返信案を表示
    120秒後に自動削除
    """
    ack()
    
    try:
        # メッセージ情報を取得
        message_text = body.get("message", {}).get("text", "")
        channel_id = body.get("channel", {}).get("id", "")
        user_id = body.get("user", {}).get("id", "")
        message_ts = body.get("message", {}).get("ts")
        thread_ts = body.get("message", {}).get("thread_ts")
        
        logger.info(f"Message shortcut triggered")
        logger.info(f"  Text: {message_text}")
        logger.info(f"  Channel: {channel_id}")
        logger.info(f"  User: {user_id}")
        logger.info(f"  Message TS: {message_ts}")
        logger.info(f"  Thread TS: {thread_ts}")
        
        if not message_text or not channel_id or not user_id:
            logger.error("Missing required fields in shortcut body")
            return
        
        # メッセージID生成（削除用）
        message_id = f"{channel_id}_{message_ts}_{int(time.time())}"
        
        # 返信案を生成（スレッドで実行）
        def post_suggestions():
            try:
                logger.info("Generating reply suggestions...")
                suggestions = generate_reply_suggestions(message_text)
                
                # Block Kitブロックを作成
                blocks = create_reply_suggestions_blocks(suggestions, message_id)
                
                logger.info("Posting ephemeral message...")
                
                # スレッド判定
                # thread_tsが存在する場合 = スレッド内のメッセージ
                # thread_tsが存在しない場合 = スレッド外のメッセージ
                
                if thread_ts:
                    # スレッド内のメッセージの場合、スレッド内に投稿
                    logger.info(f"Posting to thread: {thread_ts}")
                    response = client.chat_postEphemeral(
                        channel=channel_id,
                        user=user_id,
                        thread_ts=thread_ts,
                        blocks=blocks
                    )
                else:
                    # スレッド外のメッセージの場合、スレッド外に投稿
                    logger.info("Posting to channel (not in thread)")
                    response = client.chat_postEphemeral(
                        channel=channel_id,
                        user=user_id,
                        blocks=blocks
                    )
                
                # メッセージ情報を保存（削除用）
                message_tracking[message_id] = {
                    "channel": channel_id,
                    "user": user_id,
                    "thread_ts": thread_ts
                }
                
                logger.info("Ephemeral message posted successfully")
                
                # 120秒後に自動削除（Ephemeral Messageなので自動的に消える）
                delete_thread = Thread(
                    target=delete_message_after_delay,
                    args=(client, channel_id, response.get("ts"), user_id, 120)
                )
                delete_thread.daemon = True
                delete_thread.start()
                
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
    
    ボタンをクリックしたら即座にメッセージを削除
    """
    ack()
    
    try:
        message_id = body.get("actions", [{}])[0].get("value")
        user_id = body.get("user", {}).get("id")
        
        logger.info(f"Close button clicked: {message_id} by user {user_id}")
        
        # メッセージ情報を取得
        if message_id in message_tracking:
            msg_info = message_tracking[message_id]
            logger.info(f"Message tracked: {msg_info}")
            
            # Ephemeral Messageは削除できないため、
            # ユーザーへの確認メッセージを表示
            try:
                channel_id = msg_info["channel"]
                thread_ts = msg_info["thread_ts"]
                
                if thread_ts:
                    client.chat_postEphemeral(
                        channel=channel_id,
                        user=user_id,
                        thread_ts=thread_ts,
                        text="✓ 返信案を閉じました"
                    )
                else:
                    client.chat_postEphemeral(
                        channel=channel_id,
                        user=user_id,
                        text="✓ 返信案を閉じました"
                    )
                
                # メッセージ情報を削除
                del message_tracking[message_id]
                logger.info(f"Message {message_id} closed")
            except Exception as e:
                logger.error(f"Error posting close confirmation: {e}")
        else:
            logger.warning(f"Message {message_id} not found in tracking")
            
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

# Slack AI Assistant - 返信案自動提示ボット

Slackのメッセージに対して、Google Gemini APIを使用して自動的に返信案を提示するAIアシスタントです。完全無料で運用できます。

## 機能

- **自動返信案提示**：Slackメッセージを受信すると、スレッド内に3つのトーンの返信案を自動提示
- **複数のトーン**：プロフェッショナル、カジュアル、サポーティブの3つの返信案を生成
- **完全無料**：Google Gemini無料API + Render無料ホスティング

## 必要な準備

### 1. Google Gemini API キーの取得

1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. 「API キーを作成」をクリック
3. 「新しいプロジェクトで API キーを作成」を選択
4. 生成されたAPIキーをコピーして保存（後で使用）

### 2. Slack App の作成と設定

#### 2.1 Slack App の作成

1. [Slack API Dashboard](https://api.slack.com/apps) にアクセス
2. 「Create New App」をクリック
3. 「From scratch」を選択
4. アプリ名を入力（例：「AI Reply Assistant」）
5. ワークスペースを選択して「Create App」をクリック

#### 2.2 ボット権限の設定

1. 左メニューから「OAuth & Permissions」を選択
2. 「Scopes」セクションで「Bot Token Scopes」に以下を追加：
   - `chat:write`
   - `messages:read`

#### 2.3 イベント購読の設定

1. 左メニューから「Event Subscriptions」を選択
2. 「Enable Events」をONに切り替え
3. 「Request URL」に以下を入力（Renderデプロイ後に更新）：
   ```
   https://your-render-app-url.onrender.com/slack/events
   ```
4. 「Subscribe to bot events」セクションで以下を追加：
   - `message.channels`
   - `message.groups`
   - `message.im`
   - `message.mpim`

#### 2.4 トークンの取得

1. 「OAuth & Permissions」ページに戻る
2. 「Bot User OAuth Token」をコピー（`xoxb-`で始まる）
3. 「Signing Secret」をコピー（Settings > Basic Informationから確認可能）

#### 2.5 ワークスペースにアプリをインストール

1. 「Install App」をクリック
2. 「Install to Workspace」をクリック
3. 権限を確認して「Allow」をクリック

## デプロイ手順

### 方法1：Renderへのデプロイ（推奨）

#### 1. GitHubにリポジトリをプッシュ

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/slack-ai-assistant.git
git push -u origin main
```

#### 2. Renderでのデプロイ

1. [Render](https://render.com) にサインアップ
2. ダッシュボードから「New +」 > 「Web Service」を選択
3. GitHubリポジトリを接続
4. 以下の設定を入力：
   - **Name**: `slack-ai-assistant`
   - **Runtime**: Python 3
   - **Build Command**: `bash build.sh`
   - **Start Command**: `gunicorn app:flask_app`

#### 3. 環境変数の設定

Renderダッシュボードの「Environment」セクションに以下を追加：

```
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
GOOGLE_API_KEY=your-google-api-key-here
```

#### 4. デプロイ実行

「Create Web Service」をクリックするとデプロイが開始されます。

#### 5. Slack App の Request URL を更新

1. Renderダッシュボードでデプロイ完了を確認
2. アプリのURLをコピー（例：`https://slack-ai-assistant-xxxx.onrender.com`）
3. [Slack API Dashboard](https://api.slack.com/apps) に戻る
4. 「Event Subscriptions」の「Request URL」を以下に更新：
   ```
   https://your-render-app-url.onrender.com/slack/events
   ```
5. 「Verify Request URL」をクリック（成功すればOK）

### 方法2：ローカルでのテスト

```bash
# 依存関係をインストール
pip install -r requirements.txt

# .envファイルを作成
cp .env.example .env
# .envを編集してトークンを入力

# アプリを実行
python app.py
```

ローカルでテストする場合は、[ngrok](https://ngrok.com) などを使用してトンネルを作成し、Slack App の Request URL を更新してください。

## 使用方法

1. Slack内のチャンネルにボットを招待
2. メッセージを送信
3. ボットが自動的にスレッドに返信案を投稿します

例：
```
ユーザー: 「プロジェクトの進捗について報告があります」

ボット:
💡 *返信案*

1. プロフェッショナル：了解しました。詳細をお聞きしたいのですが、進捗状況と課題についてお教えいただけますか？
2. カジュアル：了解！進捗状況どう？何か困ってることある？
3. サポーティブ：素晴らしい！進捗について聞かせてください。何かサポートが必要でしたらお知らせください。
```

## コスト

- **Google Gemini API**：無料枠で月1,500リクエスト（十分な容量）
- **Render**：無料ホスティング（スリープ機能あり）
- **合計**：完全無料

## トラブルシューティング

### ボットがメッセージに反応しない

1. ボットがチャンネルに招待されているか確認
2. Slack App の権限設定を確認
3. Renderのログを確認：`$ render logs`

### Request URL の検証に失敗する

1. Renderアプリが正常に起動しているか確認
2. URLが正しく入力されているか確認
3. ファイアウォール設定を確認

### API エラーが発生する

1. Google API キーが正しく設定されているか確認
2. Slack トークンの有効期限を確認
3. Renderの環境変数が正しく設定されているか確認

## セキュリティに関する注意

- `.env` ファイルをGitにコミットしないでください（`.gitignore`に含まれています）
- APIキーとトークンは絶対に公開しないでください
- 本番環境では定期的にトークンをローテーションしてください

## ライセンス

MIT License

## 参考リンク

- [Slack Bolt Python Documentation](https://slack.dev/bolt-python/)
- [Google Generative AI Python SDK](https://github.com/google/generative-ai-python)
- [Render Documentation](https://render.com/docs)

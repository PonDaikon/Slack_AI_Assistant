# Slack AI Assistant - 詳細セットアップガイド

このガイドでは、Slack AI Assistantを完全に無料でセットアップする手順を詳しく説明します。

## ステップ1：Google Gemini API キーの取得

### 1.1 Google Accountの準備

Google Accountが必要です。持っていない場合は[Google Account](https://accounts.google.com/signup)で作成してください。

### 1.2 API キーの生成

1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. 「API キーを作成」ボタンをクリック
4. 「新しいプロジェクトで API キーを作成」を選択
5. ポップアップで「作成」をクリック
6. 生成されたAPIキーが表示されます
7. **「キーをコピー」をクリックしてコピー**（この値は後で必要）

**注意**：このキーは絶対に他人と共有しないでください。

## ステップ2：Slack Appの作成と設定

### 2.1 Slack Appの作成

1. [Slack API Dashboard](https://api.slack.com/apps) にアクセス
2. ログインしていない場合はSlackアカウントでログイン
3. 「Create New App」ボタンをクリック
4. 「From scratch」を選択
5. 以下を入力：
   - **App name**: `AI Reply Assistant`（任意の名前）
   - **Pick a workspace to develop your app in**: あなたのSlackワークスペースを選択
6. 「Create App」をクリック

### 2.2 ボット権限の設定

1. 左メニューから「OAuth & Permissions」をクリック
2. 「Scopes」セクションまでスクロール
3. 「Bot Token Scopes」の下の「Add an OAuth Scope」をクリック
4. 以下の権限を追加：
   - `chat:write` - メッセージを送信する権限
   - `messages:read` - メッセージを読む権限

### 2.3 イベント購読の設定

1. 左メニューから「Event Subscriptions」をクリック
2. 「Enable Events」のトグルをONに切り替え
3. 「Request URL」フィールドが表示されます（後で入力）
4. 「Subscribe to bot events」セクションまでスクロール
5. 「Add Bot User Event」をクリック
6. 以下のイベントを追加：
   - `message.channels` - パブリックチャンネルのメッセージ
   - `message.groups` - プライベートチャンネルのメッセージ
   - `message.im` - ダイレクトメッセージ
   - `message.mpim` - グループDM

### 2.4 トークンの取得

1. 左メニューから「OAuth & Permissions」をクリック
2. 「Bot User OAuth Token」を探す（`xoxb-`で始まる）
3. **「Copy」をクリックしてコピー**（この値は後で必要）

### 2.5 Signing Secretの取得

1. 左メニューから「Basic Information」をクリック
2. 「App Credentials」セクションを探す
3. 「Signing Secret」を確認
4. **「Show」をクリックして表示し、コピー**（この値は後で必要）

### 2.6 ワークスペースへのインストール

1. 左メニューから「Install App」をクリック
2. 「Install to Workspace」ボタンをクリック
3. 権限確認画面が表示されます
4. 「Allow」をクリック

## ステップ3：Renderへのデプロイ

### 3.1 GitHubリポジトリの準備

1. [GitHub](https://github.com) にサインアップ（アカウントがない場合）
2. 新しいリポジトリを作成：
   - リポジトリ名：`slack-ai-assistant`
   - 説明：`Slack AI Assistant for auto-reply suggestions`
   - 「Public」を選択
   - 「Create repository」をクリック

3. ローカルマシンでコマンドを実行：

```bash
# プロジェクトディレクトリに移動
cd slack-ai-assistant

# Gitを初期化
git init

# すべてのファイルを追加
git add .

# コミット
git commit -m "Initial commit: Slack AI Assistant"

# リモートリポジトリを追加
git remote add origin https://github.com/YOUR_USERNAME/slack-ai-assistant.git

# ブランチをmainに変更（必要に応じて）
git branch -M main

# GitHubにプッシュ
git push -u origin main
```

### 3.2 Renderでのデプロイ

1. [Render](https://render.com) にサインアップ
2. 「New +」ボタンをクリック
3. 「Web Service」を選択
4. GitHubリポジトリを接続：
   - 「Connect your GitHub account」をクリック
   - GitHubの認可画面で「Authorize render」をクリック
   - `slack-ai-assistant` リポジトリを選択
5. 以下の設定を入力：
   - **Name**: `slack-ai-assistant`
   - **Runtime**: `Python 3`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `gunicorn app:flask_app`
   - **Instance Type**: `Free`（無料）

### 3.3 環境変数の設定

1. 「Environment」セクションまでスクロール
2. 「Add Environment Variable」をクリック
3. 以下の環境変数を追加：

| Key | Value |
|-----|-------|
| `SLACK_BOT_TOKEN` | ステップ2.4でコピーしたトークン（`xoxb-`で始まる） |
| `SLACK_SIGNING_SECRET` | ステップ2.5でコピーしたSigning Secret |
| `GOOGLE_API_KEY` | ステップ1.2でコピーしたGoogle API Key |

### 3.4 デプロイの実行

1. すべての設定が完了したら「Create Web Service」をクリック
2. デプロイが開始されます（2-5分かかります）
3. デプロイ完了後、URLが表示されます（例：`https://slack-ai-assistant-xxxx.onrender.com`）
4. **このURLをコピーして保存**

## ステップ4：Slack App の Request URL を設定

1. [Slack API Dashboard](https://api.slack.com/apps) に戻る
2. 作成したアプリを選択
3. 左メニューから「Event Subscriptions」をクリック
4. 「Request URL」フィールドに以下を入力：
   ```
   https://slack-ai-assistant-xxxx.onrender.com/slack/events
   ```
   （`xxxx`はあなたのRenderアプリのURLに置き換え）
5. 「Verify Request URL」をクリック
6. 「Verified ✓」と表示されればOK

## ステップ5：ボットをチャンネルに招待

1. Slackワークスペースを開く
2. ボットを使用したいチャンネルを開く
3. チャンネル名をクリック
4. 「Integrations」タブを選択
5. 「Add an app」をクリック
6. 「AI Reply Assistant」を検索して選択
7. 「Add」をクリック

## ステップ6：テスト

1. チャンネルでメッセージを送信
2. ボットが自動的にスレッドに返信案を投稿するか確認

例：
```
あなた: 「プロジェクトの進捗について報告があります」

ボット:
💡 *返信案*

1. プロフェッショナル：了解しました。詳細をお聞きしたいのですが、進捗状況と課題についてお教えいただけますか？
2. カジュアル：了解！進捗状況どう？何か困ってることある？
3. サポーティブ：素晴らしい！進捗について聞かせてください。何かサポートが必要でしたらお知らせください。
```

## トラブルシューティング

### ボットがメッセージに反応しない

**確認項目：**
1. ボットがチャンネルに招待されているか
2. Slack App の権限が正しく設定されているか
3. Renderアプリが正常に起動しているか

**解決方法：**
```bash
# Renderのログを確認
render logs --service slack-ai-assistant
```

### Request URL の検証に失敗する

**原因：**
- Renderアプリがまだ起動していない
- URLが間違っている
- ファイアウォールがブロックしている

**解決方法：**
1. Renderダッシュボードでアプリが「Live」状態か確認
2. URLを再度確認
3. 数分待ってから再度試す

### API エラーが発生する

**確認項目：**
1. Google API キーが正しく設定されているか
2. Slack トークンが有効か
3. 環境変数がすべて設定されているか

**解決方法：**
1. Renderダッシュボードで環境変数を確認
2. 必要に応じて新しいトークンを生成

## 無料枠の制限

### Google Gemini API
- **月間リクエスト数**：1,500リクエスト/月（無料）
- **1分あたりのリクエスト数**：15リクエスト/分

### Render
- **スリープ機能**：15分間アクティビティがないと自動スリープ
- **起動時間**：スリープ状態から起動に数秒かかる
- **無料時間**：月750時間まで無料

## 今後のカスタマイズ

### 返信案の内容を変更する

`app.py`の`generate_reply_suggestions`関数内のpromptを編集：

```python
prompt = f"""
以下のSlackメッセージに対して、3つの異なるトーンの返信案を提案してください。
...
"""
```

### 返信案の数を変更する

`app.py`のpromptで返信案の数を指定：

```python
prompt = f"""
...
5つの異なるトーンの返信案を提案してください。
...
"""
```

## セキュリティのベストプラクティス

1. **APIキーを保護する**：`.env`ファイルをGitにコミットしない
2. **トークンをローテーションする**：定期的に新しいトークンを生成
3. **ログを監視する**：異常なアクティビティを確認
4. **権限を最小化する**：必要な権限のみを付与

## サポート

問題が発生した場合：

1. [Slack API Documentation](https://api.slack.com/)
2. [Render Documentation](https://render.com/docs)
3. [Google Generative AI Documentation](https://ai.google.dev/)

を参照してください。

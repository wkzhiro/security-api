# FastAPI Chatbot Server

Azure OpenAIを使用したチャットボットのバックエンドサーバーです。

## 機能

- Azure OpenAIとの統合
- MySQLでのセッション管理
- CosmosDBでの会話履歴保存
- CORS設定によるNext.jsフロントエンドとの連携

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example`を`.env`にコピーし、必要な値を設定してください。

```bash
cp .env.example .env
```

設定が必要な環境変数：

#### Azure OpenAI
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAIエンドポイント
- `AZURE_OPENAI_API_KEY`: APIキー
- `AZURE_OPENAI_DEPLOYMENT_NAME`: デプロイメント名
- `AZURE_OPENAI_API_VERSION`: APIバージョン（デフォルト: 2024-02-15-preview）

#### MySQL
- `MYSQL_HOST`: MySQLホスト（デフォルト: localhost）
- `MYSQL_PORT`: MySQLポート（デフォルト: 3306）
- `MYSQL_USER`: MySQLユーザー名
- `MYSQL_PASSWORD`: MySQLパスワード
- `MYSQL_DATABASE`: データベース名

#### CosmosDB
- `COSMOSDB_ENDPOINT`: CosmosDBエンドポイント
- `COSMOSDB_KEY`: CosmosDBアクセスキー
- `COSMOSDB_DATABASE_NAME`: データベース名（デフォルト: chatbot）
- `COSMOSDB_CONTAINER_NAME`: コンテナ名（デフォルト: conversations）

### 3. データベースセットアップ

#### MySQL
MySQLデータベースを作成し、接続情報を環境変数に設定してください。テーブルは自動で作成されます。

#### CosmosDB
CosmosDBアカウントを作成し、接続情報を環境変数に設定してください。データベースとコンテナは自動で作成されます。

### 4. サーバー起動

```bash
python main.py
```

または

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API エンドポイント

### POST /chat
チャットメッセージを処理します。

**リクエスト:**
```json
{
  "message": "こんにちは",
  "user_email": "user@example.com"
}
```

**レスポンス:**
```json
{
  "response": "こんにちは！何かお手伝いできることはありますか？",
  "success": true
}
```

### GET /health
サーバーのヘルスチェックを行います。

### GET /chat/sessions/{user_email}
ユーザーのチャットセッションを取得します。

### GET /chat/history/{user_email}?limit=20
ユーザーの会話履歴を取得します。

## ドキュメント

サーバー起動後、以下のURLでAPIドキュメントを確認できます：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## トラブルシューティング

### 1. Azure OpenAI接続エラー
- エンドポイント、APIキー、デプロイメント名が正しく設定されているか確認
- デプロイメントが正常に動作しているか確認

### 2. MySQL接続エラー
- MySQLサーバーが起動しているか確認
- データベースが存在するか確認
- 接続情報が正しいか確認

### 3. CosmosDB接続エラー
- CosmosDBアカウントが有効か確認
- エンドポイントとキーが正しいか確認
- 必要な権限が付与されているか確認
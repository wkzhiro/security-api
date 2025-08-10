import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.chat_routes import router as chat_router
from config.settings import settings

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション作成
app = FastAPI(
    title="Chatbot API",
    description="Azure OpenAI を使用したチャットボットAPI",
    version="1.0.0"
)

# CORS設定（Next.jsからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.jsのデフォルトポート
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(chat_router, tags=["chat"])

# ルートエンドポイント
@app.get("/")
async def root():
    return {
        "message": "Chatbot API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }

# アプリケーション起動時の処理
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Chatbot API server...")
    logger.info(f"API will be available at: http://{settings.API_HOST}:{settings.API_PORT}")

# アプリケーション終了時の処理
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Chatbot API server...")
    # データベース接続を閉じる
    try:
        from services.mysql_service import mysql_service
        mysql_service.close()
    except Exception as e:
        logger.error(f"Error closing MySQL connection: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
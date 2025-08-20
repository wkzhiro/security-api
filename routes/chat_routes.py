import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime
from models.chat_models import ChatRequest, ChatResponse, ConversationRecord
from services.azure_openai_service import azure_openai_service
from services.mysql_service import mysql_service
from services.cosmosdb_service import cosmosdb_service
from dependencies.security import get_current_user
from typing import Dict
from fastapi import Depends

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(get_current_user)])
async def chat_endpoint(request: ChatRequest):
    """チャットメッセージを処理するエンドポイント"""
    try:
        # 入力検証
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="メッセージが空です")
        
        if not request.user_email:
            raise HTTPException(status_code=400, detail="ユーザーメールが必要です")
        
        logger.info(f"Processing chat request from user: {request.user_email}")
        
        # MySQL: セッション管理
        session_id = mysql_service.get_or_create_session(request.user_email)
        
        # Azure OpenAI: 応答生成
        ai_response = await azure_openai_service.generate_response(request.message)
        
        # 会話履歴保存（MySQLとCosmosDBの両方に保存）
        conversation_record = ConversationRecord(
            session_id=session_id,
            user_email=request.user_email,
            message=request.message,
            response=ai_response,
            timestamp=datetime.now()
        )
        
        # MySQL: 会話履歴保存
        try:
            mysql_service.save_conversation(conversation_record)
        except Exception as e:
            # MySQLエラーはログに記録するが、レスポンスは正常に返す
            logger.error(f"MySQL save error: {e}")
        
        # CosmosDB: 会話履歴保存
        try:
            cosmosdb_service.save_conversation(conversation_record)
        except Exception as e:
            # CosmosDBエラーはログに記録するが、レスポンスは正常に返す
            logger.error(f"CosmosDB save error: {e}")
        
        return ChatResponse(
            response=ai_response,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"予期しないエラーが発生しました: {str(e)}"
        )

@router.get("/health", dependencies=[Depends(get_current_user)])
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "service": "chatbot-api"}

@router.get("/chat/sessions/{user_email}", dependencies=[Depends(get_current_user)])
async def get_user_sessions(user_email: str):
    """ユーザーのチャットセッションを取得"""
    try:
        sessions = mysql_service.get_user_sessions(user_email)
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error retrieving user sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history/{user_email}", dependencies=[Depends(get_current_user)])
async def get_conversation_history(user_email: str, limit: int = 20, source: str = "mysql"):
    """ユーザーの会話履歴を取得（MySQLまたはCosmosDBから）"""
    try:
        if source.lower() == "cosmosdb":
            conversations = cosmosdb_service.get_user_conversations(user_email, limit)
        else:
            conversations = mysql_service.get_conversation_history(user_email, limit)
        
        return {"conversations": conversations, "source": source}
    except Exception as e:
        logger.error(f"Error retrieving conversation history from {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
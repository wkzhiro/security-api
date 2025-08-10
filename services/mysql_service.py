import logging
import mysql.connector
from mysql.connector import Error
from typing import Optional
from datetime import datetime
import uuid
from config.settings import settings
from models.chat_models import ChatSession, ConversationRecord

logger = logging.getLogger(__name__)

class MySQLService:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()

    def connect(self):
        """MySQL データベースに接続"""
        try:
            self.connection = mysql.connector.connect(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                database=settings.MYSQL_DATABASE
            )
            logger.info("MySQL database connected successfully")
        except Error as e:
            logger.error(f"MySQL connection error: {e}")
            raise

    def create_tables(self):
        """必要なテーブルを作成"""
        if not self.connection:
            return

        try:
            cursor = self.connection.cursor()
            
            # chat_sessions テーブル
            create_sessions_table = """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_email VARCHAR(255) NOT NULL,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_email (user_email),
                INDEX idx_session_id (session_id)
            )
            """
            cursor.execute(create_sessions_table)
            
            self.connection.commit()
            cursor.close()
            logger.info("MySQL tables created successfully")
            
        except Error as e:
            logger.error(f"MySQL table creation error: {e}")

    def create_chat_session(self, user_email: str) -> str:
        """新しいチャットセッションを作成"""
        session_id = str(uuid.uuid4())
        
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO chat_sessions (user_email, session_id) VALUES (%s, %s)"
            cursor.execute(query, (user_email, session_id))
            self.connection.commit()
            cursor.close()
            
            logger.info(f"Created chat session for user: {user_email}")
            return session_id
            
        except Error as e:
            logger.error(f"Error creating chat session: {e}")
            return str(uuid.uuid4())  # フォールバック

    def get_or_create_session(self, user_email: str) -> str:
        """既存のセッションを取得、または新しく作成"""
        try:
            cursor = self.connection.cursor()
            
            # 最新のセッションを取得
            query = """
            SELECT session_id FROM chat_sessions 
            WHERE user_email = %s 
            ORDER BY created_at DESC 
            LIMIT 1
            """
            cursor.execute(query, (user_email,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return result[0]
            else:
                return self.create_chat_session(user_email)
                
        except Error as e:
            logger.error(f"Error getting/creating session: {e}")
            return self.create_chat_session(user_email)

    def get_user_sessions(self, user_email: str, limit: int = 10):
        """ユーザーのセッション履歴を取得"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT * FROM chat_sessions 
            WHERE user_email = %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """
            cursor.execute(query, (user_email, limit))
            sessions = cursor.fetchall()
            cursor.close()
            return sessions
            
        except Error as e:
            logger.error(f"Error getting user sessions: {e}")
            return []

    def save_conversation(self, conversation: ConversationRecord) -> bool:
        """会話記録をMySQLに保存"""
        try:
            cursor = self.connection.cursor()
            query = """
            INSERT INTO chat_messages (session_id, user_email, message, response, created_at) 
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                conversation.session_id,
                conversation.user_email,
                conversation.message,
                conversation.response,
                conversation.timestamp
            ))
            self.connection.commit()
            cursor.close()
            
            # 統計情報を更新
            self.update_user_stats(conversation.user_email)
            
            logger.info(f"Conversation saved for user: {conversation.user_email}")
            return True
            
        except Error as e:
            logger.error(f"Error saving conversation: {e}")
            return False

    def get_conversation_history(self, user_email: str, limit: int = 20):
        """ユーザーの会話履歴を取得"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT * FROM chat_messages 
            WHERE user_email = %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """
            cursor.execute(query, (user_email, limit))
            messages = cursor.fetchall()
            cursor.close()
            return messages
            
        except Error as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    def update_user_stats(self, user_email: str):
        """ユーザー統計情報を更新"""
        try:
            cursor = self.connection.cursor()
            
            # 統計情報を更新または挿入
            query = """
            INSERT INTO user_stats (user_email, total_messages, first_chat_at, last_chat_at)
            VALUES (%s, 1, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                total_messages = total_messages + 1,
                last_chat_at = NOW(),
                first_chat_at = COALESCE(first_chat_at, NOW())
            """
            cursor.execute(query, (user_email,))
            self.connection.commit()
            cursor.close()
            
        except Error as e:
            logger.error(f"Error updating user stats: {e}")

    def close(self):
        """データベース接続を閉じる"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")

# シングルトンインスタンス
mysql_service = MySQLService()
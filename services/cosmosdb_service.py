import logging
import uuid
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from typing import List, Dict, Optional
from config.settings import settings
from models.chat_models import ConversationRecord

logger = logging.getLogger(__name__)

class CosmosDBService:
    def __init__(self):
        self.client = CosmosClient(
            settings.COSMOSDB_ENDPOINT,
            settings.COSMOSDB_KEY
        )
        self.database_name = settings.COSMOSDB_DATABASE_NAME
        self.container_name = settings.COSMOSDB_CONTAINER_NAME
        self.setup_database()

    def setup_database(self):
        """データベースとコンテナを設定"""
        try:
            # データベースの作成（存在しない場合）
            database = self.client.create_database_if_not_exists(
                id=self.database_name
            )
            
            # コンテナの作成（存在しない場合）
            container = database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/user_email"),
                offer_throughput=400
            )
            
            self.container = container
            logger.info("CosmosDB database and container setup completed")
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"CosmosDB setup error: {e}")
            raise

    def save_conversation(self, conversation: ConversationRecord) -> str:
        """会話記録をCosmosDBに保存"""
        try:
            # IDが設定されていない場合は生成
            if not conversation.id:
                conversation.id = str(uuid.uuid4())
            
            # Pydanticモデルを辞書に変換
            document = conversation.dict()
            
            # datetimeをISO文字列に変換
            if isinstance(document['timestamp'], datetime):
                document['timestamp'] = document['timestamp'].isoformat()
            
            # ドキュメントを作成
            created_item = self.container.create_item(body=document)
            
            logger.info(f"Conversation saved to CosmosDB: {created_item['id']}")
            return created_item['id']
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error saving conversation to CosmosDB: {e}")
            raise

    def get_user_conversations(
        self, 
        user_email: str, 
        limit: int = 50,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """ユーザーの会話履歴を取得"""
        try:
            if session_id:
                # 特定のセッションの会話を取得
                query = """
                SELECT * FROM c 
                WHERE c.user_email = @user_email 
                AND c.session_id = @session_id 
                ORDER BY c.timestamp DESC 
                OFFSET 0 LIMIT @limit
                """
                parameters = [
                    {"name": "@user_email", "value": user_email},
                    {"name": "@session_id", "value": session_id},
                    {"name": "@limit", "value": limit}
                ]
            else:
                # ユーザーのすべての会話を取得
                query = """
                SELECT * FROM c 
                WHERE c.user_email = @user_email 
                ORDER BY c.timestamp DESC 
                OFFSET 0 LIMIT @limit
                """
                parameters = [
                    {"name": "@user_email", "value": user_email},
                    {"name": "@limit", "value": limit}
                ]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            logger.info(f"Retrieved {len(items)} conversations for user: {user_email}")
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error retrieving conversations from CosmosDB: {e}")
            return []

    def get_conversation_by_session(self, session_id: str) -> List[Dict]:
        """セッションIDで会話履歴を取得"""
        try:
            query = """
            SELECT * FROM c 
            WHERE c.session_id = @session_id 
            ORDER BY c.timestamp ASC
            """
            parameters = [{"name": "@session_id", "value": session_id}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            logger.info(f"Retrieved {len(items)} conversations for session: {session_id}")
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error retrieving session conversations: {e}")
            return []

    def delete_user_conversations(self, user_email: str) -> int:
        """ユーザーのすべての会話を削除"""
        try:
            query = "SELECT c.id, c.user_email FROM c WHERE c.user_email = @user_email"
            parameters = [{"name": "@user_email", "value": user_email}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            deleted_count = 0
            for item in items:
                self.container.delete_item(
                    item=item['id'], 
                    partition_key=item['user_email']
                )
                deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} conversations for user: {user_email}")
            return deleted_count
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error deleting user conversations: {e}")
            return 0

# シングルトンインスタンス
cosmosdb_service = CosmosDBService()
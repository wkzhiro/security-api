#!/usr/bin/env python3
"""
MySQLから会話履歴を取得するスクリプト
"""

import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
import json
import sys
from config.settings import settings

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatHistoryRetriever:
    def __init__(self):
        self.connection = None
        self.connect()

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

    def get_all_conversations(self, limit: int = 100):
        """すべての会話履歴を取得"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT 
                cm.id,
                cm.session_id,
                cm.user_email,
                cm.message,
                cm.response,
                cm.created_at
            FROM chat_messages cm
            ORDER BY cm.created_at DESC 
            LIMIT %s
            """
            cursor.execute(query, (limit,))
            messages = cursor.fetchall()
            cursor.close()
            return messages
        except Error as e:
            logger.error(f"Error getting all conversations: {e}")
            return []

    def get_conversations_by_user(self, user_email: str, limit: int = 50):
        """特定ユーザーの会話履歴を取得"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT 
                cm.id,
                cm.session_id,
                cm.user_email,
                cm.message,
                cm.response,
                cm.created_at
            FROM chat_messages cm
            WHERE cm.user_email = %s
            ORDER BY cm.created_at DESC 
            LIMIT %s
            """
            cursor.execute(query, (user_email, limit))
            messages = cursor.fetchall()
            cursor.close()
            return messages
        except Error as e:
            logger.error(f"Error getting conversations for user {user_email}: {e}")
            return []

    def get_conversations_by_session(self, session_id: str):
        """特定セッションの会話履歴を取得"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT 
                cm.id,
                cm.session_id,
                cm.user_email,
                cm.message,
                cm.response,
                cm.created_at
            FROM chat_messages cm
            WHERE cm.session_id = %s
            ORDER BY cm.created_at ASC
            """
            cursor.execute(query, (session_id,))
            messages = cursor.fetchall()
            cursor.close()
            return messages
        except Error as e:
            logger.error(f"Error getting conversations for session {session_id}: {e}")
            return []

    def get_user_statistics(self):
        """ユーザー統計情報を取得"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT 
                user_email,
                total_messages,
                total_sessions,
                first_chat_at,
                last_chat_at,
                created_at
            FROM user_stats
            ORDER BY total_messages DESC
            """
            cursor.execute(query)
            stats = cursor.fetchall()
            cursor.close()
            return stats
        except Error as e:
            logger.error(f"Error getting user statistics: {e}")
            return []

    def get_sessions_by_user(self, user_email: str):
        """特定ユーザーのセッション一覧を取得"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT 
                cs.id,
                cs.session_id,
                cs.user_email,
                cs.created_at,
                COUNT(cm.id) as message_count
            FROM chat_sessions cs
            LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
            WHERE cs.user_email = %s
            GROUP BY cs.id, cs.session_id, cs.user_email, cs.created_at
            ORDER BY cs.created_at DESC
            """
            cursor.execute(query, (user_email,))
            sessions = cursor.fetchall()
            cursor.close()
            return sessions
        except Error as e:
            logger.error(f"Error getting sessions for user {user_email}: {e}")
            return []

    def search_conversations(self, search_term: str, limit: int = 50):
        """メッセージ内容で会話を検索"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT 
                cm.id,
                cm.session_id,
                cm.user_email,
                cm.message,
                cm.response,
                cm.created_at
            FROM chat_messages cm
            WHERE cm.message LIKE %s OR cm.response LIKE %s
            ORDER BY cm.created_at DESC 
            LIMIT %s
            """
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern, search_pattern, limit))
            messages = cursor.fetchall()
            cursor.close()
            return messages
        except Error as e:
            logger.error(f"Error searching conversations: {e}")
            return []

    def close(self):
        """データベース接続を閉じる"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")

def format_datetime(dt):
    """datetime オブジェクトを文字列に変換"""
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)

def print_conversations(conversations):
    """会話履歴を整形して表示"""
    if not conversations:
        print("会話履歴が見つかりませんでした。")
        return

    print(f"\n=== 会話履歴 ({len(conversations)}件) ===")
    for i, conv in enumerate(conversations, 1):
        print(f"\n[{i}] ID: {conv['id']} | セッション: {conv['session_id'][:8]}... | ユーザー: {conv['user_email']}")
        print(f"日時: {format_datetime(conv['created_at'])}")
        print(f"質問: {conv['message'][:100]}{'...' if len(conv['message']) > 100 else ''}")
        print(f"回答: {conv['response'][:100]}{'...' if len(conv['response']) > 100 else ''}")
        print("-" * 80)

def print_statistics(stats):
    """統計情報を整形して表示"""
    if not stats:
        print("統計情報が見つかりませんでした。")
        return

    print(f"\n=== ユーザー統計 ({len(stats)}人) ===")
    for i, stat in enumerate(stats, 1):
        print(f"[{i}] {stat['user_email']}")
        print(f"  総メッセージ数: {stat['total_messages']}")
        print(f"  初回チャット: {format_datetime(stat['first_chat_at'])}")
        print(f"  最終チャット: {format_datetime(stat['last_chat_at'])}")
        print()

def main():
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python get_chat_history.py all [limit]          # 全会話履歴を取得")
        print("  python get_chat_history.py user <email> [limit] # 特定ユーザーの会話履歴")
        print("  python get_chat_history.py session <session_id> # 特定セッションの会話履歴")
        print("  python get_chat_history.py search <term> [limit] # メッセージ内容で検索")
        print("  python get_chat_history.py stats                # ユーザー統計情報")
        print("  python get_chat_history.py sessions <email>     # ユーザーのセッション一覧")
        return

    try:
        retriever = ChatHistoryRetriever()
        command = sys.argv[1]

        if command == "all":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            conversations = retriever.get_all_conversations(limit)
            print_conversations(conversations)

        elif command == "user":
            if len(sys.argv) < 3:
                print("ユーザーメールアドレスを指定してください。")
                return
            user_email = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 50
            conversations = retriever.get_conversations_by_user(user_email, limit)
            print_conversations(conversations)

        elif command == "session":
            if len(sys.argv) < 3:
                print("セッションIDを指定してください。")
                return
            session_id = sys.argv[2]
            conversations = retriever.get_conversations_by_session(session_id)
            print_conversations(conversations)

        elif command == "search":
            if len(sys.argv) < 3:
                print("検索語を指定してください。")
                return
            search_term = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 50
            conversations = retriever.search_conversations(search_term, limit)
            print_conversations(conversations)

        elif command == "stats":
            stats = retriever.get_user_statistics()
            print_statistics(stats)

        elif command == "sessions":
            if len(sys.argv) < 3:
                print("ユーザーメールアドレスを指定してください。")
                return
            user_email = sys.argv[2]
            sessions = retriever.get_sessions_by_user(user_email)
            if sessions:
                print(f"\n=== {user_email} のセッション一覧 ===")
                for session in sessions:
                    print(f"セッションID: {session['session_id']}")
                    print(f"  作成日時: {format_datetime(session['created_at'])}")
                    print(f"  メッセージ数: {session['message_count']}")
                    print()
            else:
                print("セッションが見つかりませんでした。")

        else:
            print(f"不明なコマンド: {command}")

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"エラーが発生しました: {e}")

    finally:
        if 'retriever' in locals():
            retriever.close()

if __name__ == "__main__":
    main()
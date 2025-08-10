#!/usr/bin/env python3
"""
データベースとテーブルのセットアップスクリプト
"""

import mysql.connector
from mysql.connector import Error
import logging
from config.settings import settings

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_database():
    """MySQLデータベースを作成"""
    connection = None
    try:
        # データベースを指定せずに接続
        connection = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD
        )
        
        cursor = connection.cursor()
        
        # データベースを作成（存在しない場合）
        database_name = settings.MYSQL_DATABASE
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        cursor.execute(f"USE {database_name}")
        
        logger.info(f"Database '{database_name}' created or verified successfully")
        
        # テーブルを作成
        create_tables(cursor)
        
        connection.commit()
        logger.info("Database setup completed successfully")
        
    except Error as e:
        logger.error(f"Error creating database: {e}")
        if connection:
            connection.rollback()
        raise
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            logger.info("MySQL connection closed")

def create_tables(cursor):
    """必要なテーブルを作成"""
    
    # chat_sessions テーブル
    create_sessions_table = """
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INT PRIMARY KEY AUTO_INCREMENT,
        user_email VARCHAR(255) NOT NULL,
        session_id VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_user_email (user_email),
        INDEX idx_session_id (session_id),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    cursor.execute(create_sessions_table)
    logger.info("Table 'chat_sessions' created or verified successfully")
    
    # chat_messages テーブル（会話履歴用）
    create_messages_table = """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INT PRIMARY KEY AUTO_INCREMENT,
        session_id VARCHAR(255) NOT NULL,
        user_email VARCHAR(255) NOT NULL,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_session_id (session_id),
        INDEX idx_user_email (user_email),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    cursor.execute(create_messages_table)
    logger.info("Table 'chat_messages' created or verified successfully")
    
    # user_stats テーブル（オプション：統計情報用）
    create_user_stats_table = """
    CREATE TABLE IF NOT EXISTS user_stats (
        id INT PRIMARY KEY AUTO_INCREMENT,
        user_email VARCHAR(255) NOT NULL UNIQUE,
        total_messages INT DEFAULT 0,
        total_sessions INT DEFAULT 0,
        first_chat_at TIMESTAMP NULL,
        last_chat_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_user_email (user_email),
        INDEX idx_last_chat_at (last_chat_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    cursor.execute(create_user_stats_table)
    logger.info("Table 'user_stats' created or verified successfully")

def verify_connection():
    """データベース接続をテスト"""
    try:
        connection = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            logger.info(f"Connected to MySQL Server version: {version[0]}")
            
            # テーブル一覧を表示
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            logger.info("Available tables:")
            for table in tables:
                logger.info(f"  - {table[0]}")
                
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        logger.error(f"Error verifying connection: {e}")
        return False

def main():
    """メイン実行関数"""
    logger.info("Starting database setup...")
    
    # 環境変数の確認
    required_settings = [
        settings.MYSQL_HOST,
        settings.MYSQL_USER,
        settings.MYSQL_PASSWORD,
        settings.MYSQL_DATABASE
    ]
    
    if not all(required_settings):
        logger.error("Missing required MySQL configuration. Please check your .env file.")
        return False
    
    logger.info(f"MySQL Configuration:")
    logger.info(f"  Host: {settings.MYSQL_HOST}")
    logger.info(f"  Port: {settings.MYSQL_PORT}")
    logger.info(f"  User: {settings.MYSQL_USER}")
    logger.info(f"  Database: {settings.MYSQL_DATABASE}")
    
    try:
        # データベースとテーブルを作成
        create_database()
        
        # 接続テスト
        if verify_connection():
            logger.info("✅ Database setup completed successfully!")
            return True
        else:
            logger.error("❌ Database setup failed during verification")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
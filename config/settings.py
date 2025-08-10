import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Azure OpenAI設定
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    # MySQL設定
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "chatbot_db")
    
    # CosmosDB設定
    COSMOSDB_ENDPOINT: str = os.getenv("COSMOSDB_ENDPOINT", "")
    COSMOSDB_KEY: str = os.getenv("COSMOSDB_KEY", "")
    COSMOSDB_DATABASE_NAME: str = os.getenv("COSMOSDB_DATABASE_NAME", "chatbot")
    COSMOSDB_CONTAINER_NAME: str = os.getenv("COSMOSDB_CONTAINER_NAME", "conversations")
    
    # API設定
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

settings = Settings()
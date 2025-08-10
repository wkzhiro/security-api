import logging
from openai import AzureOpenAI
from config.settings import settings

logger = logging.getLogger(__name__)

class AzureOpenAIService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    async def generate_response(self, user_message: str) -> str:
        """Azure OpenAIを使用してユーザーメッセージに対する応答を生成する"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system", 
                        "content": "あなたは親切で丁寧なAIアシスタントです。ユーザーの質問に対して、わかりやすく正確な回答を提供してください。日本語で回答してください。"
                    },
                    {
                        "role": "user", 
                        "content": user_message
                    }
                ]
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                return "申し訳ありません。応答を生成できませんでした。"
                
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {str(e)}")
            return f"エラーが発生しました: {str(e)}"

# シングルトンインスタンス
azure_openai_service = AzureOpenAIService()
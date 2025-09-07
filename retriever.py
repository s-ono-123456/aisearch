from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema import BaseRetriever, Document
from typing import List, Optional
import requests
import json
from langchain_openai import OpenAIEmbeddings
import logging
from logging_config import configure_logging


configure_logging()
logger = logging.getLogger(__name__)


embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large"
)


class AzureAISearchRetriever(BaseRetriever):
    """
    AzureAISearchRetriever retriever.
    """
    service_name: str
    api_key: str
    index_name: str
    api_version: str = '2024-07-01'
    qa_content_key: str
    qa_top: int
    qa_scoring_profile: str
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        # ヘッダーの設定
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }
        # リクエストのパラメータ
        body = json.dumps({
            'count' : True,
            'search': query,  # ここにクエリを設定
            'scoringProfile': self.qa_scoring_profile,  # スコアリングプロファイルの適用
            'top': self.qa_top,  # 上位から指定された個数文を検索に加える
            'vectorQueries': [
                {
                    "kind": "text",
                    "fields": "text_vector",
                    "k": self.qa_top,
                    "text": query,
                }
            ],
            "select": "id,text,title,imagebloburls,parent_filename,image_filenames"  # 取得するフィールドを指定
        })
        # リクエスト URL の構築
        url = f'{self.service_name}/indexes/{self.index_name}/docs/search?api-version={self.api_version}'
        # リクエストの実行
        response = requests.post(url, headers=headers, data=body)
        # レスポンスの確認
        if response.status_code == 200:
            try:
                # JSONレスポンスの取得
                data = response.json()
                # 各結果を Document オブジェクトに変換
                documents = []
                for item in data.get("value", []):
                    answer = item.get(self.qa_content_key)
                    if answer:
                        metadata = {k: v for k, v in item.items() if k != self.qa_content_key}
                        doc = Document(page_content=answer, metadata=metadata)
                        documents.append(doc)
                return documents
            except Exception as e:
                # JSON解析エラーの場合
                logger.exception("JSON解析エラー: %s", e)
                logger.debug("レスポンス内容: %s", response.text)
        else:
            # リクエスト失敗の場合
            logger.error("リクエスト失敗: ステータスコード %s", response.status_code)
            logger.debug("レスポンス内容: %s", response.text)



if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    # Azure AI Searchの設定（必要に応じて値を変更してください）
    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
    AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
    # テストコード
    retriever = AzureAISearchRetriever(
        service_name=AZURE_SEARCH_ENDPOINT,
        api_key=AZURE_SEARCH_API_KEY,
        index_name=AZURE_SEARCH_INDEX,
        qa_content_key="text",
        qa_top=5,
        qa_scoring_profile=""
    )

    query = "パスワードの暗号化方式は？"
    results = retriever.invoke(query)

    for doc in results:
        logger.info("Content: %s", doc.page_content)
        logger.info("Metadata: %s", doc.metadata)
        logger.info("-----")
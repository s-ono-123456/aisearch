# 画像リンク入りMarkdown分割＆Azure AI Search投入プログラム
import re
import os
import requests
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from blobstorage import upload_image_to_blob_storage_via_restapi
from azureaisearch import upload_to_azure_search
import logging
from logging_config import configure_logging


# ロギングを初期化（既に設定済みなら再設定しない）
configure_logging()
logger = logging.getLogger(__name__)


# .envファイルから環境変数を読み込む
load_dotenv()
# OpenAI APIキー
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Markdownファイルのパス
MARKDOWN_DIR = os.getenv("MARKDOWN_DIR")

# 画像リンク抽出用の正規表現
IMAGE_PATTERN = r'!\[.*?\]\((.*?)\)'

# LangChainのRecursiveCharacterTextSplitterでMarkdownテキストを分割する関数
def split_markdown_by_recursive_splitter(markdown_text):
    """
    LangChainのRecursiveCharacterTextSplitterを使ってMarkdownテキストを分割する関数
    """
    # chunk_sizeやchunk_overlapは用途に応じて調整可能
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # 1チャンクの最大文字数
        chunk_overlap=50,  # チャンク間の重複文字数
        separators=["\n\n", "\n", "。", ".", "!", "?", " "]  # Markdownに適した区切り
    )
    # 分割結果をリストで返す
    return splitter.split_text(markdown_text)


def main():
    # markdownディレクトリ内の全mdファイルを処理
    md_files = [f for f in os.listdir(MARKDOWN_DIR) if f.endswith('.md')]
    # OpenAI埋め込みモデルの初期化（1回だけ）
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        openai_api_key=OPENAI_API_KEY
    )

    for md_file in md_files:
        md_path = os.path.join(MARKDOWN_DIR, md_file)
        # Markdownファイルを読み込む
        with open(md_path, "r", encoding="utf-8") as f:
            markdown_text = f.read()

        mdfilename = os.path.basename(md_path)
        logger.info("タイトル: %s", mdfilename)

        # LangChainのRecursiveCharacterTextSplitterでMarkdownを分割
        chunks = split_markdown_by_recursive_splitter(markdown_text)

        docs = []
        for i, text in enumerate(chunks):
            image_blobs = []
            if re.search(IMAGE_PATTERN, text):
                image_links = re.findall(IMAGE_PATTERN, text)
                image_blobs = image_links
            
            imagebloburls = []
            image_filenames = []
            # 画像をAzure Blob StorageにアップロードしてURLを取得
            for image_link in image_blobs:
                # 画像ファイル名を取得
                image_filename = os.path.join(MARKDOWN_DIR, image_link)

                # 画像をAzure Blob Storageにアップロード
                response = upload_image_to_blob_storage_via_restapi(
                    blob_path=f"/{mdfilename}/{image_link}",  # アップロード先のBlobパス
                    image_path=image_filename,  # アップロードする画像ファイルのパス
                )
                if response.status_code == 201:
                    # アップロード成功時、BlobのURLを取得
                    blob_path = f"/{mdfilename}/{image_link}"
                    imagebloburls.append(blob_path)
                    image_filenames.append(image_link)
                else:
                    logger.error("画像アップロード失敗: %s", image_filename)

            doc = {
                "text": text,
                "imagebloburls": imagebloburls,
                "parent_filename": mdfilename,
                "image_filenames": image_filenames
            }
            # テキスト埋め込みベクトル化
            if text.strip():
                # ベクトル化（LangChainのembed_documentsはリストで渡す必要あり）
                vector = embeddings.embed_documents([text.strip()])[0]
                doc["text_vector"] = vector
            docs.append(doc)

        # Azure AI Searchにアップロード
        upload_to_azure_search(docs)

if __name__ == "__main__":
    main()


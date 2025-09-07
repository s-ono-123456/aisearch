
import requests
import mimetypes  # Content-Type自動判定用
from dotenv import load_dotenv
import os
import logging
from logging_config import configure_logging


# ロギング初期化
configure_logging()
logger = logging.getLogger(__name__)

load_dotenv()

BLOB_BASE_URL = os.getenv("BLOB_BASE_URL")
SAS_TOKEN = os.getenv("SAS_TOKEN")

# ファイルのContent-Typeを自動判定する関数
def get_content_type(file_path):
    """
    ファイルパスからContent-Type（MIMEタイプ）を自動判定して返す関数
    """
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/octet-stream'  # 判定できない場合のデフォルト
    return content_type

# requestsを使ってAzure Blob Storageに画像をアップロードする関数
def upload_image_to_blob_storage_via_restapi(blob_path, image_path):
    """
    requestsライブラリでAzure Blob Storageに画像をアップロードする関数
    :param blob_path: アップロード先のBlobのPath（例: "/test.md/images/myimage.png"）
    :param image_path: アップロードする画像ファイルのパス
    :return: レスポンスオブジェクト
    """

    # 画像ファイルをバイナリで読み込む
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Content-Typeを自動判定
    content_type = get_content_type(image_path)

    # ヘッダー設定（自動判定したContent-Typeを使用）
    headers = {
        "x-ms-blob-type": "BlockBlob",
        "Content-Type": content_type
    }

    # SASトークン付きURLを作成
    upload_url = f"{BLOB_BASE_URL}{blob_path}?{SAS_TOKEN}"
    # PUTリクエストでアップロード
    response = requests.put(upload_url, headers=headers, data=image_data)
    # ステータスコードで結果を判定
    if response.status_code == 201:
        logger.info("アップロード成功: %s", upload_url)
    else:
        logger.error("アップロード失敗: %s %s", response.status_code, response.text)
    return response

# 指定パスのファイルをAzure Blob Storageからダウンロードする関数
def download_file_from_blob_storage_via_restapi(blob_path, save_path=None):
    """
    Azure Blob Storageから指定パスのファイルをダウンロードする関数
    :param blob_path: ダウンロードするBlobのPath（例: "/test.md/images/myimage.png"）
    :param save_path: 保存先のファイルパス（省略時は返却のみ）
    :return: ファイルデータ（バイナリ）
    """
    # SASトークン付きURLを作成
    download_url = f"{BLOB_BASE_URL}{blob_path}?{SAS_TOKEN}"
    # GETリクエストでダウンロード
    response = requests.get(download_url)
    if response.status_code == 200:
        file_data = response.content
        # 保存先パスが指定されていればファイルに保存
        if save_path:
            static_save_path = os.path.join("static", save_path.lstrip("/"))
            os.makedirs(os.path.dirname(static_save_path), exist_ok=True)
            with open(static_save_path, "wb") as f:
                f.write(file_data)
        logger.info("ダウンロード成功: %s", download_url)
        return file_data
    else:
        logger.error("ダウンロード失敗: %s %s", response.status_code, response.text)
        return None

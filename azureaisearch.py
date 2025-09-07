import requests
import os
from dotenv import load_dotenv
import re
import logging
from logging_config import configure_logging

# ロギングを初期化（既に設定済みなら再設定しない）
configure_logging()
logger = logging.getLogger(__name__)

load_dotenv()
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

def upload_to_azure_search(docs):
    """
    Azure AI Searchにドキュメントをアップロードする関数
    """
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX}/docs/search.index?api-version=2024-07-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_API_KEY
    }

    # --- 追加: parent_filename一致データの削除 ---
    parent_filename = docs[0]["parent_filename"] if docs else None
    if parent_filename:
        # 検索APIでparent_filename一致のドキュメントIDを取得
        search_url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX}/docs/search?api-version=2024-07-01"
        search_body = {
            "search": "*",
            "filter": f"parent_filename eq '{parent_filename}'",
            "select": "id"
        }
        search_resp = requests.post(search_url, headers=headers, json=search_body)
        if search_resp.status_code == 200:
            results = search_resp.json()
            delete_ids = [doc["id"] for doc in results.get("value", [])]
            if delete_ids:
                # 削除リクエストを送信
                delete_docs = [{"@search.action": "delete", "id": id} for id in delete_ids]
                delete_data = {"value": delete_docs}
                delete_resp = requests.post(url, headers=headers, json=delete_data)
                logger.info(f"削除レスポンス: {delete_resp.status_code} {delete_resp.text}")
        else:
            logger.error(f"検索API失敗: {search_resp.status_code} {search_resp.text}")

    # --- 通常のアップロード処理 ---
    # parent_filenameからidに使えない文字（英字・数字・_・-・=以外）を_に置換する
    safe_parent_filename = re.sub(r'[^A-Za-z0-9_\-=]', '_', parent_filename)
    id_prefix = "doc_" + safe_parent_filename + "_"
    list_docs = []
    for i, doc in enumerate(docs):
        list_docs.append({
            "@search.action": "upload",
            "text": doc["text"],
            "id": id_prefix + str(i + 1),
            "parent_filename": doc["parent_filename"],
            "title": doc["parent_filename"],
            # ベクトル埋め込みをtext_vectorに格納
            "text_vector": doc["text_vector"],
            "imagebloburls": doc["imagebloburls"],
            "image_filenames": doc["image_filenames"]
        })
    data = {"value": list_docs}
    resp = requests.post(url, headers=headers, json=data)
    logger.info(f"Azure Searchレスポンス: {resp.status_code} {resp.text}")

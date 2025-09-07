import streamlit as st
from retriever import AzureAISearchRetriever
from dotenv import load_dotenv
import os
import re
from blobstorage import download_file_from_blob_storage_via_restapi
from langchain_openai import ChatOpenAI
import base64
import filetype
from langchain_core.output_parsers import StrOutputParser
from prompt import create_prompt_with_images
from markdown_utils import split_by_image_links, extract_image_links
import logging
from logging_config import configure_logging


# ロギング初期化
configure_logging()
logger = logging.getLogger(__name__)


def load_settings():
    """環境変数から設定を読み込む。"""
    load_dotenv()
    return {
        "AZURE_SEARCH_ENDPOINT": os.getenv("AZURE_SEARCH_ENDPOINT"),
        "AZURE_SEARCH_INDEX": os.getenv("AZURE_SEARCH_INDEX"),
        "AZURE_SEARCH_API_KEY": os.getenv("AZURE_SEARCH_API_KEY"),
    }


def init_services(settings):
    """Retriever と LLM を初期化して返す。"""
    # ... 簡易的に None チェックを行う
    if not settings.get("AZURE_SEARCH_ENDPOINT") or not settings.get("AZURE_SEARCH_API_KEY"):
        logger.warning("Azure Search のエンドポイントまたは API キーが見つかりません。環境変数を確認してください。")

    retriever = AzureAISearchRetriever(
        service_name=settings.get("AZURE_SEARCH_ENDPOINT"),
        api_key=settings.get("AZURE_SEARCH_API_KEY"),
        index_name=settings.get("AZURE_SEARCH_INDEX"),
        qa_content_key="text",
        qa_top=3,
        qa_scoring_profile="",
    )

    llm = ChatOpenAI(temperature=0, model_name="gpt-4.1")
    return retriever, llm


def download_image_and_prepare_template(img_filename, blob_url):
    """Blob Storage から画像を取得し、Streamlit 表示と LLM に渡すための image_template を作る。

    戻り値: (image_bytes, image_template) -- image_bytes は表示用、image_template は prompt 用
    """
    try:
        logger.info("Downloading image: %s", img_filename)
        img = download_file_from_blob_storage_via_restapi(blob_url, save_path=None)
    except Exception as e:
        logger.exception("画像のダウンロードに失敗しました: %s", e)
        return None, None

    # MIMEタイプ判定
    kind = filetype.guess(img)
    mime_type = kind.mime if kind is not None else "application/octet-stream"

    # AIに渡すためのBase64エンコード
    try:
        base64_string = base64.b64encode(img).decode("utf-8")
    except Exception:
        logger.exception("画像の Base64 エンコードに失敗しました")
        return img, None

    image_template = {
        "type": "image_url",
        "image_url": {"url": f"data:{mime_type};base64,{base64_string}"},
    }

    return img, image_template


def process_search_results(results, tabs):
    """検索結果を Streamlit に表示しつつ、references と image_templates を組み立てる。

    戻り値: (references_str, image_templates, imagedict_all)
    """
    references = ""
    image_templates = []
    imagedict_all = {}

    for result in results:
        title = result.metadata.get("title", "(無題)")
        image_filenames = result.metadata.get("image_filenames", [])
        imagebloburls = result.metadata.get("imagebloburls", [])
        imagedict = dict(zip(image_filenames, imagebloburls))
        imagedict_all.update(imagedict)
        logger.debug("imagedict: %s", imagedict)

        content = result.page_content
        with tabs[1], st.expander(f"{title}"):
            parts_content = split_by_image_links(content)
            for part in parts_content:
                references += part + "\n"
                if re.match(r'!\[.*?\]\(.*?\)', part):
                    img_filename = extract_image_links(part)[0] if extract_image_links(part) else None
                    if img_filename and img_filename in imagedict:
                        blob_url = imagedict[img_filename]
                        img, template = download_image_and_prepare_template(img_filename, blob_url)
                        if img is not None:
                            st.image(img, caption=img_filename)
                        if template is not None:
                            image_templates.append(template)
                else:
                    st.markdown(part)

    return references, image_templates, imagedict_all


def generate_answer(user_input, references, image_templates, llm):
    """プロンプトを作成して LLM に問い合わせ、結果を返す。"""
    prompt = create_prompt_with_images(image_templates)

    # パイプラインを組み立てる（元と同じ挙動を保つ）
    rag_chain = (
        prompt
        | llm
        | StrOutputParser()
    )

    result = rag_chain.invoke({"question": user_input, "references": references})
    return result


def main():
    """Streamlit アプリのエントリポイント。"""
    st.title("Azure AI Search チャットアプリ")

    settings = load_settings()
    retriever, llm = init_services(settings)

    # チャット履歴を保存するためのセッションステート
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_input = st.text_input("質問を入力してください：")

    if st.button("送信") and user_input:
        # Azure Searchで情報を検索
        try:
            results = retriever.invoke(user_input)
        except Exception as e:
            logger.exception("検索中にエラーが発生しました: %s", e)
            st.error("検索中にエラーが発生しました。ログを確認してください。")
            return

        tabs = st.tabs(["回答", "参考情報"])
        with tabs[0]:
            st.subheader("AIの回答")
        with tabs[1]:
            st.subheader("参考情報")

        if results:
            references, image_templates, imagedict_all = process_search_results(results, tabs)

            # LLM に渡して回答生成
            answer = generate_answer(user_input, references, image_templates, llm)

            # 回答の表示（画像リンクを含む可能性があるため分割して処理）
            with tabs[0]:
                parts_result = split_by_image_links(answer)
                for part in parts_result:
                    if re.match(r'!\[.*?\]\(.*?\)', part):
                        img_filename = extract_image_links(part)[0] if extract_image_links(part) else None
                        if img_filename and img_filename in imagedict_all:
                            blob_url = imagedict_all[img_filename]
                            img = download_file_from_blob_storage_via_restapi(blob_url, save_path=None)
                            st.image(img, caption=img_filename)
                    else:
                        st.markdown(part)
        else:
            with tabs[0]:
                st.markdown("参考になる情報が見つかりませんでした。")
            with tabs[1]:
                st.markdown("参考になる情報が見つかりませんでした。")


if __name__ == "__main__":
    main()


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

load_dotenv()
# Azure AI Searchの設定（必要に応じて値を変更してください）
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

# AzureAI Search Retrieverの初期化
retriever = AzureAISearchRetriever(
    service_name=AZURE_SEARCH_ENDPOINT,
    api_key=AZURE_SEARCH_API_KEY,
    index_name=AZURE_SEARCH_INDEX,
    qa_content_key="text",
    qa_top=3,
    qa_scoring_profile=""
)

llm = ChatOpenAI(temperature=0, model_name="gpt-4.1")

# チャット履歴を保存するためのセッションステート
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

st.title("Azure AI Search チャットアプリ")

# ユーザーからの質問入力
user_input = st.text_input("質問を入力してください：")

if st.button("送信") and user_input:
    # Azure Searchで情報を検索
    results = retriever.invoke(user_input)
    answer = ""
    references = []
    tabs = st.tabs(["回答", "参考情報"])
    with tabs[0]:
        st.subheader("AIの回答")
    with tabs[1]:
        st.subheader("参考情報")

    references = ""
    imagedict_all = {}
    if results:
        # 検索結果から参考情報を抽出
        image_templates = []
        for result in results:
            title = result.metadata["title"]
            image_filenames = result.metadata["image_filenames"]
            imagebloburls = result.metadata["imagebloburls"]
            imagedict = dict(zip(image_filenames, imagebloburls))
            imagedict_all.update(imagedict)
            print(imagedict)

            content = result.page_content
            with tabs[1]:
                st.markdown(f"### {title}")
                # 画像リンク単位で分割（画像リンクは単独の要素として保持される）
                parts_content = split_by_image_links(content)
                for part in parts_content:
                    # プロンプトに追加
                    references += part + "\n"
                    if re.match(r'!\[.*?\]\(.*?\)', part):
                        # 画像リンクの部分: 丸かっこ内を抽出
                        img_filename = extract_image_links(part)[0] if extract_image_links(part) else None
                        if img_filename and img_filename in imagedict:
                            print(f"Downloading image: {img_filename}")
                            blob_url = imagedict[img_filename]
                            print(f"Blob URL: {blob_url}")
                            # Blob Storageから画像をダウンロード
                            img = download_file_from_blob_storage_via_restapi(blob_url, save_path=None)
                            st.image(img, caption=img_filename)

                            # 画像データからMIMEタイプを自動判定
                            kind = filetype.guess(img)
                            if kind is not None:
                                mime_type = kind.mime
                            else:
                                mime_type = "application/octet-stream"  # 不明な場合

                            # AIに渡すためのBase64エンコード
                            base64_string = base64.b64encode(img).decode("utf-8")
                            image_template = {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{base64_string}"},
                            }
                            image_templates.append(image_template)
                    else:
                        # テキストの部分
                        st.markdown(part)
        
        
        
        prompt = create_prompt_with_images(image_templates)

        rag_chain = (
            prompt
            | llm
            | StrOutputParser() 
        )

        result = rag_chain.invoke({"question": user_input, "references": references})

        with tabs[0]:

            parts_result = split_by_image_links(result)
            for part in parts_result:
                if re.match(r'!\[.*?\]\(.*?\)', part):
                    # 画像リンクの部分: 丸かっこ内を抽出
                    img_filename = extract_image_links(part)[0] if extract_image_links(part) else None
                    if img_filename and img_filename in imagedict_all:
                        blob_url = imagedict_all[img_filename]
                        # Blob Storageから画像をダウンロード
                        img = download_file_from_blob_storage_via_restapi(blob_url, save_path=None)
                        st.image(img, caption=img_filename)
                else:
                    # テキストの部分
                    st.markdown(part)

    else:
        with tabs[0]:
            st.markdown("参考になる情報が見つかりませんでした。")   
        with tabs[1]:
            st.markdown("参考になる情報が見つかりませんでした。")


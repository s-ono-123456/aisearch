# AISearch プロジェクト README

このプロジェクトは、Markdownファイルや画像ファイルをAzure Cognitive Searchにアップロードし、Streamlitアプリで検索・表示できるPythonベースのシステムです。
各種スクリプトやWebアプリを通じて、ドキュメント検索体験を提供します。

## ディレクトリ構成

```
requirements.txt                # 必要なPythonパッケージ一覧
upload_to_azure_search.py       # Azure Searchへのアップロード用スクリプト
app.py                         # Streamlitによる検索Webアプリ
retriever.py                   # Azure Searchから検索・取得するためのモジュール
markdown/                      # アップロード対象のMarkdownファイルや画像
  └─ test.md                   # サンプルMarkdownファイル
  └─ image/                    # 画像ファイル格納ディレクトリ
      └─ image.png             # サンプル画像
      └─ image2.png            # サンプル画像
static/                        # Webアプリで利用する静的ファイル（画像等）
  └─ image/                    # 表示用画像
      └─ image.png
      └─ image2.png
```

## 必要な環境
- Python 3.8以上
- Azure Cognitive Search サービス
 - Streamlit

## セットアップ方法
1. 必要なパッケージをインストールします。
   ```powershell
   pip install -r requirements.txt
   ```
2. `upload_to_azure_search.py` を編集し、Azure SearchのエンドポイントやAPIキーなどの設定を行います。

## 使い方の流れ
1. Markdownや画像ファイルを `markdown/` ディレクトリに配置します。
2. PowerShellで以下のコマンドを実行し、Azure Cognitive Searchにアップロードします。
   ```powershell
   python .\upload_to_azure_search.py
   ```
3. Streamlitアプリを起動し、検索・閲覧を行います。
   ```powershell
   streamlit run .\app.py --server.enableStaticServing=true
   ```
4. Webブラウザで表示されるUIから、アップロードしたドキュメントや画像を検索・閲覧できます。

## 実行方法

### Azure Searchへのアップロード
```powershell
python .\upload_to_azure_search.py
```

### Streamlitアプリの起動
```powershell
streamlit run .\app.py --server.enableStaticServing=true
```

## 注意事項
- Azureの設定情報（APIキー等）は漏洩しないように管理してください。
- `requirements.txt` に記載されたパッケージがすべてインストールされていることを確認してください。

---
## 補足
- `retriever.py` はAzure Searchから検索結果を取得するためのモジュールです。
- `static/` ディレクトリはWebアプリで表示する画像等の静的ファイルを格納します。

---

何かご不明点があれば、`upload_to_azure_search.py` のコメントやコードをご参照ください。

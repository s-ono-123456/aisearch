# AISearch プロジェクト README

このリポジトリは、ローカルの Markdown や画像を Azure AI Search へアップロードし、`Streamlit` アプリで検索・閲覧するためのサンプル実装です。

## 主要ファイルと構成

```
requirements.txt                # 必要な Python パッケージ
upload_to_azure_search.py       # Markdown/画像を解析して Azure Search にアップロードするスクリプト
app.py                         # Streamlit による検索 Web アプリ（起動コマンドで表示）
retriever.py                   # Azure Search から検索・取得するヘルパー
markdown/                       # アップロード対象の Markdown ファイルや画像
   ├─ test.md                    # サンプル Markdown
   └─ image/                      # サンプル画像ディレクトリ
         ├─ image.png
         └─ image2.png
``` 

## 前提・必要環境

- Python 3.8 以上
- Azure AI Search のサービスとアクセスキー
- Streamlit（UI 起動に使用）

※ Azure のクレデンシャルは環境変数か設定ファイルで安全に管理してください（下記参照）。

## セットアップ（Windows PowerShell）

1. 仮想環境を作成して有効化（任意だが推奨）:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. 依存パッケージをインストール:

```powershell
pip install -r requirements.txt
```

3. Azure の設定を行う

upload スクリプト `upload_to_azure_search.py` は、Azure のエンドポイントとキーを参照してインデックス作成／ドキュメント登録を行います。設定方法は次のいずれかを採用してください:

- 環境変数（推奨）:

```powershell
$env:AZURE_SEARCH_ENDPOINT = "https://<your-service-name>.search.windows.net"
$env:AZURE_SEARCH_API_KEY = "<your-admin-api-key>"
```

- または `upload_to_azure_search.py` 内の変数を直接編集して指定します（機密情報は直接コミットしないでください）。

具体的な変数名や使い方は `upload_to_azure_search.py` の冒頭コメントを参照してください。

## 使い方

1) コンテンツを準備

`markdown/` フォルダに Markdown ファイルや画像を置きます。

2) Azure Search へアップロード（インデックス作成とドキュメント登録）

```powershell
python .\upload_to_azure_search.py
```

3) Streamlit アプリを起動して検索 UI を開く

```powershell
streamlit run .\app.py --server.enableStaticServing=true
```

起動後、ブラウザに表示される UI から検索できます。

## 注意点・運用メモ

- Azure の API キーやエンドポイントは漏洩に注意してください。CI/CD や運用環境では Azure Key Vault 等を推奨します。
- `requirements.txt` に書かれているパッケージが環境にインストールされていることを確認してください。
- 大きなファイルや大量アップロードを行う場合は、API のスループットやレート制限、タイムアウトに注意してください。

## 開発者向け補足

- `retriever.py` は Azure Search からクエリを発行し、結果を整形して返すユーティリティです。Streamlit 側 (`app.py`) はこれを利用して検索結果を表示します。
- `upload_to_azure_search.py` を実行する前に、`markdown_utils.py` などのパーサーが期待するファイル形式でコンテンツを配置してください。

## 次のステップ（提案）

- エラーハンドリングやリトライの追加（大規模アップロード向け）
- テストスイート（upload/retriever のユニットテスト）追加
- Streamlit UI の静的アセット管理（`static/` を作成して画像配信を整備）


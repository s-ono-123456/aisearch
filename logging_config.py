"""
ロギング設定モジュール
アプリ全体で共通のロガー設定（コンソール出力とファイル出力）を行う。
複数回呼ばれても重複設定しないようにガードを入れてある。
"""
import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "log"
LOG_FILE = "app.log"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def configure_logging(log_file: str = f"{LOG_DIR}/{LOG_FILE}", level: str | None = None, console: bool = False):
    """
    ロギングを初期化する。すでにハンドラが設定されている場合は再設定を避ける。

    :param log_file: ログファイル名（ワーキングディレクトリに作成される）
    :param level: 環境変数等で指定されたログレベル（例: "DEBUG"）。None の場合は INFO を既定値とする。
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        # すでに設定済みなら何もしない
        return

    # ログレベルの決定
    env_level = os.getenv("LOG_LEVEL")
    if level:
        chosen_level = level
    elif env_level:
        chosen_level = env_level
    else:
        chosen_level = "INFO"

    numeric_level = getattr(logging, chosen_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # フォーマッタ
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # コンソールハンドラ: デフォルトでは無効。console=True の場合に追加する。
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(numeric_level)
        ch.setFormatter(formatter)
        root_logger.addHandler(ch)

    # ローテーティングファイルハンドラ（最大 5MB、バックアップ3世代）
    fh = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fh.setLevel(numeric_level)
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)

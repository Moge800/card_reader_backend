"""ロギング設定モジュール。

日次ローテーション付きのロガーを提供する。
"""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from src.config.settings import get_settings

# ログフォーマット
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _ensure_log_dir() -> Path:
    """ログディレクトリを作成する。

    Returns:
        Path: ログディレクトリのパス
    """
    settings = get_settings()
    log_dir = settings.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_logger(name: str) -> logging.Logger:
    """名前付きロガーを取得する。

    Args:
        name: ロガー名（通常は __name__ を渡す）

    Returns:
        logging.Logger: 設定済みのロガー
    """
    settings = get_settings()
    logger = logging.getLogger(name)

    # 既にハンドラが設定されている場合はスキップ
    if logger.handlers:
        return logger

    # ログレベル設定
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # フォーマッター
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラ（日次ローテーション）
    log_dir = _ensure_log_dir()
    log_file = log_dir / "app.log"
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,  # 30日分保持
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"
    logger.addHandler(file_handler)

    return logger

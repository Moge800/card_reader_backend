"""NFCカードリーダーバックエンドAPI エントリーポイント。

SONY RC-S300 NFCカードリーダー用のRESTful APIを提供する。
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

# srcディレクトリをパスに追加（絶対インポート対応）
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

import uvicorn
from fastapi import FastAPI

from src.api.routes import router
from src.config.settings import get_settings
from src.logging.logger import get_logger
from src.services.user_service import _ensure_csv_file

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """アプリケーションのライフサイクル管理。"""
    # 起動時の処理
    logger.info("Application starting...")
    _ensure_csv_file()
    logger.info("Application started successfully")

    yield

    # 終了時の処理
    logger.info("Application shutting down...")
    from src.nfc.reader import get_nfc_reader

    reader = get_nfc_reader()
    if reader.is_continuous_mode_running():
        reader.stop_continuous_mode()
    logger.info("Application shutdown complete")


# FastAPIアプリケーション
app = FastAPI(
    title="NFC Card Reader Backend API",
    description="SONY RC-S300 NFCカードリーダー用バックエンドAPI",
    version="0.1.0",
    lifespan=lifespan,
)

# ルーター登録
app.include_router(router)


@app.get("/", tags=["Health"])
def health_check() -> dict[str, str]:
    """ヘルスチェックエンドポイント。"""
    return {"status": "ok", "message": "NFC Card Reader Backend API is running"}


def main() -> None:
    """メイン関数。Uvicornサーバーを起動する。"""
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug_mode,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

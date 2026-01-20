"""環境変数管理モジュール。

Pydantic Settingsを使用して型安全に環境変数を読み込む。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定。

    環境変数から設定を読み込む。
    .envファイルが存在する場合は自動的に読み込まれる。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # NFC設定
    nfc_device_path: str = "usb:054c:06c1"

    # データ設定
    user_data_csv_path: Path = Path("data/users.csv")
    max_scan_buffer_size: int = 100

    # ログ設定
    log_dir: Path = Path("logs")
    log_level: str = "INFO"

    # セキュリティ
    admin_password: str = "change_me_in_production"

    # デバッグモード
    debug_mode: bool = False


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得する。

    Returns:
        Settings: アプリケーション設定
    """
    return Settings()

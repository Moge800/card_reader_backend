"""pytest共通フィクスチャ。"""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def temp_csv_file() -> Generator[Path, None, None]:
    """一時的なCSVファイルを作成するフィクスチャ。"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as f:
        f.write("uid_hex,id,name,email,role,description\n")
        f.write("0123456789ab,user001,テストユーザー,test@example.com,admin,テスト用\n")
        temp_path = Path(f.name)

    yield temp_path

    # クリーンアップ
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def mock_settings(temp_csv_file: Path) -> Generator[None, None, None]:
    """設定をモックするフィクスチャ。"""
    with patch("src.config.settings.get_settings") as mock:
        mock_settings = mock.return_value
        mock_settings.user_data_csv_path = temp_csv_file
        mock_settings.max_scan_buffer_size = 10
        mock_settings.log_dir = Path(tempfile.gettempdir()) / "test_logs"
        mock_settings.log_level = "DEBUG"
        mock_settings.admin_password = "test_password"
        mock_settings.debug_mode = True
        mock_settings.nfc_device_path = "usb:054c:06c1"
        yield


@pytest.fixture
def test_client(mock_settings: None) -> Generator[TestClient, None, None]:
    """FastAPIテストクライアントを提供するフィクスチャ。"""
    # 設定をモックした状態でアプリをインポート
    from main import app

    with TestClient(app) as client:
        yield client

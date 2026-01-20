"""ユーザーサービスのテスト。"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.schemas.models import UserData


class TestUserService:
    """ユーザーサービスのテスト。"""

    @pytest.fixture
    def temp_csv(self) -> Path:
        """一時CSVファイルを作成。"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("uid_hex,id,name,email,role,description\n")
            f.write(
                "0123456789ab,user001,テストユーザー,test@example.com,admin,テスト用\n"
            )
            f.write("abcdef123456,user002,ユーザー2,user2@example.com,user,説明2\n")
            return Path(f.name)

    @pytest.fixture
    def mock_csv_path(self, temp_csv: Path):
        """CSVパスをモック。"""
        with patch("src.services.user_service.get_settings") as mock:
            mock.return_value.user_data_csv_path = temp_csv
            yield temp_csv

    def test_lookup_user_found(self, mock_csv_path: Path) -> None:
        """存在するユーザーを検索できる。"""
        from src.services.user_service import lookup_user

        result = lookup_user("0123456789ab")
        assert result is not None
        assert result.uid_hex == "0123456789ab"
        assert result.name == "テストユーザー"
        assert result.role == "admin"

    def test_lookup_user_case_insensitive(self, mock_csv_path: Path) -> None:
        """UID検索は大文字小文字を区別しない。"""
        from src.services.user_service import lookup_user

        result = lookup_user("0123456789AB")  # 大文字
        assert result is not None
        assert result.uid_hex == "0123456789ab"

    def test_lookup_user_not_found(self, mock_csv_path: Path) -> None:
        """存在しないユーザーはNoneを返す。"""
        from src.services.user_service import lookup_user

        result = lookup_user("nonexistent123")
        assert result is None

    def test_register_user_new(self, mock_csv_path: Path) -> None:
        """新規ユーザーを登録できる。"""
        from src.services.user_service import lookup_user, register_user

        new_user = UserData(
            uid_hex="newuser12345",
            id="user003",
            name="新規ユーザー",
            email="new@example.com",
            role="guest",
            description="新規追加",
        )

        is_update = register_user(new_user)
        assert is_update is False  # 新規登録

        # 登録されたか確認
        result = lookup_user("newuser12345")
        assert result is not None
        assert result.name == "新規ユーザー"

    def test_register_user_update(self, mock_csv_path: Path) -> None:
        """既存ユーザーを上書き更新できる。"""
        from src.services.user_service import lookup_user, register_user

        updated_user = UserData(
            uid_hex="0123456789ab",
            id="user001",
            name="更新されたユーザー",
            email="updated@example.com",
            role="superadmin",
            description="更新済み",
        )

        is_update = register_user(updated_user)
        assert is_update is True  # 上書き更新

        # 更新されたか確認
        result = lookup_user("0123456789ab")
        assert result is not None
        assert result.name == "更新されたユーザー"
        assert result.role == "superadmin"

    def test_delete_user_success(self, mock_csv_path: Path) -> None:
        """ユーザーを削除できる。"""
        from src.services.user_service import delete_user, lookup_user

        # 削除前は存在する
        assert lookup_user("0123456789ab") is not None

        result = delete_user("0123456789ab")
        assert result is True

        # 削除後は存在しない
        assert lookup_user("0123456789ab") is None

    def test_delete_user_not_found(self, mock_csv_path: Path) -> None:
        """存在しないユーザーの削除はFalseを返す。"""
        from src.services.user_service import delete_user

        result = delete_user("nonexistent123")
        assert result is False

    def test_get_all_users(self, mock_csv_path: Path) -> None:
        """全ユーザーを取得できる。"""
        from src.services.user_service import get_all_users

        users = get_all_users()
        assert len(users) == 2
        assert users[0].uid_hex == "0123456789ab"
        assert users[1].uid_hex == "abcdef123456"


class TestCsvTemplateCreation:
    """CSVテンプレート自動生成のテスト。"""

    def test_ensure_csv_file_creates_template(self) -> None:
        """CSVファイルが存在しない場合はテンプレートが作成される。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "data" / "users.csv"

            with patch("src.services.user_service.get_settings") as mock:
                mock.return_value.user_data_csv_path = csv_path

                from src.services.user_service import _ensure_csv_file

                result = _ensure_csv_file()

                assert result == csv_path
                assert csv_path.exists()

                # ヘッダーが正しいか確認
                with open(csv_path, encoding="utf-8") as f:
                    header = f.readline().strip()
                    assert header == "uid_hex,id,name,email,role,description"

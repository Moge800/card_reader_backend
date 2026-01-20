"""APIエンドポイントのテスト。"""

from unittest.mock import patch

from fastapi.testclient import TestClient


class TestHealthCheck:
    """ヘルスチェックエンドポイントのテスト。"""

    def test_health_check(self, test_client: TestClient) -> None:
        """ヘルスチェックが正常に動作する。"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "NFC Card Reader Backend API" in data["message"]


class TestReadEndpoint:
    """単発読み取りエンドポイントのテスト。"""

    def test_read_card_success(self, test_client: TestClient) -> None:
        """カード読み取り成功時にUIDが返される。"""
        with patch("src.api.routes.get_nfc_reader") as mock_reader:
            mock_reader.return_value.read_single.return_value = "0123456789ab"

            response = test_client.get("/read")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["uid_hex"] == "0123456789ab"

    def test_read_card_timeout(self, test_client: TestClient) -> None:
        """カード読み取りタイムアウト時はnullが返される。"""
        with patch("src.api.routes.get_nfc_reader") as mock_reader:
            mock_reader.return_value.read_single.return_value = None

            response = test_client.get("/read")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["uid_hex"] is None


class TestContinuousMode:
    """常時読み取りモードエンドポイントのテスト。"""

    def test_start_continuous_mode(self, test_client: TestClient) -> None:
        """常時読み取りモードを開始できる。"""
        with patch("src.api.routes.get_nfc_reader") as mock_reader:
            mock_reader.return_value.start_continuous_mode.return_value = True

            response = test_client.post("/continuous/start")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["is_running"] is True

    def test_start_continuous_mode_already_running(
        self, test_client: TestClient
    ) -> None:
        """既に実行中の場合はエラーメッセージが返される。"""
        with patch("src.api.routes.get_nfc_reader") as mock_reader:
            mock_reader.return_value.start_continuous_mode.return_value = False

            response = test_client.post("/continuous/start")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    def test_stop_continuous_mode(self, test_client: TestClient) -> None:
        """常時読み取りモードを停止できる。"""
        with patch("src.api.routes.get_nfc_reader") as mock_reader:
            mock_reader.return_value.stop_continuous_mode.return_value = True

            response = test_client.post("/continuous/stop")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["is_running"] is False

    def test_get_results(self, test_client: TestClient) -> None:
        """蓄積した結果を取得できる。"""
        with patch("src.api.routes.get_nfc_reader") as mock_reader:
            mock_reader.return_value.get_results_and_reset.return_value = [
                "uid1",
                "uid2",
                "uid3",
            ]

            response = test_client.get("/continuous/results")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 3
            assert data["uid_hex_list"] == ["uid1", "uid2", "uid3"]


class TestUserEndpoints:
    """ユーザー管理エンドポイントのテスト。"""

    def test_lookup_user_found(self, test_client: TestClient) -> None:
        """ユーザーが見つかった場合にデータが返される。"""
        with patch("src.api.routes.lookup_user_from_csv") as mock_lookup:
            from src.schemas.models import UserData

            mock_lookup.return_value = UserData(
                uid_hex="0123456789ab",
                id="user001",
                name="テストユーザー",
                email="test@example.com",
                role="admin",
                description="テスト用",
            )

            response = test_client.post(
                "/user/lookup", json={"uid_hex": "0123456789ab"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["found"] is True
            assert data["user"]["name"] == "テストユーザー"

    def test_lookup_user_not_found(self, test_client: TestClient) -> None:
        """ユーザーが見つからない場合はfoundがFalse。"""
        with patch("src.api.routes.lookup_user_from_csv") as mock_lookup:
            mock_lookup.return_value = None

            response = test_client.post("/user/lookup", json={"uid_hex": "nonexistent"})
            assert response.status_code == 200
            data = response.json()
            assert data["found"] is False
            assert data["user"] is None

    def test_register_user_new(self, test_client: TestClient) -> None:
        """新規ユーザーを登録できる。"""
        with patch("src.api.routes.register_user_to_csv") as mock_register:
            mock_register.return_value = False  # 新規登録

            response = test_client.post(
                "/user/register",
                json={
                    "uid_hex": "newuid123456",
                    "id": "user002",
                    "name": "新規ユーザー",
                    "email": "new@example.com",
                    "role": "user",
                    "description": "新規",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["is_update"] is False

    def test_register_user_update(self, test_client: TestClient) -> None:
        """既存ユーザーを上書き更新できる。"""
        with patch("src.api.routes.register_user_to_csv") as mock_register:
            mock_register.return_value = True  # 上書き更新

            response = test_client.post(
                "/user/register",
                json={
                    "uid_hex": "0123456789ab",
                    "id": "user001",
                    "name": "更新ユーザー",
                    "email": "update@example.com",
                    "role": "admin",
                    "description": "更新済み",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["is_update"] is True

    def test_delete_user_success(self, test_client: TestClient) -> None:
        """正しいパスワードでユーザーを削除できる。"""
        with (
            patch("src.api.routes.delete_user_from_csv") as mock_delete,
            patch("src.api.routes.get_settings") as mock_settings,
        ):
            mock_delete.return_value = True
            mock_settings.return_value.admin_password = "correct_password"

            response = test_client.request(
                "DELETE",
                "/user/delete",
                json={"uid_hex": "0123456789ab", "admin_password": "correct_password"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_delete_user_wrong_password(self, test_client: TestClient) -> None:
        """パスワードが間違っている場合は401エラー。"""
        with patch("src.api.routes.get_settings") as mock_settings:
            mock_settings.return_value.admin_password = "correct_password"

            response = test_client.request(
                "DELETE",
                "/user/delete",
                json={"uid_hex": "0123456789ab", "admin_password": "wrong_password"},
            )
            assert response.status_code == 401

    def test_delete_user_not_found(self, test_client: TestClient) -> None:
        """ユーザーが見つからない場合はsuccessがFalse。"""
        with (
            patch("src.api.routes.delete_user_from_csv") as mock_delete,
            patch("src.api.routes.get_settings") as mock_settings,
        ):
            mock_delete.return_value = False
            mock_settings.return_value.admin_password = "correct_password"

            response = test_client.request(
                "DELETE",
                "/user/delete",
                json={"uid_hex": "nonexistent", "admin_password": "correct_password"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

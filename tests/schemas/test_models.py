"""Pydanticモデルのテスト。"""

import pytest
from pydantic import ValidationError

from src.schemas.models import (
    ContinuousModeResponse,
    ScanBufferResponse,
    ScanResult,
    UserData,
    UserDeleteRequest,
    UserLookupRequest,
    UserRegisterRequest,
)


class TestScanResult:
    """ScanResultモデルのテスト。"""

    def test_success_result(self) -> None:
        """読み取り成功時のレスポンス。"""
        result = ScanResult(
            uid_hex="0123456789ab",
            success=True,
            message="Card read successfully",
        )
        assert result.uid_hex == "0123456789ab"
        assert result.success is True

    def test_timeout_result(self) -> None:
        """タイムアウト時のレスポンス。"""
        result = ScanResult(
            uid_hex=None,
            success=False,
            message="No card detected (timeout)",
        )
        assert result.uid_hex is None
        assert result.success is False


class TestContinuousModeResponse:
    """ContinuousModeResponseモデルのテスト。"""

    def test_started_response(self) -> None:
        """開始成功レスポンス。"""
        response = ContinuousModeResponse(
            success=True,
            message="Continuous mode started",
            is_running=True,
        )
        assert response.success is True
        assert response.is_running is True

    def test_stopped_response(self) -> None:
        """停止成功レスポンス。"""
        response = ContinuousModeResponse(
            success=True,
            message="Continuous mode stopped",
            is_running=False,
        )
        assert response.success is True
        assert response.is_running is False


class TestScanBufferResponse:
    """ScanBufferResponseモデルのテスト。"""

    def test_with_results(self) -> None:
        """結果ありのレスポンス。"""
        response = ScanBufferResponse(
            uid_hex_list=["uid1", "uid2", "uid3"],
            count=3,
        )
        assert len(response.uid_hex_list) == 3
        assert response.count == 3

    def test_empty_results(self) -> None:
        """結果なしのレスポンス。"""
        response = ScanBufferResponse(
            uid_hex_list=[],
            count=0,
        )
        assert len(response.uid_hex_list) == 0
        assert response.count == 0


class TestUserData:
    """UserDataモデルのテスト。"""

    def test_full_user_data(self) -> None:
        """全フィールドを持つユーザーデータ。"""
        user = UserData(
            uid_hex="0123456789ab",
            id="user001",
            name="テストユーザー",
            email="test@example.com",
            role="admin",
            description="テスト用ユーザー",
        )
        assert user.uid_hex == "0123456789ab"
        assert user.name == "テストユーザー"
        assert user.role == "admin"

    def test_minimal_user_data(self) -> None:
        """必須フィールドのみのユーザーデータ。"""
        user = UserData(
            uid_hex="0123456789ab",
            id="user001",
            name="テストユーザー",
        )
        assert user.uid_hex == "0123456789ab"
        assert user.email == ""  # デフォルト値
        assert user.role == ""  # デフォルト値
        assert user.description == ""  # デフォルト値

    def test_missing_required_field(self) -> None:
        """必須フィールドが欠けている場合はエラー。"""
        with pytest.raises(ValidationError):
            UserData(
                uid_hex="0123456789ab",
                id="user001",
                # name is missing
            )


class TestUserLookupRequest:
    """UserLookupRequestモデルのテスト。"""

    def test_valid_request(self) -> None:
        """有効なリクエスト。"""
        request = UserLookupRequest(uid_hex="0123456789ab")
        assert request.uid_hex == "0123456789ab"

    def test_missing_uid(self) -> None:
        """UIDが欠けている場合はエラー。"""
        with pytest.raises(ValidationError):
            UserLookupRequest()


class TestUserRegisterRequest:
    """UserRegisterRequestモデルのテスト。"""

    def test_full_request(self) -> None:
        """全フィールドを持つリクエスト。"""
        request = UserRegisterRequest(
            uid_hex="0123456789ab",
            id="user001",
            name="テストユーザー",
            email="test@example.com",
            role="admin",
            description="テスト用",
        )
        assert request.uid_hex == "0123456789ab"
        assert request.name == "テストユーザー"

    def test_minimal_request(self) -> None:
        """必須フィールドのみのリクエスト。"""
        request = UserRegisterRequest(
            uid_hex="0123456789ab",
            id="user001",
            name="テストユーザー",
        )
        assert request.email == ""
        assert request.role == ""


class TestUserDeleteRequest:
    """UserDeleteRequestモデルのテスト。"""

    def test_valid_request(self) -> None:
        """有効なリクエスト。"""
        request = UserDeleteRequest(
            uid_hex="0123456789ab",
            admin_password="secret123",
        )
        assert request.uid_hex == "0123456789ab"
        assert request.admin_password == "secret123"

    def test_missing_password(self) -> None:
        """パスワードが欠けている場合はエラー。"""
        with pytest.raises(ValidationError):
            UserDeleteRequest(uid_hex="0123456789ab")

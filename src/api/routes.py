"""FastAPIエンドポイント定義モジュール。

NFCカード読み取りとユーザー管理のAPIエンドポイントを提供する。
"""

from fastapi import APIRouter, HTTPException, status

from src.config.settings import get_settings
from src.logging.logger import get_logger
from src.nfc.reader import get_nfc_reader
from src.schemas.models import (
    ContinuousModeResponse,
    ScanBufferResponse,
    ScanResult,
    UserData,
    UserDeleteRequest,
    UserDeleteResponse,
    UserLookupRequest,
    UserLookupResponse,
    UserRegisterRequest,
    UserRegisterResponse,
)
from src.services.user_service import delete_user, lookup_user, register_user

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# NFC読み取りエンドポイント
# =============================================================================


@router.get("/read", response_model=ScanResult, tags=["NFC"])
def read_card() -> ScanResult:
    """単発でカードを読み取る。

    カードをリーダーにかざすとUID（16進数）を返却する。
    タイムアウト（デフォルト5秒）するとnullを返す。
    """
    reader = get_nfc_reader()
    uid_hex = reader.read_single()

    if uid_hex:
        return ScanResult(
            uid_hex=uid_hex,
            success=True,
            message="Card read successfully",
        )
    else:
        return ScanResult(
            uid_hex=None,
            success=False,
            message="No card detected (timeout)",
        )


@router.post("/continuous/start", response_model=ContinuousModeResponse, tags=["NFC"])
def start_continuous_mode() -> ContinuousModeResponse:
    """常時読み取りモードを開始する。

    バックグラウンドでカードの読み取りを継続し、
    読み取ったUIDをバッファに蓄積する。
    連続して同じカードを読み取った場合は無視される。
    """
    reader = get_nfc_reader()
    success = reader.start_continuous_mode()

    if success:
        return ContinuousModeResponse(
            success=True,
            message="Continuous mode started",
            is_running=True,
        )
    else:
        return ContinuousModeResponse(
            success=False,
            message="Continuous mode is already running",
            is_running=True,
        )


@router.post("/continuous/stop", response_model=ContinuousModeResponse, tags=["NFC"])
def stop_continuous_mode() -> ContinuousModeResponse:
    """常時読み取りモードを停止する。"""
    reader = get_nfc_reader()
    success = reader.stop_continuous_mode()

    if success:
        return ContinuousModeResponse(
            success=True,
            message="Continuous mode stopped",
            is_running=False,
        )
    else:
        return ContinuousModeResponse(
            success=False,
            message="Continuous mode is not running",
            is_running=False,
        )


@router.get("/continuous/results", response_model=ScanBufferResponse, tags=["NFC"])
def get_continuous_results() -> ScanBufferResponse:
    """常時読み取りモードで蓄積したUIDリストを取得する。

    取得後、バッファはリセットされる。
    """
    reader = get_nfc_reader()
    uid_list = reader.get_results_and_reset()

    return ScanBufferResponse(
        uid_hex_list=uid_list,
        count=len(uid_list),
    )


# =============================================================================
# ユーザー管理エンドポイント
# =============================================================================


@router.post("/user/lookup", response_model=UserLookupResponse, tags=["User"])
def lookup_user_by_uid(request: UserLookupRequest) -> UserLookupResponse:
    """UIDでユーザーを検索する。

    CSVファイルから該当するユーザーを検索して返却する。
    """
    user = lookup_user(request.uid_hex)

    if user:
        return UserLookupResponse(
            found=True,
            user=user,
            message="User found",
        )
    else:
        return UserLookupResponse(
            found=False,
            user=None,
            message="User not found",
        )


@router.post("/user/register", response_model=UserRegisterResponse, tags=["User"])
def register_new_user(request: UserRegisterRequest) -> UserRegisterResponse:
    """ユーザーを登録する。

    既存のUIDが存在する場合は上書き更新される。
    """
    user = UserData(
        uid_hex=request.uid_hex,
        id=request.id,
        name=request.name,
        email=request.email,
        role=request.role,
        description=request.description,
    )

    is_update = register_user(user)

    if is_update:
        return UserRegisterResponse(
            success=True,
            message="User updated successfully",
            is_update=True,
        )
    else:
        return UserRegisterResponse(
            success=True,
            message="User registered successfully",
            is_update=False,
        )


@router.delete("/user/delete", response_model=UserDeleteResponse, tags=["User"])
def delete_existing_user(request: UserDeleteRequest) -> UserDeleteResponse:
    """ユーザーを削除する。

    管理者パスワードが必要。
    """
    settings = get_settings()

    # パスワード認証
    if request.admin_password != settings.admin_password:
        logger.warning(f"Invalid admin password attempt for uid: {request.uid_hex}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password",
        )

    success = delete_user(request.uid_hex)

    if success:
        return UserDeleteResponse(
            success=True,
            message="User deleted successfully",
        )
    else:
        return UserDeleteResponse(
            success=False,
            message="User not found",
        )

"""Pydanticモデル定義モジュール。

リクエスト/レスポンス用のデータモデルを定義する。
"""

from pydantic import BaseModel, Field


class ScanResult(BaseModel):
    """単発読み取り結果。"""

    uid_hex: str | None = Field(
        description="カードのUID（16進数文字列）。タイムアウト時はnull"
    )
    success: bool = Field(description="読み取り成功フラグ")
    message: str = Field(description="結果メッセージ")


class ContinuousModeResponse(BaseModel):
    """常時読み取りモード操作結果。"""

    success: bool = Field(description="操作成功フラグ")
    message: str = Field(description="結果メッセージ")
    is_running: bool = Field(description="常時読み取りモード実行中フラグ")


class ScanBufferResponse(BaseModel):
    """常時読み取り結果レスポンス。"""

    uid_hex_list: list[str] = Field(description="読み取ったUIDのリスト")
    count: int = Field(description="読み取ったカード数")


class UserData(BaseModel):
    """ユーザーデータモデル。"""

    uid_hex: str = Field(description="カードのUID（16進数文字列）")
    id: str = Field(description="ユーザーID")
    name: str = Field(description="ユーザー名")
    email: str = Field(default="", description="メールアドレス")
    role: str = Field(default="", description="役割")
    description: str = Field(default="", description="説明")


class UserLookupRequest(BaseModel):
    """ユーザー検索リクエスト。"""

    uid_hex: str = Field(description="検索するカードのUID（16進数文字列）")


class UserLookupResponse(BaseModel):
    """ユーザー検索レスポンス。"""

    found: bool = Field(description="ユーザーが見つかったかどうか")
    user: UserData | None = Field(default=None, description="見つかったユーザーデータ")
    message: str = Field(description="結果メッセージ")


class UserRegisterRequest(BaseModel):
    """ユーザー登録リクエスト。"""

    uid_hex: str = Field(description="カードのUID（16進数文字列）")
    id: str = Field(description="ユーザーID")
    name: str = Field(description="ユーザー名")
    email: str = Field(default="", description="メールアドレス")
    role: str = Field(default="", description="役割")
    description: str = Field(default="", description="説明")


class UserRegisterResponse(BaseModel):
    """ユーザー登録レスポンス。"""

    success: bool = Field(description="登録成功フラグ")
    message: str = Field(description="結果メッセージ")
    is_update: bool = Field(description="既存ユーザーの上書きかどうか")


class UserDeleteRequest(BaseModel):
    """ユーザー削除リクエスト。"""

    uid_hex: str = Field(description="削除するカードのUID（16進数文字列）")
    admin_password: str = Field(description="管理者パスワード")


class UserDeleteResponse(BaseModel):
    """ユーザー削除レスポンス。"""

    success: bool = Field(description="削除成功フラグ")
    message: str = Field(description="結果メッセージ")

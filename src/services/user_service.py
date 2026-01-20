"""ユーザーサービスモジュール。

CSVファイルを使用したユーザーデータのCRUD操作を提供する。
"""

import csv
from pathlib import Path

from src.config.settings import get_settings
from src.logging.logger import get_logger
from src.schemas.models import UserData

logger = get_logger(__name__)

# CSVヘッダー
CSV_HEADERS = ["uid_hex", "id", "name", "email", "role", "description"]


def _ensure_csv_file() -> Path:
    """CSVファイルが存在することを確認し、なければテンプレートを作成する。

    Returns:
        Path: CSVファイルのパス
    """
    settings = get_settings()
    csv_path = settings.user_data_csv_path

    # ディレクトリ作成
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # ファイルが存在しない場合はテンプレート作成
    if not csv_path.exists():
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        logger.info(f"Created CSV template: {csv_path}")

    return csv_path


def lookup_user(uid_hex: str) -> UserData | None:
    """UIDでユーザーを検索する。

    Args:
        uid_hex: カードのUID（16進数文字列）

    Returns:
        UserData | None: 見つかったユーザーデータ、見つからない場合はNone
    """
    csv_path = _ensure_csv_file()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("uid_hex", "").lower() == uid_hex.lower():
                logger.info(f"User found: {uid_hex}")
                return UserData(
                    uid_hex=row.get("uid_hex", ""),
                    id=row.get("id", ""),
                    name=row.get("name", ""),
                    email=row.get("email", ""),
                    role=row.get("role", ""),
                    description=row.get("description", ""),
                )

    logger.info(f"User not found: {uid_hex}")
    return None


def register_user(user: UserData) -> bool:
    """ユーザーを登録する（既存の場合は上書き）。

    Args:
        user: 登録するユーザーデータ

    Returns:
        bool: 既存ユーザーの上書きの場合True、新規登録の場合False
    """
    csv_path = _ensure_csv_file()

    # 既存データを読み込み
    rows: list[dict[str, str]] = []
    is_update = False

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("uid_hex", "").lower() == user.uid_hex.lower():
                # 既存ユーザーを上書き
                rows.append(user.model_dump())
                is_update = True
                logger.info(f"User updated: {user.uid_hex}")
            else:
                rows.append(dict(row))

    # 新規ユーザーの場合は追加
    if not is_update:
        rows.append(user.model_dump())
        logger.info(f"User registered: {user.uid_hex}")

    # ファイルに書き込み
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    return is_update


def delete_user(uid_hex: str) -> bool:
    """ユーザーを削除する。

    Args:
        uid_hex: 削除するカードのUID（16進数文字列）

    Returns:
        bool: 削除成功時True、ユーザーが見つからない場合False
    """
    csv_path = _ensure_csv_file()

    # 既存データを読み込み
    rows: list[dict[str, str]] = []
    found = False

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("uid_hex", "").lower() == uid_hex.lower():
                found = True
                logger.info(f"User deleted: {uid_hex}")
            else:
                rows.append(dict(row))

    if not found:
        logger.warning(f"User not found for deletion: {uid_hex}")
        return False

    # ファイルに書き込み
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    return True


def get_all_users() -> list[UserData]:
    """全ユーザーを取得する。

    Returns:
        list[UserData]: 全ユーザーのリスト
    """
    csv_path = _ensure_csv_file()

    users: list[UserData] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(
                UserData(
                    uid_hex=row.get("uid_hex", ""),
                    id=row.get("id", ""),
                    name=row.get("name", ""),
                    email=row.get("email", ""),
                    role=row.get("role", ""),
                    description=row.get("description", ""),
                )
            )

    logger.debug(f"Retrieved {len(users)} users")
    return users

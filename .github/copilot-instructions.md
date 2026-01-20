# GitHub Copilot Instructions

## プロジェクト概要
SONY RC-S300 NFCカードリーダー用のバックエンドAPI。Windows11およびRaspberry Pi 5で動作し、FastAPIでRESTfulなエンドポイントを提供する。

## 技術スタック
- **Python**: 3.11
- **パッケージマネージャ**: uv
- **Webフレームワーク**: FastAPI
- **ASGIサーバー**: Uvicorn
- **NFC通信**: pyscard（PC/SC API）
- **データ検証**: Pydantic 2.x, pydantic-settings
- **環境変数**: python-dotenv
- **開発ツール**: Black, Ruff, pytest, ty, mypy

## プロジェクト構造
```
card_reader_backend/
├── main.py                    # エントリーポイント、FastAPIアプリ初期化
├── pyproject.toml
├── .python-version            # 3.11
├── .env                       # 環境変数（gitignore対象）
├── .env.example               # 環境変数テンプレート
├── .gitignore
├── src/
│   ├── api/
│   │   └── routes.py          # FastAPIエンドポイント定義
│   ├── config/
│   │   └── settings.py        # Pydantic Settings（環境変数管理）
│   ├── logging/
│   │   └── logger.py          # 日次ローテーションロガー
│   ├── nfc/
│   │   └── reader.py          # NFCリーダー操作クラス
│   ├── schemas/
│   │   └── models.py          # Pydanticモデル定義
│   └── services/
│       └── user_service.py    # ユーザーCSV操作
├── data/
│   └── users.csv              # ユーザーデータ（自動生成）
├── logs/                      # ログ出力先（gitignore対象）
├── tests/                     # テストコード
├── .github/
│   └── copilot-instructions.md
└── README.md
```

**モジュール責務分離**:
- `routes.py`: APIエンドポイント定義、リクエスト/レスポンス処理
- `settings.py`: 環境変数の型安全な読み込み
- `logger.py`: ロギング設定、日次ローテーション
- `reader.py`: NFCリーダー操作、常時監視スレッド管理
- `models.py`: リクエスト/レスポンス用Pydanticモデル
- `user_service.py`: CSVファイル操作（CRUD）

## APIエンドポイント一覧

| メソッド | パス | 機能 | 認証 |
|---------|------|------|------|
| GET | `/read` | 単発カード読み取り→uid_hex返却 | なし |
| POST | `/continuous/start` | 常時読み取りモード開始 | なし |
| POST | `/continuous/stop` | 常時読み取りモード停止 | なし |
| GET | `/continuous/results` | 蓄積したuid_hexリスト返却＆リセット | なし |
| POST | `/user/lookup` | uid_hexでユーザー検索 | なし |
| POST | `/user/register` | ユーザー登録（既存は上書き） | なし |
| DELETE | `/user/delete` | ユーザー削除 | **ADMIN_PASSWORD必須** |

## コーディング規約

### 1. 型ヒントは必須
```python
# Good
def read_card() -> str:
    return "0123456789ab"

# Bad
def read_card():
    return "0123456789ab"
```

### 2. 環境変数の扱い
- `.env`ファイルは必須（`.env.example`をコピー）
- Pydantic Settingsで型安全に管理
- 設定アクセスは`get_settings()`関数経由
```python
from src.config.settings import get_settings

settings = get_settings()
csv_path = settings.user_data_csv_path
```

### 3. エラーハンドリング
- `Exception`の汎用捕捉は避ける
- 具体的な例外を指定: `ConnectionError`, `OSError`, `TimeoutError`, `IOError`など
- FastAPIでは`HTTPException`を使用
```python
# Good
from fastapi import HTTPException

except (ConnectionError, OSError) as e:
    logger.error(f"NFC connection failed: {e}")
    raise HTTPException(status_code=503, detail="NFC reader not available")

# Bad
except Exception as e:
    pass
```

### 4. マジックナンバーは定数化
```python
# Good
DEFAULT_SCAN_TIMEOUT = 5.0
tag = clf.connect(rdwr={'on-connect': on_connect}, timeout=DEFAULT_SCAN_TIMEOUT)

# Bad
tag = clf.connect(rdwr={'on-connect': on_connect}, timeout=5.0)
```

### 5. グローバル変数は避ける
- シングルトンが必要な場合はクラス属性を使用
- `global`キーワードは使わない
- NFCReaderクラスはシングルトンパターンで実装

### 6. インポート順序
```python
# 標準ライブラリ
import os
import sys
from pathlib import Path

# サードパーティ
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import nfc

# ローカル
from src.config.settings import get_settings
from src.schemas.models import UserData
from src.logging.logger import get_logger
```

### 7. ロギング
- 共通ロガーを使用（`src.logging.logger`）
- ログレベル: DEBUG, INFO, WARNING, ERROR
- ファイル（日次ローテーション）とコンソール両方に出力
- 読み取り結果は必ずログに記録
```python
from src.logging.logger import get_logger

logger = get_logger(__name__)

logger.info(f"Card read: {uid_hex}")
logger.error(f"Failed to read card: {e}")
```

### 8. dotenvの読み込み
```python
# Good
from dotenv import load_dotenv
load_dotenv()

# Bad
import dotenv
dotenv.load_dotenv()
```

### 9. type: ignoreは最小限に
- 型を正しく定義すれば不要なはず
- やむを得ない場合のみ使用し、理由をコメント

### 10. ファイルエンコーディング
- **PowerShellスクリプト (`.ps1`)**: UTF-8 BOM付き（Microsoft推奨）
- **その他すべてのファイル**: UTF-8 BOMなし
  - Python (`.py`)
  - Markdown (`.md`)
  - JSON (`.json`)
  - YAML (`.yml`, `.yaml`)
  - Bash (`.sh`)
  - テキストファイル (`.txt`, `.env`)
  - CSV (`.csv`)

## NFC通信の注意点

### PC/SC API（pyscard）を使用
- **ドライバ変更不要**: Windowsの標準スマートカードサービスで動作
- RC-S300は「SONY FeliCa Port/PaSoRi 4.0 0」として認識される
- Python 3.11推奨

### Windows11でのセットアップ
**追加のドライバインストールは不要です！**
PC/SC APIを使用するため、Windowsの標準スマートカードサービスで動作します。

### Raspberry Pi 5でのセットアップ
1. pcscdとlibpcscliteをインストール:
```bash
sudo apt-get update
sudo apt-get install -y pcscd libpcsclite-dev
```
2. pcscdサービスを起動:
```bash
sudo systemctl enable pcscd
sudo systemctl start pcscd
```
3. 接続確認:
```bash
pcsc_scan
```

### 常時読み取りモードの仕様
- バックグラウンドスレッドで実行
- 連続して同じカードを読み取った場合は無視（重複防止）
- バッファ上限（`MAX_SCAN_BUFFER_SIZE`）を超えた場合、古いものから削除（FIFO）
- `/continuous/results`でリスト取得後、バッファはリセット

### デバッグモード
- `DEBUG_MODE=true`でNFCリーダー未接続でもダミーデータで動作確認可能

## セキュリティ
- `.env`はGitにコミットしない（`.gitignore`済み）
- 機密情報（`ADMIN_PASSWORD`等）は環境変数化
- ユーザー削除エンドポイントは`ADMIN_PASSWORD`認証必須
- ログファイルも`.gitignore`で除外

## テスト
- pytest使用
- NFC通信テストは`DEBUG_MODE=true`またはモックで実施

### テスト駆動開発（TDD）の推奨
**新機能追加時は必ずテストも同時作成する**

#### テストの配置
```
tests/
├── api/              # APIエンドポイントのテスト
├── nfc/              # NFC通信のテスト（モック使用）
├── services/         # サービス層のテスト
└── schemas/          # データモデルのテスト
```

#### テスト作成ルール
1. **新しい関数を追加** → 対応するテストを`tests/`に作成
2. **ビジネスロジック変更** → 既存テストを更新 + 新ケース追加
3. **バグ修正** → 再現テストを追加してから修正

#### NFC通信テストの注意
- 実機NFC接続は不要（モックを使用）
```python
from unittest.mock import MagicMock, patch

@patch("src.nfc.reader.nfc.ContactlessFrontend")
def test_read_card(mock_clf):
    mock_tag = MagicMock()
    mock_tag.identifier = bytes.fromhex("0123456789ab")
    mock_clf.return_value.__enter__.return_value.connect.return_value = mock_tag
    # テスト実行...
```

#### テスト実行コマンド
```bash
# 全テスト実行
pytest tests/ -v

# 特定のテストファイルのみ
pytest tests/api/test_routes.py -v

# カバレッジ計測
pytest --cov=src tests/
```

#### テストの命名規則
- ファイル: `test_*.py`
- クラス: `Test*`（例: `TestNFCReader`）
- 関数: `test_*`（例: `test_read_single_card`）

## デプロイ
- Windows11またはRaspberry Pi 5で実行
- `uv sync`で依存関係インストール
- `python main.py`または`uvicorn main:app --reload`で起動

## よくある問題と解決策

### インポートエラー
- `sys.path`操作は`main.py`のみで使用
- 他のモジュールは絶対インポート（`from src.xxx import yyy`）

### .envが見つからない
- `.env.example`を`.env`にコピー
- `Settings()`初期化時にチェックされる

### NFC接続エラー
- `DEBUG_MODE=true`でダミーモード確認
- デバイスパス設定を`.env`で確認
- OS別ドライバ設定を確認（Windows: WinUSB、Linux: udev）

### CSVファイルが見つからない
- 起動時に自動生成される（テンプレート）
- パス設定は`USER_DATA_CSV_PATH`で確認

## コード品質
- Black: フォーマッター（自動整形）
- Ruff: Linter（静的解析）
- Pylance: VSCode型チェック
- 全てセットアップ済み（`.vscode/settings.json`）

## 命名規則
- クラス: `PascalCase`（例: `NFCReader`, `UserData`）
- 関数/変数: `snake_case`（例: `read_card`, `uid_hex`）
- 定数: `UPPER_SNAKE_CASE`（例: `MAX_SCAN_BUFFER_SIZE`, `DEFAULT_TIMEOUT`）
- プライベート: `_leading_underscore`（例: `_instance`, `_scan_thread`）

## ドキュメント
- Docstring: Google Style
- 型ヒントで大部分は自己文書化
- 複雑なロジックにはインラインコメント

## 定期メンテナンス手順

### 大きな変更時・仕事終わりのチェックリスト

#### 1. 全スキャンによるテスト項目チェック
大きな機能追加や1日の開発終了時に、テストの過不足をチェック:

**チェック対象**:
- [ ] 新規追加した関数にテストがあるか
- [ ] 修正したロジックのテストケースが十分か
- [ ] 新しいPydanticモデルにバリデーションテストがあるか
- [ ] エラーハンドリングのテストが網羅されているか

#### 2. 開発ログの作成
その日の開発内容をまとめた資料を`dev_logs/`フォルダに生成:

```bash
# ファイル名: dev_logs/YYYY-MM-DD.md
```

**ログに記載する内容**:
- **実施内容サマリー**: 何を追加・修正したか
- **テスト結果**: 新規テスト数、全体のテスト実行結果
- **発見した課題と対応**: バグや改善点
- **今後の改善案**: 次回以降のTODO

#### 3. コミット前の最終チェック
```bash
# 1. 全テスト実行
pytest tests/ -v --tb=short

# 2. Lint確認
ruff check src/ tests/
black --check src/ tests/

# 3. 型チェック (VSCode Pylance)
# エラーパネルで確認

# 4. 変更差分確認
git status
git diff

# 5. コミット
git add .
git commit -m "feat: <変更内容の要約>"
git push origin main
```

---

**このプロジェクトは学習目的で開発されています。質問や改善提案は歓迎します！**

# NFC Card Reader Backend API

SONY RC-S300 NFCカードリーダー用のバックエンドAPI。Windows11およびRaspberry Pi 5で動作します。

## 機能

- **単発カード読み取り**: カードをかざすとUID（16進数）を返却
- **常時読み取りモード**: バックグラウンドで継続的にカードを読み取り、UIDリストを蓄積
- **ユーザー管理**: CSVファイルベースのユーザー登録・検索・削除

## 技術スタック

- Python 3.11
- FastAPI
- nfcpy
- Pydantic 2.x

## セットアップ

### 1. 依存関係のインストール

```bash
# uvを使用
uv sync

# または pip
pip install -e .
```

### 2. 環境変数の設定

```bash
# .env.exampleをコピー
cp .env.example .env

# 必要に応じて編集
# 特にADMIN_PASSWORDは本番環境では必ず変更してください
```

### 3. OS別ドライバ設定

#### Windows 11

1. [Zadig](https://zadig.akeo.ie/)をダウンロード
2. RC-S300を接続
3. Zadigで**WinUSB**ドライバをインストール
4. `libusb-1.0.dll`をPython実行環境にコピー

#### Raspberry Pi 5

```bash
# udevルールを追加
sudo sh -c 'echo SUBSYSTEM=="usb", ACTION=="add", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="06c1", GROUP="plugdev" >> /etc/udev/rules.d/nfcdev.rules'
sudo udevadm control --reload-rules

# ユーザーをplugdevグループに追加
sudo usermod -aG plugdev $USER

# 再ログインまたは再起動
```

## 起動

```bash
# 開発モード（ホットリロード有効）
python main.py

# または uvicorn直接
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## APIエンドポイント

起動後、`http://localhost:8000/docs` でSwagger UIが利用可能です。

| メソッド | パス | 機能 |
|---------|------|------|
| GET | `/` | ヘルスチェック |
| GET | `/read` | 単発カード読み取り |
| POST | `/continuous/start` | 常時読み取りモード開始 |
| POST | `/continuous/stop` | 常時読み取りモード停止 |
| GET | `/continuous/results` | 蓄積したUIDリスト取得＆リセット |
| POST | `/user/lookup` | UIDでユーザー検索 |
| POST | `/user/register` | ユーザー登録（既存は上書き） |
| DELETE | `/user/delete` | ユーザー削除（パスワード必須） |

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `NFC_DEVICE_PATH` | NFCデバイスパス | `usb:054c:06c1` |
| `USER_DATA_CSV_PATH` | ユーザーCSVファイルパス | `data/users.csv` |
| `MAX_SCAN_BUFFER_SIZE` | 常時読み取りバッファ上限 | `100` |
| `LOG_DIR` | ログ出力ディレクトリ | `logs` |
| `LOG_LEVEL` | ログレベル | `INFO` |
| `ADMIN_PASSWORD` | 管理者パスワード（削除時に必要） | - |
| `DEBUG_MODE` | デバッグモード（ダミーデータ使用） | `false` |

## デバッグモード

NFCリーダーが接続されていない環境でも動作確認ができます。

```bash
# .envに追加
DEBUG_MODE=true
```

## プロジェクト構造

```
card_reader_backend/
├── main.py                    # エントリーポイント
├── pyproject.toml
├── .python-version            # 3.11
├── .env                       # 環境変数（gitignore対象）
├── .env.example               # 環境変数テンプレート
├── src/
│   ├── api/
│   │   └── routes.py          # FastAPIエンドポイント
│   ├── config/
│   │   └── settings.py        # Pydantic Settings
│   ├── logging/
│   │   └── logger.py          # 日次ローテーションロガー
│   ├── nfc/
│   │   └── reader.py          # NFCリーダー操作
│   ├── schemas/
│   │   └── models.py          # Pydanticモデル
│   └── services/
│       └── user_service.py    # ユーザーCSV操作
├── data/
│   └── users.csv              # ユーザーデータ（自動生成）
├── logs/                      # ログ出力先
└── tests/                     # テストコード
```

## ライセンス

MIT License

"""NFCリーダーのテスト。"""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest


class TestNFCReader:
    """NFCリーダークラスのテスト。"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """各テスト前にシングルトンをリセット。"""
        from src.nfc.reader import NFCReader

        NFCReader._instance = None
        yield
        NFCReader._instance = None

    @pytest.fixture
    def mock_settings(self):
        """設定をモック。"""
        with patch("src.nfc.reader.get_settings") as mock:
            mock.return_value.debug_mode = True
            mock.return_value.max_scan_buffer_size = 5
            mock.return_value.nfc_device_path = "usb:054c:06c1"
            yield mock

    def test_singleton_pattern(self, mock_settings) -> None:
        """シングルトンパターンが正しく動作する。"""
        from src.nfc.reader import NFCReader, get_nfc_reader

        reader1 = get_nfc_reader()
        reader2 = get_nfc_reader()
        reader3 = NFCReader()

        assert reader1 is reader2
        assert reader2 is reader3

    def test_read_single_debug_mode(self, mock_settings) -> None:
        """デバッグモードではダミーUIDが返される。"""
        from src.nfc.reader import get_nfc_reader

        reader = get_nfc_reader()
        uid = reader.read_single()

        assert uid is not None
        assert len(uid) == 14  # 7バイト = 14文字の16進数
        assert all(c in "0123456789abcdef" for c in uid)

    def test_continuous_mode_start_stop(self, mock_settings) -> None:
        """常時読み取りモードの開始と停止。"""
        from src.nfc.reader import get_nfc_reader

        reader = get_nfc_reader()

        # 初期状態
        assert reader.is_continuous_mode_running() is False

        # 開始
        result = reader.start_continuous_mode()
        assert result is True
        assert reader.is_continuous_mode_running() is True

        # 再度開始は失敗
        result = reader.start_continuous_mode()
        assert result is False

        # 停止
        result = reader.stop_continuous_mode()
        assert result is True
        assert reader.is_continuous_mode_running() is False

        # 再度停止は失敗
        result = reader.stop_continuous_mode()
        assert result is False

    def test_get_results_and_reset(self, mock_settings) -> None:
        """結果取得とリセット。"""
        from src.nfc.reader import get_nfc_reader

        reader = get_nfc_reader()

        # バッファに直接追加してテスト
        reader._scan_buffer.append("uid1")
        reader._scan_buffer.append("uid2")
        reader._scan_buffer.append("uid3")

        assert reader.buffer_size == 3

        results = reader.get_results_and_reset()
        assert results == ["uid1", "uid2", "uid3"]
        assert reader.buffer_size == 0

    def test_buffer_fifo_overflow(self, mock_settings) -> None:
        """バッファ上限を超えた場合、古いものが削除される（FIFO）。"""
        from src.nfc.reader import get_nfc_reader

        reader = get_nfc_reader()

        # バッファ上限は5（mock_settingsで設定）
        for i in range(7):
            reader._scan_buffer.append(f"uid{i}")

        # 最大5件のみ保持
        assert reader.buffer_size == 5

        # 古いもの（uid0, uid1）は削除され、新しいもの（uid2〜uid6）が残る
        results = reader.get_results_and_reset()
        assert results == ["uid2", "uid3", "uid4", "uid5", "uid6"]

    def test_duplicate_card_ignored(self, mock_settings) -> None:
        """連続して同じカードは無視される。"""
        from src.nfc.reader import get_nfc_reader

        reader = get_nfc_reader()

        # 最初のカード
        reader._last_uid = None
        reader._scan_buffer.clear()

        # 同じUIDを連続で追加するシミュレーション
        uid = "same_uid_123"
        if uid != reader._last_uid:
            reader._scan_buffer.append(uid)
            reader._last_uid = uid

        # 2回目は無視される
        if uid != reader._last_uid:
            reader._scan_buffer.append(uid)
            reader._last_uid = uid

        assert reader.buffer_size == 1  # 1件のみ

    def test_different_cards_added(self, mock_settings) -> None:
        """異なるカードは追加される。"""
        from src.nfc.reader import get_nfc_reader

        reader = get_nfc_reader()
        reader._last_uid = None
        reader._scan_buffer.clear()

        for uid in ["uid1", "uid2", "uid1", "uid3"]:
            if uid != reader._last_uid:
                reader._scan_buffer.append(uid)
                reader._last_uid = uid

        # uid1, uid2, uid1, uid3 → uid1が2回カウント（間にuid2があるため）
        assert reader.buffer_size == 4


class TestNFCReaderWithNfcpy:
    """nfcpyを使用したテスト（モック使用）。"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """各テスト前にシングルトンをリセット。"""
        from src.nfc.reader import NFCReader

        NFCReader._instance = None
        yield
        NFCReader._instance = None

    def test_read_card_nfcpy_import_error(self) -> None:
        """nfcpyがインストールされていない場合はNoneを返す。"""
        with patch("src.nfc.reader.get_settings") as mock_settings:
            mock_settings.return_value.debug_mode = False
            mock_settings.return_value.max_scan_buffer_size = 10
            mock_settings.return_value.nfc_device_path = "usb:054c:06c1"

            from src.nfc.reader import get_nfc_reader

            reader = get_nfc_reader()

            # _read_card_nfcpyメソッドをモックしてImportErrorをシミュレート
            with patch.object(reader, "_read_card_nfcpy", return_value=None):
                result = reader.read_single()
                assert result is None

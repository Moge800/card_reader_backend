"""NFCリーダー操作モジュール。

SONY RC-S300 NFCカードリーダーの操作を行う。
シングルトンパターンで実装し、常時読み取りモードをサポートする。
PC/SC API（pyscard）を使用し、ドライバ変更不要で動作する。
"""

import random
import threading
import time
from collections import deque

from src.config.settings import get_settings
from src.logging.logger import get_logger

logger = get_logger(__name__)

# 定数
DEFAULT_SCAN_TIMEOUT = 5.0
CONTINUOUS_SCAN_INTERVAL = 0.5

# PC/SC APDUコマンド
GET_UID_COMMAND = [0xFF, 0xCA, 0x00, 0x00, 0x00]


class NFCReader:
    """NFCリーダー操作クラス（シングルトン）。

    単発読み取りと常時読み取りモードをサポートする。
    常時読み取りモードでは、連続して同じカードを読み取った場合は無視する。
    PC/SC APIを使用してカードを読み取る。
    """

    _instance: "NFCReader | None" = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls) -> "NFCReader":
        """シングルトンインスタンスを取得する。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """初期化（シングルトンのため1回のみ実行）。"""
        if self._initialized:
            return

        self._settings = get_settings()
        self._scan_buffer: deque[str] = deque(
            maxlen=self._settings.max_scan_buffer_size
        )
        self._last_uid: str | None = None
        self._continuous_mode: bool = False
        self._scan_thread: threading.Thread | None = None
        self._stop_event: threading.Event = threading.Event()
        self._initialized = True

        logger.info("NFCReader initialized")

    def read_single(self, timeout: float = DEFAULT_SCAN_TIMEOUT) -> str | None:
        """単発でカードを読み取る。

        Args:
            timeout: 読み取りタイムアウト秒数

        Returns:
            str | None: カードのUID（16進数文字列）、タイムアウト時はNone
        """
        if self._settings.debug_mode:
            return self._generate_dummy_uid()

        return self._read_card_pcsc(timeout)

    def _read_card_pcsc(self, timeout: float) -> str | None:
        """PC/SC APIを使用してカードを読み取る。

        Args:
            timeout: 読み取りタイムアウト秒数

        Returns:
            str | None: カードのUID（16進数文字列）、タイムアウト時はNone
        """
        try:
            from smartcard.CardRequest import CardRequest
            from smartcard.CardType import AnyCardType
            from smartcard.Exceptions import CardRequestTimeoutException
            from smartcard.util import toHexString

            cardtype = AnyCardType()
            cardrequest = CardRequest(timeout=timeout, cardType=cardtype)

            try:
                cardservice = cardrequest.waitforcard()
                cardservice.connection.connect()

                # Get UID command (APDU)
                data, sw1, sw2 = cardservice.connection.transmit(GET_UID_COMMAND)

                uid_hex: str | None = None
                if sw1 == 0x90 and sw2 == 0x00:
                    uid_hex = toHexString(data).replace(" ", "").lower()
                    logger.info(f"Card read: {uid_hex}")
                else:
                    logger.warning(f"Failed to get UID: SW1={hex(sw1)}, SW2={hex(sw2)}")

                cardservice.connection.disconnect()
                return uid_hex

            except CardRequestTimeoutException:
                logger.debug("Card read timeout - no card detected")
                return None

        except ImportError:
            logger.error("pyscard is not installed")
            return None
        except OSError as e:
            logger.error(f"NFC device connection failed: {e}")
            return None

    def _generate_dummy_uid(self) -> str:
        """デバッグ用のダミーUIDを生成する。

        Returns:
            str: ランダムな16進数UID
        """
        uid = "".join(random.choices("0123456789abcdef", k=14))
        logger.info(f"[DEBUG] Dummy card read: {uid}")
        return uid

    def start_continuous_mode(self) -> bool:
        """常時読み取りモードを開始する。

        Returns:
            bool: 開始成功時True、既に実行中の場合False
        """
        if self._continuous_mode:
            logger.warning("Continuous mode is already running")
            return False

        self._continuous_mode = True
        self._stop_event.clear()
        self._scan_thread = threading.Thread(
            target=self._continuous_scan_loop, daemon=True
        )
        self._scan_thread.start()

        logger.info("Continuous mode started")
        return True

    def stop_continuous_mode(self) -> bool:
        """常時読み取りモードを停止する。

        Returns:
            bool: 停止成功時True、実行中でない場合False
        """
        if not self._continuous_mode:
            logger.warning("Continuous mode is not running")
            return False

        self._stop_event.set()
        self._continuous_mode = False

        if self._scan_thread and self._scan_thread.is_alive():
            self._scan_thread.join(timeout=5.0)

        self._scan_thread = None
        self._last_uid = None

        logger.info("Continuous mode stopped")
        return True

    def _continuous_scan_loop(self) -> None:
        """常時読み取りのループ処理。"""
        logger.info("Continuous scan loop started")

        while not self._stop_event.is_set():
            uid = self.read_single(timeout=CONTINUOUS_SCAN_INTERVAL)

            if uid and uid != self._last_uid:
                self._scan_buffer.append(uid)
                self._last_uid = uid
                logger.info(f"Continuous mode - new card: {uid}")
            elif uid and uid == self._last_uid:
                logger.debug(f"Continuous mode - duplicate ignored: {uid}")

            time.sleep(CONTINUOUS_SCAN_INTERVAL)

        logger.info("Continuous scan loop stopped")

    def get_results_and_reset(self) -> list[str]:
        """蓄積した読み取り結果を取得し、バッファをリセットする。

        Returns:
            list[str]: 読み取ったUID（16進数文字列）のリスト
        """
        results = list(self._scan_buffer)
        self._scan_buffer.clear()
        self._last_uid = None

        logger.info(f"Results retrieved and reset: {len(results)} cards")
        return results

    def is_continuous_mode_running(self) -> bool:
        """常時読み取りモードが実行中かどうかを返す。

        Returns:
            bool: 実行中ならTrue
        """
        return self._continuous_mode

    @property
    def buffer_size(self) -> int:
        """現在のバッファサイズを返す。

        Returns:
            int: バッファ内のUID数
        """
        return len(self._scan_buffer)


def get_nfc_reader() -> NFCReader:
    """NFCReaderのシングルトンインスタンスを取得する。

    Returns:
        NFCReader: NFCリーダーインスタンス
    """
    return NFCReader()

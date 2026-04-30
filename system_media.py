import asyncio
import queue
import threading
from datetime import datetime
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

def log(msg):
    with open("media_debug.log", "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

# ── Optional WinRT imports ────────────────────────────────────────────────────
GlobalSystemMediaTransportControlsSessionManager = None
GlobalSystemMediaTransportControlsSessionPlaybackStatus = None
DataReader = None
VOLUME_AVAILABLE = False
AudioUtilities = None
IAudioEndpointVolume = None
CLSCTX_ALL = None

try:
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus,
    )
    from winrt.windows.storage.streams import DataReader
    log("WinRT modules imported.")
except ImportError as e:
    log(f"WinRT Import Error: {e}")

try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    VOLUME_AVAILABLE = True
except ImportError:
    log("PyCaw not installed.")


class SystemMediaManager(QObject):
    """
    Manages Windows media session detection and control.

    THREADING MODEL
    ---------------
    The asyncio event loop runs in a Python daemon thread (self.thread).
    Qt requires that pyqtSignals are emitted from the thread that owns the
    QObject (the main/GUI thread).  Emitting from a plain Python thread
    bypasses Qt's internal thread data and causes STATUS_STACK_BUFFER_OVERRUN.

    Fix: the asyncio thread never calls .emit() directly.  Instead it puts
    data into a thread-safe queue (_sig_queue).  A QTimer running in the
    main thread drains the queue every 50 ms and emits the signals safely.
    """

    metadata_changed       = pyqtSignal(str, str, bytes)
    playback_status_changed = pyqtSignal(bool)
    timeline_changed        = pyqtSignal(int, int)

    # ── Internal queue kinds ──────────────────────────────────────────────────
    _K_META     = 0
    _K_PLAY     = 1
    _K_TIMELINE = 2

    def __init__(self):
        super().__init__()
        self.session_manager  = None
        self.current_session  = None
        self.loop             = None
        self.running          = False
        self.volume_interface = None

        # Thread-safe queue: asyncio thread → main thread
        self._sig_queue = queue.SimpleQueue()

        # QTimer lives in the main thread; drains the queue and emits signals
        self._drain_timer = QTimer(self)
        self._drain_timer.setInterval(50)   # 50 ms
        self._drain_timer.timeout.connect(self._drain_queue)
        self._drain_timer.start()

        if VOLUME_AVAILABLE:
            threading.Thread(target=self._init_volume, daemon=True).start()

        if GlobalSystemMediaTransportControlsSessionManager:
            log("Starting worker thread...")
            self.start_worker()
        else:
            log("GlobalSystemMediaManager is None (WinRT missing).")

    # ── Queue helpers (called from asyncio thread) ────────────────────────────

    def _put_metadata(self, title, artist, thumb_data):
        self._sig_queue.put((self._K_META, title, artist, thumb_data))

    def _put_playback(self, is_playing):
        self._sig_queue.put((self._K_PLAY, is_playing))

    def _put_timeline(self, pos, dur):
        self._sig_queue.put((self._K_TIMELINE, pos, dur))

    def _drain_queue(self):
        """Called from the main thread every 50 ms. Emits queued signals."""
        try:
            while True:
                item = self._sig_queue.get_nowait()
                kind = item[0]
                if kind == self._K_META:
                    _, title, artist, thumb = item
                    self.metadata_changed.emit(title, artist, thumb)
                elif kind == self._K_PLAY:
                    _, is_playing = item
                    self.playback_status_changed.emit(is_playing)
                elif kind == self._K_TIMELINE:
                    _, pos, dur = item
                    self.timeline_changed.emit(pos, dur)
        except queue.Empty:
            pass

    # ── Volume (init in background thread, use from main thread) ─────────────

    def _init_volume(self):
        try:
            devices = AudioUtilities.GetSpeakers()
            # pycaw < 0.1 returns the raw COM IMMDevice (has .Activate)
            # pycaw ≥ 0.1 wraps it in AudioDevice; access underlying COM via ._dev
            dev = getattr(devices, '_dev', devices)
            interface = dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume_interface = interface.QueryInterface(IAudioEndpointVolume)
        except Exception as e:
            log(f"Volume Init Error: {e}")

    # ── Asyncio worker ────────────────────────────────────────────────────────

    def start_worker(self):
        self.running = True
        self.thread  = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._async_init())
        self.loop.run_forever()

    async def _async_init(self):
        try:
            self.session_manager = await (
                GlobalSystemMediaTransportControlsSessionManager.request_async()
            )
            await self._update_session_async()
            self.session_manager.add_current_session_changed(self._on_session_changed)
            asyncio.create_task(self._poller())
        except Exception as e:
            log(f"Failed to init system media: {e}")

    # ── Session / property change callbacks (called from WinRT COM thread) ───

    def _on_session_changed(self, sender, args):
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self._update_session_sync)

    def _on_properties_changed(self, sender, args):
        """Fired by Windows when the current track changes."""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(
                lambda: self.loop.create_task(self._read_media_properties())
            )

    def _update_session_sync(self):
        asyncio.create_task(self._update_session_async())

    async def _update_session_async(self):
        try:
            session = self.session_manager.get_current_session()
            if session:
                if self.current_session != session:
                    log(f"New session: {session.source_app_user_model_id}")
                    self.current_session = session
                    try:
                        session.add_media_properties_changed(
                            self._on_properties_changed)
                    except Exception:
                        pass
                await self._read_media_properties()
            else:
                self.current_session = None
                self._put_metadata("No Media", "", b"")
        except Exception as e:
            log(f"Update session error: {e}")

    async def _read_media_properties(self):
        if not self.current_session:
            return
        try:
            info = await self.current_session.try_get_media_properties_async()
            if info:
                title      = info.title  or ""
                artist     = info.artist or ""
                thumb_data = b""
                if info.thumbnail:
                    try:
                        stream = await info.thumbnail.open_read_async()
                        if stream and stream.size > 0:
                            reader = DataReader(stream.get_input_stream_at(0))
                            await reader.load_async(stream.size)
                            thumb_data = bytes(reader.read_buffer(stream.size))
                    except Exception as ex:
                        log(f"Thumb err: {ex}")
                self._put_metadata(title, artist, thumb_data)

            pb = self.current_session.get_playback_info()
            if pb and GlobalSystemMediaTransportControlsSessionPlaybackStatus:
                is_playing = (
                    pb.playback_status
                    == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING
                )
                self._put_playback(is_playing)

            tl = self.current_session.get_timeline_properties()
            if tl:
                pos = tl.position.total_seconds() if tl.position else 0
                dur = tl.end_time.total_seconds() if tl.end_time else 0
                self._put_timeline(int(pos), int(dur))
        except Exception as e:
            log(f"Read props error: {e}")

    async def _poller(self):
        """
        Lightweight playback/position poller — 2 s interval.
        Uses only synchronous COM getters; no image decode.
        Data is queued for the main thread to emit as signals.
        """
        while self.running:
            try:
                if self.current_session:
                    pb = self.current_session.get_playback_info()
                    if pb and GlobalSystemMediaTransportControlsSessionPlaybackStatus:
                        is_playing = (
                            pb.playback_status
                            == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING
                        )
                        self._put_playback(is_playing)

                    tl = self.current_session.get_timeline_properties()
                    if tl:
                        pos = tl.position.total_seconds() if tl.position else 0
                        dur = tl.end_time.total_seconds() if tl.end_time else 0
                        self._put_timeline(int(pos), int(dur))
            except Exception as e:
                log(f"Poller error: {e}")

            await asyncio.sleep(2.0)

    # ── Playback control ──────────────────────────────────────────────────────

    def play_pause(self):
        if self.loop and self.current_session:
            self.loop.call_soon_threadsafe(self._play_pause_async)

    def _play_pause_async(self):
        asyncio.create_task(self._do_toggle_play_pause())

    async def _do_toggle_play_pause(self):
        try:
            await self.current_session.try_toggle_play_pause_async()
        except Exception as e:
            log(f"Play/Pause Err: {e}")

    def next(self):
        self._fallback_keypress(0xB0)   # VK_MEDIA_NEXT_TRACK

    def prev(self):
        self._fallback_keypress(0xB1)   # VK_MEDIA_PREV_TRACK

    def _fallback_keypress(self, vk_code):
        try:
            import ctypes
            u = ctypes.windll.user32
            u.keybd_event(vk_code, 0, 1,     0)   # key down
            u.keybd_event(vk_code, 0, 1 | 2, 0)   # key up
        except Exception as e:
            log(f"Fallback key error: {e}")

    def seek(self, position_seconds):
        pass

    # ── Volume control ────────────────────────────────────────────────────────

    def set_volume(self, level_0_to_100):
        if self.volume_interface:
            try:
                vol = max(0.0, min(1.0, level_0_to_100 / 100.0))
                self.volume_interface.SetMasterVolumeLevelScalar(vol, None)
            except Exception as e:
                log(f"Vol err: {e}")

    def get_volume(self):
        if self.volume_interface:
            try:
                return int(self.volume_interface.GetMasterVolumeLevelScalar() * 100)
            except Exception:
                pass
        return 50

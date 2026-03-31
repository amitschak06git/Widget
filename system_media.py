import asyncio
import threading
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

def log(msg):
    with open("media_debug.log", "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

# -- Imports --
GlobalSystemMediaTransportControlsSessionManager = None
GlobalSystemMediaTransportControlsSessionPlaybackStatus = None
DataReader = None
VOLUME_AVAILABLE = False
AudioUtilities = None
IAudioEndpointVolume = None
CLSCTX_ALL = None

try:
    from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager, GlobalSystemMediaTransportControlsSessionPlaybackStatus
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
    metadata_changed = pyqtSignal(str, str, bytes)
    playback_status_changed = pyqtSignal(bool)
    timeline_changed = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.session_manager = None
        self.current_session = None
        self.loop = None
        self.running = False
        
        self.volume_interface = None
        if VOLUME_AVAILABLE:
            threading.Thread(target=self._init_volume, daemon=True).start()
        
        if GlobalSystemMediaTransportControlsSessionManager:
            log("Starting worker thread...")
            self.start_worker()
        else:
            log("GlobalSystemMediaManager is None (WinRT missing).")

    def _init_volume(self):
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume_interface = interface.QueryInterface(IAudioEndpointVolume)
        except Exception as e:
            log(f"Volume Init Error: {e}")

    def start_worker(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._async_init())
        self.loop.run_forever()

    async def _async_init(self):
        try:
            self.session_manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
            await self._update_session_async()
            self.session_manager.add_current_session_changed(self._on_session_changed)
            asyncio.create_task(self._poller())
        except Exception as e:
            log(f"Failed to init system media: {e}")

    def _on_session_changed(self, sender, args):
        if self.loop:
            self.loop.call_soon_threadsafe(self._update_session_sync)

    def _update_session_sync(self):
        asyncio.create_task(self._update_session_async())

    async def _update_session_async(self):
        try:
            session = self.session_manager.get_current_session()
            if session:
                if self.current_session != session:
                    log(f"New session: {session.source_app_user_model_id}")
                    self.current_session = session
                await self._read_media_properties()
            else:
                self.current_session = None
                self.metadata_changed.emit("No Media", "", b"")
        except Exception as e:
            log(f"Update session error: {e}")

    async def _read_media_properties(self):
        if not self.current_session: return
        try:
            info = await self.current_session.try_get_media_properties_async()
            if info:
                title = info.title
                artist = info.artist
                thumb_data = b""
                if info.thumbnail:
                    try:
                        stream = await info.thumbnail.open_read_async()
                        if stream and stream.size > 0:
                            reader = DataReader(stream.get_input_stream_at(0))
                            await reader.load_async(stream.size)
                            thumb_data = bytes(reader.read_buffer(stream.size))
                    except Exception as ex: log(f"Thumb err: {ex}")
                self.metadata_changed.emit(title, artist, thumb_data)
            
            pb = self.current_session.get_playback_info()
            if pb:
                is_playing = pb.playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING
                self.playback_status_changed.emit(is_playing)
                
            tl = self.current_session.get_timeline_properties()
            if tl:
                pos = tl.position.total_seconds() if tl.position else 0
                dur = tl.end_time.total_seconds() if tl.end_time else 0
                self.timeline_changed.emit(int(pos), int(dur))
        except Exception as e:
            log(f"Read props error: {e}")

    async def _poller(self):
        while self.running:
            await self._update_session_async()
            await asyncio.sleep(0.5) # Faster polling for seek bar

    # ... (Control methods)

    def _fallback_keypress(self, vk_code):
        # Fallback using ctypes to simulate media key press
        try:
            import ctypes
            user32 = ctypes.windll.user32
            # KEYEVENTF_EXTENDEDKEY = 0x0001
            # KEYEVENTF_KEYUP = 0x0002
            user32.keybd_event(vk_code, 0, 1, 0) # Press
            user32.keybd_event(vk_code, 0, 1 | 2, 0) # Release
            log(f"Fallback keypress sent: {vk_code}")
        except Exception as e:
            log(f"Fallback key error: {e}")

    def play_pause(self):
        if self.loop and self.current_session:
            self.loop.call_soon_threadsafe(self._play_pause_async)
            
    def _play_pause_async(self):
        asyncio.create_task(self._do_toggle_play_pause())
        
    async def _do_toggle_play_pause(self):
        try: await self.current_session.try_toggle_play_pause_async()
        except Exception as e: log(f"Play/Pause Err: {e}")

    def next(self):
        log("Next requested (Using Fallback)")
        # WinRT 'try_skip_next_async' works for some apps but fails for others (browsers).
        # A simulated keypress is universally handled by Windows.
        # VK_MEDIA_NEXT_TRACK = 0xB0
        self._fallback_keypress(0xB0)

    def prev(self):
        log("Prev requested (Using Fallback)")
        # VK_MEDIA_PREV_TRACK = 0xB1
        self._fallback_keypress(0xB1)

    def _next_async(self): pass # Deprecated in favor of fallback
    async def _do_next(self): pass

    def _prev_async(self): pass
    async def _do_prev(self): pass
        
    def seek(self, position_seconds):
        pass # Not used currently but preventing crash if called

    def set_volume(self, level_0_to_100):
        if self.volume_interface:
            try:
                vol = max(0.0, min(1.0, level_0_to_100 / 100.0))
                self.volume_interface.SetMasterVolumeLevelScalar(vol, None)
                log(f"Set volume to {vol}")
            except Exception as e: log(f"Vol err: {e}")
        else:
            log("set_volume called but interface is None")

    def get_volume(self):
        if self.volume_interface:
            try: return int(self.volume_interface.GetMasterVolumeLevelScalar() * 100)
            except: return 50
        return 50

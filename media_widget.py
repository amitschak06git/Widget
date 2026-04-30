"""
media_widget.py — Editorial design: 68×68 album art with rounded-12 corners,
title in display font, artist in UI font, album in mono uppercase, a live
waveform scrubber (52 bars, QPainter), and a primary play button.
"""
import math

from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QSizePolicy, QLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QFont, QPixmap, QImage, QPainter, QPainterPath, QColor, QPen
)
from base_widget import BaseWidget


# ── Waveform scrubber ─────────────────────────────────────────────────────

class WaveformWidget(QWidget):
    """52-bar deterministic waveform. Click/drag to seek."""
    seek_requested = pyqtSignal(float)   # emits 0..1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(16)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bars     = self._make_bars(52)
        self._position = 0.0   # 0..1

    def _make_bars(self, n):
        out, s = [], 7
        for i in range(n):
            s   = (s * 9301 + 49297) % 233280
            r   = s / 233280
            base = 0.5 + math.sin(i / n * math.pi) * 0.3
            out.append(max(0.12, min(1.0, base * (0.5 + r * 0.9))))
        return out

    def set_position(self, pos: float):
        self._position = max(0.0, min(1.0, pos))
        self.update()

    def paintEvent(self, event):
        p   = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h, n   = self.width(), self.height(), len(self._bars)
        current   = int(self._position * n)
        gap       = 2
        bar_w     = max(1.0, (w - gap * (n - 1)) / n)

        for i, ratio in enumerate(self._bars):
            bh  = max(2.0, ratio * h)
            bx  = i * (bar_w + gap)
            by  = (h - bh) / 2
            if i < current:
                col = QColor(250, 247, 242, 220)  # ink-1 played
            elif i == current:
                col = QColor(232, 168, 87, 255)   # accent head
            else:
                col = QColor(97, 88, 72, 255)     # ink-4 future
            p.fillRect(int(bx), int(by), max(1, int(bar_w)), int(bh), col)
        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            frac = event.pos().x() / max(1, self.width())
            self.seek_requested.emit(max(0.0, min(1.0, frac)))

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            frac = event.pos().x() / max(1, self.width())
            self.seek_requested.emit(max(0.0, min(1.0, frac)))


# ── Media widget ──────────────────────────────────────────────────────────

class MediaWidget(BaseWidget):
    def __init__(self, system_media=None, theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager, widget_id="media")

        self.system_media = system_media
        self.config       = config_manager
        self.art_data     = None
        self.is_playing   = False

        main = QVBoxLayout()
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(14)
        main.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.setLayout(main)

        # ── Top: album art + text ─────────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(14)

        self.art_label = QLabel()
        self.art_label.setMinimumSize(48, 48)
        self.art_label.setMaximumSize(120, 120)
        self.art_label.setFixedSize(68, 68)
        self.art_label.setStyleSheet(
            "background-color: rgba(97,88,72,80);"
            "border-radius: 12px; border: none;")
        self.art_label.setScaledContents(True)
        top.addWidget(self.art_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        text_col.setContentsMargins(0, 4, 0, 0)

        self.status_label = QLabel("No Media")
        self.status_label.setObjectName("media_status")
        self.status_label.setWordWrap(True)

        self.artist_label = QLabel("")
        self.artist_label.setObjectName("media_artist")

        self.album_label = QLabel("")
        self.album_label.setObjectName("media_album")

        text_col.addWidget(self.status_label)
        text_col.addWidget(self.artist_label)
        text_col.addWidget(self.album_label)
        text_col.addStretch()

        top.addLayout(text_col)
        main.addLayout(top)

        # ── Waveform scrubber ─────────────────────────────────────────────
        self.waveform = WaveformWidget()
        self.waveform.setMinimumHeight(20)
        self.waveform.setMaximumHeight(60)
        main.addWidget(self.waveform)

        # ── Elapsed / remaining ───────────────────────────────────────────
        time_row = QHBoxLayout()
        self.lbl_pos       = QLabel("0:00")
        self.lbl_remaining = QLabel("")
        for lbl in [self.lbl_pos, self.lbl_remaining]:
            lbl.setObjectName("media_artist")
        time_row.addWidget(self.lbl_pos)
        time_row.addStretch()
        time_row.addWidget(self.lbl_remaining)
        main.addLayout(time_row)

        # ── Transport controls ────────────────────────────────────────────
        ctrl = QHBoxLayout()
        ctrl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ctrl.setSpacing(10)

        self.btn_prev = QPushButton("|<")
        self.btn_prev.setFixedSize(36, 36)
        self.btn_prev.setObjectName("media_btn")

        self.btn_play = QPushButton(">")
        self.btn_play.setFixedSize(48, 48)
        self.btn_play.setObjectName("media_btn_primary")

        self.btn_next = QPushButton(">|")
        self.btn_next.setFixedSize(36, 36)
        self.btn_next.setObjectName("media_btn")

        ctrl.addWidget(self.btn_prev)
        ctrl.addWidget(self.btn_play)
        ctrl.addWidget(self.btn_next)
        main.addLayout(ctrl)

        self.apply_theme()

        self.btn_prev.clicked.connect(self.prev_track)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_next.clicked.connect(self.next_track)
        self.waveform.seek_requested.connect(self._on_seek)

        if self.system_media:
            self.system_media.metadata_changed.connect(self.update_metadata)
            self.system_media.playback_status_changed.connect(self.update_play_icon)

        self.resize(380, 220)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not getattr(self, '_scale_pending', False):
            self._scale_pending = True
            QTimer.singleShot(0, self._do_scale)

    def _do_scale(self):
        self._scale_pending = False
        self._scale_layout()

    def _scale_layout(self):
        h = self.height()
        w = self.width()

        # Art: square, 20% of width, capped 48–110px
        art_sz = max(48, min(110, int(w * 0.20)))
        self.art_label.setFixedSize(art_sz, art_sz)
        # Update border-radius to match
        r = art_sz // 6
        self.art_label.setStyleSheet(
            f"background-color: rgba(97,88,72,80);"
            f"border-radius: {r}px; border: none;")

        # Waveform: 12% of height
        wave_h = max(20, min(60, int(h * 0.12)))
        self.waveform.setFixedHeight(wave_h)

        # Play button: proportional
        play_sz = max(36, min(60, int(h * 0.22)))
        self.btn_play.setFixedSize(play_sz, play_sz)
        self.btn_play.setStyleSheet(
            f"border-radius: {play_sz // 2}px;")

        # Fonts — DPI-aware: compute desired pixel height first, then convert to
        # points so the physical size on screen is consistent across display scalings.
        dpi = max(72, self.logicalDpiY())   # 96 at 100 %, 144 at 150 %, 192 at 200 %

        fam     = self.theme_manager.get_theme().get("font_family", "Segoe UI") if self.theme_manager else "Segoe UI"
        f_main  = self.config.get("font_media_main", fam) if self.config else fam
        f_sub   = self.config.get("font_media_sub",  fam) if self.config else fam
        f_mono  = self.config.get("font_stats", "Consolas") if self.config else "Consolas"

        title_pt  = max(10, min(22, int(h * 0.075 * 72 / dpi)))
        artist_pt = max(8,  min(14, int(h * 0.055 * 72 / dpi)))
        mono_pt   = max(7,  min(11, int(h * 0.045 * 72 / dpi)))

        self.status_label.setFont(QFont(f_main, title_pt))
        self.artist_label.setFont(QFont(f_sub,  artist_pt))
        self.album_label.setFont(QFont(f_mono,  mono_pt))
        for lbl in [self.lbl_pos, self.lbl_remaining]:
            lbl.setFont(QFont(f_mono, mono_pt))

    # ── Theme ─────────────────────────────────────────────────────────────

    def apply_theme(self):
        if not self.theme_manager:
            return

        t = self.get_theme_with_opacity()
        base_style = (
            f"QWidget#media {{"
            f"  background-color: {t['background']};"
            f"  border-radius: {t.get('border_radius', '22px')};"
            f"  border: 1px solid rgba(255, 255, 255, 36);"
            f"}}"
        )
        self.setStyleSheet(base_style + self.get_qss())

        fam      = t.get("font_family", "Segoe UI")
        font_main = (self.config.get("font_media_main", fam)
                     if self.config else fam)
        font_sub  = (self.config.get("font_media_sub",  fam)
                     if self.config else fam)
        font_mono = (self.config.get("font_stats", "Consolas")
                     if self.config else "Consolas")

        self.status_label.setFont(QFont(font_main, 14))
        self.status_label.setStyleSheet(
            f"color: {t.get('text_main', '#FAF7F2')}; background: transparent;")

        self.artist_label.setFont(QFont(font_sub, 10))
        self.artist_label.setStyleSheet(
            "color: #9A8F7C; background: transparent;")

        self.album_label.setFont(QFont(font_mono, 8))
        self.album_label.setStyleSheet(
            "color: #615848; background: transparent;")

        for lbl in [self.lbl_pos, self.lbl_remaining]:
            lbl.setFont(QFont(font_mono, 9))
            lbl.setStyleSheet("color: #615848; background: transparent;")

    # ── Playback actions ──────────────────────────────────────────────────

    def prev_track(self):
        if self.system_media:
            self.system_media.prev()

    def next_track(self):
        if self.system_media:
            self.system_media.next()

    def toggle_play(self):
        if self.system_media:
            self.system_media.play_pause()

    def _on_seek(self, pos: float):
        self.waveform.set_position(pos)

    # ── Metadata update ───────────────────────────────────────────────────

    def update_metadata(self, title, artist, art_data):
        self.status_label.setText(title  or "Unknown Title")
        self.artist_label.setText(artist or "Unknown Artist")
        self.album_label.setText("")    # album not exposed yet

        self.art_data = art_data
        if art_data:
            img = QImage()
            if img.loadFromData(art_data):
                size    = 68
                rounded = QPixmap(size, size)
                rounded.fill(Qt.GlobalColor.transparent)
                scaled  = img.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation)
                x       = (scaled.width()  - size) // 2
                y       = (scaled.height() - size) // 2
                cropped = scaled.copy(x, y, size, size)

                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(0, 0, size, size, 12, 12)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, QPixmap.fromImage(cropped))
                painter.end()

                self.art_label.setPixmap(rounded)
                return
        self.art_label.clear()

    def update_play_icon(self, is_playing: bool):
        self.is_playing = is_playing
        self.btn_play.setText("||" if is_playing else ">")

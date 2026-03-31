from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QPixmap, QImage, QPainter, QPainterPath
from base_widget import BaseWidget
from datetime import timedelta

class MediaWidget(BaseWidget):
    def __init__(self, system_media=None, theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager, widget_id="media")
        
        self.system_media = system_media
        self.config = config_manager
        self.art_data = None
        self.duration = 0
        self.position = 0
        self.is_seeking = False
        
        # Main Layout (Vertical for distinct sections)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(8)
        self.setLayout(self.main_layout)
        
        # --- Top Section: Art + Text ---
        top_layout = QHBoxLayout()
        
        # Album Art
        self.art_label = QLabel()
        self.art_label.setFixedSize(48, 48)
        self.art_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            border: none;
        """)
        self.art_label.setScaledContents(True)
        top_layout.addWidget(self.art_label)
        
        # Text Info
        text_layout = QVBoxLayout()
        self.status_label = QLabel("No Media") # Title
        self.status_label.setObjectName("media_status") # For QSS
        self.status_label.setWordWrap(True)
        
        self.artist_label = QLabel("") # Artist
        self.artist_label.setObjectName("media_artist")
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        text_layout.addWidget(self.status_label)
        text_layout.addWidget(self.artist_label)
        top_layout.addLayout(text_layout)
        
        self.main_layout.addLayout(top_layout)
        
        # --- Bottom Section: Controls ---
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        # Playback
        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶")
        self.btn_next = QPushButton("⏭")
        
        for btn in [self.btn_prev, self.btn_play, self.btn_next]:
            btn.setFixedSize(32, 32)
            btn.setObjectName("media_btn")
            bottom_layout.addWidget(btn)
            
        bottom_layout.addStretch()
        
        self.main_layout.addLayout(bottom_layout)
        
        # Apply Theme
        self.apply_theme()
        
        # Connections
        self.btn_prev.clicked.connect(self.prev_track)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_next.clicked.connect(self.next_track)
        

        if self.system_media:
            self.system_media.metadata_changed.connect(self.update_metadata)
            self.system_media.playback_status_changed.connect(self.update_play_icon)
            # Timeline not needed in simplified view
            
        self.is_playing = False

        self.resize(380, 120) # Smaller height since sliders are gone

    def resizeEvent(self, event):
        super().resizeEvent(event)

    # ... (controls etc) ...

    def apply_theme(self):
        if not self.theme_manager:
            return

        t = self.get_theme_with_opacity()
        
        # Style sheet (Base + QSS)
        base_style = f"""
            QWidget#base_widget_frame, MediaWidget {{
                background-color: {t['background']};
                border-radius: {t['border_radius']};
            }}
        """
        # Append QSS
        self.setStyleSheet(base_style + self.get_qss())
        
        # Fonts
        font_main_name = self.config.get("font_media_main", t['font_family']) if self.config else t['font_family']
        font_sub_name = self.config.get("font_media_sub", t['font_family']) if self.config else t['font_family']
        
        self.status_label.setFont(QFont(font_main_name, 11, QFont.Weight.Bold))
        self.artist_label.setFont(QFont(font_sub_name, 9))

    def prev_track(self):
        if self.system_media:
            self.system_media.prev()

    def next_track(self):
        if self.system_media:
            self.system_media.next()

    def toggle_play(self):
        if self.system_media:
            self.system_media.play_pause()
            
    def update_metadata(self, title, artist, art_data):
        self.status_label.setText(title if title else "Unknown Title")
        self.artist_label.setText(artist if artist else "Unknown Artist")
        
        self.art_data = art_data
        if art_data:
            img = QImage()
            if img.loadFromData(art_data):
                # Rounded Art
                size = 60
                rounded = QPixmap(size, size)
                rounded.fill(Qt.GlobalColor.transparent)
                scaled_img = img.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                x = (scaled_img.width() - size) // 2
                y = (scaled_img.height() - size) // 2
                cropped = scaled_img.copy(x, y, size, size)
                
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(0, 0, size, size, 10, 10)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, QPixmap.fromImage(cropped))
                painter.end()
                
                self.art_label.setPixmap(rounded)
            else:
                self.art_label.clear()
        else:
            self.art_label.clear()

    def update_play_icon(self, is_playing):
        self.is_playing = is_playing
        self.btn_play.setText("⏸" if is_playing else "▶")


import sys
import os
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton, QLabel,
                             QComboBox, QCheckBox, QTabWidget, QFileDialog,
                             QProgressBar, QActionGroup, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QPixmap, QImage, QIcon

def resource_path(relative):
    """PyInstaller ile paketlendiğinde de dosya yolunu doğru döndürür."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

import yt_dlp

# ── Çeviriler ─────────────────────────────────────────────────────────────────

TRANSLATIONS = {
    "tr": {
        "window_title":  "YNDown",
        "link_ph":       "Link...",
        "tab_video":     "Video",
        "tab_audio":     "Ses",
        "ext_label":     "Uzantı:",
        "qual_label":    "Kalite:",
        "select":        "Seç",
        "metadata":      "Metadata",
        "subtitle":      "Altyazı",
        "download":      "İndir",
        "ready":         "Hazır",
        "fetching":      "Bilgiler alınıyor...",
        "done":          "Tamamlandı!",
        "warn_ffmpeg":   "UYARI: ffmpeg.exe eksik!",
        "folder_title":  "Klasör Seç",
        "conn_error":    "Bağlantı Hatası!",
        "thumbnail":     "Thumbnail",
        "menu_language": "Dil",
    },
    "en": {
        "window_title":  "YNDown",
        "link_ph":       "Link...",
        "tab_video":     "Video",
        "tab_audio":     "Audio",
        "ext_label":     "Extension:",
        "qual_label":    "Quality:",
        "select":        "Select",
        "metadata":      "Metadata",
        "subtitle":      "Subtitles",
        "download":      "Download",
        "ready":         "Ready",
        "fetching":      "Fetching info...",
        "done":          "Done!",
        "warn_ffmpeg":   "WARNING: ffmpeg.exe missing!",
        "folder_title":  "Select Folder",
        "conn_error":    "Connection Error!",
        "thumbnail":     "Thumbnail",
        "menu_language": "Language",
    },
    "fr": {
        "window_title":  "YNDown",
        "link_ph":       "Lien...",
        "tab_video":     "Vidéo",
        "tab_audio":     "Audio",
        "ext_label":     "Extension:",
        "qual_label":    "Qualité:",
        "select":        "Choisir",
        "metadata":      "Métadonnées",
        "subtitle":      "Sous-titres",
        "download":      "Télécharger",
        "ready":         "Prêt",
        "fetching":      "Récupération...",
        "done":          "Terminé !",
        "warn_ffmpeg":   "AVERTISSEMENT : ffmpeg.exe manquant !",
        "folder_title":  "Choisir un dossier",
        "conn_error":    "Erreur de connexion !",
        "thumbnail":     "Miniature",
        "menu_language": "Langue",
    },
    "es": {
        "window_title":  "YNDown",
        "link_ph":       "Enlace...",
        "tab_video":     "Vídeo",
        "tab_audio":     "Audio",
        "ext_label":     "Extensión:",
        "qual_label":    "Calidad:",
        "select":        "Seleccionar",
        "metadata":      "Metadatos",
        "subtitle":      "Subtítulos",
        "download":      "Descargar",
        "ready":         "Listo",
        "fetching":      "Obteniendo información...",
        "done":          "¡Completado!",
        "warn_ffmpeg":   "AVISO: ¡ffmpeg.exe falta!",
        "folder_title":  "Seleccionar carpeta",
        "conn_error":    "¡Error de conexión!",
        "thumbnail":     "Miniatura",
        "menu_language": "Idioma",
    },
    "it": {
        "window_title":  "YNDown",
        "link_ph":       "Link...",
        "tab_video":     "Video",
        "tab_audio":     "Audio",
        "ext_label":     "Estensione:",
        "qual_label":    "Qualità:",
        "select":        "Seleziona",
        "metadata":      "Metadati",
        "subtitle":      "Sottotitoli",
        "download":      "Scarica",
        "ready":         "Pronto",
        "fetching":      "Recupero informazioni...",
        "done":          "Completato!",
        "warn_ffmpeg":   "AVVISO: ffmpeg.exe mancante!",
        "folder_title":  "Seleziona cartella",
        "conn_error":    "Errore di connessione!",
        "thumbnail":     "Miniatura",
        "menu_language": "Lingua",
    },
    "ru": {
        "window_title":  "YNDown",
        "link_ph":       "Ссылка...",
        "tab_video":     "Видео",
        "tab_audio":     "Аудио",
        "ext_label":     "Расширение:",
        "qual_label":    "Качество:",
        "select":        "Выбрать",
        "metadata":      "Метаданные",
        "subtitle":      "Субтитры",
        "download":      "Скачать",
        "ready":         "Готово",
        "fetching":      "Получение данных...",
        "done":          "Завершено!",
        "warn_ffmpeg":   "ПРЕДУПРЕЖДЕНИЕ: ffmpeg.exe не найден!",
        "folder_title":  "Выбрать папку",
        "conn_error":    "Ошибка подключения!",
        "thumbnail":     "Миниатюра",
        "menu_language": "Язык",
    },
}

# ── Download Threads ──────────────────────────────────────────────────────────

class MetadataThread(QThread):
    metadata_loaded = pyqtSignal(dict)
    error_occurred  = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            ydl_opts = {'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                self.metadata_loaded.emit(info)
        except Exception as e:
            self.error_occurred.emit(str(e))

class DownloadThread(QThread):
    progress_updated = pyqtSignal(dict)
    finished         = pyqtSignal(bool, str)

    def __init__(self, url, options):
        super().__init__()
        self.url     = url
        self.options = options

    def run(self):
        def progress_hook(d):
            self.progress_updated.emit(d)
        try:
            ydl_opts = self.options.copy()
            ydl_opts['progress_hooks'] = [progress_hook]
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished.emit(True, "done")
        except Exception as e:
            self.finished.emit(False, str(e))

# ── Ana Pencere ───────────────────────────────────────────────────────────────

class YNDownApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("YNDown", "YNDownMain")
        self._current_lang = str(self.settings.value("language", "tr"))

        self.video_info = None
        self.save_path  = os.path.join(os.path.expanduser("~"), "Downloads")

        icon_path = resource_path("yndown.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central = QWidget()
        self.setCentralWidget(central)

        self._build_menubar()
        self.init_ui(central)
        self._retranslate_ui()

    # ── Translation helper ────────────────────────────────────────────────────

    def _t(self, key, **kw):
        text = TRANSLATIONS.get(self._current_lang, TRANSLATIONS["tr"]).get(key, key)
        return text.format(**kw) if kw else text

    # ── Menubar ───────────────────────────────────────────────────────────────

    def _build_menubar(self):
        mb = self.menuBar()
        mb.clear()

        self._lang_menu = mb.addMenu(self._t("menu_language"))
        lg = QActionGroup(self)
        lg.setExclusive(True)

        for key, label in [
            ("tr", "Türkçe"), ("en", "English"), ("fr", "Français"),
            ("es", "Español"), ("it", "Italiano"), ("ru", "Русский"),
        ]:
            act = QAction(label, self, checkable=True)
            act.setChecked(key == self._current_lang)
            act.triggered.connect(lambda checked, k=key: self._on_language(k))
            lg.addAction(act)
            self._lang_menu.addAction(act)

        self._lang_action_group = lg

    def _on_language(self, key: str):
        self._current_lang = key
        self.settings.setValue("language", key)
        self._retranslate_ui()

    # ── UI Build ──────────────────────────────────────────────────────────────

    def init_ui(self, central):
        self.setFixedSize(550, 250)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_tab_content(is_video=True),  "")
        self.tabs.addTab(self._create_tab_content(is_video=False), "")
        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs)

    def _create_tab_content(self, is_video):
        tab_widget = QWidget()
        layout = QHBoxLayout(tab_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(12)

        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        layout.addLayout(left_col, 3)

        # Link input
        link_input = QLineEdit()
        link_input.setFixedHeight(24)
        link_input.setFixedWidth(524)
        link_input.textChanged.connect(self.on_link_changed)
        left_col.addWidget(link_input)
        if is_video: self.video_link_input = link_input
        else:        self.audio_link_input = link_input

        # Dropdowns
        drop_layout = QHBoxLayout()
        ext_combo  = QComboBox(); ext_combo.setFixedHeight(22)
        qual_combo = QComboBox(); qual_combo.setFixedHeight(22)
        if is_video:
            self._ext_lbl_v  = QLabel()
            self._qual_lbl_v = QLabel()
            drop_layout.addWidget(self._ext_lbl_v)
            drop_layout.addWidget(ext_combo)
            drop_layout.addWidget(self._qual_lbl_v)
            self.v_ext_combo  = ext_combo
            self.v_qual_combo = qual_combo
        else:
            self._ext_lbl_a  = QLabel()
            self._qual_lbl_a = QLabel()
            drop_layout.addWidget(self._ext_lbl_a)
            drop_layout.addWidget(ext_combo)
            drop_layout.addWidget(self._qual_lbl_a)
            self.a_ext_combo  = ext_combo
            self.a_qual_combo = qual_combo
        drop_layout.addWidget(qual_combo)
        left_col.addLayout(drop_layout)

        # Save path
        save_layout = QHBoxLayout()
        path_input = QLineEdit(self.save_path)
        path_input.setReadOnly(True)
        path_input.setFixedHeight(22)
        btn_path = QPushButton()
        btn_path.setFixedWidth(40)
        btn_path.setFixedHeight(22)
        btn_path.clicked.connect(self.select_directory)
        save_layout.addWidget(path_input)
        save_layout.addWidget(btn_path)
        left_col.addLayout(save_layout)
        if is_video:
            self.v_path_display = path_input
            self._btn_path_v    = btn_path
        else:
            self.a_path_display = path_input
            self._btn_path_a    = btn_path

        # Checkboxes
        cb_layout = QHBoxLayout()
        meta_cb = QCheckBox()
        subs_cb = QCheckBox()
        cb_layout.addWidget(meta_cb)
        cb_layout.addWidget(subs_cb)
        left_col.addLayout(cb_layout)
        if is_video:
            self.v_meta_cb = meta_cb
            self.v_subs_cb = subs_cb
        else:
            subs_cb.hide()
            self.a_meta_cb = meta_cb
            self.a_subs_cb = subs_cb

        # Action row
        action_layout = QHBoxLayout()
        btn_dl = QPushButton()
        btn_dl.setFixedWidth(70)
        btn_dl.setFixedHeight(26)
        btn_dl.clicked.connect(self.start_download)
        prog = QProgressBar()
        prog.setFixedHeight(26)
        prog.setFixedWidth(233)
        prog.setTextVisible(False)
        action_layout.addWidget(btn_dl)
        action_layout.addWidget(prog)
        left_col.addLayout(action_layout)
        if is_video:
            self.v_dl_btn  = btn_dl
            self.v_progress = prog
        else:
            self.a_dl_btn  = btn_dl
            self.a_progress = prog

        # Status
        status = QLabel()
        status.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        left_col.addWidget(status)
        if is_video: self.v_status = status
        else:        self.a_status = status

        # Thumbnail
        thumb = QLabel()
        thumb.setFixedSize(200, 112)
        thumb.setAlignment(Qt.AlignCenter)
        thumb.setStyleSheet("border: 1px solid #ccc;")
        layout.addWidget(thumb, 2)
        if is_video: self.v_thumb = thumb
        else:        self.a_thumb = thumb

        return tab_widget

    # ── Retranslate ───────────────────────────────────────────────────────────

    def _retranslate_ui(self):
        self.setWindowTitle(self._t("window_title"))
        # Tab labels
        self.tabs.setTabText(0, self._t("tab_video"))
        self.tabs.setTabText(1, self._t("tab_audio"))
        # Link placeholders
        self.video_link_input.setPlaceholderText(self._t("link_ph"))
        self.audio_link_input.setPlaceholderText(self._t("link_ph"))
        # Dropdown labels
        self._ext_lbl_v.setText(self._t("ext_label"))
        self._qual_lbl_v.setText(self._t("qual_label"))
        self._ext_lbl_a.setText(self._t("ext_label"))
        self._qual_lbl_a.setText(self._t("qual_label"))
        # Buttons
        self._btn_path_v.setText(self._t("select"))
        self._btn_path_a.setText(self._t("select"))
        self.v_dl_btn.setText(self._t("download"))
        self.a_dl_btn.setText(self._t("download"))
        # Checkboxes
        self.v_meta_cb.setText(self._t("metadata"))
        self.v_subs_cb.setText(self._t("subtitle"))
        self.a_meta_cb.setText(self._t("metadata"))
        # Thumbnails
        self.v_thumb.setText(self._t("thumbnail"))
        self.a_thumb.setText(self._t("thumbnail"))
        # Status
        self.v_status.setText(self._t("ready"))
        self.a_status.setText(self._t("ready"))
        # Rebuild menubar with new language
        self._build_menubar()

    # ── Logic ─────────────────────────────────────────────────────────────────

    def set_status_msg(self, msg, color="#333"):
        current = self.get_current_status()
        current.setText(msg)
        current.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {color};")

    def on_tab_changed(self, index):
        source = self.audio_link_input if index == 0 else self.video_link_input
        target = self.video_link_input  if index == 0 else self.audio_link_input
        target.setText(source.text())
        self.update_quality_options()

    def on_link_changed(self, text):
        current_tab = self.tabs.currentIndex()
        other_input = self.audio_link_input if current_tab == 0 else self.video_link_input
        if other_input.text() != text:
            other_input.blockSignals(True)
            other_input.setText(text)
            other_input.blockSignals(False)

        if not text:
            self.clear_ui()
            return

        if "youtube.com" in text or "youtu.be" in text:
            self.fetch_metadata(text)

    def clear_ui(self):
        self.video_info = None
        for thumb in [self.v_thumb, self.a_thumb]:
            thumb.clear()
            thumb.setText(self._t("thumbnail"))
        self.set_status_msg(self._t("ready"))

    def fetch_metadata(self, url):
        self.set_status_msg(self._t("fetching"), "blue")
        self.metadata_thread = MetadataThread(url)
        self.metadata_thread.metadata_loaded.connect(self.on_metadata_loaded)
        self.metadata_thread.error_occurred.connect(self.on_metadata_error)
        self.metadata_thread.start()

    def on_metadata_loaded(self, info):
        self.video_info = info
        self.set_status_msg(self._t("done"), "green")
        thumb_url = info.get('thumbnail')
        if thumb_url:
            self.load_thumbnail(thumb_url)
        self.update_quality_options()

    def load_thumbnail(self, url):
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                image = QImage()
                image.loadFromData(response.content)
                pixmap = QPixmap.fromImage(image)
                for lbl in [self.v_thumb, self.a_thumb]:
                    lbl.setPixmap(pixmap.scaled(lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception:
            pass

    def update_quality_options(self):
        if not self.video_info:
            return
        is_video = self.tabs.currentIndex() == 0
        ext_c  = self.v_ext_combo  if is_video else self.a_ext_combo
        qual_c = self.v_qual_combo if is_video else self.a_qual_combo
        ext_c.clear()
        qual_c.clear()
        formats = self.video_info.get('formats', [])
        if is_video:
            ext_c.addItems(["mp4", "mkv", "webm", "flv"])
            qualities = sorted(list(set([f.get('height') for f in formats if f.get('height')])), reverse=True)
            for q in qualities:
                qual_c.addItem(f"{q}p", q)
        else:
            ext_c.addItems(["mp3", "m4a", "wav", "opus", "aac"])
            bitrates = sorted(list(set([f.get('abr') for f in formats if f.get('abr')])), reverse=True)
            for b in bitrates:
                qual_c.addItem(f"{int(b)} kbps", b)

    def select_directory(self):
        path = QFileDialog.getExistingDirectory(self, self._t("folder_title"), self.save_path)
        if path:
            self.save_path = path
            self.v_path_display.setText(path)
            self.a_path_display.setText(path)

    def get_current_status(self):
        return self.v_status if self.tabs.currentIndex() == 0 else self.a_status

    def start_download(self):
        is_video = self.tabs.currentIndex() == 0
        url = self.video_link_input.text() if is_video else self.audio_link_input.text()
        if not self.video_info:
            return

        ext       = (self.v_ext_combo  if is_video else self.a_ext_combo).currentText()
        qual_val  = (self.v_qual_combo if is_video else self.a_qual_combo).currentData()

        ydl_opts = {'outtmpl': os.path.join(self.save_path, '%(title)s.%(ext)s')}

        ffmpeg_exe = 'ffmpeg.exe'
        ffmpeg_path = None
        for p in [os.path.dirname(sys.executable), os.getcwd()]:
            candidate = os.path.join(p, ffmpeg_exe)
            if os.path.exists(candidate):
                ffmpeg_path = candidate
                break
        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path
        elif self.v_subs_cb.isChecked() or (is_video and ext != 'webm'):
            self.set_status_msg(self._t("warn_ffmpeg"), "orange")

        if is_video:
            ydl_opts['format'] = f'bestvideo[height<={qual_val}]+bestaudio/best'
            ydl_opts['merge_output_format'] = ext
            if self.v_subs_cb.isChecked():
                ydl_opts['writesubtitles'] = True
                ydl_opts['postprocessors'] = [{'key': 'FFmpegEmbedSubtitle'}]
        else:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': ext}]

        if (is_video and self.v_meta_cb.isChecked()) or (not is_video and self.a_meta_cb.isChecked()):
            if 'postprocessors' not in ydl_opts:
                ydl_opts['postprocessors'] = []
            ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata'})

        self.set_status_msg("İndiriliyor...", "blue")
        self.v_dl_btn.setEnabled(False)
        self.a_dl_btn.setEnabled(False)
        self.v_progress.setValue(0)
        self.a_progress.setValue(0)
        self.download_thread = DownloadThread(url, ydl_opts)
        self.download_thread.progress_updated.connect(self.on_progress)
        self.download_thread.finished.connect(self.on_finished)
        self.download_thread.start()

    def on_progress(self, d):
        if d['status'] == 'downloading':
            total      = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                val = int(downloaded * 100 / total)
                self.v_progress.setValue(val)
                self.a_progress.setValue(val)
            else:
                try:
                    import re
                    p_str = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_percent_str', '0%')).replace('%', '').strip()
                    val = int(float(p_str))
                    self.v_progress.setValue(val)
                    self.a_progress.setValue(val)
                except Exception:
                    pass

    def on_finished(self, success, msg):
        self.v_dl_btn.setEnabled(True)
        self.a_dl_btn.setEnabled(True)
        if success:
            self.set_status_msg(self._t("done"), "green")
        else:
            self.set_status_msg(f"Hata: {msg[:20]}...", "red")

    def on_metadata_error(self, err):
        self.set_status_msg(self._t("conn_error"), "red")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon_path = resource_path("yndown.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    window = YNDownApp()
    window.show()
    sys.exit(app.exec_())

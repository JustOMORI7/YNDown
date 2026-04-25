import sys
import os
import ctypes
import winreg
import requests

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QMainWindow, QActionGroup
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer
from PyQt5.QtGui import QPixmap, QImage, QIcon

def resource_path(relative):
    """PyInstaller ile paketlendiğinde de dosya yolunu doğru döndürür."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

from qfluentwidgets import (LineEdit, PrimaryPushButton, PushButton, ComboBox,
                            CheckBox, Pivot, CaptionLabel, SubtitleLabel,
                            ProgressBar, ImageLabel, setTheme, Theme,
                            setThemeColor, isDarkTheme, RoundMenu, Action, FluentIcon)
import yt_dlp

# DPI Ayarları
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# ── Registry helpers ──────────────────────────────────────────────────────────

def _reg_dword(hive, path, name, default=None):
    try:
        key = winreg.OpenKey(hive, path)
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return val
    except Exception:
        return default

def _get_system_theme() -> str:
    val = _reg_dword(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        "AppsUseLightTheme", default=1
    )
    return "dark" if val == 0 else "light"

def _get_accent_color() -> str:
    val = _reg_dword(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\DWM",
        "AccentColor", default=None
    )
    if val is None:
        return "#0078d4"
    val = val & 0xFFFFFFFF
    b = (val >> 16) & 0xFF
    g = (val >> 8)  & 0xFF
    r = val         & 0xFF
    return f"#{r:02X}{g:02X}{b:02X}"

# ── Çeviriler ─────────────────────────────────────────────────────────────────

TRANSLATIONS = {
    "tr": {
        "window_title": "YNDown",
        "link_ph": "Bağlantıyı yapıştırın...",
        "video": "Video",
        "audio": "Ses",
        "ext_ph": "Uzantı Seç",
        "qual_ph": "Kalite / Bitrate",
        "select": "Seç",
        "metadata": "Metadata",
        "subtitle": "Altyazı",
        "download": "İndir",
        "ready": "Hazır",
        "fetching": "Bilgiler çekiliyor...",
        "downloading": "İndiriliyor...",
        "done": "Tamamlandı!",
        "best": "En iyi",
        "folder_title": "Klasör Seç",
        "menu_theme": "Tema",
        "theme_dark": "Koyu",
        "theme_light": "Açık",
        "theme_auto": "Otomatik (Sistem)",
        "menu_language": "Dil",
    },
    "en": {
        "window_title": "YNDown",
        "link_ph": "Paste link here...",
        "video": "Video",
        "audio": "Audio",
        "ext_ph": "Select Extension",
        "qual_ph": "Quality / Bitrate",
        "select": "Select",
        "metadata": "Metadata",
        "subtitle": "Subtitles",
        "download": "Download",
        "ready": "Ready",
        "fetching": "Fetching info...",
        "downloading": "Downloading...",
        "done": "Done!",
        "best": "Best",
        "folder_title": "Select Folder",
        "menu_theme": "Theme",
        "theme_dark": "Dark",
        "theme_light": "Light",
        "theme_auto": "Auto (System)",
        "menu_language": "Language",
    },
    "fr": {
        "window_title": "YNDown",
        "link_ph": "Collez le lien ici...",
        "video": "Vidéo",
        "audio": "Audio",
        "ext_ph": "Choisir l'extension",
        "qual_ph": "Qualité / Débit",
        "select": "Choisir",
        "metadata": "Métadonnées",
        "subtitle": "Sous-titres",
        "download": "Télécharger",
        "ready": "Prêt",
        "fetching": "Récupération des infos...",
        "downloading": "Téléchargement...",
        "done": "Terminé !",
        "best": "Meilleur",
        "folder_title": "Choisir un dossier",
        "menu_theme": "Thème",
        "theme_dark": "Sombre",
        "theme_light": "Clair",
        "theme_auto": "Auto (Système)",
        "menu_language": "Langue",
    },
    "es": {
        "window_title": "YNDown",
        "link_ph": "Pega el enlace aquí...",
        "video": "Vídeo",
        "audio": "Audio",
        "ext_ph": "Seleccionar extensión",
        "qual_ph": "Calidad / Tasa de bits",
        "select": "Seleccionar",
        "metadata": "Metadatos",
        "subtitle": "Subtítulos",
        "download": "Descargar",
        "ready": "Listo",
        "fetching": "Obteniendo información...",
        "downloading": "Descargando...",
        "done": "¡Completado!",
        "best": "Mejor",
        "folder_title": "Seleccionar carpeta",
        "menu_theme": "Tema",
        "theme_dark": "Oscuro",
        "theme_light": "Claro",
        "theme_auto": "Auto (Sistema)",
        "menu_language": "Idioma",
    },
    "it": {
        "window_title": "YNDown",
        "link_ph": "Incolla il link qui...",
        "video": "Video",
        "audio": "Audio",
        "ext_ph": "Seleziona estensione",
        "qual_ph": "Qualità / Bitrate",
        "select": "Seleziona",
        "metadata": "Metadati",
        "subtitle": "Sottotitoli",
        "download": "Scarica",
        "ready": "Pronto",
        "fetching": "Recupero informazioni...",
        "downloading": "Download in corso...",
        "done": "Completato!",
        "best": "Migliore",
        "folder_title": "Seleziona cartella",
        "menu_theme": "Tema",
        "theme_dark": "Scuro",
        "theme_light": "Chiaro",
        "theme_auto": "Auto (Sistema)",
        "menu_language": "Lingua",
    },
    "ru": {
        "window_title": "YNDown",
        "link_ph": "Вставьте ссылку...",
        "video": "Видео",
        "audio": "Аудио",
        "ext_ph": "Выбрать расширение",
        "qual_ph": "Качество / Битрейт",
        "select": "Выбрать",
        "metadata": "Метаданные",
        "subtitle": "Субтитры",
        "download": "Скачать",
        "ready": "Готово",
        "fetching": "Получение данных...",
        "downloading": "Загрузка...",
        "done": "Завершено!",
        "best": "Лучшее",
        "folder_title": "Выбрать папку",
        "menu_theme": "Тема",
        "theme_dark": "Тёмная",
        "theme_light": "Светлая",
        "theme_auto": "Авто (Система)",
        "menu_language": "Язык",
    },
}

# ── Download threads ──────────────────────────────────────────────────────────

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, opts, url):
        super().__init__()
        self.opts = opts
        self.url = url

    def run(self):
        try:
            self.opts['progress_hooks'] = [self.hook]
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                error_code = ydl.download([self.url])
                if error_code != 0:
                    raise Exception("yt-dlp error code: " + str(error_code))
            self.finished.emit("done")
        except Exception as e:
            self.finished.emit(f"error:{str(e)}")

    def hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                self.progress.emit(int(downloaded * 100 / total))
            else:
                try:
                    import re
                    p = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_percent_str', '0%')).replace('%','').strip()
                    self.progress.emit(int(float(p)))
                except Exception:
                    pass

class MetadataThread(QThread):
    metadata_loaded = pyqtSignal(dict)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            ydl_opts = {'skip_download': True, 'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.metadata_loaded.emit(ydl.extract_info(self.url, download=False))
        except Exception:
            pass

# ── Ana Pencere ───────────────────────────────────────────────────────────────

class YNDownApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("YNDown", "YNDown")
        self._current_lang  = str(self.settings.value("language", "tr"))
        self._current_theme = str(self.settings.value("theme", "auto"))

        setThemeColor(_get_accent_color())

        self.menuBar().setNativeMenuBar(False)
        self._apply_theme(self._current_theme)

        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.video_info = None

        icon_path = resource_path("yndown.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central = QWidget()
        self.setCentralWidget(central)

        self._build_menubar()
        self._build_ui(central)
        self._retranslate_ui()

    # ── Translation helper ────────────────────────────────────────────────────

    def _t(self, key, **kw):
        text = TRANSLATIONS.get(self._current_lang, TRANSLATIONS["tr"]).get(key, key)
        return text.format(**kw) if kw else text

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, theme_str):
        self._current_theme = theme_str
        if theme_str == "dark":
            setTheme(Theme.DARK)
        elif theme_str == "light":
            setTheme(Theme.LIGHT)
        else:  # auto
            sys_t = _get_system_theme()
            setTheme(Theme.DARK if sys_t == "dark" else Theme.LIGHT)

        is_dark = isDarkTheme()
        bg_color = "#1C1C1C" if is_dark else "#F3F3F3"
        text_color = "white" if is_dark else "black"

        if is_dark:
            mb_style = """
                QMenuBar {
                    background-color: transparent;
                    color: white;
                    padding: 0px;
                }
                QMenuBar::item {
                    background: transparent;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QMenuBar::item:selected {
                    background: rgba(255, 255, 255, 0.1);
                }
                QMenuBar::item:pressed {
                    background: rgba(255, 255, 255, 0.15);
                }
            """
        else:
            mb_style = """
                QMenuBar {
                    background-color: transparent;
                    color: black;
                    padding: 0px;
                }
                QMenuBar::item {
                    background: transparent;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QMenuBar::item:selected {
                    background: rgba(0, 0, 0, 0.05);
                }
                QMenuBar::item:pressed {
                    background: rgba(0, 0, 0, 0.1);
                }
            """

        self.setStyleSheet(
            f"YNDownApp {{ background-color: {bg_color}; }}\n"
            f"SubtitleLabel {{ color: {text_color}; }}\n"
            f"CaptionLabel  {{ color: {text_color}; }}\n"
        )
        self.menuBar().setStyleSheet(mb_style)
        self._set_title_bar_dark(is_dark)

    def _set_title_bar_dark(self, dark):
        try:
            hwnd = int(self.winId())
            value = ctypes.c_int(1 if dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
            )
        except Exception:
            pass

    # ── Menubar ───────────────────────────────────────────────────────────────

    def _build_menubar(self):
        mb = self.menuBar()
        mb.setMinimumHeight(32)

        if hasattr(self, "theme_menu") and self.theme_menu:
            self.theme_menu.deleteLater()
            self.theme_menu = None
        if hasattr(self, "lang_menu") and self.lang_menu:
            self.lang_menu.deleteLater()
            self.lang_menu = None

        mb.clear()

        # ── Theme menu ────────────────────────────────────────────────────────
        self.theme_menu = RoundMenu(self._t("menu_theme"), self)
        self.theme_menu.setIcon(FluentIcon.PALETTE)

        tg = QActionGroup(self)
        tg.setExclusive(True)

        theme_icons = {
            "auto":  FluentIcon.SYNC,
            "light": FluentIcon.BRIGHTNESS,
            "dark":  FluentIcon.QUIET_HOURS,
        }

        for k, lk in [("auto", "theme_auto"), ("light", "theme_light"), ("dark", "theme_dark")]:
            is_sel = (str(k) == str(self._current_theme))
            icon = FluentIcon.ACCEPT if is_sel else theme_icons[k]
            act = Action(icon, self._t(lk), self, checkable=True)
            act.setChecked(is_sel)
            act.triggered.connect(lambda checked, val=k: self._on_theme(val))
            tg.addAction(act)
            self.theme_menu.addAction(act)

        self.theme_menu.aboutToHide.connect(
            lambda: QTimer.singleShot(50, lambda: mb.setActiveAction(None))
        )
        mb.addMenu(self.theme_menu)

        # ── Language menu ─────────────────────────────────────────────────────
        self.lang_menu = RoundMenu(self._t("menu_language"), self)
        self.lang_menu.setIcon(FluentIcon.LANGUAGE)

        lg = QActionGroup(self)
        lg.setExclusive(True)

        for k, label in [
            ("tr", "Türkçe"), ("en", "English"), ("fr", "Français"),
            ("es", "Español"), ("it", "Italiano"), ("ru", "Русский"),
        ]:
            is_sel = (str(k) == str(self._current_lang))
            icon = FluentIcon.ACCEPT if is_sel else FluentIcon.GLOBE
            act = Action(icon, label, self, checkable=True)
            act.setChecked(is_sel)
            act.triggered.connect(lambda checked, val=k: self._on_language(val))
            lg.addAction(act)
            self.lang_menu.addAction(act)

        self.lang_menu.aboutToHide.connect(
            lambda: QTimer.singleShot(50, lambda: mb.setActiveAction(None))
        )
        mb.addMenu(self.lang_menu)

    def _on_theme(self, theme):
        self._current_theme = str(theme)
        self.settings.setValue("theme", self._current_theme)
        self.settings.sync()
        self._apply_theme(self._current_theme)
        self._build_menubar()

    def _on_language(self, lang):
        self._current_lang = lang
        self.settings.setValue("language", lang)
        self._retranslate_ui()

    # ── UI Build ──────────────────────────────────────────────────────────────

    def _build_ui(self, central):
        self.setFixedWidth(640)
        self.setFixedHeight(420)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        self.title_label = SubtitleLabel("YNDown")
        header.addWidget(self.title_label)
        header.addStretch(1)
        self.pivot = Pivot(self)
        self.pivot.addItem("video", self._t("video"), self.update_options)
        self.pivot.addItem("audio", self._t("audio"), self.update_options)
        self.pivot.setCurrentItem("video")
        header.addWidget(self.pivot)
        layout.addLayout(header)

        # Link
        self.link_input = LineEdit(self)
        self.link_input.textChanged.connect(self.on_link_changed)
        layout.addWidget(self.link_input)

        # Middle
        middle = QHBoxLayout()
        settings_vbox = QVBoxLayout()
        settings_vbox.setSpacing(12)

        self.ext_combo  = ComboBox()
        self.qual_combo = ComboBox()
        h1 = QHBoxLayout()
        h1.addWidget(self.ext_combo)
        h1.addWidget(self.qual_combo)
        settings_vbox.addLayout(h1)

        self.path_disp = LineEdit()
        self.path_disp.setReadOnly(True)
        self.path_disp.setText(self.save_path)
        self.btn_path = PushButton("")
        self.btn_path.clicked.connect(self.select_dir)
        h2 = QHBoxLayout()
        h2.addWidget(self.path_disp)
        h2.addWidget(self.btn_path)
        settings_vbox.addLayout(h2)

        self.meta_cb = CheckBox("")
        self.subs_cb = CheckBox("")
        h3 = QHBoxLayout()
        h3.addWidget(self.meta_cb)
        h3.addWidget(self.subs_cb)
        settings_vbox.addLayout(h3)
        middle.addLayout(settings_vbox, 3)

        self.thumb = ImageLabel()
        self.thumb.setFixedSize(180, 101)
        self.thumb.setBorderRadius(8, 8, 8, 8)
        self.thumb.setStyleSheet("background-color: rgba(128,128,128,0.1); border: 1px solid rgba(128,128,128,0.2);")
        middle.addWidget(self.thumb, 2)
        layout.addLayout(middle)

        # Footer
        footer = QHBoxLayout()
        self.prog   = ProgressBar()
        self.btn_dl = PrimaryPushButton("")
        self.btn_dl.setFixedWidth(120)
        self.btn_dl.clicked.connect(self.start_download)
        footer.addWidget(self.prog)
        footer.addWidget(self.btn_dl)
        layout.addLayout(footer)

        self.status = CaptionLabel("")
        layout.addWidget(self.status)

    def _retranslate_ui(self):
        self.setWindowTitle(self._t("window_title"))
        self.link_input.setPlaceholderText(self._t("link_ph"))
        self.ext_combo.setPlaceholderText(self._t("ext_ph"))
        self.qual_combo.setPlaceholderText(self._t("qual_ph"))
        self.btn_path.setText(self._t("select"))
        self.meta_cb.setText(self._t("metadata"))
        self.subs_cb.setText(self._t("subtitle"))
        self.btn_dl.setText(self._t("download"))
        self.status.setText(self._t("ready"))
        # Update pivot tab labels via the internal items dict
        try:
            self.pivot.items["video"].setText(self._t("video"))
            self.pivot.items["audio"].setText(self._t("audio"))
        except Exception:
            pass
        self._build_menubar()

    # ── Logic ─────────────────────────────────────────────────────────────────

    def on_link_changed(self, text):
        if "http" in text:
            self.status.setText(self._t("fetching"))
            self.m_thread = MetadataThread(text)
            self.m_thread.metadata_loaded.connect(self.on_meta)
            self.m_thread.start()

    def on_meta(self, info):
        self.video_info = info
        try:
            r = requests.get(info.get('thumbnail'), timeout=5)
            img = QImage()
            img.loadFromData(r.content)
            self.thumb.setPixmap(QPixmap.fromImage(img).scaled(180, 101, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception:
            pass
        self.update_options()
        self.status.setText(self._t("ready"))

    def update_options(self):
        if not self.video_info:
            return
        try:
            current_tab = self.pivot.currentItem().text()
        except Exception:
            current_tab = self._t("video")

        is_v = (current_tab == self._t("video"))
        self.ext_combo.clear()
        self.qual_combo.clear()
        self.ext_combo.setPlaceholderText(self._t("ext_ph"))
        self.qual_combo.setPlaceholderText(self._t("qual_ph"))

        fmts = self.video_info.get('formats', [])
        if is_v:
            self.subs_cb.setEnabled(True)
            self.ext_combo.addItems(["mp4", "mkv", "webm", "flv"])
            qs = sorted(list(set([f.get('height') for f in fmts if f.get('height')])), reverse=True)
            for q in qs:
                self.qual_combo.addItem(f"{q}p", userData=q)
        else:
            self.subs_cb.setEnabled(False)
            self.ext_combo.addItems(["mp3", "m4a", "wav", "opus", "aac"])
            bitrates = sorted(list(set([int(f.get('abr')) for f in fmts if f.get('abr')])), reverse=True)
            if bitrates:
                for b in bitrates:
                    self.qual_combo.addItem(f"{b} kbps", userData=b)
            else:
                self.qual_combo.addItem(self._t("best"), userData="best")

    def select_dir(self):
        p = QFileDialog.getExistingDirectory(self, self._t("folder_title"))
        if p:
            self.path_disp.setText(p)
            self.save_path = p

    def start_download(self):
        url = self.link_input.text()
        if not url or not self.video_info:
            return

        ext = self.ext_combo.currentText()
        try:
            current_tab = self.pivot.currentItem().text()
        except Exception:
            current_tab = self._t("video")
        is_v = (current_tab == self._t("video"))
        quality_val = self.qual_combo.currentData()

        ydl_opts = {'outtmpl': os.path.join(self.save_path, '%(title)s.%(ext)s')}

        ffmpeg_exe = 'ffmpeg.exe'
        for p in [os.path.dirname(sys.executable), os.getcwd()]:
            candidate = os.path.join(p, ffmpeg_exe)
            if os.path.exists(candidate):
                ydl_opts['ffmpeg_location'] = candidate
                break

        if is_v:
            ydl_opts['format'] = f'bestvideo[height<={quality_val}]+bestaudio/best'
            ydl_opts['merge_output_format'] = ext
            if self.subs_cb.isChecked():
                ydl_opts['writesubtitles'] = True
                ydl_opts['postprocessors'] = [{'key': 'FFmpegEmbedSubtitle'}]
        else:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': ext,
                'preferredquality': str(quality_val) if quality_val and quality_val != 'best' else '192',
            }]

        if self.meta_cb.isChecked():
            if 'postprocessors' not in ydl_opts:
                ydl_opts['postprocessors'] = []
            ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata'})

        self.btn_dl.setEnabled(False)
        self.prog.setValue(0)
        self.status.setText(self._t("downloading"))
        self.dl_thread = DownloadThread(ydl_opts, url)
        self.dl_thread.progress.connect(self.prog.setValue)
        self.dl_thread.finished.connect(self.on_finished)
        self.dl_thread.start()

    def on_finished(self, msg):
        self.btn_dl.setEnabled(True)
        if msg == "done":
            self.prog.setValue(100)
            self.status.setText(self._t("done"))
        else:
            self.prog.setValue(0)
            self.status.setText(msg.replace("error:", "")[:40])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon_path = resource_path("yndown.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    w = YNDownApp()
    w.show()
    sys.exit(app.exec_())
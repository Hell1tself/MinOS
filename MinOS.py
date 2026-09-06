import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, simpledialog, filedialog
import random
import string
import time
import webbrowser
import platform
import os
import sys
import datetime
import threading
import json
import math
import re
from tkinter import font as tkfont



# ==================== ПРОВЕРКА НАЛИЧИЯ БИБЛИОТЕК ====================
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False
    print("⚠️  Библиотека pygame не установлена!")
    print("   Установите её командой: pip install pygame")
    print("   После установки перезапустите программу.")
    input("Нажмите Enter для выхода...")
    exit()

# Pillow — для пользовательских обоев (необязательна, но желательна)
try:
    import tkinter.filedialog  # noqa: F401 (гарантия инициализации tkinter до ImageTk)
    from PIL import Image, ImageTk
    HAS_PIL = True
except Exception:
    HAS_PIL = False

# requests — для загрузки файлов из интернета (fallback: urllib из стандартной библиотеки)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
import urllib.request
import urllib.parse

# ==================== БЕЗОПАСНЫЙ КАЛЬКУЛЯТОР ====================
class SafeCalculator:

    @staticmethod
    def evaluate(expr):
        expr = expr.strip().lower()
        # Убираем имена разрешённых функций и pi, проверяем остальные символы
        tmp = expr
        for token in ("abs", "round", "min", "max", "sum", "pi"):
            tmp = tmp.replace(token, "")
        allowed = set("0123456789+-*/().%^, e")
        if not all(c in allowed or c.isspace() for c in tmp):
            raise ValueError("Недопустимые символы")
        # Заменяем pi и e только как отдельные "слова", чтобы не ломать числа вида 1e5
        expr = re.sub(r'\bpi\b', repr(math.pi), expr)
        expr = re.sub(r'\be\b', repr(math.e), expr)
        expr = expr.replace('^', '**')
        safe_dict = {'__builtins__': None, 'abs': abs, 'round': round, 'min': min, 'max': max, 'sum': sum}
        try:
            result = eval(expr, safe_dict, {})
            return result
        except:
            raise ValueError("Ошибка вычисления")

# ==================== ПОДПИСКА (с одноразовыми кодами) ====================
class SubscriptionManager:
    def __init__(self, filename="subscription.json"):
        self.filename = filename
        self.data = self.load()
        self.used_codes = self.data.get("used_codes", [])
        self.save()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    return json.load(f)
            except:
                return {"active": False, "key": "", "activated_at": "", "used_codes": []}
        return {"active": False, "key": "", "activated_at": "", "used_codes": []}

    def save(self):
        self.data["used_codes"] = self.used_codes
        try:
            with open(self.filename, "w") as f:
                json.dump(self.data, f, indent=2)
        except:
            pass

    def activate(self, key):
        key = key.strip().upper()
        if key in self.used_codes:
            return False, "Этот код уже был использован"
        if key == "PREMIUM2026":
            self.data["active"] = True
            self.data["key"] = key
            self.data["activated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.used_codes.append(key)
            self.save()
            return True, "Подписка активирована"
        return False, "Неверный ключ"

    def deactivate(self):
        self.data["active"] = False
        # Возвращаем ключ в оборот, чтобы его можно было активировать снова
        key = self.data.get("key")
        if key and key in self.used_codes:
            self.used_codes.remove(key)
        self.data["key"] = ""
        self.save()

    def is_active(self):
        return self.data.get("active", False)

    def get_used_codes(self):
        return self.used_codes

# ==================== КОНФИГУРАЦИЯ (обои, шрифты, анимации, закрепления) ====================
class ConfigManager:
    """Простое JSON-хранилище настроек рабочего стола рядом со скриптом."""

    DEFAULTS = {
        "wallpaper_image": "",
        "font_family": "",       # пусто = брать из темы
        "font_size": 0,          # 0 = брать из темы
        "border_radius": None,   # None = брать из темы
        "tab_anim": "slide",     # none | slide | zoom | fade
        "anim_speed": 30,        # мс на шаг анимации
        "pinned": ["calc", "notepad", "browser", "settings"],
        "muted": False
    }

    def __init__(self, filename="minos_config.json"):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        self.data = dict(self.DEFAULTS)
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                if isinstance(stored, dict):
                    self.data.update({k: v for k, v in stored.items() if k in self.DEFAULTS})
            except Exception:
                pass
        return self.data

    def save(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key, fallback=None):
        value = self.data.get(key, self.DEFAULTS.get(key))
        if value in ("", 0, None) and fallback is not None:
            return fallback
        return value

    def set(self, key, value):
        self.data[key] = value
        self.save()

# ==================== КНОПКА СО СКРУГЛЕНИЕМ (Canvas) ====================
class RoundedButton(tk.Canvas):
    """Плоская кнопка со скруглёнными углами (tk.Button так не умеет).
    Используется для кнопки «Пуск» и системных элементов панели задач."""

    def __init__(self, master, text="", command=None, radius=8,
                 bg="#3a7a3a", fg="white", hover_bg=None, width=110, height=34,
                 font=("Segoe UI", 10, "bold"), **kw):
        self._bg_master = master.cget("bg") if hasattr(master, "cget") else "#000000"
        try:
            self._bg_master = master["bg"]
        except Exception:
            pass
        super().__init__(master, width=width, height=height,
                         bg=self._bg_master, highlightthickness=0, bd=0, **kw)
        self.command = command
        self.radius = max(0, int(radius))
        self.bg = bg
        self.fg = fg
        self.hover_bg = hover_bg or bg
        self.font = font
        self.text = text
        self._hovered = False
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Configure>", lambda e: self.redraw())
        self.redraw()

    def _rounded_points(self, x1, y1, x2, y2, r):
        r = max(0, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
        pts = []
        # Обход по часовой: 4 стороны + 4 дуги по 3 точки
        pts += [x2 - r, y1, x2 - r / 2, y1, x2, y1 + r / 2, x2, y1 + r]          # верх-право
        pts += [x2, y2 - r, x2, y2 - r / 2, x2 - r / 2, y2, x2 - r, y2]          # низ-право
        pts += [x1 + r, y2, x1 + r / 2, y2, x1, y2 - r / 2, x1, y2 - r]          # низ-лево
        pts += [x1, y1 + r, x1, y1 + r / 2, x1 + r / 2, y1, x1 + r, y1]          # верх-лево
        return pts

    def redraw(self):
        self.delete("all")
        w = int(self.winfo_width()) or int(self["width"])
        h = int(self.winfo_height()) or int(self["height"])
        fill = self.hover_bg if self._hovered else self.bg
        if self.radius > 0:
            pts = self._rounded_points(1, 1, w - 2, h - 2, self.radius)
            self.create_polygon(pts, fill=fill, outline=fill, smooth=True)
        else:
            self.create_rectangle(1, 1, w - 2, h - 2, fill=fill, outline=fill)
        self.create_text(w // 2, h // 2, text=self.text,
                         fill=self.fg, font=self.font)

    def _set_hover(self, hovered):
        self._hovered = hovered
        self.redraw()

    def _on_click(self, event=None):
        if self.command:
            try:
                self.command()
            except Exception:
                pass

    def config_button(self, bg=None, fg=None, hover_bg=None, radius=None, font=None, text=None):
        if bg is not None: self.bg = bg
        if fg is not None: self.fg = fg
        if hover_bg is not None: self.hover_bg = hover_bg
        if radius is not None: self.radius = max(0, int(radius))
        if font is not None: self.font = font
        if text is not None: self.text = text
        self.configure(bg=self._bg_master)
        self.redraw()

# ==================== МЕНЕДЖЕР ЗАГРУЗОК ИЗ ИНТЕРНЕТА ====================
class DownloadJob:
    """Одна загрузка: потокобезопасные поля, флаги паузы/отмены."""

    def __init__(self, url, path):
        self.url = url
        self.path = path
        self.name = os.path.basename(path)
        self.status = "ожидание"   # ожидание | загрузка | пауза | готово | ошибка | отменено
        self.downloaded = 0
        self.total = 0
        self.error = ""
        self.cancel_flag = False
        self.pause_flag = False

    @property
    def progress(self):
        if self.total <= 0:
            return 0.0
        return min(100.0, self.downloaded / self.total * 100.0)

    @property
    def is_finished(self):
        return self.status in ("готово", "ошибка", "отменено")


class DownloadManager:
    """Очередь загрузок. Сеть работает в потоках, UI обновляется через after()."""

    def __init__(self, downloads_dir=None):
        self.downloads_dir = downloads_dir or os.path.join(os.path.expanduser("~"), "Downloads")
        try:
            os.makedirs(self.downloads_dir, exist_ok=True)
        except Exception:
            self.downloads_dir = os.getcwd()
        self.jobs = []
        self.lock = threading.Lock()

    def start(self, url, on_update=None):
        url = (url or "").strip()
        if not url:
            return None
        if not url.lower().startswith(("http://", "https://")):
            url = "https://" + url
        name = os.path.basename(urllib.parse.urlparse(url).path) or "download.bin"
        name = urllib.parse.unquote(name)
        path = self._unique_path(os.path.join(self.downloads_dir, name))
        job = DownloadJob(url, path)
        with self.lock:
            self.jobs.append(job)
        thread = threading.Thread(target=self._worker, args=(job, on_update), daemon=True)
        thread.start()
        return job

    def _unique_path(self, path):
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        i = 1
        while os.path.exists(f"{base} ({i}){ext}"):
            i += 1
        return f"{base} ({i}){ext}"

    @staticmethod
    def _format_size(n):
        if n <= 0:
            return "—"
        for unit in ("Б", "КБ", "МБ", "ГБ"):
            if n < 1024:
                return f"{n:.1f} {unit}" if unit != "Б" else f"{int(n)} Б"
            n /= 1024.0
        return f"{n:.1f} ТБ"

    def _worker(self, job, on_update):
        def ui_update():
            if on_update:
                try:
                    on_update()
                except Exception:
                    pass

        job.status = "загрузка"
        try:
            if HAS_REQUESTS:
                # Accept-Encoding: identity — чтобы Content-Length совпадал с телом
                # (иначе gzip-сжатие ломает подсчёт прогресса)
                with requests.get(job.url, stream=True, timeout=15,
                                  headers={"User-Agent": "MinOS/0.3",
                                           "Accept-Encoding": "identity"}) as resp:
                    resp.raise_for_status()
                    if job.cancel_flag:
                        job.status = "отменено"
                    else:
                        cl = resp.headers.get("Content-Length")
                        job.total = int(cl) if cl and cl.isdigit() else 0
                        with open(job.path, "wb") as f:
                            for chunk in resp.iter_content(chunk_size=65536):
                                if job.cancel_flag:
                                    job.status = "отменено"
                                    break
                                while job.pause_flag and not job.cancel_flag:
                                    job.status = "пауза"
                                    ui_update()
                                    time.sleep(0.2)
                                if job.cancel_flag:
                                    job.status = "отменено"
                                    break
                                if job.status == "пауза":
                                    job.status = "загрузка"
                                f.write(chunk)
                                job.downloaded += len(chunk)
                                ui_update()
            else:
                # Fallback без requests
                req = urllib.request.Request(job.url, headers={"User-Agent": "MinOS/0.3"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if job.cancel_flag:
                        job.status = "отменено"
                    else:
                        cl = resp.headers.get("Content-Length")
                        job.total = int(cl) if cl and cl.isdigit() else 0
                        with open(job.path, "wb") as f:
                            while True:
                                if job.cancel_flag:
                                    job.status = "отменено"
                                    break
                                while job.pause_flag and not job.cancel_flag:
                                    job.status = "пауза"
                                    ui_update()
                                    time.sleep(0.2)
                                if job.cancel_flag:
                                    job.status = "отменено"
                                    break
                                if job.status == "пауза":
                                    job.status = "загрузка"
                                chunk = resp.read(65536)
                                if not chunk:
                                    break
                                f.write(chunk)
                                job.downloaded += len(chunk)
                                ui_update()
            if job.status == "загрузка":
                job.status = "готово"
        except Exception as e:
            # Отмена во время соединения/чтения — не ошибка
            if job.cancel_flag or job.status == "отменено":
                job.status = "отменено"
            else:
                job.status = "ошибка"
                job.error = str(e)
        # Удаляем недокачанный файл
        if job.status in ("отменено", "ошибка"):
            try:
                if os.path.exists(job.path) and job.downloaded < max(job.total, 1):
                    os.remove(job.path)
            except Exception:
                pass
        ui_update()

    def pause(self, job):
        if job and not job.is_finished:
            job.pause_flag = True

    def resume(self, job):
        if job and not job.is_finished:
            job.pause_flag = False

    def cancel(self, job):
        if job and not job.is_finished:
            job.cancel_flag = True

    def cancel_all(self):
        for job in self.jobs:
            self.cancel(job)

# ==================== ЗВУКОВЫЕ ДВИЖКИ ====================
def play_windows(freq=800, dur=200):
    try:
        import winsound
        winsound.Beep(freq, dur)
    except:
        pass

def play_linux(freq=800, dur=200):
    try:
        os.system(f'beep -f {freq} -l {dur}')
    except:
        try:
            print('\a', end='', flush=True)
        except:
            pass

def play_macos(freq=800, dur=200):
    try:
        os.system('afplay /System/Library/Sounds/Glass.aiff')
    except:
        pass

SOUND_ENGINES = {
    'windows': play_windows,
    'linux': play_linux,
    'macos': play_macos
}
CURRENT_OS = platform.system().lower()
DEFAULT_ENGINE = 'windows' if CURRENT_OS == 'windows' else 'linux' if CURRENT_OS == 'linux' else 'macos'

# ==================== ТЕМЫ ОФОРМЛЕНИЯ ====================
# Каждая тема задаёт цвета, шрифт интерфейса и скругление кнопок.
THEMES = {
    "moss": {
        "bg": "#2b5a2b",
        "fg": "#c0e0c0",
        "btn_bg": "#3a7a3a",
        "btn_fg": "white",
        "taskbar_bg": "#1f4a1f",
        "title_bg": "#1f4a1f",
        "title_fg": "#a0d6a0",
        "select_bg": "#4a8a4a",
        "font_family": "Segoe UI",
        "font_size": 10,
        "border_radius": 10
    },
    "dark": {
        "bg": "#1a1a2e",
        "fg": "#e0e0e0",
        "btn_bg": "#2d2d44",
        "btn_fg": "#ffffff",
        "taskbar_bg": "#0f0f1a",
        "title_bg": "#0f0f1a",
        "title_fg": "#8888cc",
        "select_bg": "#3d3d66",
        "font_family": "Segoe UI",
        "font_size": 10,
        "border_radius": 12
    },
    "light": {
        "bg": "#f0f0e8",
        "fg": "#222222",
        "btn_bg": "#d4d4cc",
        "btn_fg": "#111111",
        "taskbar_bg": "#c8c8c0",
        "title_bg": "#c8c8c0",
        "title_fg": "#333333",
        "select_bg": "#b0b0a8",
        "font_family": "Verdana",
        "font_size": 9,
        "border_radius": 6
    },
    "cyber": {
        "bg": "#0a0a1a",
        "fg": "#00ffcc",
        "btn_bg": "#1a1a3a",
        "btn_fg": "#00ffcc",
        "taskbar_bg": "#0a0a1a",
        "title_bg": "#0a0a1a",
        "title_fg": "#00ffcc",
        "select_bg": "#004466",
        "font_family": "Consolas",
        "font_size": 10,
        "border_radius": 2
    }
}

# ==================== ЕДИНАЯ КАРТА ВКЛАДОК ====================
# Единственный источник истины для индексов вкладок AppsWindow.
# Порядок должен совпадать с порядком notebook.add(...) в setup_notebook().
TABS = {
    "calc": 0, "notepad": 1, "game": 2, "translator": 3, "generator": 4,
    "clicker": 5, "cards": 6, "casino": 7, "ultrakill": 8, "ai": 9,
    "pet": 10, "console": 11, "all": 12, "games": 13, "internet": 14,
    "downloads": 15, "cipher": 16, "links": 17, "settings": 18, "quests": 19,
    "search": 20, "calendar": 21, "paint": 22, "snake": 23, "alarm": 24,
    "system": 25, "disk": 26, "minesweeper": 27, "taskmanager": 28,
    "browser": 29, "datecalc": 30, "changelog": 31, "subscription": 32,
    "player": 33
}

# ==================== ИКОНКИ РАБОЧЕГО СТОЛА ====================
# Единый список (подпись, ключ, x, y). Используется setup_desktop() и
# refresh_desktop_icons() — раньше он дублировался в обоих методах и при
# добавлении иконки рассинхронизировался.
DESKTOP_ICONS = [
    ("🧮 Калькулятор", "calc", 120, 100), ("📝 Блокнот", "notepad", 290, 100),
    ("🎲 Игра", "game", 460, 100), ("🌐 Перевод", "translator", 630, 100),
    ("🔢 Генератор", "generator", 800, 100), ("🍄 Кликер", "clicker", 120, 200),
    ("🃏 Карточки", "cards", 290, 200), ("🎰 Казино", "casino", 460, 200),
    ("🩸 ULTRAKILL", "ultrakill", 630, 200), ("🤖 ИИ", "ai", 800, 200),
    ("🌱 Питомец", "pet", 120, 300), ("💻 Консоль", "console", 290, 300),
    ("📂 Все", "all", 460, 300), ("📁 Игры", "games", 630, 300),
    ("🌐 Интернет", "internet", 800, 300), ("⬇️ Загрузки", "downloads", 120, 400),
    ("🔐 Шифратор", "cipher", 290, 400), ("🔗 Ссылки", "links", 460, 400),
    ("⚙️ Настройки", "settings", 630, 400), ("📜 Задания", "quests", 800, 400),
    ("🔍 Поиск", "search", 120, 500), ("📜 О MinOS", "about", 290, 500),
    ("🔒 Блокировка", "lock", 460, 500),
    ("📅 Календарь", "calendar", 120, 600), ("🎨 Рисование", "paint", 290, 600),
    ("⏰ Будильник", "alarm", 460, 600), ("ℹ️ Система", "system", 630, 600),
    ("💾 Диск", "disk", 800, 600),
    ("💣 Сапёр", "minesweeper", 120, 700), ("📊 Диспетчер", "taskmanager", 290, 700),
    ("🌐 Браузер", "browser", 460, 700),
    ("📆 Калькулятор дат", "datecalc", 630, 700),
    ("🎵 Плеер", "player", 800, 700)
]

# ==================== ЭКРАНЫ ====================
class BootScreen(tk.Toplevel):
    def __init__(self, master, on_complete):
        super().__init__(master)
        self.on_complete = on_complete
        self.overrideredirect(True)
        self.geometry("400x300")
        self.configure(bg='#2b5a2b')
        self.update_idletasks()
        w, h = 400, 300
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        tk.Label(self, text="🌿 MinOS", font=("Segoe UI", 40, "bold"),
                 fg="#a0d6a0", bg="#2b5a2b").pack(pady=30)
        tk.Label(self, text="Загрузка...", font=("Segoe UI", 12),
                 fg="#c0e0c0", bg="#2b5a2b").pack(pady=10)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("green.Horizontal.TProgressbar",
                        background='#3a7a3a', troughcolor='#1f4a1f')
        self.progress = ttk.Progressbar(self, length=250, mode='determinate',
                                        maximum=100, style="green.Horizontal.TProgressbar")
        self.progress.pack(pady=20)
        self.after(100, self.update_progress, 0)
    def update_progress(self, value):
        if value <= 100:
            self.progress['value'] = value
            self.after(50, self.update_progress, value + 2)
        else:
            self.destroy()
            self.on_complete()

class LoginScreen(tk.Toplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.master_app = master
        self.on_success = on_success
        self.overrideredirect(True)
        self.geometry("400x300")
        self.configure(bg='#2b5a2b')
        self.update_idletasks()
        w, h = 400, 300
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        tk.Label(self, text="🔐 Вход в MinOS", font=("Segoe UI", 20, "bold"),
                 fg="#a0d6a0", bg="#2b5a2b").pack(pady=20)
        self.pass_entry = tk.Entry(self, show="•", font=("Segoe UI", 14),
                                   bg="#3a7a3a", fg="white", insertbackground="white",
                                   relief="flat", bd=0)
        self.pass_entry.pack(pady=10, ipadx=10, ipady=5)
        self.pass_entry.bind("<Return>", self.check_password)
        self.pass_entry.focus()
        self.error_label = tk.Label(self, text="", fg="red", bg="#2b5a2b", font=("Segoe UI", 10))
        self.error_label.pack(pady=5)
        btn_style = {"bg": "#3a7a3a", "fg": "white", "activebackground": "#4a8a4a",
                     "relief": "flat", "bd": 0, "padx": 20, "pady": 8, "font": ("Segoe UI", 12)}
        tk.Button(self, text="Войти", command=self.check_password, **btn_style).pack(pady=5)
    def check_password(self, event=None):
        entered = self.pass_entry.get()
        if self.master_app.password == "" or entered == self.master_app.password:
            self.master_app.play_success()
            self.destroy()
            self.on_success()
        else:
            self.master_app.play_error()
            self.error_label.config(text="Неверный пароль")
            self.pass_entry.delete(0, tk.END)
            self.pass_entry.focus()

class LockScreen(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_app = master
        self.overrideredirect(True)
        self.geometry("900x650")
        self.configure(bg='#2b5a2b')
        self.update_idletasks()
        w, h = 900, 650
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        tk.Label(self, text="🌿🌱🍃", font=("Segoe UI", 24), bg='#2b5a2b', fg='#5a8a5a').place(x=20, y=20)
        tk.Label(self, text="🍃🌱🌿", font=("Segoe UI", 24), bg='#2b5a2b', fg='#5a8a5a').place(x=800, y=580)
        self.time_label = tk.Label(self, font=("Segoe UI", 60, "bold"),
                                   fg="#a0d6a0", bg="#2b5a2b")
        self.time_label.pack(pady=(80, 10))
        self.date_label = tk.Label(self, font=("Segoe UI", 20),
                                   fg="#c0e0c0", bg="#2b5a2b")
        self.date_label.pack(pady=10)
        self.pass_entry = tk.Entry(self, show="•", font=("Segoe UI", 16),
                                   bg="#3a7a3a", fg="white", insertbackground="white",
                                   relief="flat", bd=0, width=20)
        self.pass_entry.pack(pady=20)
        self.pass_entry.bind("<Return>", self.unlock)
        self.pass_entry.focus()
        self.error_label = tk.Label(self, text="", fg="red", bg="#2b5a2b", font=("Segoe UI", 10))
        self.error_label.pack()
        self.update_clock()
        self.bind("<Button-1>", lambda e: self.pass_entry.focus())
    def update_clock(self):
        if not self.winfo_exists():
            return
        self.time_label.config(text=time.strftime("%H:%M:%S"))
        self.date_label.config(text=time.strftime("%A, %d %B %Y"))
        self.after(1000, self.update_clock)
    def unlock(self, event=None):
        if not self.master_app.password:
            self.destroy()
            return
        entered = self.pass_entry.get()
        if entered == self.master_app.password:
            self.master_app.play_success()
            self.destroy()
        else:
            self.master_app.play_error()
            self.error_label.config(text="Неверный пароль")
            self.pass_entry.delete(0, tk.END)
            self.pass_entry.focus()

class ShutdownScreen(tk.Toplevel):
    def __init__(self, master, on_complete):
        super().__init__(master)
        self.on_complete = on_complete
        self.overrideredirect(True)
        self.geometry("400x200")
        self.configure(bg='#2b5a2b')
        self.update_idletasks()
        w, h = 400, 200
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        tk.Label(self, text="Выключение...", font=("Segoe UI", 20, "bold"),
                 fg="#a0d6a0", bg="#2b5a2b").pack(expand=True)
        self.after(2000, self.finish)
    def finish(self):
        self.destroy()
        self.on_complete()

class AdWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Подписка MinOS")
        self.geometry("400x250")
        self.configure(bg='#2b5a2b')
        self.resizable(False, False)
        self.update_idletasks()
        w, h = 400, 250
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        tk.Label(self, text="🌿 MinOS", font=("Segoe UI", 20, "bold"),
                 fg="#a0d6a0", bg="#2b5a2b").pack(pady=10)
        tk.Label(self, text="Пожалуйста, поддержите разработку!\nПодписка открывает все возможности.",
                 font=("Segoe UI", 10), fg="#c0e0c0", bg="#2b5a2b",
                 justify='center').pack(pady=5)
        links_frame = tk.Frame(self, bg='#2b5a2b')
        links_frame.pack(pady=5)
        tk.Label(links_frame, text="Наши каналы:", font=("Segoe UI", 10, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack()
        tk.Button(links_frame, text="t.me/shie_za", fg="LightBlue", cursor="hand2",
                  bg='#2b5a2b', bd=0, command=lambda: webbrowser.open("https://t.me/shie_za")).pack()
        tk.Button(links_frame, text="t.me/hell_1tself", fg="LightBlue", cursor="hand2",
                  bg='#2b5a2b', bd=0, command=lambda: webbrowser.open("https://t.me/hell_1tself")).pack()
        btn_frame = tk.Frame(self, bg='#2b5a2b')
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Купить", font=("Segoe UI", 10),
                  bg='#3a7a3a', fg='White', command=lambda: messagebox.showinfo("Подписка", "Спасибо за поддержку! (функция ещё не реализована)")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Позже", font=("Segoe UI", 10),
                  bg='#3a7a3a', fg='White', command=self.destroy).pack(side=tk.LEFT, padx=5)

# ==================== СИСТЕМА УВЕДОМЛЕНИЙ ====================
class NotificationManager:
    def __init__(self, master, app=None):
        self.master = master
        self.app = app
        self.notifications = []
        self.spacing = 10

    def show_notification(self, title, message, duration=3000):
        if not self.master.winfo_exists():
            return
        theme = THEMES.get(self.app.current_theme, THEMES["moss"]) if self.app else THEMES["moss"]
        win = tk.Toplevel(self.master)
        win.overrideredirect(True)
        win.configure(bg=theme["taskbar_bg"], relief='ridge', bd=2)
        tk.Label(win, text=title, font=("Segoe UI", 10, "bold"),
                 bg=theme["taskbar_bg"], fg=theme["title_fg"]).pack(anchor='w', padx=10, pady=(5,0))
        tk.Label(win, text=message, font=("Segoe UI", 9),
                 bg=theme["taskbar_bg"], fg=theme["fg"], wraplength=250, justify='left').pack(anchor='w', padx=10, pady=(0,5))
        btn = tk.Button(win, text="✕", command=win.destroy,
                        bg=theme["btn_bg"], fg=theme["btn_fg"], relief='flat', bd=0, width=2)
        btn.place(x=280, y=5)
        win.update_idletasks()
        w_width = win.winfo_width()
        w_height = win.winfo_height()
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        offset = len(self.notifications) * (w_height + self.spacing)
        x = screen_width - w_width - 20
        y = screen_height - w_height - 60 - offset
        if y < 20:
            y = screen_height - w_height - 60
            self.notifications = [n for n in self.notifications if n.winfo_exists()]
        win.geometry(f"+{x}+{y}")
        win.after(duration, win.destroy)
        self.notifications.append(win)

# ==================== ГЛАВНОЕ ПРИЛОЖЕНИЕ ====================
class MinOSApp:
    VERSION = "v0.2.9"
    CHANGELOG = """
v0.2.9 (2026-09-01) — исправления и надёжность
- Загрузки: выделение строки больше не сбрасывается авто-обновлением списка (из-за этого не работали «Пауза/Отмена»); UI обновляется только когда вкладка видима.
- Вкладки: быстрое переключение во время анимации больше не «возвращает» на предыдущую вкладку.
- Часы на панели задач: запускаются одним циклом (было два параллельных).
- Смена темы: корректно перекрашиваются трей, закреплённые и запущенные приложения на панели задач.
- Иконки: возвращён звук клика; «подпрыгивание» не падает при закрытом окне; шрифт иконок учитывает настройки.
- Меню Пуск: защита от дублирования при рассинхронизации состояния.
- Настройки шрифта: мусор в поле размера не ломает применение (откат к теме).
- Закрепления: повреждённый конфиг не приводит к падению.
- Очистка кода: убраны неиспользуемые импорты и переменные (pyflakes).
- Список иконок рабочего стола вынесен в единую константу DESKTOP_ICONS (устранено дублирование).

v0.2.8 (2026-09-01) — Windows 10 Edition
- Рабочий стол в стиле Windows 10: панель задач с кнопкой «Пуск», трей (звук, статус подписки, часы и дата), закрепление приложений (правый клик по иконке в панели), контекстное меню рабочего стола.
- Меню «Пуск»: поиск по приложениям, сетка иконок, кнопки питания и настроек; закрывается кликом вне меню.
- Иконки рабочего стола: hover-подсветка с плавным увеличением, «подпрыгивание» при клике, перетаскивание мышью, пункт «Обновить» сохраняет позиции.
- Загрузки из интернета: URL + прогресс в реальном времени (requests, fallback urllib), пауза/продолжение/отмена, список активных и завершённых загрузок. Файлы сохраняются в папку «Загрузки» пользователя.
- Пользовательские обои: выбор PNG/JPG/BMP/GIF, масштабирование на весь экран через Pillow, обои хранятся в конфиге и переживают смену темы и перезапуск.
- Темы с шрифтами: каждая тема задаёт шрифт, базовый размер и скругление; в настройках можно выбрать шрифт и размер вручную (применяется ко всем виджетам).
- Скругления кнопок: RoundedButton на Canvas для «Пуска»; настройка радиуса 0–24.
- Анимации переключения вкладок: сдвиг (slide), масштаб (zoom), появление (fade); настройка режима и скорости.
- Окна приложений: кнопка «развернуть» как в Windows.
- Трей: 🔊/🔇 — выключение звука, 💎/❌ — статус подписки (клик — открыть подписку).
- Все прежние функции сохранены: калькулятор, блокнот, игры, диск, медиаплеер, подписка, задания, темы.

v0.2.7 (2026-09-01)
- Блокнот: полоса прокрутки теперь видна (исправлен порядок упаковки виджетов).
- Калькулятор: добавлены кнопки скобок и степени «^».
- Коллекция карточек: все кнопки показывали название последней карточки (замыкание в цикле).
- Диспетчер кликера: исправлено исключение TclError от notebook.index('current').
- Браузер: «Назад/Вперёд» больше не дублируют записи в истории.
- Диск: нет двойного слеша в путях при создании в корне; индикатор занятого места заполняется сразу.
- Система: os.getlogin() защищён от OSError; время работы теперь считается и на Windows (через psutil).
- Ежедневный бонус и бонусы змейки: таймеры корректно отменяются/игнорируются после закрытия окна.
- Сброс данных: сбрасывается стадия питомца.
- Вкладка «Все»: вместо текстового списка — кнопки быстрого перехода к приложениям.

v0.2.6 (2026-08-30)
- Исправлены неверные индексы вкладок: иконки рабочего стола, ИИ, консоль, поиск и игры теперь открывают правильные приложения (добавлена единая карта вкладок TABS).
- Исправлено падение окна приложений при смене темы (ttk.Frame не поддерживает bg).
- Исправлены кнопки «Назад/Вперёд/Обновить» в браузере (AttributeError).
- Исправлен выбор файлов на Диске при активном поиске/сортировке.
- Будильник больше не вызывает tkinter из фонового потока; проверка времени каждые 5 секунд.
- Змейка: рестарт больше не запускает второй игровой цикл; корректная отвязка клавиш при закрытии.
- Калькулятор: работают функции abs/round/min/max/sum, pi и e; запись после ошибки начинается заново.
- Периодические задачи (диспетчер, задания, кулдаун карточек) корректно останавливаются после закрытия окна.
- Тестовый ключ подписки после деактивации снова можно использовать.
- Уведомления оформляются в цветах текущей темы; обои больше не перебивают цвет панели задач.
- Список заданий перерисовывается только при изменениях (оптимизация).

v0.2.5 (2026-08-30)
- Карточки теперь имеют названия, связанные с мхом (например, «Золотой мох», «Мшистый камень» и т.д.).
- Обновлён вывод карточек: единый стиль с эмодзи 💎 и 💫.
- Убран лишний текст (ТП, владельцы) из сообщений о карточках.

v0.2.4 (2026-08-30)
- Добавлены сменные темы оформления (Moss, Dark, Light, Cyber).
- Косметика: аналоговые часы с датой на рабочем столе.
- Расширенный диск: поиск, сортировка, предпросмотр.
- Медиаплеер с управлением (pygame).
- Одноразовые коды для подписки.
- Вход без пароля сразу открывает рабочий стол.

v0.2.3 (2026-08-29)
- Полноэкранный рабочий стол, увеличенные иконки, панель задач 60px.

v0.2.2 (2026-08-28)
- Безопасность калькулятора, исправлен будильник, диск, консоль.

v0.2.1 (2026-08-28)
- Исправлена нумерация версии и восстановлен полный список изменений.

v0.2.0 (2026-08-28)
- Система платной подписки (премиум-функции).

v0.1.7 (2026-08-28)
- Окно входа всегда показывается, любой пароль принимается, если не установлен.

v0.1.6 (2026-08-28)
- Исправлена визуальная проблема с чёрным фоном после blackout.

v0.1.5 (2026-08-28)
- Исправлены ошибки 'NoneType' и 'bonus_foods'.

v0.1.4 (2026-08-28)
- Исправлена ошибка 'taskbar'.

v0.1.3 (2026-08-28)
- Исправлена ошибка change_theme, браузер, сапёр, закрытие коллекции.

v0.1.2 (2026-08-27)
- Исправлена змейка и навигация по вкладкам.

v0.1.1 (2026-08-25)
- Питомец переработан в мох, добавлен ченджлог.

v0.1.0 (2026-08-26)
- Улучшен диск, цветовая схема, калькулятор дат, график ЦП, сапёр в игры.

v0.0.9 (2026-08-25)
- Блокнот, сапёр, диспетчер, браузер, уведомления.

v0.0.8 (2026-08-25)
- Кликер, змейка с бонусами, коллекция карточек, казино, задания, обои.

v0.0.7 (2026-08-24)
- Файловый менеджер "Диск".

v0.0.6 (2026-08-23)
- Системная информация, авторские права.

v0.0.5 (2026-08-23)
- Календарь, рисование, змейка, будильник.

v0.0.4 (2026-08-22)
- ChangeLog.

v0.0.3 (2026-08-22)
- Учётная запись, звуки.

v0.0.2 (2026-08-21)
- Карточки, казино, питомец, консоль, интернет, загрузки.

v0.0.1d (2026-08-20)
- Базовый функционал.
"""

    def __init__(self, root):
        self.root = root
        self.root.title("MinOS")
        self.root.attributes('-fullscreen', True)
        self.root.overrideredirect(True)
        self.root.bind("<Escape>", lambda e: self.toggle_fullscreen())
        self.fullscreen = True
        self.root.configure(bg='#2b5a2b')
        self.root.resizable(False, False)
        self.apps_window = None
        self.task_buttons = {}
        self.password = ""
        self.sound_engine = DEFAULT_ENGINE
        self.wallpaper = "moss"
        self.current_theme = "moss"
        self.config = ConfigManager()
        self.muted = bool(self.config.get("muted", False))
        self.start_menu = None
        self.start_menu_open = False
        self._icon_hover_after = {}
        self.wallpaper_photo = None      # удерживаем ссылку, иначе картинка исчезнет
        self.wallpaper_label = None
        self.download_manager = DownloadManager()
        self.notification_manager = NotificationManager(self.root, self)
        self.subscription = SubscriptionManager()
        if self.subscription.is_active():
            self.show_ad_flag = False
        else:
            self.show_ad_flag = True

        self.setup_desktop()
        self.setup_taskbar()
        self.apply_wallpaper()
        self.restore_wallpaper_image()
        self.apply_theme_to_app(self.current_theme)
        self.update_clock()
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        # Контекстное меню рабочего стола (правая кнопка мыши)
        self.root.bind("<Button-3>", self.show_desktop_menu)
        if self.show_ad_flag and random.random() < 0.15:
            self.root.after(2000, self.show_ad)

    def play_sound(self, freq=800, dur=200):
        if self.muted:
            return
        engine = SOUND_ENGINES.get(self.sound_engine)
        if engine:
            engine(freq, dur)
    def play_error(self): self.play_sound(400, 300)
    def play_success(self): self.play_sound(1200, 150)
    def play_click(self): self.play_sound(600, 80)

    def notify(self, title, message, duration=3000):
        self.notification_manager.show_notification(title, message, duration)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        if not self.fullscreen:
            self.root.overrideredirect(False)
            self.root.geometry("900x650")
            self.root.title("MinOS (оконный режим)")
        else:
            self.root.overrideredirect(True)
            self.root.title("")

    def _ui_font(self, size=None, bold=False):
        """Шрифт интерфейса с учётом темы и пользовательских настроек."""
        theme = THEMES.get(self.current_theme, THEMES["moss"])
        family = self.config.get("font_family", "") or theme.get("font_family", "Segoe UI")
        base = self.config.get("font_size", 0) or theme.get("font_size", 10)
        if size is None:
            size = base
        styles = ("bold",) if bold else ()
        return (family, size) + styles

    def _get_border_radius(self):
        theme = THEMES.get(self.current_theme, THEMES["moss"])
        radius = self.config.get("border_radius", None)
        if radius is None:
            radius = theme.get("border_radius", 8)
        return int(radius)

    def _apply_font_family_recursive(self, widget, family, size=None):
        """Рекурсивно заменяет гарнитуру шрифта у всех потомков, сохраняя размеры/стили."""
        try:
            font = widget.cget("font")
        except Exception:
            font = None
        if font:
            new_font = self._rebase_font(font, family, size)
            if new_font is not None:
                try:
                    widget.configure(font=new_font)
                except Exception:
                    pass
        for child in widget.winfo_children():
            self._apply_font_family_recursive(child, family, size)

    @staticmethod
    def _rebase_font(font, family, size=None):
        """Возвращает шрифт с заменённой гарнитурой (или None, если менять нечего)."""
        try:
            if isinstance(font, tuple):
                parts = list(font)
                if not parts or parts[0] == family:
                    if size is None or len(parts) < 2 or parts[1] == size:
                        return None
                parts[0] = family
                if size is not None and len(parts) >= 2 and isinstance(parts[1], int):
                    parts[1] = size
                return tuple(parts)
            if isinstance(font, str) and font and not font.startswith("Tk"):
                tokens = font.split()
                # Ищем размер (число) — всё до него может быть многословной гарнитурой
                size_idx = None
                for i, tok in enumerate(tokens):
                    if tok.isdigit():
                        size_idx = i
                        break
                if size_idx is None:
                    return (family,) if family != font else None
                styles = tuple(t for t in tokens[size_idx + 1:] if t in ("bold", "italic", "underline", "overstrike"))
                new_size = size if size is not None else int(tokens[size_idx])
                return (family, new_size) + styles
        except Exception:
            return None
        return None

    def apply_theme_to_app(self, theme_name):
        theme = THEMES.get(theme_name, THEMES["moss"])
        self.current_theme = theme_name
        self.root.configure(bg=theme["bg"])
        # Размер шрифта интерфейса меняется только через настройки
        # (apply_font_settings); здесь обновляются цвета и гарнитура темы
        family = self.config.get("font_family", "") or theme.get("font_family", "Segoe UI")
        if hasattr(self, 'taskbar'):
            self.taskbar.configure(bg=theme["taskbar_bg"])
            for child in self.taskbar.winfo_children():
                if isinstance(child, RoundedButton):
                    child.config_button(bg=theme["btn_bg"], fg=theme["btn_fg"],
                                        hover_bg=theme["select_bg"],
                                        radius=self._get_border_radius())
                elif isinstance(child, tk.Frame):
                    # Зоны панели задач (закрепления, трей): красим сам фрейм
                    # и все метки внутри него
                    child.configure(bg=theme["taskbar_bg"])
                    for sub in child.winfo_children():
                        if isinstance(sub, tk.Label):
                            sub.configure(bg=theme["taskbar_bg"], fg=theme["title_fg"])
                elif isinstance(child, (tk.Button, tk.Label)):
                    child.configure(bg=theme["taskbar_bg"], fg=theme["title_fg"])
            # Кнопки запущенных приложений на панели задач
            for btn in getattr(self, 'task_buttons', {}).values():
                try:
                    btn.configure(bg=theme["btn_bg"], fg=theme["btn_fg"],
                                  activebackground=theme["select_bg"])
                except Exception:
                    pass
        if hasattr(self, 'clock_label'):
            self.clock_label.configure(bg=theme["taskbar_bg"], fg=theme["title_fg"])
        if hasattr(self, 'date_label'):
            self.date_label.configure(bg=theme["taskbar_bg"], fg=theme["title_fg"])
        if hasattr(self, 'sound_btn'):
            self.sound_btn.configure(bg=theme["taskbar_bg"], fg=theme["title_fg"])
        if hasattr(self, 'sub_btn'):
            self.sub_btn.configure(bg=theme["taskbar_bg"], fg=theme["title_fg"])
        if hasattr(self, 'desktop_clock'):
            self.desktop_clock.configure(bg=theme["bg"], fg=theme["title_fg"])
            self.desktop_date.configure(bg=theme["bg"], fg=theme["title_fg"])
        for child in self.root.winfo_children():
            if isinstance(child, RoundedButton) and child != self.start_btn:
                child.config_button(bg=theme["btn_bg"], fg=theme["btn_fg"],
                                    hover_bg=theme["select_bg"],
                                    radius=self._get_border_radius())
            elif isinstance(child, tk.Button) and child != self.start_btn:
                child.configure(bg=theme["btn_bg"], fg=theme["fg"],
                                activebackground=theme["select_bg"])
        # Шрифты на рабочем столе
        for child in self.root.winfo_children():
            if isinstance(child, (tk.Button, tk.Label)):
                new_font = self._rebase_font(child.cget("font"), family, None)
                if new_font:
                    try:
                        child.configure(font=new_font)
                    except Exception:
                        pass
        if self.apps_window and self.apps_window.winfo_exists():
            self.apps_window.apply_theme_to_window(theme_name)
            self.apps_window.apply_font_to_window(family, None)

    def apply_wallpaper(self):
        themes_wall = {"moss":"#2b5a2b","grass":"#3a7a3a","forest":"#1f4a1f","dark":"#0f2a0f"}
        color = themes_wall.get(self.wallpaper, "#2b5a2b")
        # Меняем только фон рабочего стола; панель задач остаётся в цвете темы
        self.root.configure(bg=color)

    # ---------- ПОЛЬЗОВАТЕЛЬСКИЕ ОБОИ (PIL) ----------
    def choose_wallpaper(self):
        """Диалог выбора изображения и установка его фоном рабочего стола."""
        if not HAS_PIL:
            messagebox.showerror("Обои", "Для пользовательских обоев установите Pillow:\npip install Pillow")
            return
        filepath = filedialog.askopenfilename(
            title="Выберите обои",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"),
                       ("Все файлы", "*.*")])
        if not filepath:
            return
        try:
            self.apply_wallpaper_image(filepath)
            self.config.set("wallpaper_image", filepath)
            self.notify("Обои", f"Установлены обои: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Обои", f"Не удалось установить обои: {e}")

    def apply_wallpaper_image(self, filepath):
        """Масштабирует изображение на весь экран и кладёт его на задний план."""
        if not HAS_PIL:
            return
        img = Image.open(filepath)
        try:
            img = img.convert("RGB")
        except Exception:
            pass
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        img = img.resize((screen_w, screen_h), Image.LANCZOS)
        self.wallpaper_photo = ImageTk.PhotoImage(img)
        if self.wallpaper_label is None or not self.wallpaper_label.winfo_exists():
            self.wallpaper_label = tk.Label(self.root, image=self.wallpaper_photo, bd=0)
        else:
            self.wallpaper_label.configure(image=self.wallpaper_photo)
        # Обои строго под иконками и панелью задач
        self.wallpaper_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.wallpaper_label.lower()

    def clear_wallpaper(self):
        """Убирает пользовательские обои, возвращает цветовой фон."""
        self.config.set("wallpaper_image", "")
        self.wallpaper_photo = None
        if self.wallpaper_label is not None and self.wallpaper_label.winfo_exists():
            self.wallpaper_label.destroy()
        self.wallpaper_label = None
        self.apply_wallpaper()
        self.notify("Обои", "Пользовательские обои убраны")

    def restore_wallpaper_image(self):
        """Восстанавливает обои из конфига при запуске."""
        path = self.config.get("wallpaper_image", "")
        if path and HAS_PIL and os.path.exists(path):
            try:
                self.apply_wallpaper_image(path)
            except Exception:
                pass

    def setup_desktop(self):
        self.desktop_clock = tk.Label(self.root, font=("Segoe UI", 32, "bold"),
                                      fg="#a0d6a0", bg="#2b5a2b")
        self.desktop_clock.place(x=self.root.winfo_screenwidth()-250, y=20)
        self.desktop_date = tk.Label(self.root, font=("Segoe UI", 14),
                                     fg="#a0d6a0", bg="#2b5a2b")
        self.desktop_date.place(x=self.root.winfo_screenwidth()-250, y=70)
        self.update_desktop_clock()

        tk.Label(self.root, text="🌿", font=("Segoe UI", 36), bg='#2b5a2b', fg='#4a7a4a').place(x=20, y=600)
        tk.Label(self.root, text="🍃", font=("Segoe UI", 36), bg='#2b5a2b', fg='#4a7a4a').place(x=self.root.winfo_screenwidth()-60, y=20)
        tk.Label(self.root, text="🌱", font=("Segoe UI", 36), bg='#2b5a2b', fg='#4a7a4a').place(x=self.root.winfo_screenwidth()-60, y=self.root.winfo_screenheight()-80)

        self.label_minos = tk.Label(self.root, text="🌿 MinOS", font=("Segoe UI", 32, "bold"),
                                    fg="#a0d6a0", bg="#2b5a2b")
        self.label_minos.place(x=30, y=30)
        self.label_version = tk.Label(self.root, text=self.VERSION, font=("Segoe UI", 12),
                                      fg="#7aaa7a", bg="#2b5a2b")
        self.label_version.place(x=30, y=self.root.winfo_screenheight()-80)
        self.label_copyright = tk.Label(self.root, text="© 2026 MinOS | Made in China 🌿",
                                        font=("Segoe UI", 10), fg="#6a8a6a", bg="#2b5a2b")
        self.label_copyright.place(x=self.root.winfo_screenwidth()-300, y=self.root.winfo_screenheight()-80)

        self.desktop_icons = {}
        for text, key, x, y in DESKTOP_ICONS:
            btn = self.create_desktop_icon(text, key, x, y)
            btn._text_key = key
            self.desktop_icons[key] = btn

    def update_desktop_clock(self):
        now = datetime.datetime.now()
        self.desktop_clock.config(text=now.strftime("%H:%M:%S"))
        self.desktop_date.config(text=now.strftime("%d %B %Y"))
        self.root.after(1000, self.update_desktop_clock)

    def create_desktop_icon(self, text, tab_key, x, y):
        theme = THEMES.get(self.current_theme, THEMES["moss"])
        if tab_key == "about":
            command = self.show_about
        elif tab_key == "lock":
            command = self.lock_screen
        else:
            command = lambda k=tab_key: self.open_apps_window(k)
        font = self._ui_font(12, bold=True)
        btn = tk.Button(self.root, text=text, font=font,
                        bg=theme["btn_bg"], fg=theme["fg"],
                        activebackground=theme["select_bg"], activeforeground="White",
                        relief="flat", bd=2, padx=15, pady=10)
        btn.place(x=x, y=y, width=150, height=70)
        # --- Анимации: hover-подсветка, плавное «увеличение», прыжок при клике, drag&drop ---
        btn._base_pos = (x, y)
        btn._base_font = font[1]   # фактический размер (учитывает настройки шрифта)
        btn._cur_font = font[1]
        btn._command = command
        btn._dragging = False
        btn.bind("<Enter>", lambda e, b=btn: self.icon_hover_enter(b))
        btn.bind("<Leave>", lambda e, b=btn: self.icon_hover_leave(b))
        btn.bind("<Button-1>", lambda e, b=btn: self.icon_press(b, e))
        btn.bind("<B1-Motion>", lambda e, b=btn: self.icon_drag(b, e))
        btn.bind("<ButtonRelease-1>", lambda e, b=btn: self.icon_release(b, e))
        return btn

    # ---------- АНИМАЦИИ ИКОНОК ----------
    def icon_hover_enter(self, btn):
        """Подсветка + плавное увеличение шрифта (эффект приближения)."""
        theme = THEMES.get(self.current_theme, THEMES["moss"])
        btn.configure(bg=theme["select_bg"], fg="White")
        self._animate_icon_font(btn, btn._base_font, btn._base_font + 1)

    def icon_hover_leave(self, btn):
        theme = THEMES.get(self.current_theme, THEMES["moss"])
        btn.configure(bg=theme["btn_bg"], fg=theme["fg"])
        cur = getattr(btn, "_cur_font", btn._base_font)
        self._animate_icon_font(btn, cur, btn._base_font)

    def _animate_icon_font(self, btn, from_size, to_size, step=0):
        """Плавное изменение размера шрифта иконки через after()."""
        key = id(btn)
        old = self._icon_hover_after.pop(key, None)
        if old is not None:
            try:
                self.root.after_cancel(old)
            except Exception:
                pass
        if from_size == to_size:
            self._set_icon_font(btn, to_size)
            return
        # 2 промежуточных шага для плавности
        mid = from_size + (1 if to_size > from_size else -1)
        if step == 0 and mid != to_size:
            self._set_icon_font(btn, mid)
            self._icon_hover_after[key] = self.root.after(
                40, lambda: self._animate_icon_font(btn, mid, to_size, step=1))
        else:
            self._set_icon_font(btn, to_size)

    def _set_icon_font(self, btn, size):
        try:
            family = self.config.get("font_family", "") or THEMES.get(self.current_theme, {}).get("font_family", "Segoe UI")
            btn._cur_font = size
            btn.configure(font=(family, size, "bold"))
        except Exception:
            pass

    def icon_press(self, btn, event):
        btn._press_x = event.x
        btn._press_y = event.y
        btn._dragging = False

    def icon_drag(self, btn, event):
        """Перетаскивание иконки по рабочему столу."""
        dx = event.x - getattr(btn, "_press_x", 0)
        dy = event.y - getattr(btn, "_press_y", 0)
        if abs(dx) + abs(dy) > 6:
            btn._dragging = True
        if btn._dragging:
            x = btn.winfo_x() + dx
            y = btn.winfo_y() + dy
            # Не даём утопить иконку в панели задач
            max_y = self.root.winfo_screenheight() - 60 - btn.winfo_height()
            y = max(0, min(y, max_y))
            x = max(0, min(x, self.root.winfo_screenwidth() - btn.winfo_width()))
            btn.place(x=x, y=y)
            btn._press_x = event.x
            btn._press_y = event.y

    def icon_release(self, btn, event):
        if btn._dragging:
            btn._dragging = False
            return
        # Клик без перетаскивания: звук, «подпрыгивание» и открытие приложения
        self.play_click()
        self.icon_jump(btn)
        if btn._command:
            try:
                btn._command()
            except Exception:
                pass

    def icon_jump(self, btn):
        """Лёгкий эффект подпрыгивания при клике."""
        if not btn.winfo_exists():
            return
        cur_y = btn.winfo_y()
        btn.place(x=btn.winfo_x(), y=cur_y + 4)
        def restore():
            # Окно могло закрыться за 90 мс — иначе TclError в callback
            if btn.winfo_exists():
                btn.place(x=btn.winfo_x(), y=cur_y)
        self.root.after(90, restore)

    def setup_taskbar(self):
        """Панель задач в стиле Windows 10: Пуск, закреплённые/запущенные приложения, трей."""
        theme = THEMES.get(self.current_theme, THEMES["moss"])
        self.taskbar = tk.Frame(self.root, bg=theme["taskbar_bg"], height=52)
        self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.taskbar.pack_propagate(False)

        # --- Кнопка «Пуск» (скруглённая) ---
        self.start_btn = RoundedButton(self.taskbar, text="⊞ Пуск", width=92, height=36,
                                       radius=self._get_border_radius(),
                                       bg=theme["btn_bg"], fg=theme["btn_fg"],
                                       hover_bg=theme["select_bg"],
                                       font=self._ui_font(11, bold=True),
                                       command=self.toggle_start_menu)
        self.start_btn.pack(side=tk.LEFT, padx=8, pady=8)

        # --- Зона закреплённых и запущенных приложений ---
        self.task_buttons_frame = tk.Frame(self.taskbar, bg=theme["taskbar_bg"])
        self.task_buttons_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.pinned_buttons = {}
        self.rebuild_pinned_buttons()

        # --- Трей ---
        self.tray_frame = tk.Frame(self.taskbar, bg=theme["taskbar_bg"])
        self.tray_frame.pack(side=tk.RIGHT, padx=6, pady=6)

        self.sound_btn = tk.Label(self.tray_frame, text="🔊" if not self.muted else "🔇",
                                  font=("Segoe UI", 13), bg=theme["taskbar_bg"],
                                  fg=theme["title_fg"], cursor="hand2")
        self.sound_btn.pack(side=tk.RIGHT, padx=4)
        self.sound_btn.bind("<Button-1>", lambda e: self.toggle_mute())

        self.sub_btn = tk.Label(self.tray_frame,
                                text="💎" if self.subscription.is_active() else "❌",
                                font=("Segoe UI", 13), bg=theme["taskbar_bg"],
                                fg=theme["title_fg"], cursor="hand2")
        self.sub_btn.pack(side=tk.RIGHT, padx=4)
        self.sub_btn.bind("<Button-1>", lambda e: self.open_apps_window("subscription"))

        self.clock_label = tk.Label(self.tray_frame, font=self._ui_font(10, bold=True),
                                    bg=theme["taskbar_bg"], fg=theme["title_fg"],
                                    justify=tk.CENTER)
        self.clock_label.pack(side=tk.RIGHT, padx=6)

        self.date_label = tk.Label(self.tray_frame, font=self._ui_font(9),
                                   bg=theme["taskbar_bg"], fg=theme["title_fg"])
        self.date_label.pack(side=tk.RIGHT, padx=2)

        # Системные кнопки (блокировка, полноэкранный режим, перезагрузка, выключение)
        for text, cmd in (("🔒", self.lock_screen), ("⛶", self.toggle_fullscreen),
                          ("⭮", self.reboot), ("⏻", self.shutdown)):
            b = tk.Label(self.taskbar, text=text, font=("Segoe UI", 13),
                         bg=theme["taskbar_bg"], fg=theme["title_fg"], cursor="hand2",
                         padx=4)
            b.pack(side=tk.RIGHT)
            b.bind("<Button-1>", lambda e, c=cmd: c())
        # Часы запускаются один раз из MinOSApp.__init__ — второй цикл здесь
        # приводил бы к двойному обновлению и накоплению after-цепочек

    def rebuild_pinned_buttons(self):
        """Пересоздаёт кнопки закреплённых приложений на панели задач."""
        for btn in self.pinned_buttons.values():
            try:
                btn.destroy()
            except Exception:
                pass
        self.pinned_buttons = {}
        theme = THEMES.get(self.current_theme, THEMES["moss"])
        for key in self._pinned_list():
            if key not in TABS:
                continue
            icon_map = {
                "calc": "🧮", "notepad": "📝", "browser": "🌐", "settings": "⚙️",
                "game": "🎲", "clicker": "🍄", "cards": "🃏", "casino": "🎰",
                "snake": "🐍", "disk": "💾", "player": "🎵", "ai": "🤖"
            }
            label = icon_map.get(key, "📱")
            btn = tk.Label(self.task_buttons_frame, text=label, font=("Segoe UI", 13),
                           bg=theme["taskbar_bg"], fg=theme["title_fg"],
                           cursor="hand2", padx=5, pady=6)
            btn.pack(side=tk.LEFT)
            btn.bind("<Button-1>", lambda e, k=key: self.open_apps_window(k))
            btn.bind("<Button-3>", lambda e, k=key: self.unpin_app(k))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=THEMES.get(self.current_theme, THEMES["moss"])["select_bg"]))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=THEMES.get(self.current_theme, THEMES["moss"])["taskbar_bg"]))
            self.pinned_buttons[key] = btn

    def _pinned_list(self):
        """Список закреплений с защитой от повреждённого конфига."""
        pinned = self.config.get("pinned", [])
        return list(pinned) if isinstance(pinned, (list, tuple)) else []

    def pin_app(self, key):
        pinned = self._pinned_list()
        if key not in pinned:
            pinned.append(key)
            self.config.set("pinned", pinned)
            self.rebuild_pinned_buttons()
            self.notify("Панель задач", "Приложение закреплено")

    def unpin_app(self, key):
        pinned = self._pinned_list()
        if key in pinned:
            pinned.remove(key)
            self.config.set("pinned", pinned)
            self.rebuild_pinned_buttons()
            self.notify("Панель задач", "Приложение откреплено")

    def toggle_mute(self):
        self.muted = not self.muted
        self.config.set("muted", self.muted)
        if hasattr(self, 'sound_btn'):
            self.sound_btn.config(text="🔇" if self.muted else "🔊")
        if not self.muted:
            self.play_success()

    def update_clock(self):
        now = datetime.datetime.now()
        if hasattr(self, 'clock_label'):
            self.clock_label.config(text=now.strftime("%H:%M"))
            self.date_label.config(text=now.strftime("%d.%m.%Y"))
        self.root.after(1000, self.update_clock)

    # ---------- МЕНЮ «ПУСК» (стиль Windows 10) ----------
    def toggle_start_menu(self):
        if self.start_menu_open:
            self.close_start_menu()
        else:
            self.open_start_menu()

    def open_start_menu(self):
        if self.start_menu_open:
            return
        # Страховка: уничтожаем «осиротевшее» меню, если флаг рассинхронизировался
        if self.start_menu is not None:
            try:
                self.start_menu.destroy()
            except Exception:
                pass
            self.start_menu = None
        self.start_menu_open = True
        self.start_menu = self._build_start_menu()
        self.root.bind_all("<Button-1>", self._start_menu_global_click, add="+")

    def close_start_menu(self):
        self.start_menu_open = False
        if self.start_menu is not None:
            try:
                self.start_menu.destroy()
            except Exception:
                pass
            self.start_menu = None
        try:
            self.root.unbind_all("<Button-1>")
        except Exception:
            pass
        try:
            self.root.unbind_all("<MouseWheel>")
        except Exception:
            pass

    def _start_menu_global_click(self, event):
        """Закрывает меню Пуск при клике вне его."""
        if not self.start_menu_open:
            return
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        if widget is None:
            self.close_start_menu()
            return
        # Клик внутри меню или по кнопке Пуск — не закрывать
        if str(widget).startswith(str(self.start_menu)):
            return
        if widget is self.start_btn or str(widget).startswith(str(self.start_btn)):
            return
        self.close_start_menu()

    def _build_start_menu(self):
        theme = THEMES.get(self.current_theme, THEMES["moss"])
        menu = tk.Toplevel(self.root)
        menu.overrideredirect(True)
        w, h = 560, 560
        x = 8
        y = self.root.winfo_screenheight() - 52 - h - 6
        menu.geometry(f"{w}x{h}+{x}+{y}")
        menu.configure(bg=theme["taskbar_bg"], bd=1, relief="solid")
        menu.attributes("-topmost", True)

        # --- Поиск ---
        search_frame = tk.Frame(menu, bg=theme["taskbar_bg"])
        search_frame.pack(fill=tk.X, padx=14, pady=(14, 6))
        search_entry = tk.Entry(search_frame, font=self._ui_font(11),
                                bg=theme["btn_bg"], fg=theme["fg"],
                                insertbackground=theme["fg"], relief="flat", bd=0)
        search_entry.pack(fill=tk.X, ipady=6, padx=2)
        search_entry.focus()

        # --- Сетка приложений ---
        grid_holder = tk.Frame(menu, bg=theme["taskbar_bg"])
        grid_holder.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        canvas = tk.Canvas(grid_holder, bg=theme["taskbar_bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(grid_holder, orient="vertical", command=canvas.yview)
        apps_frame = tk.Frame(canvas, bg=theme["taskbar_bg"])
        apps_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=apps_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        apps = [
            ("🧮", "Калькулятор", "calc"), ("📝", "Блокнот", "notepad"),
            ("🎲", "Игра", "game"), ("🌐", "Перевод", "translator"),
            ("🔢", "Генератор", "generator"), ("🍄", "Кликер", "clicker"),
            ("🃏", "Карточки", "cards"), ("🎰", "Казино", "casino"),
            ("🩸", "ULTRAKILL", "ultrakill"), ("🤖", "ИИ", "ai"),
            ("🌱", "Питомец", "pet"), ("💻", "Консоль", "console"),
            ("📁", "Игры", "games"), ("🌐", "Интернет", "internet"),
            ("⬇️", "Загрузки", "downloads"), ("🔐", "Шифратор", "cipher"),
            ("🔗", "Ссылки", "links"), ("⚙️", "Настройки", "settings"),
            ("📜", "Задания", "quests"), ("🔍", "Поиск", "search"),
            ("📅", "Календарь", "calendar"), ("🎨", "Рисование", "paint"),
            ("🐍", "Змейка", "snake"), ("⏰", "Будильник", "alarm"),
            ("ℹ️", "Система", "system"), ("💾", "Диск", "disk"),
            ("💣", "Сапёр", "minesweeper"), ("📊", "Диспетчер", "taskmanager"),
            ("🌐", "Браузер", "browser"), ("📆", "Кальк. дат", "datecalc"),
            ("📜", "Ченджлог", "changelog"), ("💎", "Подписка", "subscription"),
            ("🎵", "Плеер", "player"), ("🌿", "О MinOS", "about"),
        ]

        def render_apps(filter_text=""):
            for child in apps_frame.winfo_children():
                child.destroy()
            ft = filter_text.strip().lower()
            row, col = 0, 0
            for emoji, name, key in apps:
                if ft and ft not in name.lower():
                    continue
                btn = tk.Button(apps_frame, text=f"{emoji}\n{name}",
                                font=self._ui_font(9), width=9, height=3,
                                bg=theme["btn_bg"], fg=theme["fg"],
                                activebackground=theme["select_bg"],
                                relief="flat", bd=0,
                                command=lambda k=key: self._start_menu_launch(k))
                btn.grid(row=row, column=col, padx=4, pady=4)
                col += 1
                if col >= 6:
                    col = 0
                    row += 1
            if ft and row == 0 and col == 0:
                tk.Label(apps_frame, text="Ничего не найдено", font=self._ui_font(11),
                         bg=theme["taskbar_bg"], fg=theme["fg"]).pack(pady=30)

        search_entry.bind("<KeyRelease>", lambda e: render_apps(search_entry.get()))
        render_apps()

        # --- Нижняя панель меню ---
        bottom = tk.Frame(menu, bg=theme["title_bg"])
        bottom.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(bottom, text="🌿 Пользователь", font=self._ui_font(10, bold=True),
                 bg=theme["title_bg"], fg=theme["title_fg"]).pack(side=tk.LEFT, padx=14, pady=10)
        for text, cmd in (("⚙️", lambda: self._start_menu_launch("settings")),
                          ("⭮", self.reboot),
                          ("⏻", self.shutdown)):
            b = tk.Label(bottom, text=text, font=("Segoe UI", 14),
                         bg=theme["title_bg"], fg=theme["title_fg"], cursor="hand2", padx=8)
            b.pack(side=tk.RIGHT)
            b.bind("<Button-1>", lambda e, c=cmd: c())
        return menu

    def _start_menu_launch(self, key):
        self.close_start_menu()
        if key == "about":
            self.show_about()
        elif key == "lock":
            self.lock_screen()
        else:
            self.open_apps_window(key)

    # ---------- КОНТЕКСТНОЕ МЕНЮ РАБОЧЕГО СТОЛА ----------
    def show_desktop_menu(self, event):
        """Правый клик по рабочему столу: создать/обновить/обои/настройки."""
        # Меню только по фону рабочего стола (не по иконкам)
        if event.widget is not self.root and event.widget is not self.wallpaper_label:
            return
        theme = THEMES.get(self.current_theme, THEMES["moss"])
        menu = tk.Menu(self.root, tearoff=0, bg=theme["btn_bg"], fg=theme["fg"],
                       activebackground=theme["select_bg"], activeforeground="White",
                       font=self._ui_font(10))
        menu.add_command(label="📁 Создать папку", command=self.desktop_create_folder)
        menu.add_command(label="📄 Создать текстовый файл", command=self.desktop_create_file)
        menu.add_separator()
        menu.add_command(label="🔄 Обновить", command=self.refresh_desktop_icons)
        menu.add_command(label="🖼 Выбрать обои…", command=self.choose_wallpaper)
        menu.add_command(label="🚫 Убрать обои", command=self.clear_wallpaper)
        menu.add_separator()
        menu.add_command(label="⚙️ Настройки экрана",
                         command=lambda: self.open_apps_window("settings"))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def desktop_create_folder(self):
        """Создание папки на виртуальном диске MinOS."""
        self.open_apps_window("disk")
        if self.apps_window and self.apps_window.winfo_exists():
            self.apps_window.disk_create_folder()

    def desktop_create_file(self):
        """Создание текстового файла на виртуальном диске MinOS."""
        self.open_apps_window("disk")
        if self.apps_window and self.apps_window.winfo_exists():
            self.apps_window.disk_create_file()

    def refresh_desktop_icons(self):
        """Пересоздаёт иконки, сохраняя их текущие (возможно, перетащенные) позиции."""
        # Собираем актуальные позиции живых кнопок
        positions = {}
        for child in list(self.root.winfo_children()):
            if isinstance(child, tk.Button) and hasattr(child, "_base_pos") and hasattr(child, "_text_key"):
                positions[child._text_key] = (child.winfo_x(), child.winfo_y())
                child.destroy()
        # Пересоздаём по единому списку DESKTOP_ICONS
        self.desktop_icons = {}
        for text, key, def_x, def_y in DESKTOP_ICONS:
            x, y = positions.get(key, (def_x, def_y))
            btn = self.create_desktop_icon(text, key, x, y)
            btn._text_key = key
            self.desktop_icons[key] = btn
        self.play_click()

    def open_apps_window(self, tab_key="all"):
        tab_index = TABS.get(tab_key, TABS["all"])
        if self.apps_window is not None and self.apps_window.winfo_exists():
            if self.apps_window.state() == 'withdrawn':
                self.apps_window.deiconify()
            self.apps_window.switch_to_tab(tab_index)
            self.apps_window.lift()
            self.apps_window.focus_force()
        else:
            self.apps_window = AppsWindow(self.root, self, tab_index, theme=self.current_theme)
            self.apps_window._opened_for = tab_key
            self.add_task_button(self.apps_window)

    def add_task_button(self, window):
        if window in self.task_buttons:
            return
        theme = THEMES.get(self.current_theme, THEMES["moss"])
        label = getattr(window, "_opened_for", "all")
        names = {
            "calc": "🧮 Калькулятор", "notepad": "📝 Блокнот", "game": "🎲 Игра",
            "translator": "🌐 Перевод", "generator": "🔢 Генератор", "clicker": "🍄 Кликер",
            "cards": "🃏 Карточки", "casino": "🎰 Казино", "ultrakill": "🩸 ULTRAKILL",
            "ai": "🤖 ИИ", "pet": "🌱 Питомец", "console": "💻 Консоль", "all": "📱 Приложения",
            "games": "📁 Игры", "internet": "🌐 Интернет", "downloads": "⬇️ Загрузки",
            "cipher": "🔐 Шифратор", "links": "🔗 Ссылки", "settings": "⚙️ Настройки",
            "quests": "📜 Задания", "search": "🔍 Поиск", "calendar": "📅 Календарь",
            "paint": "🎨 Рисование", "snake": "🐍 Змейка", "alarm": "⏰ Будильник",
            "system": "ℹ️ Система", "disk": "💾 Диск", "minesweeper": "💣 Сапёр",
            "taskmanager": "📊 Диспетчер", "browser": "🌐 Браузер", "datecalc": "📆 Кальк. дат",
            "changelog": "📜 Ченджлог", "subscription": "💎 Подписка", "player": "🎵 Плеер"
        }
        btn = tk.Button(self.task_buttons_frame, text=names.get(label, "📱 Приложения"),
                        font=self._ui_font(9), bg=theme["btn_bg"], fg=theme["btn_fg"],
                        activebackground=theme["select_bg"], relief="flat", bd=1,
                        command=lambda: self.restore_window_from_taskbar(window))
        btn.pack(side=tk.LEFT, padx=3, pady=8)
        btn.bind("<Button-3>", lambda e, k=label: self.pin_app(k))
        self.task_buttons[window] = btn

    def remove_task_button(self, window):
        if window in self.task_buttons:
            self.task_buttons[window].destroy()
            del self.task_buttons[window]

    def restore_window_from_taskbar(self, window):
        if window.winfo_exists():
            if window.state() == 'withdrawn':
                window.deiconify()
            window.lift()
            window.focus_force()

    def on_apps_window_closed(self):
        if self.apps_window is not None:
            self.remove_task_button(self.apps_window)
            self.apps_window = None

    def lock_screen(self):
        LockScreen(self.root)

    def show_ad(self):
        if not self.subscription.is_active():
            AdWindow(self.root)

    def show_about(self):
        about = tk.Toplevel(self.root)
        about.title("О MinOS")
        about.geometry("500x450")
        about.configure(bg='#2b5a2b')
        about.resizable(False, False)
        tk.Label(about, text="🌿 MinOS", font=("Segoe UI", 28, "bold"),
                 fg="#a0d6a0", bg="#2b5a2b").pack(pady=20)
        tk.Label(about, text="Операционная система в стиле мха", font=("Segoe UI", 14),
                 fg="#c0e0c0", bg="#2b5a2b").pack()
        tk.Label(about, text=f"Версия {self.VERSION}", font=("Segoe UI", 12),
                 fg="#a0d6a0", bg="#2b5a2b").pack()
        tk.Label(about, text="Сделано тобой и ИИ", font=("Segoe UI", 14),
                 fg="#a0d6a0", bg="#2b5a2b").pack(pady=5)
        tk.Label(about, text="© 2026 MinOS | Made in China 🌿", font=("Segoe UI", 10),
                 fg="#6a8a6a", bg="#2b5a2b").pack(pady=5)
        btn_frame = tk.Frame(about, bg='#2b5a2b')
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="📜 История изменений", command=self.show_changelog,
                  bg="#3a7a3a", fg="White", relief="flat", bd=0, padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Закрыть", command=about.destroy,
                  bg="#3a7a3a", fg="White", relief="flat", bd=0, padx=10, pady=5).pack(side=tk.LEFT, padx=5)

    def show_changelog(self):
        changelog_win = tk.Toplevel(self.root)
        changelog_win.title("История изменений")
        changelog_win.geometry("600x450")
        changelog_win.configure(bg='#2b5a2b')
        changelog_win.resizable(False, False)
        x = (changelog_win.winfo_screenwidth() // 2) - 300
        y = (changelog_win.winfo_screenheight() // 2) - 225
        changelog_win.geometry(f"+{x}+{y}")
        tk.Label(changelog_win, text="Что нового в MinOS", font=("Segoe UI", 18, "bold"),
                 fg="#a0d6a0", bg="#2b5a2b").pack(pady=10)
        text_widget = tk.Text(changelog_win, wrap='word', bg='#3a7a3a', fg='#c0e0c0',
                              font=("Consolas", 10), relief='flat', bd=0, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, self.CHANGELOG)
        text_widget.configure(state='disabled')
        tk.Button(changelog_win, text="Закрыть", command=changelog_win.destroy,
                  bg="#3a7a3a", fg="White", relief="flat", bd=0, padx=10, pady=5).pack(pady=5)

    def shutdown(self):
        self.close_start_menu()
        if messagebox.askyesno("MinOS", "Вы уверены, что хотите выключить MinOS?"):
            self.root.withdraw()
            ShutdownScreen(self.root, self.root.quit)

    def reboot(self):
        self.close_start_menu()
        if messagebox.askyesno("MinOS", "Перезагрузить MinOS?"):
            self.root.withdraw()
            BootScreen(self.root, self.after_reboot)

    def after_reboot(self):
        self.root.deiconify()
        self.show_login_or_desktop()

    def set_wallpaper(self, wp):
        self.wallpaper = wp
        self.apply_wallpaper()

    def show_login_or_desktop(self):
        if self.password == "":
            self.after_login()
        else:
            LoginScreen(self.root, self.after_login)

    def after_login(self):
        pass

# ==================== ОКНО ПРИЛОЖЕНИЙ ====================
class AppsWindow(tk.Toplevel):
    def __init__(self, master, app, tab_index=0, theme="moss"):
        super().__init__(master)
        self.app = app
        self.subscription = app.subscription
        self.download_manager = app.download_manager
        self.current_theme = theme
        self.title("MinOS Apps")
        self.geometry("840x600")
        self.configure(bg='#2b5a2b')
        self.overrideredirect(True)
        self.resizable(False, False)
        self.drag_start_x = 0
        self.drag_start_y = 0

        # --- Данные для игр и приложений ---
        self.clicker_score = 0
        self.clicker_click_power = 1
        self.clicker_auto_income = 0
        self.clicker_prestige_multiplier = 1
        self.clicker_upgrade_cost = 10
        self.clicker_auto_cost = 50
        self.clicker_prestige_cost = 1000
        self.clicker_inventory = []
        self.daily_bonus_available = True
        self.clicker_start_time = time.time()

        self.cards_score = 0
        self.cards_rare_chance = 0.05
        self.cards_cooldown = 3
        self.cards_cooldown_active = False
        self.cards_inventory = []
        self.cards_upgrade_rare_cost = 100
        self.cards_upgrade_cooldown_cost = 150
        self.cards_collection_window = None

        self.casino_balance = 0

        self.ultrakill_categories = {
            0: ["Труп короля Миноса", "1000-THR 'EARTHMOVER'", "Тюрьма плоти",
                "Паноптикум плоти", "Минос прайм", "Сизиф прайм", "Большой Джонинатор",
                "Таинственный рыцарь друид и Сова", "Герион", "Левиафан",
                "Минотавр", "Идол", "Ловец смерти", "Гавриил Судья ада",
                "Гавриил Отступник ненависти", "Повстанец Сизифа", "Жнец зеркал"],
            1: ["Отброс", "Бродяга", "Схизм", "Солдат", "Дрон"],
            2: ["Манекен", "Турель", "Очень раковый грызун"],
            3: ["Меч машина", "Злобное лицо", "Цербер", "Сталкер", "Чистильщик"],
            4: ["Гаттертанк", "Гаттермен", "В2", "Паромщик", "Добродетель",
                "Власть", "Свежеватель Разума", "Отвратная масса", "Провиденье"]
        }
        self.ultrakill_count_rules = {0:(1,1),1:(5,10),2:(3,5),3:(1,3),4:(1,2)}

        self.pet_moisture = 80
        self.pet_health = 80
        self.pet_growth = 0
        self.pet_stage = 0
        self.pet_care_points = 0
        self.pet_level = 1

        self.downloads = []
        self.cipher_shift = tk.IntVar(value=3)
        self.theme_var = tk.StringVar(value=theme)
        self.ad_var = tk.BooleanVar(value=self.app.show_ad_flag)
        self.sound_var = tk.StringVar(value=self.app.sound_engine)
        self.wallpaper_var = tk.StringVar(value=self.app.wallpaper)
        self.color_bg = "#2b5a2b"
        self.color_btn = "#3a7a3a"
        self.color_text = "#c0e0c0"

        self.quests = []
        self.quests_labels = []
        self.quest_completed_count = 0
        self.quest_last_update = time.time()
        self.quest_pool = [
            {"description": "Сделайте 10 кликов в кликере", "type": "clicker_clicks", "target": 10, "reward_type": "clicker_score", "reward_value": 50},
            {"description": "Откройте 5 карточек", "type": "cards_opened", "target": 5, "reward_type": "cards_score", "reward_value": 50},
            {"description": "Сыграйте 3 раза в казино", "type": "casino_plays", "target": 3, "reward_type": "casino_balance", "reward_value": 100},
            {"description": "Полейте мох 3 раза", "type": "pet_water", "target": 3, "reward_type": "pet_care_points", "reward_value": 20},
            {"description": "Достигните 100 очков в кликере", "type": "clicker_score_reach", "target": 100, "reward_type": "clicker_score", "reward_value": 100},
            {"description": "Выиграйте в казино (цвет) 2 раза", "type": "casino_color_wins", "target": 2, "reward_type": "casino_balance", "reward_value": 200},
            {"description": "Соберите 3 редкие карточки", "type": "cards_rare_collect", "target": 3, "reward_type": "cards_score", "reward_value": 150},
            {"description": "Выиграйте в сапёре 2 раза", "type": "minesweeper_wins", "target": 2, "reward_type": "clicker_score", "reward_value": 200},
            {"description": "Активируйте премиум-подписку", "type": "premium_activate", "target": 1, "reward_type": "clicker_score", "reward_value": 500}
        ]
        self.quest_progress = {}

        self.search_items = []

        self.clicker_after_id = None
        self.cards_cooldown_after_id = None
        self.pet_after_id = None
        self.snake_game = None
        self.alarm_time = None
        self.alarm_active = False
        self.alarm_thread = None
        self.alarm_stop_flag = False

        # --- Данные для диска ---
        self.disk_total_size = 1024
        self.disk_used_size = 0
        self.disk_root = {"name": "Корень", "type": "folder", "children": [], "path": "/"}
        self.disk_current_path = "/"
        self.disk_selected_item = None
        self.disk_visible_items = []
        self.disk_sort_col = "name"
        self.disk_sort_reverse = False

        self.browser_tabs = []
        self.browser_current_tab = 0

        self.all_tabs = []

        self.setup_title_bar()
        self.setup_notebook()
        self.apply_theme_to_window(theme)
        self.notebook.select(tab_index)
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.generate_quests()
        self.update_quests_display()
        self.quest_update_after_id = self.after(60000, self.check_quest_update)
        self.clicker_close_check_id = self.after(10000, self.check_clicker_timeout)

        # --- Анимации вкладок ---
        self._tab_anim_state = None
        self._tab_anim_after = None
        self._last_tab_index = tab_index
        self._tab_anim_ready = False
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._tab_anim_ready = True

        self._downloads_ui_after = None

    def apply_theme_to_window(self, theme_name):
        theme = THEMES.get(theme_name, THEMES["moss"])
        self.current_theme = theme_name
        self.configure(bg=theme["bg"])
        self.color_bg = theme["bg"]
        self.color_text = theme["fg"]
        self.color_btn = theme["btn_bg"]
        if hasattr(self, 'title_bar'):
            self.title_bar.configure(bg=theme["title_bg"])
            for child in self.title_bar.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=theme["title_bg"], fg=theme["title_fg"])
                elif isinstance(child, tk.Button):
                    child.configure(bg=theme["title_bg"], fg="white")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=theme["bg"])
        style.configure("TNotebook.Tab", background=theme["btn_bg"], foreground=theme["fg"])
        style.map("TNotebook.Tab", background=[("selected", theme["select_bg"])])
        style.configure("green.Horizontal.TProgressbar",
                        background=theme["btn_bg"], troughcolor=theme["bg"])
        for frame in self.all_tabs:
            if frame.winfo_exists():
                frame.configure(bg=theme["bg"])

    def setup_title_bar(self):
        theme = THEMES.get(self.current_theme, THEMES["moss"])
        self.title_bar = tk.Frame(self, bg=theme["title_bg"], height=35)
        self.title_bar.pack(side=tk.TOP, fill=tk.X)
        self.title_bar.pack_propagate(False)
        title_label = tk.Label(self.title_bar, text="🌿 MinOS Applications", font=("Segoe UI", 12, "bold"),
                               bg=theme["title_bg"], fg=theme["title_fg"])
        title_label.pack(side=tk.LEFT, padx=10)
        self.btn_min = tk.Button(self.title_bar, text="─", font=("Segoe UI", 14),
                                 bg=theme["title_bg"], fg='White',
                                 activebackground=theme["select_bg"], activeforeground='White',
                                 relief="flat", bd=0, width=4, command=self.minimize)
        self.btn_min.pack(side=tk.RIGHT, padx=0, pady=2)
        self.btn_max = tk.Button(self.title_bar, text="□", font=("Segoe UI", 12),
                                 bg=theme["title_bg"], fg='White',
                                 activebackground=theme["select_bg"], activeforeground='White',
                                 relief="flat", bd=0, width=4, command=self.toggle_maximize)
        self.btn_max.pack(side=tk.RIGHT, padx=0, pady=2)
        self.btn_close = tk.Button(self.title_bar, text="✕", font=("Segoe UI", 14),
                                   bg=theme["title_bg"], fg='White',
                                   activebackground='#8f2a2a', activeforeground='White',
                                   relief="flat", bd=0, width=4, command=self.close)
        self.btn_close.pack(side=tk.RIGHT, padx=0, pady=2)
        self.maximized = False
        self._restore_geometry = None
        self.title_bar.bind("<Button-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.on_drag)
        title_label.bind("<Button-1>", self.start_drag)
        title_label.bind("<B1-Motion>", self.on_drag)

    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag(self, event):
        x = self.winfo_x() + event.x - self.drag_start_x
        y = self.winfo_y() + event.y - self.drag_start_y
        self.geometry(f"+{x}+{y}")

    def setup_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.tab_calc = tk.Frame(self.notebook)
        self.tab_notepad = tk.Frame(self.notebook)
        self.tab_game = tk.Frame(self.notebook)
        self.tab_translator = tk.Frame(self.notebook)
        self.tab_generator = tk.Frame(self.notebook)
        self.tab_clicker = tk.Frame(self.notebook)
        self.tab_cards = tk.Frame(self.notebook)
        self.tab_casino = tk.Frame(self.notebook)
        self.tab_ultrakill = tk.Frame(self.notebook)
        self.tab_ai = tk.Frame(self.notebook)
        self.tab_pet = tk.Frame(self.notebook)
        self.tab_console = tk.Frame(self.notebook)
        self.tab_all = tk.Frame(self.notebook)
        self.tab_games = tk.Frame(self.notebook)
        self.tab_internet = tk.Frame(self.notebook)
        self.tab_downloads = tk.Frame(self.notebook)
        self.tab_cipher = tk.Frame(self.notebook)
        self.tab_links = tk.Frame(self.notebook)
        self.tab_settings = tk.Frame(self.notebook)
        self.tab_quests = tk.Frame(self.notebook)
        self.tab_search = tk.Frame(self.notebook)
        self.tab_calendar = tk.Frame(self.notebook)
        self.tab_paint = tk.Frame(self.notebook)
        self.tab_snake = tk.Frame(self.notebook)
        self.tab_alarm = tk.Frame(self.notebook)
        self.tab_system = tk.Frame(self.notebook)
        self.tab_disk = tk.Frame(self.notebook)
        self.tab_minesweeper = tk.Frame(self.notebook)
        self.tab_taskmanager = tk.Frame(self.notebook)
        self.tab_browser = tk.Frame(self.notebook)
        self.tab_datecalc = tk.Frame(self.notebook)
        self.tab_changelog = tk.Frame(self.notebook)
        self.tab_subscription = tk.Frame(self.notebook)
        self.tab_player = tk.Frame(self.notebook)

        self.notebook.add(self.tab_calc, text="🧮 Калькулятор")
        self.notebook.add(self.tab_notepad, text="📝 Блокнот")
        self.notebook.add(self.tab_game, text="🎲 Игра")
        self.notebook.add(self.tab_translator, text="🌐 Перевод")
        self.notebook.add(self.tab_generator, text="🔢 Генератор")
        self.notebook.add(self.tab_clicker, text="🍄 Кликер")
        self.notebook.add(self.tab_cards, text="🃏 Карточки")
        self.notebook.add(self.tab_casino, text="🎰 Казино")
        self.notebook.add(self.tab_ultrakill, text="🩸 ULTRAKILL")
        self.notebook.add(self.tab_ai, text="🤖 ИИ")
        self.notebook.add(self.tab_pet, text="🌱 Питомец")
        self.notebook.add(self.tab_console, text="💻 Консоль")
        self.notebook.add(self.tab_all, text="📂 Все")
        self.notebook.add(self.tab_games, text="📁 Игры")
        self.notebook.add(self.tab_internet, text="🌐 Интернет")
        self.notebook.add(self.tab_downloads, text="⬇️ Загрузки")
        self.notebook.add(self.tab_cipher, text="🔐 Шифратор")
        self.notebook.add(self.tab_links, text="🔗 Ссылки")
        self.notebook.add(self.tab_settings, text="⚙️ Настройки")
        self.notebook.add(self.tab_quests, text="📜 Задания")
        self.notebook.add(self.tab_search, text="🔍 Поиск")
        self.notebook.add(self.tab_calendar, text="📅 Календарь")
        self.notebook.add(self.tab_paint, text="🎨 Рисование")
        self.notebook.add(self.tab_snake, text="🐍 Змейка")
        self.notebook.add(self.tab_alarm, text="⏰ Будильник")
        self.notebook.add(self.tab_system, text="ℹ️ Система")
        self.notebook.add(self.tab_disk, text="💾 Диск")
        self.notebook.add(self.tab_minesweeper, text="💣 Сапёр")
        self.notebook.add(self.tab_taskmanager, text="📊 Диспетчер")
        self.notebook.add(self.tab_browser, text="🌐 Браузер")
        self.notebook.add(self.tab_datecalc, text="📆 Калькулятор дат")
        self.notebook.add(self.tab_changelog, text="📜 Ченджлог")
        self.notebook.add(self.tab_subscription, text="💎 Подписка")
        self.notebook.add(self.tab_player, text="🎵 Плеер")

        self.all_tabs = [
            self.tab_calc, self.tab_notepad, self.tab_game, self.tab_translator,
            self.tab_generator, self.tab_clicker, self.tab_cards, self.tab_casino,
            self.tab_ultrakill, self.tab_ai, self.tab_pet, self.tab_console,
            self.tab_all, self.tab_games, self.tab_internet, self.tab_downloads,
            self.tab_cipher, self.tab_links, self.tab_settings, self.tab_quests,
            self.tab_search, self.tab_calendar, self.tab_paint, self.tab_snake,
            self.tab_alarm, self.tab_system, self.tab_disk, self.tab_minesweeper,
            self.tab_taskmanager, self.tab_browser, self.tab_datecalc, self.tab_changelog,
            self.tab_subscription, self.tab_player
        ]

        self.create_calculator_tab(self.tab_calc)
        self.create_notepad_tab(self.tab_notepad)
        self.create_game_tab(self.tab_game)
        self.create_translator_tab(self.tab_translator)
        self.create_generator_tab(self.tab_generator)
        self.create_clicker_tab(self.tab_clicker)
        self.create_cards_tab(self.tab_cards)
        self.create_casino_tab(self.tab_casino)
        self.create_ultrakill_tab(self.tab_ultrakill)
        self.create_ai_tab(self.tab_ai)
        self.create_pet_tab(self.tab_pet)
        self.create_console_tab(self.tab_console)
        self.create_all_tab(self.tab_all)
        self.create_games_tab(self.tab_games)
        self.create_internet_tab(self.tab_internet)
        self.create_downloads_tab(self.tab_downloads)
        self.create_cipher_tab(self.tab_cipher)
        self.create_links_tab(self.tab_links)
        self.create_settings_tab(self.tab_settings)
        self.create_quests_tab(self.tab_quests)
        self.create_search_tab(self.tab_search)
        self.create_calendar_tab(self.tab_calendar)
        self.create_paint_tab(self.tab_paint)
        self.create_snake_tab(self.tab_snake)
        self.create_alarm_tab(self.tab_alarm)
        self.create_system_tab(self.tab_system)
        self.create_disk_tab(self.tab_disk)
        self.create_minesweeper_tab(self.tab_minesweeper)
        self.create_taskmanager_tab(self.tab_taskmanager)
        self.create_browser_tab(self.tab_browser)
        self.create_datecalc_tab(self.tab_datecalc)
        self.create_changelog_tab(self.tab_changelog)
        self.create_subscription_tab(self.tab_subscription)
        self.create_player_tab(self.tab_player)

    # ---------- ВСЕ МЕТОДЫ СОЗДАНИЯ ВКЛАДОК ----------
    def create_calculator_tab(self, frame):
        self.calc_expr = tk.StringVar()
        entry = tk.Entry(frame, textvariable=self.calc_expr, font=("Segoe UI", 18),
                         justify='right', state='readonly',
                         readonlybackground='#3a7a3a', fg='White', relief='sunken', bd=2)
        entry.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky='ew')
        buttons = [
            ('7',1,0),('8',1,1),('9',1,2),('/',1,3),
            ('4',2,0),('5',2,1),('6',2,2),('*',2,3),
            ('1',3,0),('2',3,1),('3',3,2),('-',3,3),
            ('0',4,0),('.',4,1),('=',4,2),('+',4,3),
            ('C',5,0),('(',5,1),(')',5,2),('^',5,3)
        ]
        for (text,row,col) in buttons:
            if text == '=':
                cmd = self.calc_evaluate
            elif text == 'C':
                cmd = self.calc_clear
            else:
                cmd = lambda t=text: self.calc_add(t)
            btn = tk.Button(frame, text=text, font=("Segoe UI", 14),
                            bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                            relief='raised', bd=2, width=6, command=cmd)
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
            btn.bind("<Button-1>", lambda e: self.app.play_click())
        for i in range(4): frame.columnconfigure(i, weight=1)
        for i in range(6): frame.rowconfigure(i, weight=1)

    def calc_add(self, char):
        current = self.calc_expr.get()
        if current == "Ошибка":
            current = ""
        if len(current) < 100:
            self.calc_expr.set(current + char)
    def calc_clear(self):
        self.calc_expr.set("")
    def calc_evaluate(self):
        expr = self.calc_expr.get()
        if not expr:
            return
        try:
            result = SafeCalculator.evaluate(expr)
            if isinstance(result, float):
                result = round(result, 10)
                if result.is_integer():
                    result = int(result)
            self.calc_expr.set(str(result))
        except Exception:
            self.calc_expr.set("Ошибка")

    def create_notepad_tab(self, frame):
        toolbar = tk.Frame(frame, bg='#2b5a2b')
        toolbar.pack(fill=tk.X, pady=5)
        tk.Button(toolbar, text="Открыть", command=self.notepad_open,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Сохранить", command=self.notepad_save,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Сохранить как", command=self.notepad_save_as,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=5)
        self.notepad_text = tk.Text(frame, wrap='word', bg='#3a7a3a', fg='#c0e0c0',
                                    insertbackground='White', font=("Segoe UI", 12),
                                    relief='sunken', bd=2)
        scrollbar = tk.Scrollbar(frame, command=self.notepad_text.yview)
        self.notepad_text.configure(yscrollcommand=scrollbar.set)
        # Сначала упаковываем скроллбар (справа), затем текст — иначе текст
        # занимает всё место и скроллбар остаётся без места
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,5), pady=5)
        self.notepad_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notepad_current_file = None

    def notepad_open(self):
        filepath = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.notepad_text.delete(1.0, tk.END)
                self.notepad_text.insert(1.0, content)
                self.notepad_current_file = filepath
                self.notify("Блокнот", f"Открыт файл: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")

    def notepad_save(self):
        if self.notepad_current_file:
            try:
                with open(self.notepad_current_file, 'w', encoding='utf-8') as f:
                    f.write(self.notepad_text.get(1.0, tk.END).strip())
                self.notify("Блокнот", "Файл сохранён")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
        else:
            self.notepad_save_as()

    def notepad_save_as(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.notepad_text.get(1.0, tk.END).strip())
                self.notepad_current_file = filepath
                self.notify("Блокнот", f"Файл сохранён как: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def create_game_tab(self, frame):
        self.secret_number = random.randint(1,100)
        self.attempts = 0
        tk.Label(frame, text="Угадай число от 1 до 100", font=("Segoe UI", 16, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        self.guess_entry = tk.Entry(frame, font=("Segoe UI", 14), bg='#3a7a3a',
                                    fg='White', insertbackground='White', relief='sunken', bd=2)
        self.guess_entry.pack(pady=5)
        self.guess_entry.focus()
        btn = tk.Button(frame, text="Проверить", font=("Segoe UI", 12), bg='#3a7a3a',
                        fg='White', activebackground='#4a8a4a', relief='raised', bd=2,
                        command=self.check_guess)
        btn.pack(pady=5)
        btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.game_hint = tk.Label(frame, text="Введите число и нажмите Проверить",
                                  font=("Segoe UI", 12), bg='#2b5a2b', fg='#c0e0c0')
        self.game_hint.pack(pady=10)
        btn2 = tk.Button(frame, text="Новая игра", font=("Segoe UI", 12), bg='#3a7a3a',
                         fg='White', activebackground='#4a8a4a', relief='raised', bd=2,
                         command=self.new_game)
        btn2.pack(pady=5)
        btn2.bind("<Button-1>", lambda e: self.app.play_click())

    def new_game(self):
        self.secret_number = random.randint(1,100)
        self.attempts = 0
        self.game_hint.config(text="Новое число загадано! Введите догадку.")
        self.guess_entry.delete(0, tk.END)
        self.guess_entry.focus()

    def check_guess(self):
        try:
            guess = int(self.guess_entry.get())
        except ValueError:
            self.game_hint.config(text="Введите целое число!")
            return
        self.attempts += 1
        if guess < self.secret_number:
            self.game_hint.config(text=f"Загаданное число больше (попытка {self.attempts})")
        elif guess > self.secret_number:
            self.game_hint.config(text=f"Загаданное число меньше (попытка {self.attempts})")
        else:
            self.game_hint.config(text=f"🎉 Поздравляю! Вы угадали за {self.attempts} попыток!")
            self.notify("Игра", f"Вы угадали число за {self.attempts} попыток!")
        self.guess_entry.delete(0, tk.END)
        self.guess_entry.focus()

    def create_translator_tab(self, frame):
        self.english_to_russian = {
            "hello":"привет","world":"мир","apple":"яблоко","dog":"собака",
            "cat":"кошка","house":"дом","car":"машина","book":"книга",
            "water":"вода","fire":"огонь","love":"любовь","friend":"друг",
            "good":"хорошо","bad":"плохо","big":"большой","small":"маленький",
            "sun":"солнце","moon":"луна","star":"звезда","tree":"дерево",
            "flower":"цветок","green":"зелёный","moss":"мох","computer":"компьютер",
            "system":"система","mouse":"мышь","keyboard":"клавиатура","code":"код",
            "game":"игра","clicker":"кликер"
        }
        self.russian_to_english = {v:k for k,v in self.english_to_russian.items()}
        tk.Label(frame, text="Переводчик", font=("Segoe UI", 14, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=5)
        self.translate_input = tk.Entry(frame, font=("Segoe UI", 12), bg='#3a7a3a',
                                        fg='White', insertbackground='White', relief='sunken', bd=2)
        self.translate_input.pack(pady=5, fill=tk.X, padx=10)
        self.translate_direction = tk.StringVar(value="en-ru")
        for text,val in [("Англ. → Рус.","en-ru"),("Рус. → Англ.","ru-en"),("Транслит → Рус.","translit-ru")]:
            tk.Radiobutton(frame, text=text, variable=self.translate_direction,
                           value=val, bg='#2b5a2b', fg='#c0e0c0',
                           activebackground='#2b5a2b', selectcolor='#3a7a3a').pack()
        btn = tk.Button(frame, text="Перевести", font=("Segoe UI", 12), bg='#3a7a3a',
                        fg='White', activebackground='#4a8a4a', relief='raised', bd=2,
                        command=self.translate_word)
        btn.pack(pady=5)
        btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.translate_result = tk.Label(frame, text="", font=("Segoe UI", 14),
                                         bg='#2b5a2b', fg='#a0d6a0')
        self.translate_result.pack(pady=10)

    def translit_to_ru(self, text):
        mapping = {'a':'ф','b':'и','c':'с','d':'в','e':'у','f':'а',
                   'g':'п','h':'р','i':'ш','j':'о','k':'л','l':'д',
                   'm':'ь','n':'т','o':'щ','p':'з','q':'й','r':'к',
                   's':'ы','t':'е','u':'г','v':'м','w':'ц','x':'ч',
                   'y':'н','z':'я','A':'Ф','B':'И','C':'С','D':'В','E':'У','F':'А',
                   'G':'П','H':'Р','I':'Ш','J':'О','K':'Л','L':'Д',
                   'M':'Ь','N':'Т','O':'Щ','P':'З','Q':'Й','R':'К',
                   'S':'Ы','T':'Е','U':'Г','V':'М','W':'Ц','X':'Ч',
                   'Y':'Н','Z':'Я'}
        return ''.join(mapping.get(ch,ch) for ch in text)

    def translate_word(self):
        word = self.translate_input.get().strip().lower()
        if not word:
            self.translate_result.config(text="Введите слово")
            return
        direction = self.translate_direction.get()
        if direction == "en-ru":
            result = self.english_to_russian.get(word)
        elif direction == "ru-en":
            result = self.russian_to_english.get(word)
        elif direction == "translit-ru":
            result = self.translit_to_ru(word)
        else:
            result = None
        if result:
            self.translate_result.config(text=f"Перевод: {result}")
        else:
            self.translate_result.config(text="Не найдено")

    def create_generator_tab(self, frame):
        tk.Label(frame, text="Генератор случайных символов", font=("Segoe UI", 14, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=5)
        tk.Label(frame, text="Длина:", bg='#2b5a2b', fg='#c0e0c0').pack()
        self.generator_length = tk.Entry(frame, font=("Segoe UI", 12), bg='#3a7a3a',
                                         fg='White', insertbackground='White', relief='sunken', bd=2)
        self.generator_length.pack(pady=5)
        self.generator_length.insert(0, "12")
        btn = tk.Button(frame, text="Сгенерировать", font=("Segoe UI", 12), bg='#3a7a3a',
                        fg='White', activebackground='#4a8a4a', relief='raised', bd=2,
                        command=self.generate_random)
        btn.pack(pady=5)
        btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.generator_result = tk.Label(frame, text="", font=("Consolas", 14),
                                         bg='#2b5a2b', fg='#a0d6a0', wraplength=400)
        self.generator_result.pack(pady=10)

    def generate_random(self):
        try:
            length = int(self.generator_length.get())
            if length <1 or length >100:
                self.generator_result.config(text="Длина от 1 до 100")
                return
        except ValueError:
            self.generator_result.config(text="Введите число")
            return
        chars = string.ascii_letters + string.digits
        result = ''.join(random.choice(chars) for _ in range(length))
        self.generator_result.config(text=result)

    def create_clicker_tab(self, frame):
        self.clicker_score_label = tk.Label(frame, text="Очки: 0", font=("Segoe UI", 18, "bold"),
                                            bg='#2b5a2b', fg='#a0d6a0')
        self.clicker_score_label.pack(pady=10)
        self.clicker_btn = tk.Button(frame, text="🍄 Клик!", font=("Segoe UI", 16, "bold"),
                                     bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                                     relief='raised', bd=3, width=12, height=2,
                                     command=self.clicker_click)
        self.clicker_btn.pack(pady=5)
        self.clicker_btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.clicker_info_label = tk.Label(frame, text="Клик даёт: 1", bg='#2b5a2b', fg='#c0e0c0')
        self.clicker_info_label.pack(pady=2)
        self.clicker_upgrade_btn = tk.Button(frame, text=f"Улучшить клик (стоимость: {self.clicker_upgrade_cost})",
                                             font=("Segoe UI", 12), bg='#3a7a3a', fg='White',
                                             activebackground='#4a8a4a', relief='raised', bd=2,
                                             command=self.clicker_upgrade)
        self.clicker_upgrade_btn.pack(pady=3)
        self.clicker_upgrade_btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.clicker_auto_label = tk.Label(frame, text="Авто-доход: 0/сек", bg='#2b5a2b', fg='#c0e0c0')
        self.clicker_auto_label.pack(pady=2)
        self.clicker_auto_btn = tk.Button(frame, text=f"Купить авто-клик (стоимость: {self.clicker_auto_cost})",
                                          font=("Segoe UI", 12), bg='#3a7a3a', fg='White',
                                          activebackground='#4a8a4a', relief='raised', bd=2,
                                          command=self.clicker_buy_auto)
        self.clicker_auto_btn.pack(pady=3)
        self.clicker_auto_btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.clicker_prestige_label = tk.Label(frame, text="Множитель престижа: x1",
                                               bg='#2b5a2b', fg='#c0e0c0')
        self.clicker_prestige_label.pack(pady=2)
        self.clicker_prestige_btn = tk.Button(frame, text=f"Престиж (сброс, множитель +1) - нужно {self.clicker_prestige_cost}",
                                              font=("Segoe UI", 12), bg='#3a7a3a', fg='White',
                                              activebackground='#4a8a4a', relief='raised', bd=2,
                                              command=self.clicker_prestige)
        self.clicker_prestige_btn.pack(pady=3)
        self.clicker_prestige_btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.daily_bonus_btn = tk.Button(frame, text="Ежедневный бонус (+100)",
                                         font=("Segoe UI", 12), bg='#3a7a3a', fg='White',
                                         activebackground='#4a8a4a', relief='raised', bd=2,
                                         command=self.clicker_daily_bonus)
        self.daily_bonus_btn.pack(pady=3)
        self.daily_bonus_btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.clicker_inv_label = tk.Label(frame, text="Инвентарь: пусто", bg='#2b5a2b',
                                          fg='#c0e0c0', justify='left')
        self.clicker_inv_label.pack(pady=5)
        btn_sell = tk.Button(frame, text="Продать все предметы", font=("Segoe UI", 12),
                             bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                             relief='raised', bd=2, command=self.clicker_sell_all)
        btn_sell.pack(pady=3)
        btn_sell.bind("<Button-1>", lambda e: self.app.play_click())
        self.clicker_after_id = self.after(1000, self.clicker_tick)

    def clicker_daily_bonus(self):
        if self.daily_bonus_available:
            self.clicker_score += 100
            self.daily_bonus_available = False
            if hasattr(self,'daily_bonus_btn'):
                self.daily_bonus_btn.config(state='disabled', text="Бонус получен")
            self.update_clicker_ui()
            self.after(60000, self.reset_daily_bonus)
            self.notify("Бонус", "Вы получили ежедневный бонус +100 очков!")
        else:
            messagebox.showinfo("Бонус", "Ежедневный бонус уже использован. Подождите минуту.")

    def reset_daily_bonus(self):
        # Окно могло быть закрыто к моменту срабатывания таймера
        if not self.winfo_exists():
            return
        self.daily_bonus_available = True
        if hasattr(self,'daily_bonus_btn'):
            self.daily_bonus_btn.config(state='normal', text="Ежедневный бонус (+100)")

    def clicker_click(self):
        if hasattr(self,'clicker_btn'):
            self.clicker_btn.config(relief='sunken')
            self.after(100, lambda: self.clicker_btn.config(relief='raised'))
        multiplier = self.clicker_prestige_multiplier
        if self.subscription.is_active():
            multiplier *= 2
        self.clicker_score += self.clicker_click_power * multiplier
        if random.random() < 0.05:
            item = self.generate_clicker_item()
            self.clicker_inventory.append(item)
            self.update_clicker_inventory()
        self.update_clicker_ui()
        self.update_quest_progress("clicker_clicks", 1)
        self.update_quest_progress("clicker_score_reach")

    def generate_clicker_item(self):
        items = [{"name":"Золотой мох","value":50,"rarity":"rare"},
                 {"name":"Кристалл мха","value":200,"rarity":"epic"},
                 {"name":"Легендарный лист","value":1000,"rarity":"legendary"},
                 {"name":"Обычный пучок","value":10,"rarity":"common"}]
        weights = [0.4,0.3,0.1,0.2]
        return random.choices(items, weights=weights, k=1)[0]

    def update_clicker_inventory(self):
        if not hasattr(self,'clicker_inv_label'): return
        counts = {}
        for item in self.clicker_inventory:
            counts[item['name']] = counts.get(item['name'],0)+1
        text = "Инвентарь:\n" + "\n".join(f"{name}: {cnt}" for name,cnt in counts.items())
        if not counts: text = "Инвентарь: пусто"
        self.clicker_inv_label.config(text=text)

    def clicker_sell_all(self):
        total = sum(item['value'] for item in self.clicker_inventory)
        self.clicker_score += total
        self.clicker_inventory.clear()
        self.update_clicker_inventory()
        self.update_clicker_ui()
        messagebox.showinfo("Продажа", f"Продано предметов на {total} очков!")

    def clicker_upgrade(self):
        if self.clicker_score >= self.clicker_upgrade_cost:
            self.clicker_score -= self.clicker_upgrade_cost
            self.clicker_click_power += 1
            self.clicker_upgrade_cost = int(self.clicker_upgrade_cost * 1.5)
            if hasattr(self,'clicker_upgrade_btn'):
                self.clicker_upgrade_btn.config(text=f"Улучшить клик (стоимость: {self.clicker_upgrade_cost})")
            self.update_clicker_ui()

    def clicker_buy_auto(self):
        if self.clicker_score >= self.clicker_auto_cost:
            self.clicker_score -= self.clicker_auto_cost
            self.clicker_auto_income += 1
            self.clicker_auto_cost = int(self.clicker_auto_cost * 1.8)
            if hasattr(self,'clicker_auto_btn'):
                self.clicker_auto_btn.config(text=f"Купить авто-клик (стоимость: {self.clicker_auto_cost})")
            self.update_clicker_ui()

    def clicker_prestige(self):
        if self.clicker_score >= self.clicker_prestige_cost:
            self.clicker_prestige_multiplier += 1
            self.clicker_score = 0
            self.clicker_click_power = 1
            self.clicker_auto_income = 0
            self.clicker_upgrade_cost = 10
            self.clicker_auto_cost = 50
            self.clicker_prestige_cost = int(self.clicker_prestige_cost * 2)
            self.clicker_inventory.clear()
            if hasattr(self,'clicker_upgrade_btn'):
                self.clicker_upgrade_btn.config(text=f"Улучшить клик (стоимость: {self.clicker_upgrade_cost})")
            if hasattr(self,'clicker_auto_btn'):
                self.clicker_auto_btn.config(text=f"Купить авто-клик (стоимость: {self.clicker_auto_cost})")
            if hasattr(self,'clicker_prestige_btn'):
                self.clicker_prestige_btn.config(text=f"Престиж (сброс, множитель +1) - нужно {self.clicker_prestige_cost}")
            self.update_clicker_inventory()
            self.update_clicker_ui()

    def update_clicker_ui(self):
        if not hasattr(self,'clicker_score_label'): return
        self.clicker_score_label.config(text=f"Очки: {int(self.clicker_score)}")
        multiplier = self.clicker_prestige_multiplier
        if self.subscription.is_active():
            multiplier *= 2
        self.clicker_info_label.config(text=f"Клик даёт: {self.clicker_click_power * multiplier}")
        auto = self.clicker_auto_income * multiplier
        self.clicker_auto_label.config(text=f"Авто-доход: {auto}/сек")
        self.clicker_prestige_label.config(text=f"Множитель престижа: x{self.clicker_prestige_multiplier}")

    def clicker_tick(self):
        if not self.winfo_exists(): return
        multiplier = self.clicker_prestige_multiplier
        if self.subscription.is_active():
            multiplier *= 2
        self.clicker_score += self.clicker_auto_income * multiplier
        self.update_clicker_ui()
        self.update_quest_progress("clicker_score_reach")
        self.clicker_after_id = self.after(1000, self.clicker_tick)

    def create_cards_tab(self, frame):
        self.cards_score_label = tk.Label(frame, text="Очки: 0", font=("Segoe UI", 18, "bold"),
                                          bg='#2b5a2b', fg='#a0d6a0')
        self.cards_score_label.pack(pady=10)
        self.cards_btn = tk.Button(frame, text="🃏 Открыть карточку", font=("Segoe UI", 16, "bold"),
                                   bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                                   relief='raised', bd=3, width=16, height=2,
                                   command=self.open_card)
        self.cards_btn.pack(pady=5)
        self.cards_btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.cards_info_label = tk.Label(frame, text="Кулдаун: 3 сек.", bg='#2b5a2b', fg='#c0e0c0')
        self.cards_info_label.pack(pady=2)
        self.cards_result_label = tk.Label(frame, text="", font=("Segoe UI", 14),
                                           bg='#2b5a2b', fg='#a0d6a0', wraplength=500)
        self.cards_result_label.pack(pady=10)
        self.cards_upgrade_rare_btn = tk.Button(frame, text=f"Улучшить шанс редкой (стоимость: {self.cards_upgrade_rare_cost})",
                                                font=("Segoe UI", 12), bg='#3a7a3a', fg='White',
                                                activebackground='#4a8a4a', relief='raised', bd=2,
                                                command=self.cards_upgrade_rare)
        self.cards_upgrade_rare_btn.pack(pady=3)
        self.cards_upgrade_rare_btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.cards_upgrade_cooldown_btn = tk.Button(frame, text=f"Уменьшить кулдаун (стоимость: {self.cards_upgrade_cooldown_cost})",
                                                    font=("Segoe UI", 12), bg='#3a7a3a', fg='White',
                                                    activebackground='#4a8a4a', relief='raised', bd=2,
                                                    command=self.cards_upgrade_cooldown)
        self.cards_upgrade_cooldown_btn.pack(pady=3)
        self.cards_upgrade_cooldown_btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.cards_inv_label = tk.Label(frame, text="Инвентарь карточек: пусто", bg='#2b5a2b',
                                        fg='#c0e0c0', justify='left')
        self.cards_inv_label.pack(pady=5)
        btn_col = tk.Button(frame, text="📚 Коллекция", font=("Segoe UI", 12),
                            bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                            relief='raised', bd=2, command=self.show_cards_collection)
        btn_col.pack(pady=3)
        btn_col.bind("<Button-1>", lambda e: self.app.play_click())
        btn_sell = tk.Button(frame, text="Продать все карточки", font=("Segoe UI", 12),
                             bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                             relief='raised', bd=2, command=self.cards_sell_all)
        btn_sell.pack(pady=3)
        btn_sell.bind("<Button-1>", lambda e: self.app.play_click())

    # ---- НОВЫЕ МЕТОДЫ КАРТОЧЕК (v0.2.5) ----
    def open_card(self):
        if self.cards_cooldown_active:
            self.cards_result_label.config(text="Подождите, кулдаун активен!")
            return
        if hasattr(self,'cards_btn'):
            self.cards_btn.config(relief='sunken')
            self.after(100, lambda: self.cards_btn.config(relief='raised'))

        rare_chance = self.cards_rare_chance
        if self.subscription.is_active():
            rare_chance += 0.05
        rand = random.random()
        
        if rand < rare_chance:
            rarity, points, color_bg, color_fg = "rare", 20, '#4a8a4a', 'White'
            names = ["Золотой мох", "Серебряный мох", "Мох-самоцвет", "Янтарный мох"]
        elif rand < rare_chance + 0.02:
            rarity, points, color_bg, color_fg = "epic", 80, 'Purple', 'White'
            names = ["Изумрудный мох", "Кристалл мха", "Мох-звезда", "Сапфировый мох"]
        elif rand < rare_chance + 0.02 + 0.005:
            rarity, points, color_bg, color_fg = "legendary", 300, 'Gold', 'Black'
            names = ["Древний мох", "Мох-дракон", "Легендарный лист", "Мох бессмертия"]
        elif rand < rare_chance + 0.02 + 0.005 + 0.002:
            rarity, points, color_bg, color_fg = "fire", 1000, 'OrangeRed', 'White'
            names = ["Огненный мох", "Пламенный мох", "Вулканический мох"]
        else:
            rarity, points, color_bg, color_fg = "common", 5, '#2a4a2a', '#c0e0c0'
            names = ["Мшистый камень", "Лист мха", "Пучок мха", "Моховая подушка", "Лесной мох"]

        name = random.choice(names)
        index = random.randint(1, 100)
        card = {
            "rarity": rarity,
            "points": points,
            "color_bg": color_bg,
            "color_fg": color_fg,
            "index": index,
            "name": name
        }
        self.cards_inventory.append(card)
        self.cards_score += points

        msg = f"💎 Редкость: {rarity}\n💫 Очки: +{points} (общ. {self.cards_score})"
        self.cards_score_label.config(text=f"Очки: {self.cards_score}")
        self.cards_result_label.config(text=msg, bg=color_bg, fg=color_fg)
        self.update_cards_inventory()
        self.update_quest_progress("cards_opened", 1)
        self.update_quest_progress("cards_rare_collect")
        if self.cards_collection_window is not None and self.cards_collection_window.winfo_exists():
            self.cards_collection_window.destroy()
            self.show_cards_collection()
        self.cards_cooldown_active = True
        if hasattr(self,'cards_btn'):
            self.cards_btn.config(state='disabled')
        self.cards_cooldown_remaining = self.cards_cooldown
        self.cards_cooldown_after_id = self.after(1000, self.cards_cooldown_tick)

    def update_cards_inventory(self):
        if not hasattr(self,'cards_inv_label'):
            return
        counts = {}
        for card in self.cards_inventory:
            name = card.get("name", card['rarity'])
            counts[name] = counts.get(name, 0) + 1
        text = "Инвентарь:\n" + "\n".join(f"{name}: {cnt}" for name, cnt in counts.items())
        if not counts:
            text = "Инвентарь карточек: пусто"
        self.cards_inv_label.config(text=text)

    def show_cards_collection(self):
        if self.cards_collection_window is not None and self.cards_collection_window.winfo_exists():
            self.cards_collection_window.lift()
            return
        win = tk.Toplevel(self)
        win.title("Коллекция карточек")
        win.geometry("600x400")
        win.configure(bg='#2b5a2b')
        self.cards_collection_window = win

        all_cards = []
        for i in range(1, 101):
            if i % 50 == 0:
                rarity = "legendary"
            elif i % 20 == 0:
                rarity = "epic"
            elif i % 10 == 0:
                rarity = "rare"
            else:
                rarity = "common"
            all_cards.append({"index": i, "rarity": rarity})

        canvas = tk.Canvas(win, bg='#2b5a2b')
        scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2b5a2b')
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row, col = 0, 0
        for card in all_cards:
            idx = card["index"]
            rarity = card["rarity"]
            owned = None
            for c in self.cards_inventory:
                if c["index"] == idx:
                    owned = c
                    break
            obtained = owned is not None
            bg_color = "#2a4a2a" if not obtained else "#4a8a4a"
            fg_color = "#666" if not obtained else "#fff"
            if obtained and owned:
                display = owned.get("name", f"#{idx}")[:8] + ("…" if len(owned.get("name", "")) > 8 else "")
            else:
                display = f"#{idx}"
            btn = tk.Button(
                scrollable_frame,
                text=display,
                bg=bg_color,
                fg=fg_color,
                width=8,
                height=3,
                relief="flat",
                bd=0,
                command=lambda i=idx, r=rarity, o=owned: messagebox.showinfo(
                    "Карточка",
                    f"Карточка #{i} ({r})" + (f"\nНазвание: {o.get('name', '')}" if o else "")
                )
            )
            btn.grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col >= 10:
                col = 0
                row += 1

    # ---- ОСТАЛЬНЫЕ МЕТОДЫ (продолжение) ----
    def cards_cooldown_tick(self):
        if not self.winfo_exists(): return
        if self.cards_cooldown_remaining > 0:
            if hasattr(self,'cards_info_label'):
                self.cards_info_label.config(text=f"Кулдаун: {self.cards_cooldown_remaining} сек.")
            self.cards_cooldown_remaining -= 1
            self.cards_cooldown_after_id = self.after(1000, self.cards_cooldown_tick)
        else:
            self.cards_cooldown_active = False
            if hasattr(self,'cards_btn'): self.cards_btn.config(state='normal')
            if hasattr(self,'cards_info_label'):
                self.cards_info_label.config(text=f"Кулдаун: {self.cards_cooldown} сек.")

    def cards_upgrade_rare(self):
        if self.cards_score >= self.cards_upgrade_rare_cost:
            self.cards_score -= self.cards_upgrade_rare_cost
            self.cards_rare_chance += 0.01
            if self.cards_rare_chance > 0.5: self.cards_rare_chance = 0.5
            self.cards_upgrade_rare_cost = int(self.cards_upgrade_rare_cost * 1.5)
            self.cards_score_label.config(text=f"Очки: {self.cards_score}")
            self.cards_result_label.config(text=f"Шанс редкой увеличен до {self.cards_rare_chance:.2f}")
            if hasattr(self,'cards_upgrade_rare_btn'):
                self.cards_upgrade_rare_btn.config(text=f"Улучшить шанс редкой (стоимость: {self.cards_upgrade_rare_cost})")

    def cards_upgrade_cooldown(self):
        if self.cards_score >= self.cards_upgrade_cooldown_cost:
            self.cards_score -= self.cards_upgrade_cooldown_cost
            self.cards_cooldown = max(1, self.cards_cooldown - 1)
            self.cards_upgrade_cooldown_cost = int(self.cards_upgrade_cooldown_cost * 1.8)
            self.cards_score_label.config(text=f"Очки: {self.cards_score}")
            self.cards_info_label.config(text=f"Кулдаун: {self.cards_cooldown} сек.")
            self.cards_result_label.config(text=f"Кулдаун уменьшен до {self.cards_cooldown} сек.")
            if hasattr(self,'cards_upgrade_cooldown_btn'):
                self.cards_upgrade_cooldown_btn.config(text=f"Уменьшить кулдаун (стоимость: {self.cards_upgrade_cooldown_cost})")

    def cards_sell_all(self):
        total = sum(card['points'] for card in self.cards_inventory)
        self.cards_score += total
        self.cards_inventory.clear()
        self.update_cards_inventory()
        self.cards_score_label.config(text=f"Очки: {self.cards_score}")
        messagebox.showinfo("Продажа", f"Продано карточек на {total} очков!")

    def create_casino_tab(self, frame):
        self.casino_balance_label = tk.Label(frame, text="Баланс: 0", font=("Segoe UI", 18, "bold"),
                                             bg='#2b5a2b', fg='#a0d6a0')
        self.casino_balance_label.pack(pady=10)
        tk.Label(frame, text="Ставка:", bg='#2b5a2b', fg='#c0e0c0').pack()
        self.casino_bet_entry = tk.Entry(frame, font=("Segoe UI", 12), bg='#3a7a3a',
                                         fg='White', insertbackground='White', relief='sunken', bd=2)
        self.casino_bet_entry.pack(pady=5)
        self.casino_bet_entry.insert(0, "10")
        self.casino_mode = tk.StringVar(value="number")
        for text,val in [("Число 1-10","number"),("Смайлик","emoji"),("Цвет","color")]:
            tk.Radiobutton(frame, text=text, variable=self.casino_mode,
                           value=val, bg='#2b5a2b', fg='#c0e0c0',
                           activebackground='#2b5a2b', selectcolor='#3a7a3a').pack()
        self.casino_choice_label = tk.Label(frame, text="Выбери число (1-10):", bg='#2b5a2b', fg='#c0e0c0')
        self.casino_choice_label.pack(pady=2)
        self.casino_choice_entry = tk.Entry(frame, font=("Segoe UI", 12), bg='#3a7a3a',
                                            fg='White', insertbackground='White', relief='sunken', bd=2)
        self.casino_choice_entry.pack(pady=5)
        btn = tk.Button(frame, text="🎰 Играть!", font=("Segoe UI", 16, "bold"),
                        bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                        relief='raised', bd=3, command=self.casino_play)
        btn.pack(pady=10)
        btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.casino_result_label = tk.Label(frame, text="", font=("Segoe UI", 14),
                                            bg='#2b5a2b', fg='#a0d6a0', wraplength=500)
        self.casino_result_label.pack(pady=10)
        btn2 = tk.Button(frame, text="Обменять 100 очков кликера -> 100 фишек",
                         font=("Segoe UI", 12), bg='#3a7a3a', fg='White',
                         activebackground='#4a8a4a', relief='raised', bd=2,
                         command=self.exchange_clicker_to_casino)
        btn2.pack(pady=5)
        btn2.bind("<Button-1>", lambda e: self.app.play_click())
        self.casino_mode.trace('w', lambda *args: self.update_casino_choice_ui())

    def update_casino_choice_ui(self):
        mode = self.casino_mode.get()
        if mode == "number":
            self.casino_choice_label.config(text="Выбери число (1-10):")
            self.casino_choice_entry.delete(0, tk.END)
            self.casino_choice_entry.insert(0, "5")
        elif mode == "emoji":
            self.casino_choice_label.config(text="Выбери смайлик (🍀, 🌟, 🍄, 💎, 🎲):")
            self.casino_choice_entry.delete(0, tk.END)
            self.casino_choice_entry.insert(0, "🍀")
        else:
            self.casino_choice_label.config(text="Выбери цвет (красный, черный, зеленый):")
            self.casino_choice_entry.delete(0, tk.END)
            self.casino_choice_entry.insert(0, "красный")

    def exchange_clicker_to_casino(self):
        if self.clicker_score >= 100:
            self.clicker_score -= 100
            self.casino_balance += 100
            self.update_clicker_ui()
            self.casino_balance_label.config(text=f"Баланс: {self.casino_balance}")
            self.casino_result_label.config(text="Обменяно 100 очков кликера на 100 фишек.")
        else:
            self.casino_result_label.config(text="Недостаточно очков кликера (нужно 100).")

    def casino_play(self):
        try:
            bet = int(self.casino_bet_entry.get())
            if bet <= 0: self.casino_result_label.config(text="Ставка должна быть положительной!"); return
            if bet > self.casino_balance: self.casino_result_label.config(text="Недостаточно средств!"); return
        except ValueError:
            self.casino_result_label.config(text="Введите число для ставки!"); return
        mode = self.casino_mode.get()
        choice = self.casino_choice_entry.get().strip().lower()

        if mode == "number":
            try:
                choice_num = int(choice)
                if choice_num <1 or choice_num >10:
                    self.casino_result_label.config(text="Число должно быть от 1 до 10!"); return
            except ValueError:
                self.casino_result_label.config(text="Введите число!"); return
            result_num = random.randint(1,10)
            if result_num == choice_num:
                win = bet * 9
                self.casino_balance += win
                self.casino_result_label.config(text=f"Выпало {result_num}! Вы угадали! Выигрыш: {win}")
                self.notify("Казино", f"Вы выиграли {win} фишек (угадали число {result_num})")
            else:
                self.casino_balance -= bet
                self.casino_result_label.config(text=f"Выпало {result_num}. Вы проиграли ставку {bet}.")
        elif mode == "emoji":
            emojis = ["🍀","🌟","🍄","💎","🎲"]
            if choice not in emojis:
                self.casino_result_label.config(text="Выберите один из: " + ", ".join(emojis)); return
            result_emoji = random.choice(emojis)
            if result_emoji == choice:
                win = bet * 5
                self.casino_balance += win
                self.casino_result_label.config(text=f"Выпало {result_emoji}! Вы угадали! Выигрыш: {win}")
                self.notify("Казино", f"Вы выиграли {win} фишек (угадали эмодзи)")
            else:
                self.casino_balance -= bet
                self.casino_result_label.config(text=f"Выпало {result_emoji}. Вы проиграли ставку {bet}.")
        else:
            colors = ["красный", "черный", "зеленый"]
            if choice not in colors:
                self.casino_result_label.config(text="Выберите цвет: красный, черный или зеленый")
                return
            r = random.random()
            if r < 0.45: result_color = "красный"
            elif r < 0.90: result_color = "черный"
            else: result_color = "зеленый"
            if result_color == choice:
                if choice == "зеленый":
                    win = bet * 4
                else:
                    win = bet * 2
                self.casino_balance += win
                self.casino_result_label.config(text=f"Выпал {result_color}! Вы угадали! Выигрыш: {win}")
                self.notify("Казино", f"Вы выиграли {win} фишек (угадали цвет {result_color})")
                self.update_quest_progress("casino_color_wins", 1)
            else:
                self.casino_balance -= bet
                self.casino_result_label.config(text=f"Выпал {result_color}. Вы проиграли ставку {bet}.")
        self.casino_balance_label.config(text=f"Баланс: {self.casino_balance}")
        self.update_quest_progress("casino_plays", 1)

    def create_ultrakill_tab(self, frame):
        tk.Label(frame, text="Генератор врагов ULTRAKILL", font=("Segoe UI", 16, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        self.ultrakill_category = tk.IntVar(value=-1)
        for text,val in [("Случайная категория",-1),("0 — Боссы (одиночные)",0),
                         ("1 — Много (5-10)",1),("2 — Меньше (3-5)",2),
                         ("3 — От 1 до 3",3),("4 — От 1 до 2",4)]:
            tk.Radiobutton(frame, text=text, variable=self.ultrakill_category,
                           value=val, bg='#2b5a2b', fg='#c0e0c0',
                           activebackground='#2b5a2b', selectcolor='#3a7a3a').pack(anchor='w')
        btn = tk.Button(frame, text="⚔️ Сгенерировать", font=("Segoe UI", 14, "bold"),
                        bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                        relief='raised', bd=3, command=self.generate_ultrakill)
        btn.pack(pady=10)
        btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.ultrakill_result = tk.Label(frame, text="", font=("Segoe UI", 14),
                                         bg='#2b5a2b', fg='#a0d6a0', justify='left')
        self.ultrakill_result.pack(pady=10)

    def generate_ultrakill(self):
        cat = self.ultrakill_category.get()
        if cat == -1: cat = random.choice([0,1,2,3,4])
        enemies = self.ultrakill_categories[cat]
        min_c, max_c = self.ultrakill_count_rules[cat]
        count = random.randint(min_c, max_c)
        chosen = random.choice(enemies)
        if cat == 0: text = f"Враг: {chosen}\nКоличество: 1 (босс)"
        else: text = f"Враг: {chosen}\nКоличество: {count}"
        self.ultrakill_result.config(text=text)

    def create_ai_tab(self, frame):
        tk.Label(frame, text="MinOS Assistant", font=("Segoe UI", 16, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        self.ai_output = tk.Text(frame, height=10, width=60, bg='#2b5a2b', fg='#c0e0c0',
                                 font=("Segoe UI", 12), state='disabled')
        self.ai_output.pack(padx=5, pady=5)
        self.ai_entry = tk.Entry(frame, font=("Segoe UI", 12), bg='#3a7a3a',
                                 fg='White', insertbackground='White', relief='sunken', bd=2)
        self.ai_entry.pack(fill=tk.X, padx=5, pady=5)
        self.ai_entry.bind("<Return>", self.ai_process)
        self.ai_entry.focus()
        self.ai_print("Привет! Я ассистент MinOS. Спроси меня о чём-нибудь.")

    def ai_print(self, text):
        self.ai_output.configure(state='normal')
        self.ai_output.insert(tk.END, text + "\n")
        self.ai_output.see(tk.END)
        self.ai_output.configure(state='disabled')

    def ai_process(self, event=None):
        user_input = self.ai_entry.get().strip().lower()
        self.ai_entry.delete(0, tk.END)
        if not user_input: return
        self.ai_print(f"Вы: {user_input}")
        response = self.get_ai_response(user_input)
        self.ai_print(f"Ассистент: {response}")

    def get_ai_response(self, text):
        if "привет" in text or "hello" in text or "hi" in text:
            return "Привет! Рад тебя видеть. Чем могу помочь?"
        elif "как дела" in text or "как ты" in text:
            return "У меня всё отлично, я же программа. А у тебя?"
        elif "что ты умеешь" in text or "помощь" in text or "help" in text:
            return "Я могу отвечать на вопросы, открывать приложения, давать советы по мху, рассказывать о погоде (сейчас везде зелено) и многое другое. Теперь я могу показывать уведомления!"
        elif "калькулятор дат" in text or "datecalc" in text: self.switch_to_tab(TABS["datecalc"]); return "Открываю калькулятор дат."
        elif "калькулятор" in text: self.switch_to_tab(TABS["calc"]); return "Открываю калькулятор."
        elif "блокнот" in text: self.switch_to_tab(TABS["notepad"]); return "Открываю блокнот."
        elif "игра" in text: self.switch_to_tab(TABS["game"]); return "Открываю игру."
        elif "перевод" in text: self.switch_to_tab(TABS["translator"]); return "Открываю переводчик."
        elif "генератор" in text: self.switch_to_tab(TABS["generator"]); return "Открываю генератор."
        elif "кликер" in text: self.switch_to_tab(TABS["clicker"]); return "Открываю кликер."
        elif "карточк" in text: self.switch_to_tab(TABS["cards"]); return "Открываю карточки."
        elif "казино" in text: self.switch_to_tab(TABS["casino"]); return "Открываю казино."
        elif "ультракилл" in text: self.switch_to_tab(TABS["ultrakill"]); return "Открываю ULTRAKILL."
        elif "питомец" in text: self.switch_to_tab(TABS["pet"]); return "Открываю питомца (мох)."
        elif "игры" in text: self.switch_to_tab(TABS["games"]); return "Открываю игры."
        elif "интернет" in text: self.switch_to_tab(TABS["internet"]); return "Открываю интернет."
        elif "загрузки" in text: self.switch_to_tab(TABS["downloads"]); return "Открываю загрузки."
        elif "шифр" in text: self.switch_to_tab(TABS["cipher"]); return "Открываю шифратор."
        elif "ссылки" in text: self.switch_to_tab(TABS["links"]); return "Открываю ссылки."
        elif "настройки" in text: self.switch_to_tab(TABS["settings"]); return "Открываю настройки."
        elif "задания" in text: self.switch_to_tab(TABS["quests"]); return "Открываю задания."
        elif "поиск" in text: self.switch_to_tab(TABS["search"]); return "Открываю поиск."
        elif "календарь" in text: self.switch_to_tab(TABS["calendar"]); return "Открываю календарь."
        elif "рисование" in text: self.switch_to_tab(TABS["paint"]); return "Открываю рисование."
        elif "змейка" in text: self.switch_to_tab(TABS["snake"]); return "Открываю змейку."
        elif "будильник" in text: self.switch_to_tab(TABS["alarm"]); return "Открываю будильник."
        elif "система" in text: self.switch_to_tab(TABS["system"]); return "Открываю системную информацию."
        elif "диск" in text: self.switch_to_tab(TABS["disk"]); return "Открываю диск."
        elif "сапёр" in text or "minesweeper" in text: self.switch_to_tab(TABS["minesweeper"]); return "Открываю сапёр."
        elif "диспетчер" in text or "taskmanager" in text: self.switch_to_tab(TABS["taskmanager"]); return "Открываю диспетчер задач."
        elif "браузер" in text or "browser" in text: self.switch_to_tab(TABS["browser"]); return "Открываю браузер."
        elif "ченджлог" in text or "changelog" in text: self.switch_to_tab(TABS["changelog"]); return "Открываю ченджлог."
        elif "подписка" in text or "премиум" in text: self.switch_to_tab(TABS["subscription"]); return "Открываю подписку."
        elif "плеер" in text or "музык" in text: self.switch_to_tab(TABS["player"]); return "Открываю плеер."
        elif "мох" in text: return "Мох — это прекрасно! Зелёный, пушистый, как интерфейс MinOS. Кстати, в игре на цвет зелёный даёт х4!"
        elif "погода" in text: return "Сегодня везде зелено и солнечно. Идеально для выращивания мха!"
        elif "пока" in text or "bye" in text: return "До встречи! Заходи ещё."
        else: return "Я ещё учусь, но скоро буду знать ответ на любой вопрос!"

    def create_pet_tab(self, frame):
        self.pet_emoji_label = tk.Label(frame, text="🌰", font=("Segoe UI", 56),
                                        bg='#2b5a2b', fg='#a0d6a0')
        self.pet_emoji_label.pack(pady=10)
        self.pet_stage_label = tk.Label(frame, text="Стадия: Семечко", font=("Segoe UI", 16, "bold"),
                                        bg='#2b5a2b', fg='#a0d6a0')
        self.pet_stage_label.pack(pady=5)
        self.pet_stats_label = tk.Label(frame, text="Влажность: 80%\nЗдоровье: 80%\nРост: 0%",
                                        font=("Segoe UI", 14), bg='#2b5a2b', fg='#c0e0c0')
        self.pet_stats_label.pack(pady=10)
        btn1 = tk.Button(frame, text="💧 Полить (+20 влажность, -5 здоровье, +5 рост)",
                         font=("Segoe UI", 12), bg='#3a7a3a', fg='White',
                         activebackground='#4a8a4a', relief='raised', bd=2,
                         command=self.pet_water)
        btn1.pack(pady=3)
        btn1.bind("<Button-1>", lambda e: self.app.play_click())
        btn2 = tk.Button(frame, text="🌿 Удобрить (+15 рост, -10 здоровье)",
                         font=("Segoe UI", 12), bg='#3a7a3a', fg='White',
                         activebackground='#4a8a4a', relief='raised', bd=2,
                         command=self.pet_fertilize)
        btn2.pack(pady=3)
        btn2.bind("<Button-1>", lambda e: self.app.play_click())
        btn3 = tk.Button(frame, text="☀️ На солнце (+10 рост, -15 влажность)",
                         font=("Segoe UI", 12), bg='#3a7a3a', fg='White',
                         activebackground='#4a8a4a', relief='raised', bd=2,
                         command=self.pet_sun)
        btn3.pack(pady=3)
        btn3.bind("<Button-1>", lambda e: self.app.play_click())
        btn4 = tk.Button(frame, text="🌙 В тень (+15 влажность, -10 рост)",
                         font=("Segoe UI", 12), bg='#3a7a3a', fg='White',
                         activebackground='#4a8a4a', relief='raised', bd=2,
                         command=self.pet_shade)
        btn4.pack(pady=3)
        btn4.bind("<Button-1>", lambda e: self.app.play_click())
        self.pet_message = tk.Label(frame, text="", font=("Segoe UI", 12),
                                    bg='#2b5a2b', fg='#a0d6a0')
        self.pet_message.pack(pady=5)
        self.pet_after_id = self.after(10000, self.pet_tick)
        self.update_pet_ui()

    def pet_water(self):
        self.pet_moisture = min(100, self.pet_moisture + 20)
        self.pet_health = max(0, self.pet_health - 5)
        self.pet_growth = min(100, self.pet_growth + 5)
        self.pet_care_points += 1
        self.pet_message.config(text="🌱 Вы полили мох! Он благодарен.")
        self.update_pet_ui()
        self.update_quest_progress("pet_water", 1)

    def pet_fertilize(self):
        self.pet_growth = min(100, self.pet_growth + 15)
        self.pet_health = max(0, self.pet_health - 10)
        self.pet_care_points += 1
        self.pet_message.config(text="🌿 Мох получил удобрение! Растёт быстрее.")
        self.update_pet_ui()

    def pet_sun(self):
        self.pet_growth = min(100, self.pet_growth + 10)
        self.pet_moisture = max(0, self.pet_moisture - 15)
        self.pet_care_points += 1
        self.pet_message.config(text="☀️ Мох наслаждается солнцем! Растёт.")
        self.update_pet_ui()

    def pet_shade(self):
        self.pet_moisture = min(100, self.pet_moisture + 15)
        self.pet_growth = max(0, self.pet_growth - 10)
        self.pet_care_points += 1
        self.pet_message.config(text="🌙 Мох отдыхает в тени. Влажность повышена.")
        self.update_pet_ui()

    def pet_tick(self):
        if not self.winfo_exists(): return
        self.pet_moisture = max(0, self.pet_moisture - 2)
        self.pet_health = max(0, self.pet_health - 1)
        if self.pet_moisture < 20 or self.pet_health < 20:
            self.pet_growth = max(0, self.pet_growth - 1)
        else:
            self.pet_growth = min(100, self.pet_growth + 1)
        self.update_pet_ui()
        self.pet_after_id = self.after(10000, self.pet_tick)

    def update_pet_ui(self):
        if not hasattr(self, 'pet_emoji_label'): return
        if self.pet_growth < 20:
            emoji = "🌰"
            stage_name = "Семечко"
        elif self.pet_growth < 40:
            emoji = "🌱"
            stage_name = "Росток"
        elif self.pet_growth < 60:
            emoji = "🌿"
            stage_name = "Мох"
        elif self.pet_growth < 80:
            emoji = "🌳"
            stage_name = "Куст"
        else:
            emoji = "🌸"
            stage_name = "Цветущий мох"
        if self.pet_health < 20 or self.pet_moisture < 15:
            emoji = "😢" + emoji
            stage_name += " (болеет)"
        self.pet_emoji_label.config(text=emoji)
        self.pet_stage_label.config(text=f"Стадия: {stage_name} ({self.pet_growth}%)")
        self.pet_stats_label.config(
            text=f"Влажность: {self.pet_moisture}%\nЗдоровье: {self.pet_health}%\nРост: {self.pet_growth}%"
        )

    def create_console_tab(self, frame):
        self.console_output = tk.Text(frame, wrap='word', bg='#2b5a2b', fg='#c0e0c0',
                                      insertbackground='White', font=("Consolas", 12),
                                      relief='flat', state='disabled')
        self.console_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5,0))
        self.console_entry = tk.Entry(frame, bg='#3a7a3a', fg='White',
                                      insertbackground='White', font=("Consolas", 12),
                                      relief='sunken', bd=2)
        self.console_entry.pack(fill=tk.X, padx=5, pady=5)
        self.console_entry.bind("<Return>", self.process_command)
        self.console_entry.focus()
        self.console_print(f"MinOS Console {self.app.VERSION}")
        self.console_print("Введите 'help' для списка команд.")

    def console_print(self, text):
        self.console_output.configure(state='normal')
        self.console_output.insert(tk.END, text + "\n")
        self.console_output.see(tk.END)
        self.console_output.configure(state='disabled')

    def process_command(self, event=None):
        cmd = self.console_entry.get().strip()
        self.console_entry.delete(0, tk.END)
        if not cmd: return
        self.console_print(f"> {cmd}")
        self._execute_command(cmd)

    def _execute_command(self, cmd):
        parts = cmd.split()
        if not parts: return
        command = parts[0].lower()
        args = parts[1:]
        if command == "help":
            self.console_print("Доступные команды: calc, notepad, game, translator, generator, clicker, cards, casino, ultrakill, ai, pet, apps, games, internet, downloads, cipher, links, settings, quests, search, calendar, paint, snake, alarm, system, disk, about, ad, start, pin [ключ], lock, shutdown, reboot, exit, clear, version, wallpaper [moss/grass/forest/dark], snake_bonus, cards_collection, minesweeper, taskmanager, browser, datecalc, changelog, subscription, player, notify [текст]")
        elif command == "calc": self.switch_to_tab(TABS["calc"])
        elif command == "notepad": self.switch_to_tab(TABS["notepad"])
        elif command == "game": self.switch_to_tab(TABS["game"])
        elif command == "translator": self.switch_to_tab(TABS["translator"])
        elif command == "generator": self.switch_to_tab(TABS["generator"])
        elif command == "clicker": self.switch_to_tab(TABS["clicker"])
        elif command == "cards": self.switch_to_tab(TABS["cards"])
        elif command == "casino": self.switch_to_tab(TABS["casino"])
        elif command == "ultrakill": self.switch_to_tab(TABS["ultrakill"])
        elif command == "ai": self.switch_to_tab(TABS["ai"])
        elif command == "pet": self.switch_to_tab(TABS["pet"])
        elif command == "apps": self.switch_to_tab(TABS["all"])
        elif command == "games": self.switch_to_tab(TABS["games"])
        elif command == "internet": self.switch_to_tab(TABS["internet"])
        elif command == "downloads": self.switch_to_tab(TABS["downloads"])
        elif command == "cipher": self.switch_to_tab(TABS["cipher"])
        elif command == "links": self.switch_to_tab(TABS["links"])
        elif command == "settings": self.switch_to_tab(TABS["settings"])
        elif command == "quests": self.switch_to_tab(TABS["quests"])
        elif command == "search": self.switch_to_tab(TABS["search"])
        elif command == "calendar": self.switch_to_tab(TABS["calendar"])
        elif command == "paint": self.switch_to_tab(TABS["paint"])
        elif command == "snake": self.switch_to_tab(TABS["snake"])
        elif command == "alarm": self.switch_to_tab(TABS["alarm"])
        elif command == "system": self.switch_to_tab(TABS["system"])
        elif command == "disk": self.switch_to_tab(TABS["disk"])
        elif command == "minesweeper": self.switch_to_tab(TABS["minesweeper"])
        elif command == "taskmanager": self.switch_to_tab(TABS["taskmanager"])
        elif command == "browser": self.switch_to_tab(TABS["browser"])
        elif command == "datecalc": self.switch_to_tab(TABS["datecalc"])
        elif command == "changelog": self.switch_to_tab(TABS["changelog"])
        elif command == "subscription": self.switch_to_tab(TABS["subscription"])
        elif command == "player": self.switch_to_tab(TABS["player"])
        elif command == "about": self.app.show_about()
        elif command == "ad": self.app.show_ad()
        elif command == "start": self.app.toggle_start_menu(); self.console_print("Меню Пуск переключено.")
        elif command == "pin":
            if args and args[0] in TABS:
                self.app.pin_app(args[0]); self.console_print(f"Закреплено: {args[0]}")
            else:
                self.console_print("Укажите ключ приложения: pin calc")
        elif command == "lock": self.app.lock_screen(); self.console_print("Экран заблокирован.")
        elif command == "shutdown": self.console_print("Выключение..."); self.after(500, self.app.shutdown)
        elif command == "reboot": self.console_print("Перезагрузка..."); self.after(500, self.app.reboot)
        elif command == "exit": self.close()
        elif command == "clear": self.console_output.configure(state='normal'); self.console_output.delete(1.0, tk.END); self.console_output.configure(state='disabled')
        elif command == "version": self.console_print(f"MinOS {self.app.VERSION}")
        elif command == "wallpaper":
            if len(args) == 0:
                self.console_print("Укажите тип обоев: wallpaper moss")
            else:
                wp = args[0]
                if wp in ["moss","grass","forest","dark"]:
                    self.app.set_wallpaper(wp)
                    self.console_print(f"Обои изменены на {wp}")
                else:
                    self.console_print("Доступные обои: moss, grass, forest, dark")
        elif command == "cards_collection":
            self.show_cards_collection()
        elif command == "snake_bonus":
            self.console_print("В змейке доступны бонусы: бессмертие, замедление, расширение карты, больше яблок.")
        elif command == "notify":
            if len(args) == 0:
                self.console_print("Укажите текст: notify 'ваш текст'")
            else:
                self.notify("Уведомление из консоли", " ".join(args))
                self.console_print("Уведомление отправлено")
        else:
            self.console_print(f"Неизвестная команда: {command}")

    def create_all_tab(self, frame):
        tk.Label(frame, text="🌿 Все приложения MinOS", font=("Segoe UI", 20, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=20)
        apps = [
            ("🧮 Калькулятор", "calc"), ("📝 Блокнот", "notepad"), ("🎲 Игра", "game"),
            ("🌐 Переводчик", "translator"), ("🔢 Генератор", "generator"), ("🍄 Кликер", "clicker"),
            ("🃏 Карточки", "cards"), ("🎰 Казино", "casino"), ("🩸 ULTRAKILL", "ultrakill"),
            ("🤖 ИИ", "ai"), ("🌱 Питомец", "pet"), ("💻 Консоль", "console"),
            ("📁 Игры", "games"), ("🌐 Интернет", "internet"), ("⬇️ Загрузки", "downloads"),
            ("🔐 Шифратор", "cipher"), ("🔗 Ссылки", "links"), ("⚙️ Настройки", "settings"),
            ("📜 Задания", "quests"), ("🔍 Поиск", "search"), ("📅 Календарь", "calendar"),
            ("🎨 Рисование", "paint"), ("🐍 Змейка", "snake"), ("⏰ Будильник", "alarm"),
            ("ℹ️ Система", "system"), ("💾 Диск", "disk"), ("💣 Сапёр", "minesweeper"),
            ("📊 Диспетчер задач", "taskmanager"), ("🌐 Браузер", "browser"),
            ("📆 Калькулятор дат", "datecalc"), ("📜 Ченджлог", "changelog"),
            ("💎 Подписка", "subscription"), ("🎵 Плеер", "player")
        ]
        btn_frame = tk.Frame(frame, bg='#2b5a2b')
        btn_frame.pack()
        for col in range(3):
            btn_frame.columnconfigure(col, weight=1)
        for i, (name, key) in enumerate(apps):
            btn = tk.Button(btn_frame, text=name, font=("Segoe UI", 12),
                            bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                            relief='raised', bd=2, width=22,
                            command=lambda k=key: self.switch_to_tab(TABS[k]))
            btn.grid(row=i // 3, column=i % 3, padx=4, pady=3)
            btn.bind("<Button-1>", lambda e: self.app.play_click())

    def create_games_tab(self, frame):
        tk.Label(frame, text="Игры", font=("Segoe UI", 20, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        games = [
            ("🎲 Угадай число", TABS["game"]),
            ("🍄 Кликер", TABS["clicker"]),
            ("🃏 Карточки", TABS["cards"]),
            ("🎰 Казино", TABS["casino"]),
            ("🩸 ULTRAKILL", TABS["ultrakill"]),
            ("🐍 Змейка", TABS["snake"]),
            ("💣 Сапёр", TABS["minesweeper"])
        ]
        for text, idx in games:
            btn = tk.Button(frame, text=text, font=("Segoe UI", 14),
                            bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                            relief='raised', bd=2, width=22,
                            command=lambda i=idx: self.switch_to_tab(i))
            btn.pack(pady=4)
            btn.bind("<Button-1>", lambda e: self.app.play_click())

    def create_internet_tab(self, frame):
        tk.Label(frame, text="Старая версия Интернета", font=("Segoe UI", 16, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        tk.Label(frame, text="Рекомендуем использовать новый Браузер", 
                 bg='#2b5a2b', fg='#c0e0c0').pack()
        btn = tk.Button(frame, text="Перейти в Браузер", command=lambda: self.switch_to_tab(TABS["browser"]),
                        bg='#3a7a3a', fg='white', relief='flat', bd=0)
        btn.pack(pady=10)
        btn.bind("<Button-1>", lambda e: self.app.play_click())

    def create_downloads_tab(self, frame):
        # ---------- ЗАГРУЗКИ ИЗ ИНТЕРНЕТА ----------
        net_label = tk.Label(frame, text="🌐 Загрузки из интернета", font=("Segoe UI", 14, "bold"),
                             bg='#2b5a2b', fg='#a0d6a0')
        net_label.pack(pady=(8, 2))
        url_frame = tk.Frame(frame, bg='#2b5a2b')
        url_frame.pack(fill=tk.X, padx=8)
        tk.Label(url_frame, text="URL:", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT)
        self.dl_url_entry = tk.Entry(url_frame, font=("Segoe UI", 11), bg='#3a7a3a',
                                     fg='White', insertbackground='White', relief='sunken', bd=2)
        self.dl_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, ipady=3)
        self.dl_url_entry.bind("<Return>", lambda e: self.dl_start())
        dl_btn = tk.Button(url_frame, text="⬇ Скачать", command=self.dl_start,
                           bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                           relief='raised', bd=1)
        dl_btn.pack(side=tk.LEFT, padx=2)
        dl_btn.bind("<Button-1>", lambda e: self.app.play_click())

        # Таблица загрузок: имя, размер, прогресс, статус
        columns = ("name", "size", "progress", "status")
        self.dl_tree = ttk.Treeview(frame, columns=columns, show="headings", height=6)
        self.dl_tree.heading("name", text="Файл")
        self.dl_tree.heading("size", text="Размер")
        self.dl_tree.heading("progress", text="Прогресс")
        self.dl_tree.heading("status", text="Статус")
        self.dl_tree.column("name", width=220)
        self.dl_tree.column("size", width=90, anchor="center")
        self.dl_tree.column("progress", width=90, anchor="center")
        self.dl_tree.column("status", width=110, anchor="center")
        self.dl_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Прогресс-бар выбранной загрузки + кнопки управления
        prog_frame = tk.Frame(frame, bg='#2b5a2b')
        prog_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        self.dl_progress = ttk.Progressbar(prog_frame, mode='determinate', maximum=100,
                                           style="green.Horizontal.TProgressbar")
        self.dl_progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.dl_progress_label = tk.Label(prog_frame, text="0%", bg='#2b5a2b', fg='#c0e0c0', width=6)
        self.dl_progress_label.pack(side=tk.LEFT, padx=6)
        for text, cmd in [("⏸ Пауза", self.dl_pause), ("▶ Продолжить", self.dl_resume),
                          ("✖ Отменить", self.dl_cancel), ("🗑 Очистить список", self.dl_clear_finished)]:
            b = tk.Button(prog_frame, text=text, command=cmd,
                          bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                          relief='raised', bd=1)
            b.pack(side=tk.LEFT, padx=2)
            b.bind("<Button-1>", lambda e: self.app.play_click())
        if not HAS_REQUESTS:
            tk.Label(frame, text="(requests не установлен — используется стандартный urllib)",
                     font=("Segoe UI", 8), bg='#2b5a2b', fg='#8aa88a').pack()
        self.dl_refresh_tree()
        self._downloads_ui_after = self.after(400, self._downloads_ui_tick)

        # ---------- ФАЙЛЫ MINOS (старая функция — виртуальные документы) ----------
        tk.Label(frame, text="📄 Файлы MinOS", font=("Segoe UI", 12, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=(8, 2))
        self.downloads_list = tk.Listbox(frame, bg='#3a7a3a', fg='White',
                                         font=("Segoe UI", 12), selectbackground='#4a8a4a', height=4)
        self.downloads_list.pack(fill=tk.BOTH, padx=5, pady=2)
        buttons_frame = tk.Frame(frame, bg='#2b5a2b')
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        for text, cmd in [("Открыть", self.open_download), ("Удалить", self.delete_download)]:
            btn = tk.Button(buttons_frame, text=text, command=cmd,
                            bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                            relief='raised', bd=1)
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind("<Button-1>", lambda e: self.app.play_click())
        self.update_downloads_list()

    # ---------- УПРАВЛЕНИЕ ЗАГРУЗКАМИ ИЗ ИНТЕРНЕТА ----------
    def dl_start(self):
        url = self.dl_url_entry.get().strip()
        if not url:
            self.notify("Загрузки", "Введите URL файла")
            return
        job = self.download_manager.start(url, on_update=self._schedule_dl_refresh)
        if job:
            self.dl_url_entry.delete(0, tk.END)
            self.dl_refresh_tree()
            self.notify("Загрузки", f"Начата загрузка: {job.name}")

    def _selected_job(self):
        sel = self.dl_tree.selection()
        if not sel:
            return None
        try:
            job_id = int(sel[0])
        except ValueError:
            return None
        for job in self.download_manager.jobs:
            if id(job) == job_id:
                return job
        return None

    def dl_pause(self):
        job = self._selected_job()
        if job:
            self.download_manager.pause(job)
            self.dl_refresh_tree()

    def dl_resume(self):
        job = self._selected_job()
        if job:
            self.download_manager.resume(job)
            self.dl_refresh_tree()

    def dl_cancel(self):
        job = self._selected_job()
        if job:
            self.download_manager.cancel(job)
            self.notify("Загрузки", f"Загрузка отменена: {job.name}")
            self.dl_refresh_tree()

    def dl_clear_finished(self):
        self.download_manager.jobs = [j for j in self.download_manager.jobs if not j.is_finished]
        self.dl_refresh_tree()

    def _schedule_dl_refresh(self):
        """Колбэк из потока загрузки — планируем обновление UI в главном потоке."""
        try:
            self.after(0, self.dl_refresh_tree)
        except Exception:
            pass

    def _downloads_ui_tick(self):
        """Периодическое обновление списка загрузок (страховка от пропусков).
        Обновляем только когда вкладка «Загрузки» перед глазами — без лишней работы."""
        if not self.winfo_exists():
            return
        try:
            if self.notebook.index(self.notebook.select()) == TABS["downloads"]:
                self.dl_refresh_tree()
        except Exception:
            pass
        self._downloads_ui_after = self.after(800, self._downloads_ui_tick)

    def dl_refresh_tree(self):
        if not hasattr(self, 'dl_tree') or not self.dl_tree.winfo_exists():
            return
        # delete() сбрасывает выделение — запоминаем и восстанавливаем его,
        # иначе кнопки «Пауза/Отмена» перестают работать после авто-обновления
        sel = self.dl_tree.selection()
        sel_iid = sel[0] if sel else None
        self.dl_tree.delete(*self.dl_tree.get_children())
        for job in self.download_manager.jobs:
            size_text = DownloadManager._format_size(job.downloaded)
            if job.total > 0:
                size_text += f" / {DownloadManager._format_size(job.total)}"
            progress = f"{job.progress:.0f}%" if job.total > 0 else "—"
            self.dl_tree.insert("", "end", iid=str(id(job)),
                                values=(job.name, size_text, progress, job.status))
        if sel_iid and self.dl_tree.exists(sel_iid):
            self.dl_tree.selection_set(sel_iid)
        # Обновляем прогресс-бар выбранной загрузки
        job = self._selected_job()
        if job is None:
            self.dl_progress['value'] = 0
            self.dl_progress_label.config(text="0%")
        else:
            self.dl_progress['value'] = job.progress
            self.dl_progress_label.config(text=f"{job.progress:.0f}%")

    def update_downloads_list(self):
        if not hasattr(self,'downloads_list'): return
        self.downloads_list.delete(0, tk.END)
        for file in self.downloads:
            self.downloads_list.insert(tk.END, file["name"])

    def open_download(self):
        sel = self.downloads_list.curselection()
        if sel:
            idx = sel[0]
            file = self.downloads[idx]
            win = tk.Toplevel(self)
            win.title(file["name"])
            win.geometry("400x300")
            win.configure(bg='#2b5a2b')
            tk.Label(win, text=file["content"], font=("Segoe UI", 12),
                     bg='#2b5a2b', fg='#c0e0c0', justify='left').pack(padx=10, pady=10)

    def delete_download(self):
        sel = self.downloads_list.curselection()
        if sel:
            idx = sel[0]
            name = self.downloads[idx]["name"]
            if messagebox.askyesno("MinOS", f"Удалить '{name}'?"):
                del self.downloads[idx]
                self.update_downloads_list()

    def create_cipher_tab(self, frame):
        tk.Label(frame, text="Шифратор (Цезарь)", font=("Segoe UI", 16, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        tk.Label(frame, text="Сдвиг:", bg='#2b5a2b', fg='#c0e0c0').pack()
        shift_entry = tk.Entry(frame, textvariable=self.cipher_shift, font=("Segoe UI", 12),
                               bg='#3a7a3a', fg='White', insertbackground='White',
                               relief='sunken', bd=2, width=10)
        shift_entry.pack(pady=5)
        tk.Label(frame, text="Текст:", bg='#2b5a2b', fg='#c0e0c0').pack()
        self.cipher_input = tk.Text(frame, height=4, width=60, bg='#3a7a3a', fg='White',
                                    insertbackground='White', relief='sunken', bd=2)
        self.cipher_input.pack(pady=5)
        btn_frame = tk.Frame(frame, bg='#2b5a2b')
        btn_frame.pack(pady=5)
        for text, cmd in [("Зашифровать", self.cipher_encrypt), ("Дешифровать", self.cipher_decrypt)]:
            btn = tk.Button(btn_frame, text=text, command=cmd,
                            bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                            relief='raised', bd=2)
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Button-1>", lambda e: self.app.play_click())
        tk.Label(frame, text="Результат:", bg='#2b5a2b', fg='#c0e0c0').pack()
        self.cipher_output = tk.Text(frame, height=4, width=60, bg='#3a7a3a', fg='White',
                                     relief='sunken', bd=2, state='disabled')
        self.cipher_output.pack(pady=5)

    def cipher_encrypt(self): self.cipher_transform(encrypt=True)
    def cipher_decrypt(self): self.cipher_transform(encrypt=False)

    def cipher_transform(self, encrypt=True):
        try:
            shift = int(self.cipher_shift.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Сдвиг должен быть числом!"); return
        text = self.cipher_input.get("1.0", tk.END).strip()
        if not text: return
        result = []
        for ch in text:
            if ch.isalpha():
                base = ord('A') if ch.isupper() else ord('a')
                if encrypt:
                    new_ch = chr((ord(ch) - base + shift) % 26 + base)
                else:
                    new_ch = chr((ord(ch) - base - shift) % 26 + base)
                result.append(new_ch)
            else:
                result.append(ch)
        self.cipher_output.configure(state='normal')
        self.cipher_output.delete(1.0, tk.END)
        self.cipher_output.insert(tk.END, ''.join(result))
        self.cipher_output.configure(state='disabled')

    def create_links_tab(self, frame):
        tk.Label(frame, text="Полезные ссылки", font=("Segoe UI", 16, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        links = [("YouTube","https://youtube.com"), ("Roblox","https://roblox.com"),
                 ("GitHub","https://github.com"), ("Reddit","https://reddit.com")]
        for name, url in links:
            btn = tk.Button(frame, text=name, font=("Segoe UI", 14),
                            bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                            relief='raised', bd=2, width=20,
                            command=lambda u=url: webbrowser.open(u))
            btn.pack(pady=3)
            btn.bind("<Button-1>", lambda e: self.app.play_click())

    def create_settings_tab(self, frame):
        tk.Label(frame, text="Настройки", font=("Segoe UI", 16, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        # Тема
        tk.Label(frame, text="Тема оформления:", bg='#2b5a2b', fg='#c0e0c0').pack()
        theme_frame = tk.Frame(frame, bg='#2b5a2b')
        theme_frame.pack(pady=5)
        for theme_name in ["moss", "dark", "light", "cyber"]:
            rb = tk.Radiobutton(theme_frame, text=theme_name.capitalize(), variable=self.theme_var,
                                value=theme_name, bg='#2b5a2b', fg='#c0e0c0',
                                activebackground='#2b5a2b', selectcolor='#3a7a3a',
                                command=self.apply_theme_from_settings)
            rb.pack(side=tk.LEFT, padx=5)

        # Обои
        tk.Label(frame, text="Обои:", bg='#2b5a2b', fg='#c0e0c0').pack()
        wp_frame = tk.Frame(frame, bg='#2b5a2b')
        wp_frame.pack(pady=5)
        for wp_name in ["moss","grass","forest","dark"]:
            rb = tk.Radiobutton(wp_frame, text=wp_name.capitalize(), variable=self.wallpaper_var,
                                value=wp_name, bg='#2b5a2b', fg='#c0e0c0',
                                activebackground='#2b5a2b', selectcolor='#3a7a3a',
                                command=lambda: self.app.set_wallpaper(self.wallpaper_var.get()))
            rb.pack(side=tk.LEFT, padx=5)

        # Пользовательские обои (изображение)
        img_frame = tk.Frame(frame, bg='#2b5a2b')
        img_frame.pack(pady=2)
        tk.Button(img_frame, text="🖼 Выбрать обои (картинка)…", command=self.app.choose_wallpaper,
                  bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                  relief='raised', bd=1).pack(side=tk.LEFT, padx=4)
        tk.Button(img_frame, text="🚫 Убрать обои", command=self.app.clear_wallpaper,
                  bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                  relief='raised', bd=1).pack(side=tk.LEFT, padx=4)

        # Шрифт интерфейса
        tk.Label(frame, text="Шрифт интерфейса:", bg='#2b5a2b', fg='#c0e0c0').pack(pady=(8, 0))
        font_frame = tk.Frame(frame, bg='#2b5a2b')
        font_frame.pack(pady=2)
        popular_fonts = ["Segoe UI", "Arial", "Verdana", "Tahoma", "Consolas",
                         "Courier New", "Comic Sans MS", "Georgia", "Times New Roman"]
        try:
            available = set(tkfont.families())
            popular_fonts = [f for f in popular_fonts if f in available] or ["Segoe UI"]
        except Exception:
            pass
        self.font_choice_var = tk.StringVar(
            value=self.app.config.get("font_family", "") or
            THEMES.get(self.app.current_theme, {}).get("font_family", "Segoe UI"))
        tk.OptionMenu(font_frame, self.font_choice_var, *popular_fonts).pack(side=tk.LEFT, padx=4)
        self.font_size_var = tk.IntVar(
            value=self.app.config.get("font_size", 0) or
            THEMES.get(self.app.current_theme, {}).get("font_size", 10))
        tk.Spinbox(font_frame, from_=8, to=20, textvariable=self.font_size_var,
                   width=4, bg='#3a7a3a', fg='white', relief='flat').pack(side=tk.LEFT, padx=4)
        tk.Button(font_frame, text="Применить шрифт", command=self.apply_font_settings,
                  bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                  relief='raised', bd=1).pack(side=tk.LEFT, padx=4)

        # Скругления
        tk.Label(frame, text="Скругления кнопок:", bg='#2b5a2b', fg='#c0e0c0').pack(pady=(8, 0))
        radius_frame = tk.Frame(frame, bg='#2b5a2b')
        radius_frame.pack(pady=2)
        self.radius_var = tk.IntVar(value=self.app._get_border_radius())
        tk.Scale(radius_frame, from_=0, to=24, orient=tk.HORIZONTAL, length=180,
                 variable=self.radius_var, bg='#2b5a2b', fg='#c0e0c0',
                 highlightthickness=0).pack(side=tk.LEFT)
        tk.Button(radius_frame, text="Применить", command=self.apply_radius_settings,
                  bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                  relief='raised', bd=1).pack(side=tk.LEFT, padx=6)

        # Анимация вкладок
        tk.Label(frame, text="Анимация вкладок:", bg='#2b5a2b', fg='#c0e0c0').pack(pady=(8, 0))
        anim_frame = tk.Frame(frame, bg='#2b5a2b')
        anim_frame.pack(pady=2)
        self.anim_var = tk.StringVar(value=self.app.config.get("tab_anim", "slide"))
        for text, val in [("Нет", "none"), ("Сдвиг", "slide"),
                          ("Масштаб", "zoom"), ("Появление", "fade")]:
            tk.Radiobutton(anim_frame, text=text, variable=self.anim_var, value=val,
                           bg='#2b5a2b', fg='#c0e0c0', activebackground='#2b5a2b',
                           selectcolor='#3a7a3a', command=self.apply_anim_settings).pack(side=tk.LEFT, padx=4)
        speed_frame = tk.Frame(frame, bg='#2b5a2b')
        speed_frame.pack(pady=2)
        tk.Label(speed_frame, text="Скорость анимации:", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT)
        self.anim_speed_var = tk.IntVar(value=max(10, int(self.app.config.get("anim_speed", 30))))
        tk.Scale(speed_frame, from_=10, to=80, orient=tk.HORIZONTAL, length=160,
                 variable=self.anim_speed_var, bg='#2b5a2b', fg='#c0e0c0',
                 highlightthickness=0, command=lambda v: self.apply_anim_speed()).pack(side=tk.LEFT, padx=6)

        # Цветовая схема
        tk.Label(frame, text="Цветовая схема:", bg='#2b5a2b', fg='#c0e0c0').pack(pady=(10,0))
        color_frame = tk.Frame(frame, bg='#2b5a2b')
        color_frame.pack(pady=5)
        tk.Label(color_frame, text="Фон:", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT)
        self.color_bg_btn = tk.Button(color_frame, bg=self.color_bg, width=3, relief='flat',
                                      command=lambda: self.choose_color("bg"))
        self.color_bg_btn.pack(side=tk.LEFT, padx=5)
        tk.Label(color_frame, text="Кнопки:", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT)
        self.color_btn_btn = tk.Button(color_frame, bg=self.color_btn, width=3, relief='flat',
                                       command=lambda: self.choose_color("btn"))
        self.color_btn_btn.pack(side=tk.LEFT, padx=5)
        tk.Label(color_frame, text="Текст:", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT)
        self.color_text_btn = tk.Button(color_frame, bg=self.color_text, width=3, relief='flat',
                                        command=lambda: self.choose_color("text"))
        self.color_text_btn.pack(side=tk.LEFT, padx=5)

        self.ad_checkbox = tk.Checkbutton(frame, text="Показывать рекламу",
                                          variable=self.ad_var,
                                          command=lambda: setattr(self.app, 'show_ad_flag', self.ad_var.get()),
                                          bg='#2b5a2b', fg='#c0e0c0',
                                          activebackground='#2b5a2b', selectcolor='#3a7a3a')
        self.ad_checkbox.pack(pady=5)
        tk.Label(frame, text="Звуковой движок:", bg='#2b5a2b', fg='#c0e0c0', font=("Segoe UI", 13, "bold")).pack(pady=(10,5))
        self.sound_var = tk.StringVar(value=self.app.sound_engine)
        for engine, display in [('windows','Windows'),('linux','Linux'),('macos','macOS')]:
            rb = tk.Radiobutton(frame, text=display, variable=self.sound_var,
                                value=engine, bg='#2b5a2b', fg='#c0e0c0',
                                activebackground='#2b5a2b', selectcolor='#3a7a3a',
                                command=self.change_sound_engine)
            rb.pack(anchor='w', padx=20)
        tk.Label(frame, text="", bg='#2b5a2b').pack(pady=5)
        tk.Label(frame, text="Смена пароля", font=("Segoe UI", 14, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack()
        self.old_pass_entry = tk.Entry(frame, show="•", bg='#3a7a3a', fg='white',
                                       insertbackground='white', relief='flat', bd=0)
        self.old_pass_entry.pack(pady=2)
        self.new_pass_entry = tk.Entry(frame, show="•", bg='#3a7a3a', fg='white',
                                       insertbackground='white', relief='flat', bd=0)
        self.new_pass_entry.pack(pady=2)
        self.confirm_pass_entry = tk.Entry(frame, show="•", bg='#3a7a3a', fg='white',
                                           insertbackground='white', relief='flat', bd=0)
        self.confirm_pass_entry.pack(pady=2)
        btn_change = tk.Button(frame, text="Установить/сменить пароль", font=("Segoe UI", 12),
                               bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                               relief='flat', bd=0, command=self.change_password)
        btn_change.pack(pady=5)
        btn_change.bind("<Button-1>", lambda e: self.app.play_click())
        btn_reset = tk.Button(frame, text="Сбросить все данные", font=("Segoe UI", 12),
                              bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                              relief='flat', bd=0, command=self.reset_all_data)
        btn_reset.pack(pady=5)
        btn_reset.bind("<Button-1>", lambda e: self.app.play_click())
        btn_clear = tk.Button(frame, text="Очистить загрузки", font=("Segoe UI", 12),
                              bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                              relief='flat', bd=0, command=self.clear_downloads)
        btn_clear.pack(pady=5)
        btn_clear.bind("<Button-1>", lambda e: self.app.play_click())

    def apply_theme_from_settings(self):
        theme = self.theme_var.get()
        self.app.apply_theme_to_app(theme)
        self.apply_theme_to_window(theme)

    def apply_font_settings(self):
        """Применяет выбранные пользователем шрифт и размер ко всему интерфейсу."""
        family = self.font_choice_var.get()
        try:
            size = int(self.font_size_var.get())
        except Exception:
            # В Spinbox мог попасть мусор — берём размер текущей темы
            size = THEMES.get(self.app.current_theme, {}).get("font_size", 10)
        size = max(8, min(20, size))
        self.app.config.set("font_family", family)
        self.app.config.set("font_size", size)
        # Рабочий стол (кнопки и метки; для иконок обновляем и базу hover-анимации)
        for child in self.app.root.winfo_children():
            if isinstance(child, (tk.Button, tk.Label)):
                new_font = self.app._rebase_font(child.cget("font"), family, size)
                if new_font:
                    try:
                        child.configure(font=new_font)
                    except Exception:
                        pass
            if isinstance(child, tk.Button) and hasattr(child, "_base_font"):
                child._base_font = size
                child._cur_font = size
        if hasattr(self.app, 'start_btn'):
            self.app.start_btn.config_button(font=self.app._ui_font(11, bold=True))
        # Окно приложений (все виджеты рекурсивно)
        self.apply_font_to_window(family, size)
        self.notify("Настройки", f"Шрифт применён: {family} {size}")

    def apply_radius_settings(self):
        """Применяет скругления к кнопкам со скруглением (Canvas)."""
        radius = int(self.radius_var.get())
        self.app.config.set("border_radius", radius)
        if hasattr(self.app, 'start_btn'):
            self.app.start_btn.config_button(radius=radius)
        for child in self.app.root.winfo_children():
            if isinstance(child, RoundedButton) and child != self.app.start_btn:
                child.config_button(radius=radius)
        self.notify("Настройки", f"Скругление: {radius}")

    def apply_anim_settings(self):
        mode = self.anim_var.get()
        self.app.config.set("tab_anim", mode)
        self.notify("Настройки", f"Анимация вкладок: {mode}")

    def apply_anim_speed(self):
        try:
            speed = int(self.anim_speed_var.get())
            self.app.config.set("anim_speed", speed)
        except Exception:
            pass

    def choose_color(self, target):
        color = colorchooser.askcolor(title=f"Выберите цвет для {target}")[1]
        if color:
            if target == "bg":
                self.color_bg = color
                self.color_bg_btn.config(bg=color)
            elif target == "btn":
                self.color_btn = color
                self.color_btn_btn.config(bg=color)
            elif target == "text":
                self.color_text = color
                self.color_text_btn.config(bg=color)
            self.apply_colors()

    def apply_colors(self):
        self.configure(bg=self.color_bg)
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=self.color_bg, fg=self.color_text)
            elif isinstance(widget, tk.Button):
                widget.config(bg=self.color_btn, fg=self.color_text)

    def change_sound_engine(self):
        self.app.sound_engine = self.sound_var.get()
        self.app.play_success()

    def change_password(self):
        old, new, confirm = self.old_pass_entry.get(), self.new_pass_entry.get(), self.confirm_pass_entry.get()
        if self.app.password and old != self.app.password:
            messagebox.showerror("Ошибка", "Неверный старый пароль."); self.app.play_error(); return
        if len(new) < 4:
            messagebox.showerror("Ошибка", "Пароль не менее 4 символов."); self.app.play_error(); return
        if new != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают."); self.app.play_error(); return
        self.app.password = new
        messagebox.showinfo("Успех", "Пароль изменён."); self.app.play_success()
        self.old_pass_entry.delete(0, tk.END); self.new_pass_entry.delete(0, tk.END); self.confirm_pass_entry.delete(0, tk.END)

    def reset_all_data(self):
        if not messagebox.askyesno("MinOS", "Сбросить все данные?"): return
        self.clicker_score = 0
        self.clicker_click_power = 1
        self.clicker_auto_income = 0
        self.clicker_prestige_multiplier = 1
        self.clicker_upgrade_cost = 10
        self.clicker_auto_cost = 50
        self.clicker_prestige_cost = 1000
        self.clicker_inventory = []
        self.daily_bonus_available = True
        if hasattr(self,'daily_bonus_btn'): self.daily_bonus_btn.config(state='normal', text="Ежедневный бонус (+100)")
        self.update_clicker_ui()
        self.update_clicker_inventory()
        self.cards_score = 0
        self.cards_rare_chance = 0.05
        self.cards_cooldown = 3
        self.cards_cooldown_active = False
        if hasattr(self,'cards_btn'): self.cards_btn.config(state='normal')
        self.cards_inventory = []
        self.cards_upgrade_rare_cost = 100
        self.cards_upgrade_cooldown_cost = 150
        self.update_cards_inventory()
        if hasattr(self,'cards_score_label'): self.cards_score_label.config(text="Очки: 0")
        self.casino_balance = 0
        if hasattr(self,'casino_balance_label'): self.casino_balance_label.config(text="Баланс: 0")
        self.pet_moisture = 80
        self.pet_health = 80
        self.pet_growth = 0
        self.pet_stage = 0
        self.pet_care_points = 0
        self.update_pet_ui()
        self.generate_quests()
        self.update_quests_display()
        self.downloads = []
        self.update_downloads_list()
        messagebox.showinfo("MinOS", "Все данные сброшены.")

    def clear_downloads(self):
        if not messagebox.askyesno("MinOS", "Очистить загрузки?"): return
        self.downloads = []
        self.update_downloads_list()
        messagebox.showinfo("MinOS", "Загрузки очищены.")

    def create_quests_tab(self, frame):
        tk.Label(frame, text="Задания", font=("Segoe UI", 18, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        self.quests_labels = []
        self.update_quests_display()

    def generate_quests(self):
        self.quests = []
        num = random.randint(3, 5)
        selected = random.sample(self.quest_pool, min(num, len(self.quest_pool)))
        for q in selected:
            new_q = q.copy()
            new_q["progress"] = 0
            new_q["completed"] = False
            self.quests.append(new_q)
        self.quest_progress = {}
        for q in self.quests:
            self.quest_progress[q["type"]] = 0

    def check_quest_update(self):
        if not self.winfo_exists(): return
        all_done = all(q["completed"] for q in self.quests)
        if all_done or (time.time() - self.quest_last_update) > 1800:
            self.generate_quests()
            self.quest_last_update = time.time()
            self.update_quests_display()
        self.quest_update_after_id = self.after(60000, self.check_quest_update)

    def check_clicker_timeout(self):
        if not self.winfo_exists(): return
        if hasattr(self, 'notebook') and self.notebook.index(self.notebook.select()) == TABS["clicker"]:
            elapsed = time.time() - self.clicker_start_time
            if elapsed > 5 * 3600:
                messagebox.showinfo("Кликер", "Вы слишком долго играли в кликер! Окно закроется для вашего блага.")
                self.close()
                return
        self.clicker_close_check_id = self.after(60000, self.check_clicker_timeout)

    def update_quest_progress(self, qtype, inc=1):
        changed = False
        for q in self.quests:
            if q["type"] == qtype and not q["completed"]:
                old_progress = q["progress"]
                if qtype == "clicker_score_reach":
                    q["progress"] = min(self.clicker_score, q["target"])
                elif qtype == "cards_rare_collect":
                    rare_count = sum(1 for c in self.cards_inventory if c["rarity"] in ["rare","epic","legendary","fire"])
                    q["progress"] = min(rare_count, q["target"])
                elif qtype == "premium_activate":
                    if self.subscription.is_active():
                        q["progress"] = 1
                else:
                    q["progress"] = min(q["progress"] + inc, q["target"])
                if q["progress"] != old_progress:
                    changed = True
                break
        # Перерисовываем список только при реальных изменениях (иначе — каждый тик кликера)
        if changed:
            self.check_quests()
            self.update_quests_display()

    def check_quests(self):
        for q in self.quests:
            if not q["completed"] and q["progress"] >= q["target"]:
                q["completed"] = True
                self.give_quest_reward(q)
                msg = f"«{q['description']}» выполнено! Награда: {q['reward_value']} {q['reward_type']}"
                messagebox.showinfo("Задание выполнено!", msg)
                self.notify("Задание выполнено", msg)

    def give_quest_reward(self, q):
        if q["reward_type"] == "clicker_score":
            self.clicker_score += q["reward_value"]; self.update_clicker_ui()
        elif q["reward_type"] == "cards_score":
            self.cards_score += q["reward_value"]; self.cards_score_label.config(text=f"Очки: {self.cards_score}")
        elif q["reward_type"] == "casino_balance":
            self.casino_balance += q["reward_value"]; self.casino_balance_label.config(text=f"Баланс: {self.casino_balance}")
        elif q["reward_type"] == "pet_care_points":
            self.pet_care_points += q["reward_value"]; self.update_pet_ui()
        self.update_quests_display()

    def update_quests_display(self):
        if not hasattr(self,'quests_labels'): return
        for lbl in self.quests_labels:
            lbl.destroy()
        self.quests_labels = []
        if not self.quests:
            self.generate_quests()
        for q in self.quests:
            status = "Выполнено" if q["completed"] else f"{q['progress']}/{q['target']}"
            lbl = tk.Label(self.tab_quests, text=f"{q['description']} - {status}",
                           bg='#2b5a2b', fg='#c0e0c0', font=("Segoe UI", 13))
            lbl.pack(anchor='w', padx=10, pady=2)
            self.quests_labels.append(lbl)

    def create_search_tab(self, frame):
        tk.Label(frame, text="Поиск", font=("Segoe UI", 16, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        self.search_entry = tk.Entry(frame, font=("Segoe UI", 12), bg='#3a7a3a',
                                     fg='White', insertbackground='White', relief='sunken', bd=2)
        self.search_entry.pack(fill=tk.X, padx=10, pady=5)
        self.search_entry.bind("<KeyRelease>", self.update_search_results)
        self.search_entry.focus()
        self.search_listbox = tk.Listbox(frame, bg='#3a7a3a', fg='White',
                                         font=("Segoe UI", 12), selectbackground='#4a8a4a')
        self.search_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.search_listbox.bind("<Double-Button-1>", lambda e: self.activate_search_item())
        btn_open = tk.Button(frame, text="Открыть", font=("Segoe UI", 12),
                             bg='#3a7a3a', fg='White', activebackground='#4a8a4a',
                             relief='raised', bd=2, command=self.activate_search_item)
        btn_open.pack(pady=5)
        btn_open.bind("<Button-1>", lambda e: self.app.play_click())

    def update_search_results(self, event=None):
        query = self.search_entry.get().strip().lower()
        self.search_listbox.delete(0, tk.END)
        self.search_items = []
        if not query: return
        app_display = {
            "calc": "Калькулятор", "notepad": "Блокнот", "game": "Игра",
            "translator": "Переводчик", "generator": "Генератор", "clicker": "Кликер",
            "cards": "Карточки", "casino": "Казино", "ultrakill": "ULTRAKILL",
            "ai": "ИИ", "pet": "Питомец", "console": "Консоль", "all": "Все",
            "games": "Игры", "internet": "Интернет", "downloads": "Загрузки",
            "cipher": "Шифратор", "links": "Ссылки", "settings": "Настройки",
            "quests": "Задания", "search": "Поиск", "calendar": "Календарь",
            "paint": "Рисование", "snake": "Змейка", "alarm": "Будильник",
            "system": "Система", "disk": "Диск", "minesweeper": "Сапёр",
            "taskmanager": "Диспетчер задач", "browser": "Браузер",
            "datecalc": "Калькулятор дат", "changelog": "Ченджлог",
            "subscription": "Подписка", "player": "Плеер"
        }
        for key, name in app_display.items():
            if query in name.lower():
                self.search_items.append((f"Приложение: {name}", ("app", TABS[key])))
                self.search_listbox.insert(tk.END, f"Приложение: {name}")
        commands = ["calc","notepad","game","translator","generator","clicker","cards","casino",
                    "ultrakill","ai","pet","apps","games","internet","downloads","cipher",
                    "links","settings","quests","search","calendar","paint","snake","alarm",
                    "system","disk","minesweeper","taskmanager","browser","datecalc","changelog",
                    "subscription","about","ad","lock","shutdown","reboot","exit","clear","version","help",
                    "wallpaper","snake_bonus","cards_collection","notify"]
        for cmd in commands:
            if query in cmd.lower():
                self.search_items.append((f"Команда: {cmd}", ("command", cmd)))
                self.search_listbox.insert(tk.END, f"Команда: {cmd}")
        for i, file in enumerate(self.downloads):
            if query in file["name"].lower():
                self.search_items.append((f"Файл: {file['name']}", ("file", i)))
                self.search_listbox.insert(tk.END, f"Файл: {file['name']}")
        settings = ["Тема оформления","Показывать рекламу","Звуковой движок","Сброс данных","Очистка загрузок","Обои","Цветовая схема"]
        for name in settings:
            if query in name.lower():
                self.search_items.append((f"Настройка: {name}", ("settings", name)))
                self.search_listbox.insert(tk.END, f"Настройка: {name}")

    def activate_search_item(self):
        sel = self.search_listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx < len(self.search_items):
            typ, data = self.search_items[idx][1]
            if typ == "app": self.switch_to_tab(data)
            elif typ == "command": self._execute_command(data)
            elif typ == "file":
                file = self.downloads[data]
                win = tk.Toplevel(self)
                win.title(file["name"])
                win.geometry("400x300")
                win.configure(bg='#2b5a2b')
                tk.Label(win, text=file["content"], font=("Segoe UI", 12),
                         bg='#2b5a2b', fg='#c0e0c0', justify='left').pack(padx=10, pady=10)
            elif typ == "settings": self.switch_to_tab(TABS["settings"])

    def create_calendar_tab(self, frame):
        self.cal_year = datetime.datetime.now().year
        self.cal_month = datetime.datetime.now().month
        self.cal_frame = tk.Frame(frame, bg='#2b5a2b')
        self.cal_frame.pack(fill=tk.BOTH, expand=True)
        self.update_calendar()

    def update_calendar(self):
        for widget in self.cal_frame.winfo_children(): widget.destroy()
        header = tk.Frame(self.cal_frame, bg='#2b5a2b')
        header.pack(pady=5)
        tk.Button(header, text="◀", command=lambda: self.change_month(-1),
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=5)
        tk.Label(header, text=f"{self.cal_month}.{self.cal_year}", font=("Segoe UI", 16, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(side=tk.LEFT, padx=10)
        tk.Button(header, text="▶", command=lambda: self.change_month(1),
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=5)
        days = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
        day_frame = tk.Frame(self.cal_frame, bg='#2b5a2b')
        day_frame.pack()
        for d in days:
            tk.Label(day_frame, text=d, width=4, font=("Segoe UI", 12, "bold"),
                     bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT, padx=2)
        first_day = datetime.date(self.cal_year, self.cal_month, 1).weekday()
        if self.cal_month == 2:
            days_in_month = 29 if (self.cal_year%4==0 and (self.cal_year%100!=0 or self.cal_year%400==0)) else 28
        elif self.cal_month in [4,6,9,11]: days_in_month = 30
        else: days_in_month = 31
        grid = tk.Frame(self.cal_frame, bg='#2b5a2b')
        grid.pack()
        row, col = 0, first_day
        for day in range(1, days_in_month+1):
            if col == 7: col = 0; row += 1
            btn = tk.Button(grid, text=str(day), width=4, height=2,
                            bg='#3a7a3a', fg='white', relief='flat', bd=0,
                            command=lambda d=day: messagebox.showinfo("Календарь", f"Выбрано {d}.{self.cal_month}.{self.cal_year}"))
            btn.grid(row=row, column=col, padx=2, pady=2)
            col += 1

    def change_month(self, delta):
        new_month = self.cal_month + delta
        if new_month > 12: self.cal_month = 1; self.cal_year += 1
        elif new_month < 1: self.cal_month = 12; self.cal_year -= 1
        else: self.cal_month = new_month
        self.update_calendar()

    def create_paint_tab(self, frame):
        self.paint_color = "#000000"
        self.paint_brush_size = 3
        self.paint_prev_x = None
        self.paint_prev_y = None
        toolbar = tk.Frame(frame, bg='#2b5a2b')
        toolbar.pack(fill=tk.X, pady=5)
        tk.Label(toolbar, text="Цвет:", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT, padx=5)
        self.paint_color_btn = tk.Button(toolbar, bg='#000000', width=3, relief='flat',
                                         command=self.choose_paint_color)
        self.paint_color_btn.pack(side=tk.LEFT, padx=5)
        tk.Label(toolbar, text="Размер:", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT, padx=5)
        self.paint_size_var = tk.IntVar(value=3)
        tk.Spinbox(toolbar, from_=1, to=20, textvariable=self.paint_size_var,
                   width=3, bg='#3a7a3a', fg='white', relief='flat',
                   command=lambda: setattr(self, 'paint_brush_size', self.paint_size_var.get())).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Ластик", command=self.paint_erase,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Очистить", command=self.paint_clear,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=5)
        self.paint_canvas = tk.Canvas(frame, bg='white', relief='sunken', bd=2)
        self.paint_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.paint_canvas.bind("<B1-Motion>", self.paint_draw)
        self.paint_canvas.bind("<ButtonRelease-1>", self.paint_reset)

    def choose_paint_color(self):
        color = colorchooser.askcolor(title="Выберите цвет")[1]
        if color: self.paint_color = color; self.paint_color_btn.config(bg=color)

    def paint_erase(self): self.paint_color = "white"; self.paint_color_btn.config(bg="white")
    def paint_clear(self): self.paint_canvas.delete("all")

    def paint_draw(self, event):
        x, y = event.x, event.y
        if self.paint_prev_x is not None:
            self.paint_canvas.create_line(self.paint_prev_x, self.paint_prev_y, x, y,
                                          fill=self.paint_color, width=self.paint_brush_size,
                                          capstyle=tk.ROUND, smooth=True)
        self.paint_prev_x, self.paint_prev_y = x, y

    def paint_reset(self, event): self.paint_prev_x = None; self.paint_prev_y = None

    def create_snake_tab(self, frame):
        self.snake_canvas = tk.Canvas(frame, bg='#1f3a1f', width=500, height=400)
        self.snake_canvas.pack(pady=10)
        self.snake_score_label = tk.Label(frame, text="Счёт: 0", font=("Segoe UI", 14),
                                          bg='#2b5a2b', fg='#a0d6a0')
        self.snake_score_label.pack()
        self.snake_bonus_label = tk.Label(frame, text="", font=("Segoe UI", 12),
                                          bg='#2b5a2b', fg='#ffaa00')
        self.snake_bonus_label.pack()
        self.snake_restart_btn = tk.Button(frame, text="Новая игра", command=self.snake_restart,
                                           bg='#3a7a3a', fg='white', relief='flat', bd=0)
        self.snake_restart_btn.pack(pady=5)
        self.snake_restart()

    def snake_restart(self):
        if self.snake_game:
            # Останавливаем старую игру: иначе старый цикл move() работал параллельно с новым
            self.snake_game.stop()
        self.snake_game = SnakeGame(self.snake_canvas, self.snake_score_label, self.snake_bonus_label, self.app, premium=self.subscription.is_active())

    def create_alarm_tab(self, frame):
        self.alarm_frame = frame
        tk.Label(frame, text="Будильник", font=("Segoe UI", 18, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        tk.Label(frame, text="Установите время (ЧЧ:ММ):", bg='#2b5a2b', fg='#c0e0c0').pack()
        time_frame = tk.Frame(frame, bg='#2b5a2b')
        time_frame.pack(pady=5)
        self.alarm_hour = tk.StringVar(value="08")
        self.alarm_min = tk.StringVar(value="00")
        tk.Spinbox(time_frame, from_=0, to=23, textvariable=self.alarm_hour, width=3,
                   bg='#3a7a3a', fg='white', relief='flat').pack(side=tk.LEFT, padx=2)
        tk.Label(time_frame, text=":", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT)
        tk.Spinbox(time_frame, from_=0, to=59, textvariable=self.alarm_min, width=3,
                   bg='#3a7a3a', fg='white', relief='flat').pack(side=tk.LEFT, padx=2)
        self.alarm_status = tk.Label(frame, text="Будильник выключен", bg='#2b5a2b', fg='#c0e0c0')
        self.alarm_status.pack(pady=5)
        btn_frame = tk.Frame(frame, bg='#2b5a2b')
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Включить", command=self.alarm_set,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Выключить", command=self.alarm_stop,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=5)

    def alarm_set(self):
        try:
            h = int(self.alarm_hour.get()); m = int(self.alarm_min.get())
            if 0 <= h <= 23 and 0 <= m <= 59:
                self.alarm_time = (h, m)
                self.alarm_active = True
                self.alarm_stop_flag = False
                self.alarm_status.config(text=f"Будильник установлен на {h:02d}:{m:02d}", fg="#a0d6a0")
                if not (self.alarm_thread and self.alarm_thread.is_alive()):
                    self.alarm_thread = threading.Thread(target=self.alarm_check, daemon=True)
                    self.alarm_thread.start()
                messagebox.showinfo("Будильник", f"Будильник установлен на {h:02d}:{m:02d}")
                self.notify("Будильник", f"Установлен на {h:02d}:{m:02d}")
            else: messagebox.showerror("Ошибка", "Неверное время")
        except ValueError: messagebox.showerror("Ошибка", "Введите числа")

    def alarm_stop(self):
        self.alarm_active = False
        self.alarm_stop_flag = True
        self.alarm_status.config(text="Будильник выключен", fg="#c0e0c0")
        if self.alarm_thread and self.alarm_thread.is_alive():
            self.alarm_thread.join(timeout=0.5)
        self.alarm_thread = None

    def alarm_check(self):
        # Работает в фоновом потоке: только ждём нужное время.
        # Весь tkinter (messagebox, notify) вызывается из главного потока через after().
        while self.alarm_active and not self.alarm_stop_flag:
            now = datetime.datetime.now()
            if self.alarm_time and now.hour == self.alarm_time[0] and now.minute == self.alarm_time[1]:
                try:
                    self.after(0, self.alarm_ring)
                except Exception:
                    pass
                break
            time.sleep(5)

    def alarm_ring(self):
        self.app.play_sound(800,500); self.app.play_sound(1000,500); self.app.play_sound(1200,500)
        messagebox.showinfo("Будильник", "Просыпайтесь! Время пришло!")
        self.notify("Будильник", "Просыпайтесь! Время пришло!")
        self.alarm_stop()

    def create_system_tab(self, frame):
        tk.Label(frame, text="Системная информация", font=("Segoe UI", 18, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        # os.getlogin() может бросить OSError — используем надёжный fallback
        try:
            user = os.getlogin()
        except Exception:
            user = os.environ.get("USERNAME", "неизвестно")
        info = f"""ОС: {platform.system()} {platform.release()}
Архитектура: {platform.machine()}
Процессор: {platform.processor()}
Python: {sys.version.split()[0]}
Пользователь: {user}
Время работы: {self.get_uptime()}"""
        try:
            import psutil
            mem = psutil.virtual_memory()
            info += f"\nОЗУ: {mem.total // (1024**3)} ГБ (доступно: {mem.available // (1024**3)} ГБ)"
            info += f"\nЗагрузка ЦП: {psutil.cpu_percent(interval=0.5)}%"
        except ImportError:
            info += "\n(установите psutil для деталей)"
        text = tk.Text(frame, wrap='word', bg='#3a7a3a', fg='#c0e0c0',
                       font=("Consolas", 12), relief='flat', bd=0, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, info)
        text.configure(state='disabled')

    def get_uptime(self):
        sec = None
        try:
            with open('/proc/uptime','r') as f:
                sec = float(f.read().split()[0])
        except Exception:
            pass
        if sec is None:
            # Windows и другие платформы: считаем от времени загрузки через psutil
            try:
                import psutil
                sec = time.time() - psutil.boot_time()
            except Exception:
                return "недоступно"
        d = int(sec//86400); h = int((sec%86400)//3600); m = int((sec%3600)//60)
        return f"{d} дн, {h} ч, {m} мин"

    def create_disk_tab(self, frame):
        top_frame = tk.Frame(frame, bg='#2b5a2b')
        top_frame.pack(fill=tk.X, pady=5)
        tk.Label(top_frame, text="💾 Диск (1 ГБ)", font=("Segoe UI", 14, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(side=tk.LEFT, padx=10)
        self.disk_usage_label = tk.Label(top_frame, text="", bg='#2b5a2b', fg='#c0e0c0')
        self.disk_usage_label.pack(side=tk.RIGHT, padx=10)
        self.disk_progress = ttk.Progressbar(top_frame, length=200, mode='determinate', maximum=self.disk_total_size,
                                             style="green.Horizontal.TProgressbar")
        self.disk_progress.pack(side=tk.RIGHT, padx=5)

        search_frame = tk.Frame(frame, bg='#2b5a2b')
        search_frame.pack(fill=tk.X, pady=2)
        tk.Label(search_frame, text="Поиск:", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT, padx=5)
        self.disk_search_entry = tk.Entry(search_frame, bg='#3a7a3a', fg='white', insertbackground='white')
        self.disk_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.disk_search_entry.bind("<KeyRelease>", self.disk_search_files)

        main_panel = tk.Frame(frame, bg='#2b5a2b')
        main_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        left_frame = tk.Frame(main_panel, bg='#2b5a2b')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        tk.Label(left_frame, text="Папки", font=("Segoe UI", 10, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(anchor='w')
        self.disk_tree = ttk.Treeview(left_frame, show='tree', height=12)
        self.disk_tree.pack(fill=tk.BOTH, expand=True)
        self.disk_tree.bind("<<TreeviewSelect>>", self.disk_on_tree_select)

        right_frame = tk.Frame(main_panel, bg='#2b5a2b')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2)
        tk.Label(right_frame, text="Файлы", font=("Segoe UI", 10, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(anchor='w')
        sort_frame = tk.Frame(right_frame, bg='#2b5a2b')
        sort_frame.pack(fill=tk.X)
        tk.Button(sort_frame, text="Имя", command=lambda: self.disk_sort_files("name"),
                  bg='#3a7a3a', fg='white', relief='flat').pack(side=tk.LEFT, padx=2)
        tk.Button(sort_frame, text="Размер", command=lambda: self.disk_sort_files("size"),
                  bg='#3a7a3a', fg='white', relief='flat').pack(side=tk.LEFT, padx=2)
        tk.Button(sort_frame, text="Дата", command=lambda: self.disk_sort_files("date"),
                  bg='#3a7a3a', fg='white', relief='flat').pack(side=tk.LEFT, padx=2)

        self.disk_files_listbox = tk.Listbox(right_frame, bg='#3a7a3a', fg='white',
                                             selectbackground='#4a8a4a', height=12)
        self.disk_files_listbox.pack(fill=tk.BOTH, expand=True)
        self.disk_files_listbox.bind("<<ListboxSelect>>", self.disk_on_file_select)
        self.disk_files_listbox.bind("<Double-Button-1>", self.disk_open_file)

        preview_frame = tk.Frame(right_frame, bg='#2b5a2b', height=100)
        preview_frame.pack(fill=tk.X, pady=2)
        self.disk_preview_label = tk.Label(preview_frame, text="Предпросмотр", bg='#2b5a2b', fg='#c0e0c0')
        self.disk_preview_label.pack()

        btn_frame = tk.Frame(frame, bg='#2b5a2b')
        btn_frame.pack(fill=tk.X, pady=5)
        for text, cmd in [("Создать папку", self.disk_create_folder),
                          ("Создать файл", self.disk_create_file),
                          ("Удалить", self.disk_delete),
                          ("Дублировать", self.disk_duplicate),
                          ("Переместить", self.disk_move),
                          ("Переименовать", self.disk_rename)]:
            btn = tk.Button(btn_frame, text=text, command=cmd,
                            bg='#3a7a3a', fg='white', activebackground='#4a8a4a',
                            relief='flat', bd=0, padx=8, pady=3)
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind("<Button-1>", lambda e: self.app.play_click())

        self.disk_refresh_tree()
        self.disk_refresh_files()

    def disk_search_files(self, event=None):
        query = self.disk_search_entry.get().strip().lower()
        self.disk_refresh_files(query)

    def disk_sort_files(self, col):
        if self.disk_sort_col == col:
            self.disk_sort_reverse = not self.disk_sort_reverse
        else:
            self.disk_sort_col = col
            self.disk_sort_reverse = False
        self.disk_refresh_files()

    def disk_refresh_files(self, query=""):
        self.disk_files_listbox.delete(0, tk.END)
        node = self.find_node_by_path(self.disk_current_path)
        if node and node["type"] == "folder":
            items = node.get("children", [])
            if query:
                items = [item for item in items if query in item["name"].lower()]
            if self.disk_sort_col == "name":
                items.sort(key=lambda x: x["name"].lower(), reverse=self.disk_sort_reverse)
            elif self.disk_sort_col == "size":
                items.sort(key=lambda x: x.get("size", 0), reverse=self.disk_sort_reverse)
            elif self.disk_sort_col == "date":
                items.sort(key=lambda x: x.get("date", 0), reverse=self.disk_sort_reverse)
            for item in items:
                if item["type"] == "file":
                    label = f"{item['name']} ({item.get('size',0)} МБ)"
                else:
                    label = f"📁 {item['name']}"
                self.disk_files_listbox.insert(tk.END, label)
            # Запоминаем отображаемый список: индексы в listbox соответствуют ему,
            # а не исходному node["children"] (важно при поиске и сортировке)
            self.disk_visible_items = items

    def disk_on_file_select(self, event):
        sel = self.disk_files_listbox.curselection()
        if not sel:
            self.disk_preview_label.config(text="")
            return
        idx = sel[0]
        if idx >= len(self.disk_visible_items):
            return
        item = self.disk_visible_items[idx]
        self.disk_selected_item = item
        if item["type"] == "file":
            # Диск виртуальный — показываем демо-предпросмотр вместо чтения реальной ФС
            self.disk_preview_label.config(
                text=f"Предпросмотр:\n(виртуальный файл '{item['name']}', {item.get('size', 0)} МБ)")
        else:
            self.disk_preview_label.config(text=f"Папка: {item['name']}")

    def disk_on_tree_select(self, event):
        sel = self.disk_tree.selection()
        if sel:
            path = self.disk_tree.item(sel[0], "values")[0]
            self.disk_current_path = path
            self.disk_refresh_files()

    def disk_refresh_tree(self):
        self.disk_tree.delete(*self.disk_tree.get_children())
        self.disk_add_tree_node("", self.disk_root)

    def disk_add_tree_node(self, parent, node):
        if node["type"] == "folder":
            nid = self.disk_tree.insert(parent, "end", text=node["name"], values=[node["path"]])
            for child in node.get("children", []):
                self.disk_add_tree_node(nid, child)

    def find_node_by_path(self, path, node=None):
        if node is None: node = self.disk_root
        if node.get("path") == path: return node
        if node["type"] == "folder":
            for child in node.get("children", []):
                res = self.find_node_by_path(path, child)
                if res: return res
        return None

    def get_parent_path(self, path):
        if path == "/": return "/"
        parts = path.strip("/").split("/")
        if len(parts) <= 1: return "/"
        return "/" + "/".join(parts[:-1]) + "/"

    def disk_open_file(self, event=None):
        sel = self.disk_files_listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx >= len(self.disk_visible_items): return
        item = self.disk_visible_items[idx]
        if item["type"] == "file" and item["name"].endswith(".txt"):
            self.switch_to_tab(TABS["notepad"])
            self.notepad_text.delete(1.0, tk.END)
            self.notepad_text.insert(1.0, f"Содержимое файла {item['name']}:\n(демонстрация)")
            self.notepad_current_file = None
            self.notify("Диск", f"Открыт файл {item['name']} в блокноте")
        else:
            messagebox.showinfo("Инфо", "Можно открыть только .txt файлы")

    def disk_create_folder(self):
        name = simpledialog.askstring("Создать папку", "Введите имя папки:")
        if not name: return
        path = self.disk_current_path
        node = self.find_node_by_path(path)
        if node and node["type"] == "folder":
            for ch in node["children"]:
                if ch["name"] == name:
                    messagebox.showerror("Ошибка", "Папка уже существует")
                    return
            base = path if path.endswith("/") else path + "/"
            new_folder = {"name": name, "type": "folder", "children": [], "path": base + name + "/"}
            node["children"].append(new_folder)
            self.disk_update_usage()
            self.disk_refresh_tree()
            self.disk_refresh_files()

    def disk_create_file(self):
        name = simpledialog.askstring("Создать файл", "Введите имя файла:")
        if not name: return
        size_str = simpledialog.askstring("Создать файл", "Введите размер (МБ, число):")
        try:
            size = float(size_str) if size_str else 5
        except:
            messagebox.showerror("Ошибка", "Размер должен быть числом")
            return
        path = self.disk_current_path
        node = self.find_node_by_path(path)
        if node and node["type"] == "folder":
            for ch in node["children"]:
                if ch["name"] == name and ch["type"] == "file":
                    messagebox.showerror("Ошибка", "Файл уже существует")
                    return
            if self.disk_used_size + size > self.disk_total_size:
                messagebox.showerror("Ошибка", "Недостаточно места на диске")
                return
            base = path if path.endswith("/") else path + "/"
            new_file = {"name": name, "type": "file", "size": size, "path": base + name,
                        "date": time.time()}
            node["children"].append(new_file)
            self.disk_update_usage()
            self.disk_refresh_files()

    def disk_delete(self):
        if self.disk_selected_item is None:
            messagebox.showinfo("Инфо", "Выберите файл или папку")
            return
        item = self.disk_selected_item
        parent_path = self.get_parent_path(item["path"])
        parent = self.find_node_by_path(parent_path)
        if parent and "children" in parent:
            if messagebox.askyesno("Удаление", f"Удалить '{item['name']}'?"):
                parent["children"] = [ch for ch in parent["children"] if ch["path"] != item["path"]]
                self.disk_selected_item = None
                self.disk_update_usage()
        self.disk_refresh_tree()
        self.disk_refresh_files()
        self.disk_update_usage()

    def disk_duplicate(self):
        if self.disk_selected_item is None:
            messagebox.showinfo("Инфо", "Выберите файл или папку")
            return
        item = self.disk_selected_item
        parent_path = self.get_parent_path(item["path"])
        parent = self.find_node_by_path(parent_path)
        if parent and "children" in parent:
            new_name = "копия_" + item["name"]
            for ch in parent["children"]:
                if ch["name"] == new_name:
                    messagebox.showerror("Ошибка", "Копия с таким именем уже существует")
                    return
            import copy
            new_item = copy.deepcopy(item)
            new_item["name"] = new_name
            if new_item["type"] == "folder":
                new_item["path"] = parent_path + new_name + "/"
                self.disk_update_paths(new_item, parent_path + new_name + "/")
            else:
                new_item["path"] = parent_path + new_name
            parent["children"].append(new_item)
            self.disk_selected_item = None
            self.disk_update_usage()
            self.disk_refresh_tree()
            self.disk_refresh_files()

    def disk_update_paths(self, node, new_base):
        if node["type"] == "folder":
            node["path"] = new_base
            for child in node.get("children", []):
                if child["type"] == "folder":
                    self.disk_update_paths(child, new_base + child["name"] + "/")
                else:
                    child["path"] = new_base + child["name"]
        else:
            node["path"] = new_base

    def disk_move(self):
        if self.disk_selected_item is None:
            messagebox.showinfo("Инфо", "Выберите файл или папку")
            return
        item = self.disk_selected_item
        folders = []
        self.disk_collect_folders(self.disk_root, folders)
        if item["type"] == "folder":
            folders = [f for f in folders if f["path"] != item["path"]]
        dest_name = None
        while True:
            choices = [f["name"] for f in folders if f["path"] != item["path"] and not item["path"].startswith(f["path"])]
            if not choices:
                messagebox.showinfo("Инфо", "Нет доступных папок для перемещения")
                return
            dest_name = simpledialog.askstring("Переместить", f"Выберите папку из списка:\n{', '.join(choices)}\nВведите имя папки:")
            if not dest_name: return
            dest = None
            for f in folders:
                if f["name"] == dest_name and f["path"] != item["path"] and not item["path"].startswith(f["path"]):
                    dest = f
                    break
            if dest: break
            else:
                messagebox.showerror("Ошибка", "Некорректная папка (нельзя переместить в саму себя или в дочернюю)")
        parent_path = self.get_parent_path(item["path"])
        parent = self.find_node_by_path(parent_path)
        if parent and "children" in parent:
            parent["children"] = [ch for ch in parent["children"] if ch["path"] != item["path"]]
            dest["children"].append(item)
            if item["type"] == "folder":
                item["path"] = dest["path"] + item["name"] + "/"
                self.disk_update_paths(item, item["path"])
            else:
                item["path"] = dest["path"] + item["name"]
            self.disk_selected_item = None
            self.disk_update_usage()
            self.disk_refresh_tree()
            self.disk_refresh_files()

    def disk_collect_folders(self, node, result):
        if node["type"] == "folder":
            result.append(node)
            for child in node.get("children", []):
                if child["type"] == "folder":
                    self.disk_collect_folders(child, result)

    def disk_rename(self):
        if self.disk_selected_item is None:
            messagebox.showinfo("Инфо", "Выберите файл или папку")
            return
        item = self.disk_selected_item
        new_name = simpledialog.askstring("Переименовать", f"Введите новое имя для {item['name']}:")
        if not new_name: return
        parent_path = self.get_parent_path(item["path"])
        parent = self.find_node_by_path(parent_path)
        if not parent: return
        for ch in parent["children"]:
            if ch["name"] == new_name and ch is not item:
                messagebox.showerror("Ошибка", "Имя уже существует")
                return
        item["name"] = new_name
        if item["type"] == "folder":
            new_path = parent_path + new_name + "/"
            item["path"] = new_path
            self.disk_update_paths(item, new_path)
        else:
            item["path"] = parent_path + new_name
        self.disk_selected_item = None
        self.disk_update_usage()
        self.disk_refresh_tree()
        self.disk_refresh_files()

    def disk_update_usage(self):
        self.disk_used_size = self.calc_folder_size(self.disk_root)
        self.disk_progress['value'] = self.disk_used_size
        pct = (self.disk_used_size / self.disk_total_size * 100) if self.disk_total_size else 0
        self.disk_usage_label.config(text=f"Использовано: {self.disk_used_size:.1f} МБ / {self.disk_total_size} МБ ({pct:.1f}%)")

    def calc_folder_size(self, node):
        if node["type"] == "file":
            return node.get("size", 0)
        total = 0
        for child in node.get("children", []):
            total += self.calc_folder_size(child)
        return total

    def create_minesweeper_tab(self, frame):
        self.ms_frame = frame
        self.ms_game = None
        self.ms_difficulty = tk.StringVar(value="easy")
        diff_frame = tk.Frame(frame, bg='#2b5a2b')
        diff_frame.pack(pady=5)
        tk.Label(diff_frame, text="Сложность:", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT)
        for text, val in [("Лёгкая (8x8, 10 мин)","easy"),("Средняя (12x12, 30 мин)","medium"),("Сложная (16x16, 60 мин)","hard")]:
            rb = tk.Radiobutton(diff_frame, text=text, variable=self.ms_difficulty,
                                value=val, bg='#2b5a2b', fg='#c0e0c0',
                                activebackground='#2b5a2b', selectcolor='#3a7a3a',
                                command=self.ms_restart)
            rb.pack(side=tk.LEFT, padx=5)
        self.ms_canvas = tk.Canvas(frame, bg='#3a7a3a', width=400, height=400)
        self.ms_canvas.pack(pady=5)
        self.ms_status = tk.Label(frame, text="", bg='#2b5a2b', fg='#a0d6a0')
        self.ms_status.pack()
        btn_restart = tk.Button(frame, text="Новая игра", command=self.ms_restart,
                                bg='#3a7a3a', fg='white', relief='flat', bd=0)
        btn_restart.pack(pady=5)
        self.ms_restart()

    def ms_restart(self):
        if self.ms_game:
            self.ms_canvas.delete("all")
        diff = self.ms_difficulty.get()
        if diff == "easy": rows, cols, mines = 8, 8, 10
        elif diff == "medium": rows, cols, mines = 12, 12, 30
        else: rows, cols, mines = 16, 16, 60
        self.ms_game = Minesweeper(self.ms_canvas, self.ms_status, rows, cols, mines, self)

    def create_taskmanager_tab(self, frame):
        self.tm_frame = frame
        tk.Label(frame, text="Диспетчер задач", font=("Segoe UI", 18, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        try:
            import psutil
            _ = psutil.version_info  # убеждаемся, что модуль не только найден, но и рабочий
            self.psutil_available = True
        except ImportError:
            self.psutil_available = False
            tk.Label(frame, text="Для работы диспетчера задач установите psutil: pip install psutil",
                     bg='#2b5a2b', fg='red').pack(pady=20)
            return
        top_frame = tk.Frame(frame, bg='#2b5a2b')
        top_frame.pack(fill=tk.X, pady=5)
        tk.Button(top_frame, text="Обновить", command=self.tm_refresh,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Завершить процесс", command=self.tm_kill,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=5)
        self.tm_info_label = tk.Label(top_frame, text="", bg='#2b5a2b', fg='#c0e0c0')
        self.tm_info_label.pack(side=tk.RIGHT, padx=5)
        self.tm_graph_canvas = tk.Canvas(frame, bg='#2b5a2b', height=100)
        self.tm_graph_canvas.pack(fill=tk.X, padx=5, pady=5)
        self.tm_history = []
        columns = ("PID", "Имя", "ЦП %", "ОЗУ %")
        self.tm_tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.tm_tree.heading(col, text=col)
            self.tm_tree.column(col, width=100)
        self.tm_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tm_refresh()

    def tm_refresh(self):
        if not self.psutil_available: return
        if not self.winfo_exists(): return
        import psutil
        for item in self.tm_tree.get_children():
            self.tm_tree.delete(item)
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    pid = info['pid']
                    name = info['name'] or '?'
                    cpu = info['cpu_percent'] or 0.0
                    mem = info['memory_percent'] or 0.0
                    self.tm_tree.insert("", "end", values=(pid, name, f"{cpu:.1f}", f"{mem:.1f}"))
                except:
                    pass
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            self.tm_info_label.config(text=f"ЦП: {cpu_percent}% | ОЗУ: {mem.percent}%")
            self.tm_history.append(cpu_percent)
            if len(self.tm_history) > 60:
                self.tm_history.pop(0)
            self.tm_graph_canvas.delete("all")
            if len(self.tm_history) > 1:
                w = self.tm_graph_canvas.winfo_width()
                h = 90
                step = w / max(1, len(self.tm_history)-1)
                for i in range(1, len(self.tm_history)):
                    x1 = (i-1)*step
                    x2 = i*step
                    y1 = h - (self.tm_history[i-1] * h / 100)
                    y2 = h - (self.tm_history[i] * h / 100)
                    self.tm_graph_canvas.create_line(x1, y1, x2, y2, fill="#a0d6a0", width=2)
        except:
            pass
        self.tm_after_id = self.after(3000, self.tm_refresh)

    def tm_kill(self):
        selected = self.tm_tree.selection()
        if not selected:
            messagebox.showinfo("Инфо", "Выберите процесс")
            return
        item = selected[0]
        pid = self.tm_tree.item(item, "values")[0]
        try:
            import psutil
            proc = psutil.Process(int(pid))
            if messagebox.askyesno("Завершить процесс", f"Завершить процесс {proc.name()} (PID {pid})?"):
                proc.terminate()
                self.notify("Диспетчер", f"Процесс {proc.name()} завершён")
                self.tm_refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def create_browser_tab(self, frame):
        self.browser_frame = frame
        toolbar = tk.Frame(frame, bg='#2b5a2b')
        toolbar.pack(fill=tk.X, pady=5)
        tk.Button(toolbar, text="Новая вкладка", command=self.browser_new_tab,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Закрыть вкладку", command=self.browser_close_tab,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Назад", command=self.browser_back,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Вперёд", command=self.browser_forward,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Обновить", command=self.browser_refresh,
                  bg='#3a7a3a', fg='white', relief='flat', bd=0).pack(side=tk.LEFT, padx=2)
        self.browser_notebook = ttk.Notebook(frame)
        self.browser_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.browser_new_tab()

    def browser_new_tab(self):
        tab = ttk.Frame(self.browser_notebook)
        self.browser_notebook.add(tab, text="Новая вкладка")
        addr_frame = tk.Frame(tab, bg='#2b5a2b')
        addr_frame.pack(fill=tk.X, pady=2)
        tk.Label(addr_frame, text="URL:", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT, padx=2)
        url_entry = tk.Entry(addr_frame, bg='#3a7a3a', fg='white', insertbackground='white',
                             relief='sunken', bd=1)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        url_entry.bind("<Return>", lambda e, t=tab: self.browser_load(t, url_entry.get()))
        go_btn = tk.Button(addr_frame, text="Перейти", command=lambda t=tab: self.browser_load(t, url_entry.get()),
                           bg='#3a7a3a', fg='white', relief='flat', bd=0)
        go_btn.pack(side=tk.LEFT, padx=2)
        content = tk.Text(tab, wrap='word', bg='#2b5a2b', fg='#c0e0c0',
                          font=("Segoe UI", 12), state='disabled')
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tab.browser_url = ""
        tab.browser_content = content
        tab.browser_url_entry = url_entry
        tab.browser_history = []
        tab.browser_history_pos = -1
        self.browser_load(tab, "home")

    def browser_close_tab(self):
        if self.browser_notebook.index('end') > 1:
            self.browser_notebook.forget(self.browser_notebook.select())

    def browser_load(self, tab, url, record=True):
        # record=False — навигация по истории (Назад/Вперёд), чтобы не дублировать записи
        url = url.strip().lower()
        if not url:
            url = "home"
        pages = {
            "home": "🌿 MinOS Browser\nДобро пожаловать! Введите URL в строке.",
            "news": "Новости MinOS\nВышла версия 0.2.5 с улучшениями!",
            "about": "О браузере\nПростой браузер с вкладками для MinOS.",
            "wiki": "MinOS Wiki\nБраузер поддерживает вкладки, навигацию и историю."
        }
        content = pages.get(url, f"Страница '{url}' не найдена.\nДоступно: home, news, about, wiki")
        tab.browser_content.configure(state='normal')
        tab.browser_content.delete(1.0, tk.END)
        tab.browser_content.insert(tk.END, content)
        tab.browser_content.configure(state='disabled')
        tab.browser_url = url
        tab.browser_url_entry.delete(0, tk.END)
        tab.browser_url_entry.insert(0, url)
        if record:
            if tab.browser_history_pos < len(tab.browser_history)-1:
                tab.browser_history = tab.browser_history[:tab.browser_history_pos+1]
            tab.browser_history.append(url)
            tab.browser_history_pos = len(tab.browser_history)-1
        idx = self.browser_notebook.index(tab)
        self.browser_notebook.tab(idx, text=url)

    def _browser_current_tab(self):
        # notebook.select() возвращает строку-путь, а не виджет — преобразуем
        return self.browser_notebook.nametowidget(self.browser_notebook.select())

    def browser_back(self):
        tab = self._browser_current_tab()
        if tab.browser_history_pos > 0:
            tab.browser_history_pos -= 1
            self.browser_load(tab, tab.browser_history[tab.browser_history_pos], record=False)

    def browser_forward(self):
        tab = self._browser_current_tab()
        if tab.browser_history_pos < len(tab.browser_history)-1:
            tab.browser_history_pos += 1
            self.browser_load(tab, tab.browser_history[tab.browser_history_pos], record=False)

    def browser_refresh(self):
        tab = self._browser_current_tab()
        if tab.browser_url:
            self.browser_load(tab, tab.browser_url)

    def create_datecalc_tab(self, frame):
        tk.Label(frame, text="Калькулятор дат", font=("Segoe UI", 16, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        date_frame = tk.Frame(frame, bg='#2b5a2b')
        date_frame.pack(pady=5)
        tk.Label(date_frame, text="Дата 1:", bg='#2b5a2b', fg='#c0e0c0').grid(row=0, column=0)
        self.dc_date1 = tk.Entry(date_frame, width=12, bg='#3a7a3a', fg='white')
        self.dc_date1.insert(0, time.strftime("%Y-%m-%d"))
        self.dc_date1.grid(row=0, column=1, padx=5)
        tk.Label(date_frame, text="Дата 2:", bg='#2b5a2b', fg='#c0e0c0').grid(row=0, column=2)
        self.dc_date2 = tk.Entry(date_frame, width=12, bg='#3a7a3a', fg='white')
        self.dc_date2.insert(0, time.strftime("%Y-%m-%d"))
        self.dc_date2.grid(row=0, column=3, padx=5)
        btn_calc = tk.Button(date_frame, text="Рассчитать", command=self.dc_calc,
                             bg='#3a7a3a', fg='white', relief='flat', bd=0)
        btn_calc.grid(row=0, column=4, padx=5)
        btn_calc.bind("<Button-1>", lambda e: self.app.play_click())
        self.dc_result = tk.Label(frame, text="", font=("Segoe UI", 14),
                                  bg='#2b5a2b', fg='#a0d6a0')
        self.dc_result.pack(pady=10)
        btn_ny = tk.Button(frame, text="Сколько дней до Нового года?", command=self.dc_newyear,
                           bg='#3a7a3a', fg='white', relief='flat', bd=0)
        btn_ny.pack(pady=5)
        btn_ny.bind("<Button-1>", lambda e: self.app.play_click())

    def dc_calc(self):
        try:
            from datetime import datetime
            d1 = datetime.strptime(self.dc_date1.get(), "%Y-%m-%d")
            d2 = datetime.strptime(self.dc_date2.get(), "%Y-%m-%d")
            diff = abs((d2 - d1).days)
            weeks = diff // 7
            days_left = diff % 7
            self.dc_result.config(text=f"Разница: {diff} дней ({weeks} недель, {days_left} дней)")
        except ValueError:
            self.dc_result.config(text="Ошибка: введите даты в формате ГГГГ-ММ-ДД")

    def dc_newyear(self):
        from datetime import datetime
        now = datetime.now()
        ny = datetime(now.year+1, 1, 1)
        if now.month == 1 and now.day == 1:
            ny = datetime(now.year, 1, 1)
        diff = (ny - now).days
        self.dc_result.config(text=f"До Нового года осталось {diff} дней")

    def create_changelog_tab(self, frame):
        tk.Label(frame, text="📜 История изменений MinOS", font=("Segoe UI", 18, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        text_widget = tk.Text(frame, wrap='word', bg='#3a7a3a', fg='#c0e0c0',
                              font=("Consolas", 12), relief='flat', bd=0, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, self.app.CHANGELOG)
        text_widget.configure(state='disabled')

    def create_subscription_tab(self, frame):
        tk.Label(frame, text="💎 Премиум-подписка MinOS", font=("Segoe UI", 20, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)
        self.sub_status_label = tk.Label(frame, text="", font=("Segoe UI", 14),
                                         bg='#2b5a2b', fg='#c0e0c0')
        self.sub_status_label.pack(pady=5)
        self.update_subscription_status()

        tk.Label(frame, text="Премиум-функции:", font=("Segoe UI", 15, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=5)
        benefits = [
            "✅ Удвоенный множитель в кликере",
            "✅ +5% шанс редких карточек",
            "✅ Бессмертие в змейке",
            "✅ Отключение рекламы",
            "✅ Премиум-задание с наградой 500 очков"
        ]
        for b in benefits:
            tk.Label(frame, text=b, font=("Segoe UI", 12), bg='#2b5a2b', fg='#c0e0c0').pack(anchor='w', padx=20)

        tk.Label(frame, text="Для приобретения подписки обратитесь:", font=("Segoe UI", 13, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=(10,0))
        contacts_frame = tk.Frame(frame, bg='#2b5a2b')
        contacts_frame.pack(pady=2)
        tk.Button(contacts_frame, text="t.me/hell_1tself", fg="LightBlue", cursor="hand2",
                  bg='#2b5a2b', bd=0, command=lambda: webbrowser.open("https://t.me/hell_1tself")).pack(side=tk.LEFT, padx=5)
        tk.Label(contacts_frame, text="или", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT)
        tk.Button(contacts_frame, text="t.me/shie_za", fg="LightBlue", cursor="hand2",
                  bg='#2b5a2b', bd=0, command=lambda: webbrowser.open("https://t.me/shie_za")).pack(side=tk.LEFT, padx=5)

        tk.Label(frame, text="Введите ключ активации (тестовый: PREMIUM2026):", 
                 bg='#2b5a2b', fg='#c0e0c0').pack(pady=5)
        self.sub_key_entry = tk.Entry(frame, font=("Segoe UI", 14), bg='#3a7a3a', fg='white',
                                      insertbackground='white', relief='sunken', bd=2)
        self.sub_key_entry.pack(pady=5, ipadx=10)
        btn_frame = tk.Frame(frame, bg='#2b5a2b')
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Активировать", command=self.activate_subscription,
                  bg='#3a7a3a', fg='white', activebackground='#4a8a4a',
                  relief='raised', bd=2).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отключить (для теста)", command=self.deactivate_subscription,
                  bg='#3a7a3a', fg='white', activebackground='#4a8a4a',
                  relief='raised', bd=2).pack(side=tk.LEFT, padx=5)

    def update_subscription_status(self):
        if self.subscription.is_active():
            self.sub_status_label.config(text="✅ Подписка активна! Все премиум-функции доступны.",
                                         fg="#a0d6a0")
        else:
            self.sub_status_label.config(text="❌ Подписка неактивна. Приобретите подписку для доступа к премиум-функциям.",
                                         fg="#ff6666")

    def activate_subscription(self):
        key = self.sub_key_entry.get().strip()
        success, msg = self.subscription.activate(key)
        if success:
            messagebox.showinfo("Успех", msg + " Все премиум-функции включены.")
            self.update_subscription_status()
            self.app.show_ad_flag = False
            self.app.subscription = self.subscription
            self.update_premium_status()
            self.update_quest_progress("premium_activate")
        else:
            messagebox.showerror("Ошибка", msg)

    def deactivate_subscription(self):
        if messagebox.askyesno("Отключить", "Вы уверены, что хотите отключить подписку?"):
            self.subscription.deactivate()
            self.update_subscription_status()
            self.app.show_ad_flag = True
            self.update_premium_status()
            messagebox.showinfo("Отключено", "Подписка отключена.")

    def update_premium_status(self):
        if hasattr(self, 'clicker_info_label'):
            self.update_clicker_ui()
        if hasattr(self, 'snake_game'):
            self.snake_game.premium = self.subscription.is_active()
        self.update_quest_progress("premium_activate")

    def create_player_tab(self, frame):
        self.player = None
        self.player_playing = False
        self.player_file = None
        self.player_volume = 0.5

        tk.Label(frame, text="🎵 Медиаплеер", font=("Segoe UI", 18, "bold"),
                 bg='#2b5a2b', fg='#a0d6a0').pack(pady=10)

        if not HAS_PYGAME:
            tk.Label(frame, text="Для работы плеера установите pygame:\npip install pygame",
                     bg='#2b5a2b', fg='red', font=("Segoe UI", 12)).pack(pady=20)
            return

        control_frame = tk.Frame(frame, bg='#2b5a2b')
        control_frame.pack(pady=10)
        tk.Button(control_frame, text="📂 Открыть", command=self.player_open,
                  bg='#3a7a3a', fg='white', relief='raised').pack(side=tk.LEFT, padx=5)
        self.player_play_btn = tk.Button(control_frame, text="▶ Играть", command=self.player_play_pause,
                                         bg='#3a7a3a', fg='white', relief='raised')
        self.player_play_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="⏹ Стоп", command=self.player_stop,
                  bg='#3a7a3a', fg='white', relief='raised').pack(side=tk.LEFT, padx=5)

        volume_frame = tk.Frame(frame, bg='#2b5a2b')
        volume_frame.pack(pady=5)
        tk.Label(volume_frame, text="Громкость:", bg='#2b5a2b', fg='#c0e0c0').pack(side=tk.LEFT)
        self.player_volume_scale = tk.Scale(volume_frame, from_=0, to=1, resolution=0.05,
                                            orient=tk.HORIZONTAL, length=200,
                                            bg='#2b5a2b', fg='#c0e0c0',
                                            command=self.player_set_volume)
        self.player_volume_scale.set(0.5)
        self.player_volume_scale.pack(side=tk.LEFT, padx=10)

        self.player_status = tk.Label(frame, text="Статус: готов", bg='#2b5a2b', fg='#c0e0c0')
        self.player_status.pack(pady=10)

    def player_open(self):
        filepath = filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3 *.wav *.ogg"), ("All files", "*.*")])
        if filepath:
            self.player_file = filepath
            self.player_status.config(text=f"Загружен: {os.path.basename(filepath)}")
            if self.player:
                self.player_stop()
            try:
                pygame.mixer.init()
                self.player = pygame.mixer.Sound(filepath)
                self.player_play_btn.config(text="▶ Играть")
                self.player_playing = False
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {e}")
                self.player = None

    def player_play_pause(self):
        if not self.player:
            messagebox.showinfo("Инфо", "Сначала откройте аудиофайл")
            return
        if self.player_playing:
            self.player.stop()
            self.player_play_btn.config(text="▶ Играть")
            self.player_playing = False
            self.player_status.config(text="Пауза")
        else:
            try:
                self.player.play()
                self.player_play_btn.config(text="⏸ Пауза")
                self.player_playing = True
                self.player_status.config(text="Воспроизведение...")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def player_stop(self):
        if self.player:
            try:
                self.player.stop()
            except Exception:
                pass
        if hasattr(self, 'player_play_btn'):
            self.player_play_btn.config(text="▶ Играть")
        if hasattr(self, 'player_status'):
            self.player_status.config(text="Остановлено")
        self.player_playing = False

    def player_set_volume(self, val):
        if self.player:
            self.player.set_volume(float(val))

    def flash_blackout(self):
        self.configure(bg='black')
        for frame in self.all_tabs:
            if frame.winfo_exists():
                frame.configure(bg='black')
        self.after(10000, self.restore_colors)

    def restore_colors(self):
        self.configure(bg=self.color_bg)
        for frame in self.all_tabs:
            if frame.winfo_exists():
                frame.configure(bg=self.color_bg)

    # ---- ОБЩИЕ МЕТОДЫ ----
    def notify(self, title, message, duration=3000):
        self.app.notification_manager.show_notification(title, message, duration)

    def switch_to_tab(self, index):
        if 0 <= index < self.notebook.index('end'):
            self.notebook.select(index)

    # ---------- АНИМАЦИИ ПЕРЕКЛЮЧЕНИЯ ВКЛАДОК ----------
    def _on_tab_changed(self, event=None):
        """Точка входа анимации: срабатывает при любом переключении вкладки."""
        if not getattr(self, '_tab_anim_ready', False):
            return
        try:
            index = self.notebook.index(self.notebook.select())
        except Exception:
            return
        if index == self._last_tab_index:
            return
        self._last_tab_index = index
        # Прерываем предыдущую анимацию (уничтожаем её оверлей)
        if self._tab_anim_state is not None:
            self._finish_tab_anim()
        self._animate_tab_switch(index)

    def _animate_tab_switch(self, index):
        mode = self.app.config.get("tab_anim", "slide")
        if mode not in ("slide", "zoom", "fade"):
            return
        speed = max(10, int(self.app.config.get("anim_speed", 30)))
        theme = THEMES.get(self.app.current_theme, THEMES["moss"])
        # ВАЖНО: анимируем оверлей ПОВЕРХ notebook, а не сам фрейм вкладки.
        # Раньше фрейм забирался у notebook через place(in_=...) — он выпадал
        # из списка вкладок, индексы TABS смещались и switch_to_tab ломался.
        overlay = tk.Canvas(self, bg=theme["bg"], highlightthickness=0, bd=0)
        overlay.place(in_=self.notebook, relx=0, rely=0, relwidth=1, relheight=1)
        # Оверлей создан последним — уже поверх notebook (у Canvas lift()/tkraise()
        # переопределены как tag_raise и поднимают элемент рисунка, не виджет)
        self._tab_anim_state = {"overlay": overlay, "index": index}
        try:
            if mode == "slide":
                self._anim_slide(overlay, speed)
            elif mode == "zoom":
                self._anim_zoom(overlay, speed)
            elif mode == "fade":
                self._anim_fade(overlay, speed)
        except Exception:
            self._finish_tab_anim()

    def _anim_slide(self, overlay, speed):
        """Шторка уезжает влево, открывая вкладку."""
        steps = 6
        def step(i):
            if not self.winfo_exists() or not overlay.winfo_exists():
                self._finish_tab_anim()
                return
            frac = i / steps
            width = max(1, self.notebook.winfo_width())
            overlay.place_configure(x=-int(width * frac))
            if i < steps:
                self._tab_anim_after = self.after(speed, lambda: step(i + 1))
            else:
                self._finish_tab_anim()
        step(0)

    def _anim_zoom(self, overlay, speed):
        """Вкладка открывается «окном», расширяющимся от центра."""
        steps = 6
        def step(i):
            if not self.winfo_exists() or not overlay.winfo_exists():
                self._finish_tab_anim()
                return
            w = max(1, self.notebook.winfo_width())
            h = max(1, self.notebook.winfo_height())
            frac = i / steps
            cw, ch = int(w * frac), int(h * frac)
            cx, cy = w // 2, h // 2
            bg = overlay["bg"]
            overlay.delete("all")
            if cw < w:  # заслонки слева и справа
                overlay.create_rectangle(cx + cw // 2, 0, w, h, fill=bg, outline=bg)
                overlay.create_rectangle(0, 0, cx - cw // 2, h, fill=bg, outline=bg)
            if ch < h:  # заслонки сверху и снизу
                overlay.create_rectangle(0, 0, w, cy - ch // 2, fill=bg, outline=bg)
                overlay.create_rectangle(0, cy + ch // 2, w, h, fill=bg, outline=bg)
            if i < steps:
                self._tab_anim_after = self.after(speed, lambda: step(i + 1))
            else:
                self._finish_tab_anim()
        step(0)

    def _anim_fade(self, overlay, speed):
        """Вертикальная шторка сжимается, открывая вкладку (tk не умеет alpha у Frame)."""
        steps = 6
        def step(i):
            if not self.winfo_exists() or not overlay.winfo_exists():
                self._finish_tab_anim()
                return
            frac = 1.0 - i / steps
            overlay.place_configure(relheight=max(0.0, frac))
            if i < steps:
                self._tab_anim_after = self.after(speed, lambda: step(i + 1))
            else:
                self._finish_tab_anim()
        step(0)

    def _finish_tab_anim(self):
        """Завершает анимацию: убирает оверлей. Вкладки не трогаем — они всё
        время оставались в notebook, поэтому порядок и индексы не меняются."""
        state = self._tab_anim_state
        self._tab_anim_state = None
        if self._tab_anim_after is not None:
            try:
                self.after_cancel(self._tab_anim_after)
            except Exception:
                pass
            self._tab_anim_after = None
        if not state:
            return
        ov = state.get("overlay")
        if ov is not None:
            try:
                ov.destroy()
            except Exception:
                pass

    def apply_font_to_window(self, family, size=None):
        """Обновляет гарнитуру шрифта у всех виджетов окна приложений."""
        if not family:
            return
        try:
            self._apply_font_family_recursive(self, family, size)
        except Exception:
            pass

    def toggle_maximize(self):
        """Разворачивает окно приложений на весь экран (как в Windows)."""
        if self.maximized:
            if self._restore_geometry:
                self.geometry(self._restore_geometry)
            self.maximized = False
        else:
            self._restore_geometry = self.geometry()
            screen_h = self.winfo_screenheight()
            self.geometry(f"{self.winfo_screenwidth()}x{screen_h - 52}+0+0")
            self.maximized = True

    def minimize(self):
        self.withdraw()

    def close(self):
        if self.clicker_after_id is not None:
            self.after_cancel(self.clicker_after_id)
            self.clicker_after_id = None
        if self.cards_cooldown_after_id is not None:
            self.after_cancel(self.cards_cooldown_after_id)
            self.cards_cooldown_after_id = None
        if self.pet_after_id is not None:
            self.after_cancel(self.pet_after_id)
            self.pet_after_id = None
        if self.clicker_close_check_id is not None:
            self.after_cancel(self.clicker_close_check_id)
            self.clicker_close_check_id = None
        if self.quest_update_after_id is not None:
            self.after_cancel(self.quest_update_after_id)
            self.quest_update_after_id = None
        if getattr(self, 'tm_after_id', None) is not None:
            self.after_cancel(self.tm_after_id)
            self.tm_after_id = None
        # Анимации вкладок: отменяем таймер и убираем оверлей
        self._finish_tab_anim()
        self._tab_anim_ready = False
        # Таймер UI загрузок
        if getattr(self, '_downloads_ui_after', None) is not None:
            try:
                self.after_cancel(self._downloads_ui_after)
            except Exception:
                pass
            self._downloads_ui_after = None
        if self.snake_game:
            self.snake_game.stop()
            self.snake_game = None
        self.alarm_stop()
        if self.cards_collection_window is not None and self.cards_collection_window.winfo_exists():
            self.cards_collection_window.destroy()
            self.cards_collection_window = None
        self.player_stop()
        self.app.on_apps_window_closed()
        self.destroy()

# ==================== КЛАССЫ ЗМЕЙКИ И САПЁРА ====================
class SnakeGame:
    def __init__(self, canvas, score_label, bonus_label, app, premium=False):
        self.canvas = canvas
        self.score_label = score_label
        self.bonus_label = bonus_label
        self.app = app
        self.premium = premium
        self.running = True
        self.score = 0
        self.direction = "Right"
        self.next_direction = "Right"
        self.snake = [(100,100), (80,100), (60,100)]
        self.width = 500
        self.height = 400
        self.bonus_foods = []
        self.bonus_active = {"immortal": False, "slow": False, "big_map": False, "more_food": False}
        self.bonus_timers = {}
        self.speed = 150
        self.food = self.place_food()
        self.draw()
        self.canvas.bind_all("<KeyPress>", self.key_press)
        self.move()

    def stop(self):
        """Полная остановка игры: цикл движения, таймеры бонусов и обработчик клавиш."""
        self.running = False
        # Отменяем отложенные таймеры бонусов, иначе они сработают на закрытом окне
        for timer in self.bonus_timers.values():
            try:
                self.canvas.after_cancel(timer)
            except Exception:
                pass
        self.bonus_timers = {}
        try:
            self.canvas.unbind_all("<KeyPress>")
        except Exception:
            pass

    def reset(self):
        """Перезапуск без создания нового экземпляра (иначе старый цикл move() продолжал работать)."""
        self.stop()
        self.score = 0
        self.direction = "Right"
        self.next_direction = "Right"
        self.snake = [(100,100), (80,100), (60,100)]
        self.width = 500
        self.height = 400
        self.bonus_foods = []
        self.bonus_active = {"immortal": False, "slow": False, "big_map": False, "more_food": False}
        self.bonus_timers = {}
        self.speed = 150
        try:
            self.canvas.config(width=self.width, height=self.height)
        except Exception:
            return
        self.score_label.config(text="Счёт: 0")
        self.bonus_label.config(text="")
        self.food = self.place_food()
        self.running = True
        self.draw()
        self.canvas.bind_all("<KeyPress>", self.key_press)
        self.move()

    def place_food(self):
        import random
        x = random.randint(0, (self.width//20)-1)*20+10
        y = random.randint(0, (self.height//20)-1)*20+10
        while (x,y) in self.snake or (x,y) in [b["pos"] for b in self.bonus_foods]:
            x = random.randint(0, (self.width//20)-1)*20+10
            y = random.randint(0, (self.height//20)-1)*20+10
        return (x,y)

    def place_bonus_food(self):
        import random
        x = random.randint(0, (self.width//20)-1)*20+10
        y = random.randint(0, (self.height//20)-1)*20+10
        while (x,y) in self.snake or (x,y) in [b["pos"] for b in self.bonus_foods] or (x,y)==self.food:
            x = random.randint(0, (self.width//20)-1)*20+10
            y = random.randint(0, (self.height//20)-1)*20+10
        return x, y

    def spawn_bonus(self, btype):
        if btype == "more_food":
            for _ in range(2):
                pos = self.place_bonus_food()
                self.bonus_foods.append({"pos":pos, "type":"food"})
        elif btype == "big_map":
            self.width += 100
            self.height += 100
            self.canvas.config(width=self.width, height=self.height)
        elif btype == "slow":
            self.speed = 300
            self.bonus_active["slow"] = True
            self.bonus_timers["slow"] = self.canvas.after(10000, self.deactivate_bonus, "slow")
        elif btype == "immortal":
            self.bonus_active["immortal"] = True
            self.bonus_timers["immortal"] = self.canvas.after(10000, self.deactivate_bonus, "immortal")
        self.update_bonus_label()

    def deactivate_bonus(self, btype):
        if btype == "immortal":
            self.bonus_active["immortal"] = False
        elif btype == "slow":
            self.speed = 150
            self.bonus_active["slow"] = False
        self.update_bonus_label()

    def update_bonus_label(self):
        texts = []
        if self.bonus_active["immortal"]: texts.append("🛡️ Бессмертие")
        if self.bonus_active["slow"]: texts.append("🐢 Замедление")
        if self.width > 500: texts.append("🗺️ Большая карта")
        if len(self.bonus_foods) > 0: texts.append("🍎 Больше яблок")
        self.bonus_label.config(text=" | ".join(texts))

    def key_press(self, event):
        key = event.keysym
        if key in ["Up","Down","Left","Right"]:
            opposites = {"Up":"Down","Down":"Up","Left":"Right","Right":"Left"}
            if opposites.get(key) != self.direction:
                self.next_direction = key
        elif key == "space" and not self.running:
            self.reset()

    def move(self):
        if not self.running: return
        if not self.canvas.winfo_exists():
            self.running = False
            return
        self.direction = self.next_direction
        head = self.snake[0]
        dx, dy = 0,0
        if self.direction == "Up": dy = -20
        elif self.direction == "Down": dy = 20
        elif self.direction == "Left": dx = -20
        elif self.direction == "Right": dx = 20
        new_head = (head[0]+dx, head[1]+dy)

        if not self.premium and not self.bonus_active["immortal"]:
            if new_head[0] <0 or new_head[0]>=self.width or new_head[1]<0 or new_head[1]>=self.height:
                self.game_over(); return
            if new_head in self.snake:
                self.game_over(); return
        else:
            if new_head[0] < 0: new_head = (self.width-10, new_head[1])
            elif new_head[0] >= self.width: new_head = (10, new_head[1])
            if new_head[1] < 0: new_head = (new_head[0], self.height-10)
            elif new_head[1] >= self.height: new_head = (new_head[0], 10)
            if not self.premium and new_head in self.snake:
                self.game_over(); return

        self.snake.insert(0, new_head)
        ate = False
        if new_head == self.food:
            self.score += 1
            self.score_label.config(text=f"Счёт: {self.score}")
            self.food = self.place_food()
            ate = True
            self.app.play_click()
            if random.random() < 0.1:
                btypes = ["immortal","slow","big_map","more_food"]
                btype = random.choice(btypes)
                self.spawn_bonus(btype)
                self.app.notify("Бонус!", f"Активирован бонус: {btype}!")
        else:
            for b in self.bonus_foods:
                if new_head == b["pos"]:
                    self.score += 1
                    self.score_label.config(text=f"Счёт: {self.score}")
                    self.bonus_foods.remove(b)
                    ate = True
                    self.app.play_click()
                    break
            if not ate:
                self.snake.pop()
        self.draw()
        self.canvas.after(self.speed, self.move)

    def draw(self):
        self.canvas.delete("all")
        for seg in self.snake:
            x,y = seg
            self.canvas.create_rectangle(x-8,y-8,x+8,y+8, fill="#3a7a3a", outline="#a0d6a0")
        x,y = self.snake[0]
        self.canvas.create_rectangle(x-8,y-8,x+8,y+8, fill="#4a8a4a", outline="#a0d6a0")
        x,y = self.food
        self.canvas.create_oval(x-8,y-8,x+8,y+8, fill="red", outline="white")
        for b in self.bonus_foods:
            x,y = b["pos"]
            self.canvas.create_oval(x-8,y-8,x+8,y+8, fill="gold", outline="white")
        if self.bonus_active["immortal"] or self.premium:
            self.canvas.create_rectangle(0,0,self.width,self.height, outline="yellow", width=3, dash=(5,5))

    def game_over(self):
        self.running = False
        self.canvas.delete("all")
        self.canvas.create_text(self.width//2, self.height//2-20, text="Игра окончена", fill="red", font=("Segoe UI",24,"bold"))
        self.canvas.create_text(self.width//2, self.height//2+30, text="Нажмите 'Новая игра' или пробел", fill="white", font=("Segoe UI",14))
        self.canvas.unbind_all("<KeyPress>")
        self.canvas.bind_all("<KeyPress>", self.key_press)

class Minesweeper:
    def __init__(self, canvas, status_label, rows, cols, mines, parent):
        self.canvas = canvas
        self.status_label = status_label
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.parent = parent
        self.game_over = False
        self.first_click = True
        self.board = [[0]*cols for _ in range(rows)]
        self.revealed = [[False]*cols for _ in range(rows)]
        self.flagged = [[False]*cols for _ in range(rows)]
        self.cell_size = min(400 // cols, 400 // rows, 30)
        self.canvas.delete("all")
        self.canvas.config(width=self.cell_size*cols, height=self.cell_size*rows)
        self.draw_board()
        self.canvas.bind("<Button-1>", self.left_click)
        self.canvas.bind("<Button-3>", self.right_click)
        self.status_label.config(text=f"Мин: {self.mines} | Осталось: {self.mines}")

    def draw_board(self):
        self.canvas.delete("all")
        for r in range(self.rows):
            for c in range(self.cols):
                x1 = c*self.cell_size
                y1 = r*self.cell_size
                x2 = x1+self.cell_size
                y2 = y1+self.cell_size
                if self.revealed[r][c]:
                    if self.board[r][c] == -1:
                        self.canvas.create_rectangle(x1,y1,x2,y2, fill="red", outline="gray")
                        self.canvas.create_text(x1+self.cell_size//2, y1+self.cell_size//2, text="💣")
                    else:
                        color = "#4a7a4a" if (r+c)%2==0 else "#3a6a3a"
                        self.canvas.create_rectangle(x1,y1,x2,y2, fill=color, outline="gray")
                        if self.board[r][c] > 0:
                            self.canvas.create_text(x1+self.cell_size//2, y1+self.cell_size//2,
                                                    text=str(self.board[r][c]), fill="white")
                elif self.flagged[r][c]:
                    self.canvas.create_rectangle(x1,y1,x2,y2, fill="#5a5a3a", outline="gray")
                    self.canvas.create_text(x1+self.cell_size//2, y1+self.cell_size//2, text="🚩")
                else:
                    color = "#3a7a3a" if (r+c)%2==0 else "#2a6a2a"
                    self.canvas.create_rectangle(x1,y1,x2,y2, fill=color, outline="gray")

    def left_click(self, event):
        if self.game_over: return
        r = event.y // self.cell_size
        c = event.x // self.cell_size
        if r >= self.rows or c >= self.cols: return
        if self.flagged[r][c]: return
        if self.first_click:
            self.place_mines(r, c)
            self.first_click = False
        if self.revealed[r][c]: return
        if self.board[r][c] == -1:
            self.game_over = True
            self.reveal_all()
            self.status_label.config(text="💥 Вы проиграли!")
            self.parent.notify("Сапёр", "Вы подорвались на мине!")
            return
        self.reveal(r, c)
        self.draw_board()
        flags = sum(1 for r in range(self.rows) for c in range(self.cols) if self.flagged[r][c])
        self.status_label.config(text=f"Мин: {self.mines} | Осталось: {self.mines - flags}")
        if self.check_win():
            self.game_over = True
            self.status_label.config(text="🎉 Вы выиграли!")
            self.parent.notify("Сапёр", "Вы выиграли в сапёре!")
            self.parent.update_quest_progress("minesweeper_wins", 1)

    def right_click(self, event):
        if self.game_over or self.first_click: return
        r = event.y // self.cell_size
        c = event.x // self.cell_size
        if r >= self.rows or c >= self.cols: return
        if self.revealed[r][c]: return
        self.flagged[r][c] = not self.flagged[r][c]
        self.draw_board()
        flags = sum(1 for r in range(self.rows) for c in range(self.cols) if self.flagged[r][c])
        self.status_label.config(text=f"Мин: {self.mines} | Осталось: {self.mines - flags}")

    def place_mines(self, safe_r, safe_c):
        import random
        placed = 0
        while placed < self.mines:
            r = random.randint(0, self.rows-1)
            c = random.randint(0, self.cols-1)
            if self.board[r][c] == -1: continue
            if abs(r-safe_r)<=1 and abs(c-safe_c)<=1: continue
            self.board[r][c] = -1
            placed += 1
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1: continue
                count = 0
                for dr in [-1,0,1]:
                    for dc in [-1,0,1]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols and self.board[nr][nc] == -1:
                            count += 1
                self.board[r][c] = count

    def reveal(self, r, c):
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols: return
        if self.revealed[r][c] or self.flagged[r][c]: return
        self.revealed[r][c] = True
        if self.board[r][c] == 0:
            for dr in [-1,0,1]:
                for dc in [-1,0,1]:
                    self.reveal(r+dr, c+dc)

    def reveal_all(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.revealed[r][c] = True
        self.draw_board()

    def check_win(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != -1 and not self.revealed[r][c]:
                    return False
        return True

# ==================== ЗАПУСК ====================
def main():
    root = tk.Tk()
    root.withdraw()

    def after_boot():
        root.deiconify()
        app = MinOSApp(root)
        app.show_login_or_desktop()
        root.protocol("WM_DELETE_WINDOW", app.shutdown)

    BootScreen(root, after_boot)
    root.mainloop()

if __name__ == "__main__":
    main()
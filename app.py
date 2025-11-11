import customtkinter as ctk
import subprocess
import threading
import os
import sys
import json
from tkinter import filedialog, messagebox

# --- КОНФИГУРАЦИЯ ---
# Файл для сохранения путей
CONFIG_FILE = "config.json"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Kick VOD Downloader (kick-dlp Wrapper)")
        self.geometry("800x600")
        self.resizable(False, False)

        # --- Интерфейс ---
        path_frame = ctk.CTkFrame(self)
        path_frame.pack(padx=10, pady=10, fill="x")

        # --- Виджеты для выбора путей ---
        self.ffmpeg_label = ctk.CTkLabel(path_frame, text="Путь к ffmpeg.exe:")
        self.ffmpeg_label.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        self.ffmpeg_entry = ctk.CTkEntry(path_frame, width=500)
        self.ffmpeg_entry.grid(row=0, column=1, padx=5, pady=10)
        self.ffmpeg_button = ctk.CTkButton(path_frame, text="Обзор...", width=100, command=self.browse_ffmpeg)
        self.ffmpeg_button.grid(row=0, column=2, padx=(5, 10), pady=10)

        self.download_label = ctk.CTkLabel(path_frame, text="Папка для скачивания:")
        self.download_label.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="w")
        self.download_entry = ctk.CTkEntry(path_frame, width=500)
        self.download_entry.grid(row=1, column=1, padx=5, pady=10)
        self.download_button_browse = ctk.CTkButton(path_frame, text="Обзор...", width=100, command=self.browse_download_folder)
        self.download_button_browse.grid(row=1, column=2, padx=(5, 10), pady=10)
        
        # --- Виджеты для скачивания ---
        self.url_label = ctk.CTkLabel(self, text="Ссылка на Kick VOD:")
        self.url_label.pack(padx=20, pady=(10, 5))

        self.url_entry = ctk.CTkEntry(self, width=760, placeholder_text="https://kick.com/...")
        self.url_entry.pack(padx=20, pady=5)

        self.download_button = ctk.CTkButton(self, text="🚀 Скачать", command=self.start_download_thread, height=40)
        self.download_button.pack(padx=20, pady=20)

        self.log_textbox = ctk.CTkTextbox(self, width=760, height=250, state="disabled")
        self.log_textbox.pack(padx=20, pady=5)

        self.status_label = ctk.CTkLabel(self, text="Заполните пути и вставьте ссылку.")
        self.status_label.pack(padx=20, pady=10)

        self.load_config() # Загружаем сохраненные пути при старте
        
        # Проверяем, был ли первый запуск
        self.is_first_run = not os.path.exists(os.path.join(self.get_app_data_path(), ".installed"))
        if self.is_first_run:
            self.after(100, self.first_run_setup)

    def get_app_data_path(self):
        """Возвращает путь к папке AppData для хранения маркера установки."""
        return os.path.join(os.environ['APPDATA'], "KickDownloader")

    def log(self, message):
        """Безопасно добавляет сообщение в лог из любого потока."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.update_idletasks()

    def browse_ffmpeg(self):
        path = filedialog.askopenfilename(title="Выберите ffmpeg.exe", filetypes=[("Executable", "*.exe")])
        if path:
            self.ffmpeg_entry.delete(0, "end")
            self.ffmpeg_entry.insert(0, path)
            self.save_config()

    def browse_download_folder(self):
        path = filedialog.askdirectory(title="Выберите папку для сохранения видео")
        if path:
            self.download_entry.delete(0, "end")
            self.download_entry.insert(0, path)
            self.save_config()

    def save_config(self):
        config = {
            "ffmpeg_path": self.ffmpeg_entry.get(),
            "download_path": self.download_entry.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            self.ffmpeg_entry.insert(0, config.get("ffmpeg_path", ""))
            self.download_entry.insert(0, config.get("download_path", ""))
        else:
             # Устанавливаем пути по умолчанию, если конфига нет
             self.download_entry.insert(0, "D:\\kickdownload\\VODs")

    def first_run_setup(self):
        """Устанавливает kick-dlp и playwright при первом запуске."""
        self.download_button.configure(state="disabled", text="Идет первоначальная настройка...")
        self.log("Первый запуск. Начинаю установку зависимостей (это может занять несколько минут)...\n")
        
        setup_thread = threading.Thread(target=self.run_setup_commands)
        setup_thread.start()

    def run_setup_commands(self):
        try:
            self.log("1/2: Установка kick-dlp через npm...\n")
            subprocess.run("npm i kick-dlp -g", check=True, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            self.log("kick-dlp успешно установлен.\n")

            self.log("2/2: Установка браузеров для Playwright (скачивание ~300 МБ)...\n")
            subprocess.run("npx playwright install", check=True, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            self.log("Браузеры установлены.\nНастройка завершена!\n")
            
            # Создаем папку и маркер, что установка прошла
            app_data_path = self.get_app_data_path()
            os.makedirs(app_data_path, exist_ok=True)
            with open(os.path.join(app_data_path, ".installed"), "w") as f:
                f.write("done")
            self.after(0, lambda: messagebox.showinfo("Успех", "Настройка завершена. Приложение готово к работе!"))

        except subprocess.CalledProcessError as e:
            error_message = f"Ошибка при настройке:\n{e.stderr or e.stdout}"
            self.log(error_message + "\n")
            self.after(0, lambda: messagebox.showerror("Ошибка", error_message))
        finally:
            self.after(0, self.reset_ui)
            
    def start_download_thread(self):
        self.download_button.configure(state="disabled", text="Скачивание...")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

        thread = threading.Thread(target=self.download_video)
        thread.start()

    def download_video(self):
        url = self.url_entry.get()
        ffmpeg_path = self.ffmpeg_entry.get()
        download_path = self.download_entry.get()

        if not all([url, ffmpeg_path, download_path]):
            self.after(0, lambda: messagebox.showerror("Ошибка", "Все поля (путь к ffmpeg, папка для скачивания и URL) должны быть заполнены."))
            self.after(0, self.reset_ui)
            return
        
        if not os.path.exists(ffmpeg_path):
            self.after(0, lambda: messagebox.showerror("Ошибка", f"Файл ffmpeg.exe не найден по пути:\n{ffmpeg_path}"))
            self.after(0, self.reset_ui)
            return
            
        os.makedirs(download_path, exist_ok=True)
        
        command = f"npx kick-dlp {url}"
        
        # Создаем копию переменных окружения и добавляем путь к нашему ffmpeg
        env = os.environ.copy()
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        env["PATH"] = ffmpeg_dir + os.pathsep + env["PATH"]
        
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                encoding='utf-8', errors='replace', shell=True, cwd=download_path, env=env
            )

            for line in process.stdout:
                self.log(line)

            process.wait()

            if process.returncode == 0:
                self.log("\nСкачивание успешно завершено!\n")
                self.after(0, lambda: messagebox.showinfo("Успех", "Видео скачано!"))
            else:
                log_content = self.log_textbox.get("1.0", "end")
                if "FFmpeg is not installed" in log_content:
                     self.log("\nОШИБКА: kick-dlp не смог найти FFmpeg. Убедитесь, что путь указан верно.\n")
                else:
                     self.log(f"\nПроцесс завершился с ошибкой (код: {process.returncode}).\n")
                self.after(0, lambda: messagebox.showerror("Ошибка", "Скачивание не удалось. Смотрите лог."))

        except Exception as e:
            error_message = f"Критическая ошибка: {str(e)}\n"
            self.log(error_message)
            self.after(0, lambda: messagebox.showerror("Критическая ошибка", error_message))
        finally:
            self.after(0, self.reset_ui)

    def reset_ui(self):
        self.download_button.configure(state="normal", text="🚀 Скачать")
        self.status_label.configure(text="Готов к работе.")

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()
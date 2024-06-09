import os
import sys
import json
import subprocess
import zipfile
import requests
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox, QMainWindow, QProgressBar
from qasync import QEventLoop, QApplication
from PyQt6.QtGui import QPixmap
import asyncio
from threading import Thread
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, Qt

#09.06.2024
def get_server_ip():
    try:
        response = requests.get('***')
        if response.status_code == 200:
            ip_address = response.text.strip()  # Убираем лишние символы, например, пробелы и переводы строк
            print(ip_address)
            return ip_address
        else:
            print(f"Ошибка при получении IP-адреса: {response.status_code}")
    except Exception as e:
        print(f"Ошибка: {e}")
    return None

def check_for_updates():
    github_repo_url = "***"
    try:
        response = requests.get(github_repo_url)
        if response.status_code == 200:
            release_info = response.json()
            latest_version = release_info['tag_name']
            app_version = "1.0.7"  # Ваш текущий номер версии
            if latest_version != app_version:
                result = QMessageBox.warning(None, "Обновление", "Доступна новая версия программы. Для установки обновления скачайте файлы игры.", QMessageBox.StandardButton.Ok)
                if result == QMessageBox.StandardButton.Ok:
                    subprocess.Popen(["updater.exe"])
                sys.exit()
            else:
                QMessageBox.information(None, "Внимание", "Последняя версия программы уже установлена.")
        else:
            QMessageBox.warning(None, "Внимание",f"Проверьте установлены ли файлы игры. Ошибка при получении информации о релизе: {response.status_code}")
    except Exception as e:
        QMessageBox.warning(None, "Внимание",f"Проверьте установлены ли файлы игры. Ошибка: {e}")

class Downloader(QObject):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, url, download_path, extract_path):
        super().__init__()
        self.url = url
        self.download_path = download_path
        self.extract_path = extract_path

    @pyqtSlot()
    def download_files(self):
        try:
            response = requests.get(self.url, stream=True)
            if response.status_code != 200:
                self.error_occurred.emit(f"HTTP Error: {response.status_code}")
                return

            downloaded_file_path = os.path.join(self.download_path, "temp.zip")

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(downloaded_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int(downloaded_size / total_size * 100)
                        self.progress_updated.emit(progress)

            with zipfile.ZipFile(downloaded_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_path)

            os.remove(downloaded_file_path)

            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))

class MinecraftLauncher(QMainWindow):
    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setFixedSize(500, 500)
        check_for_updates()
        get_server_ip()

    def init_ui(self):
        self.setWindowTitle('Minecraft Launcher')
        self.setGeometry(100, 100, 500, 500)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        self.logopng = QLabel(self)
        self.logopng.setGeometry(100, 20, 100, 100)

        png1 = self.resource_path("logo1.png")
        pixmap = QPixmap(png1)
        scaled_pixmap = pixmap.scaled(100, 100)

        self.logopng.setPixmap(scaled_pixmap)
        self.logo = QLabel('ABX', self)
        self.logo.setGeometry(200, 20, 100, 100)

        self.buttonClose = QPushButton('x', self)
        self.buttonClose.setGeometry(460, 10, 25, 25)
        self.buttonClose.clicked.connect(self.close)
        self.buttonMinimize = QPushButton('-', self)
        self.buttonMinimize.setGeometry(430, 10, 25, 25)
        self.buttonMinimize.clicked.connect(self.showMinimized)

        self.username_label = QLabel('Игровое имя:', self)
        self.username_label.setGeometry(30, 122, 107, 19)

        self.password_label = QLabel('Пароль:', self)
        self.password_label.setGeometry(290, 122, 64, 19)

        self.password_entry = QLineEdit(self)
        self.password_entry.setGeometry(290, 151, 180, 35)
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)

        self.username_entry = QLineEdit(self)
        self.username_entry.setGeometry(30, 151, 180, 35)

        self.save_button = QPushButton('Авторизация', self)
        self.save_button.setGeometry(30, 206, 167, 35)
        self.save_button.clicked.connect(self.save_credentials)

        self.change_path = QPushButton('Сменить пути', self)
        self.change_path.setGeometry(290, 250, 167, 35)
        self.change_path.clicked.connect(self.update_bat_file)

        self.show_password_button = QPushButton('Показать пароль', self)
        self.show_password_button.setGeometry(290, 206, 167, 35)
        self.show_password_button.setCheckable(True)
        self.show_password_button.clicked.connect(self.toggle_password_visibility)

        self.download_button = QPushButton('Скачать файлы', self)
        self.download_button.setGeometry(30, 319, 167, 35)
        self.download_button.clicked.connect(self.download_version_files)

        self.download_mods_button = QPushButton('Скачать моды', self)
        self.download_mods_button.setGeometry(207, 319, 167, 35)
        self.download_mods_button.clicked.connect(self.download_mods)

        self.launch_button = QPushButton('Запустить игру', self)
        self.launch_button.setGeometry(30, 383, 167, 35)
        self.launch_button.setEnabled(False)
        self.launch_button.clicked.connect(self.launch_minecraft)

        self.connect_checkbox = QCheckBox(self)
        self.connect_checkbox.setGeometry(30, 261, 15, 15)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(30, 433, 404, 28)

        self.connect_checkbox_text = QLabel('Отключить автоподключение', self)
        self.connect_checkbox_text.setGeometry(55, 261, 244, 15)

        self.downloader = Downloader("", "", "")  # Инициализируем downloader без URL и пути
        self.downloader.progress_updated.connect(self.update_progress)
        self.downloader.finished.connect(self.on_download_finished)
        self.downloader.error_occurred.connect(self.on_download_error)

        self.change_path.setObjectName("change_path")
        self.logo.setObjectName("logo")
        self.username_label.setObjectName("username_label")
        self.password_label.setObjectName("password_label")
        self.password_entry.setObjectName("password_entry")
        self.username_entry.setObjectName("username_entry")
        self.save_button.setObjectName("save_button")
        self.show_password_button.setObjectName("show_password_button")
        self.download_button.setObjectName("download_button")
        self.download_mods_button.setObjectName("download_mods_button")
        self.launch_button.setObjectName("launch_button")
        self.connect_checkbox.setObjectName("connect_checkbox")
        self.connect_checkbox_text.setObjectName("connect_checkbox_text")
        self.progress_bar.setObjectName("progress_bar")
        self.buttonMinimize.setObjectName('buttonMinimize')
        self.buttonClose.setObjectName('buttonClose')

        style_file = self.resource_path("style.qss")
        with open(style_file, "r") as f:
            _style = f.read()
        self.setStyleSheet(_style)
        current_directory = os.getcwd()
        credentials_file_path = os.path.join(current_directory, "credentials.json")
        try:
            with open(credentials_file_path, 'r') as file:
                credentials = json.load(file)
                username = credentials.get("username")
                password = credentials.get("password")
            if username:
                self.username_entry.setText(username)
            if password:
                self.password_entry.setText(password)
        except FileNotFoundError: 
            pass
        self.check_download_status()
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)

    def update_bat_file(self):
        current_directory = os.getcwd()
        print(f"Current Directory: {current_directory}")  
        relative_bat_file_path = 'start_orig.bat'
        bat_file_path = os.path.join(current_directory, relative_bat_file_path)
        print(f"BAT File Path: {bat_file_path}")
        with open(bat_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        updated_content = content.replace('$_local', current_directory)
        new_bat_file_path = os.path.join(current_directory, 'start.bat')
        with open(new_bat_file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def save_credentials(self):
        username = self.username_entry.text()
        password = self.password_entry.text()
        data = json.dumps({"agent":{"name":"Minecraft","version":1}, "username":username,"password":password})
        headers = {'Content-Type': 'application/json'}
        r = requests.post('***', data=data, headers=headers)
        current_directory = os.getcwd()
        file_path = os.path.join(current_directory, "credentials.json")
        credentials = {
            "username": username,
            "password": password,
        }
        credentials["add_data"] = json.loads(r.text)
        with open(file_path, 'w') as file:
            json.dump(credentials, file)

    def toggle_password_visibility(self):
        if self.show_password_button.isChecked():
            self.password_entry.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_button.setText('Скрыть пароль')
        else:
            self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_button.setText('Показать пароль')

    def download_version_files(self):
        url = "***"
        script_directory = os.getcwd()
        self.download_button.setEnabled(False)
        self.downloader.url = url
        self.downloader.download_path = script_directory
        self.downloader.extract_path = script_directory
        self.start_download_thread()

    def download_mods(self):
        url = "***"  # Replace with the actual URL for downloading mods
        script_directory = os.getcwd()
        extracted_path = os.path.join(script_directory, "minecraft")
        self.download_mods_button.setEnabled(False)
        self.downloader.url = url
        self.downloader.download_path = extracted_path
        self.downloader.extract_path = extracted_path
        self.start_download_thread()

    def start_download_thread(self):
        self.download_thread = QThread()
        self.downloader.moveToThread(self.download_thread)
        self.download_thread.started.connect(self.downloader.download_files)
        self.download_thread.start()

    def on_download_finished(self):
        QMessageBox.information(None, "Успех", "Файлы успешно скачаны.")
        self.launch_button.setEnabled(True)
        self.download_button.setEnabled(True)
        self.download_mods_button.setEnabled(True)

    def on_download_error(self, error):
        QMessageBox.warning(None, "Ошибка", f"Ошибка при скачивании файлов: {error}")
        self.download_button.setEnabled(True)
        self.download_mods_button.setEnabled(True)

    def launch_minecraft(self):
        self.launch_button.setEnabled(False)
        username = self.username_entry.text()

        if not username:
            QMessageBox.warning(None, "Ошибка", "Введите никнейм.")
            return
        
        with open("credentials.json", 'r') as file:
            credentials = json.load(file)
        
        minecraft_thread = Thread(target=self.launch_minecraft_thread, args=(username, credentials))
        minecraft_thread.start()

    def launch_minecraft_thread(self, username, credentials):
        script_directory = os.getcwd()
        minecraft_path = script_directory  # Используем текущую директорию скрипта
        not_connect_to_server = self.connect_checkbox.isChecked()
        ip_address = get_server_ip()
        os.environ['USERNAME'] = credentials['add_data']['selectedProfile']['name']
        os.environ['UUID'] = credentials['add_data']['selectedProfile']['id']
        os.environ['clientId'] = credentials['add_data']['clientToken']
        os.environ['accessToken'] = credentials['add_data']['accessToken']
        if not not_connect_to_server:
            os.environ['SERVER'] = f"--quickPlayMultiplayer {ip_address}"
            command = [r"start.bat"]
            subprocess.run(command, shell=True, cwd=script_directory)
        else:
            command = [r"start.bat"]
            os.environ['SERVER'] = f" "
            subprocess.run(command, shell=True, cwd=script_directory)

        not_connect_to_server = self.connect_checkbox.isChecked()
        self.launch_button.setEnabled(True)

    def check_download_status(self):
        version = "Minecraft"
        script_directory = os.getcwd()
        downloaded_files_path = os.path.join(script_directory, version)  # Путь к скачанным файлам

        if os.path.exists(downloaded_files_path) and os.listdir(downloaded_files_path):
            self.launch_button.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    ex = MinecraftLauncher()
    with loop:
        sys.exit(loop.run_forever())

import os
import sys
import json
import subprocess
import zipfile
import requests
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox, QMainWindow, QProgressBar, QSlider
from qasync import QEventLoop, QApplication
from PyQt6.QtGui import QPixmap
import asyncio
from threading import Thread
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, Qt

#17.08.2024
#Это все изменения. 1.0.8
#f"--quickPlayMultiplayer {ip_address}"
#f"--server {ip_address}"
#26.08.2024 фикс бага потоков скачивания 1.0.9
#добавление выделения памяти 28.08.2024 1.0.10
#04.09.2024 кнопка сменить пути удалена добавлено в при загрузке файлов и самой программы
def get_server_ip():
    try:
        response = requests.get('****')
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
    github_repo_url = "****"
    try:
        response = requests.get(github_repo_url)
        if response.status_code == 200:
            release_info = response.json()
            latest_version = release_info['tag_name']
            app_version = "1.0.11"  # Ваш текущий номер версии
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
        self.update_bat_file()
        self.download_thread = None
        self.downloader = None
        self.check_credentials_file()

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

        self.show_password_button = QPushButton('Показать пароль', self)
        self.show_password_button.setGeometry(290, 206, 167, 35)
        self.show_password_button.setCheckable(True)
        self.show_password_button.clicked.connect(self.toggle_password_visibility)

        self.download_button = QPushButton('Скачать файлы', self)
        self.download_button.setGeometry(30, 300, 167, 35)
        self.download_button.clicked.connect(self.download_version_files)

        self.download_mods_button = QPushButton('Скачать моды', self)
        self.download_mods_button.setGeometry(207, 300, 167, 35)
        self.download_mods_button.clicked.connect(self.download_mods)

        self.launch_button = QPushButton('Запустить игру', self)
        self.launch_button.setGeometry(30, 410, 167, 35)
        self.launch_button.setEnabled(False)
        self.launch_button.clicked.connect(self.launch_minecraft)

        self.connect_checkbox = QCheckBox(self)
        self.connect_checkbox.setGeometry(30, 261, 15, 15)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(30, 465, 404, 28)

        self.connect_checkbox_text = QLabel('Отключить автоподключение', self)
        self.connect_checkbox_text.setGeometry(55, 261, 244, 15)

        self.memory_label = QLabel('Выделенная память (МБ):', self)
        self.memory_label.setGeometry(30, 330, 200, 35)
        self.memory_entry = QLineEdit(self)
        self.memory_entry.setGeometry(30, 360, 50, 25)
        self.memory_apply_button = QPushButton('Применить', self)
        self.memory_apply_button.setGeometry(100, 360, 100, 25)
        self.memory_apply_button.clicked.connect(self.apply_memory_size)


        self.downloader = Downloader("", "", "")  # Инициализируем downloader без URL и пути
        self.downloader.progress_updated.connect(self.update_progress)
        self.downloader.finished.connect(self.on_download_finished)
        self.downloader.error_occurred.connect(self.on_download_error)

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
        self.memory_label.setObjectName("memory_label")
        self.memory_entry.setObjectName("memory_entry")
        self.memory_apply_button.setObjectName("memory_apply_button")

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


    def check_credentials_file(self):
        # Check if the 'credentials.json' file exists in the root directory
        if not os.path.isfile('credentials.json'):
            self.memory_apply_button.setEnabled(False)
        else:
            self.memory_apply_button.setEnabled(True)

    def apply_memory_size(self):
        try:
            memory_size = int(self.memory_entry.text())
            if memory_size <= 0:
                raise ValueError

            file_path = 'credentials.json'
            if os.path.isfile(file_path):
                with open(file_path, 'r') as file:
                    data = json.load(file)

                data['add_data']['memory'] = str(memory_size)
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)
                print(f"Memory size updated to: {memory_size} MB")
            else:
                print("credentials.json file does not exist.")
        except ValueError:
            print("Invalid memory size. Please enter a positive integer.")



    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)

    def update_bat_file(self):
        current_directory = os.getcwd()
        relative_bat_file_path = 'start_orig.bat'
        bat_file_path = os.path.join(current_directory, relative_bat_file_path)

        if not os.path.isfile(bat_file_path):  # Проверка существования файла
            QMessageBox.information(self, "Уведомление!", "Пожалуйста, скачайте файлы игры.")
            return  # Выход из функции, если файл отсутствует

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
        data = json.dumps({"agent": {"name": "Minecraft", "version": 1}, "username": username, "password": password})
        headers = {'Content-Type': 'application/json'}
        r = requests.post('****', data=data, headers=headers)
        credentials = {
            "username": username,
            "password": password,
            "add_data": json.loads(r.text)
        }
        credentials["add_data"]["memory"] = "3072"
        current_directory = os.getcwd()
        file_path = os.path.join(current_directory, "credentials.json")
        with open(file_path, 'w') as file:
            json.dump(credentials, file, indent=4)
        self.memory_apply_button.setEnabled(True)


    def toggle_password_visibility(self):
        if self.show_password_button.isChecked():
            self.password_entry.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_button.setText('Скрыть пароль')
        else:
            self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_button.setText('Показать пароль')

    def download_version_files(self):
        url = "****"
        script_directory = os.getcwd()
        self.download_button.setEnabled(False)
        self.start_download_thread(url, script_directory, script_directory)

    def download_mods(self):
        url = "****"
        script_directory = os.getcwd()
        extracted_path = os.path.join(script_directory, "minecraft")
        self.download_mods_button.setEnabled(False)
        self.start_download_thread(url, extracted_path, extracted_path)

    def start_download_thread(self, url, download_path, extract_path):
        # Если поток уже существует, завершаем его
        if self.download_thread is not None:
            self.download_thread.quit()
            self.download_thread.wait()
            self.download_thread = None

        # Создаем новый объект Downloader для нового скачивания
        self.downloader = Downloader(url, download_path, extract_path)
        self.download_thread = QThread()
        self.downloader.moveToThread(self.download_thread)
        self.download_thread.started.connect(self.downloader.download_files)
        self.downloader.progress_updated.connect(self.update_progress)
        self.downloader.finished.connect(self.on_download_thread_finished)
        self.downloader.error_occurred.connect(self.on_download_error)
        self.download_thread.start()

    def on_download_thread_finished(self):
        if self.download_thread is not None:
            self.download_thread.quit()
            self.download_thread.wait()
            self.download_thread = None
        self.on_download_finished()

    def on_download_finished(self):
        QMessageBox.information(None, "Успех", "Файлы успешно скачаны.")
        self.update_bat_file()
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
        os.environ['memory'] = credentials['add_data']['memory']
        if not not_connect_to_server:
            os.environ['SERVER'] = f"--server {ip_address}"
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

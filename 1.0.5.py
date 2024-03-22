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

#22.03.2024
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
    # URL, где содержится информация о последней версии на GitHub
    github_repo_url = "****"

    try:
        # Отправляем GET-запрос к репозиторию GitHub
        response = requests.get(github_repo_url)
        
        # Проверяем успешность запроса
        if response.status_code == 200:
            # Получаем информацию о релизе из ответа
            release_info = response.json()
            latest_version = release_info['tag_name']

            # Текущая версия вашего приложения
            app_version = "1.0.5"  # Ваш текущий номер версии

            # Проверяем, совпадает ли версия
            if latest_version != app_version:
                # Запускаем updater.exe
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
    
    
    @pyqtSlot()
    def download_files(self):
        try:
            script_directory = os.getcwd()
            url = "****"
            response = requests.get(url, stream=True)
            downloaded_file_path = os.path.join(script_directory, "Files.zip")

            # Получаем общий размер файла для отслеживания прогресса
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(downloaded_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int(downloaded_size / total_size * 100)
                        # Эмитируем сигнал обновления прогресса загрузки
                        self.progress_updated.emit(progress)

            with zipfile.ZipFile(downloaded_file_path, 'r') as zip_ref:
                zip_ref.extractall(script_directory)
            os.remove(downloaded_file_path)

            # Эмитируем сигнал о завершении скачивания
            self.finished.emit()
        except Exception as e:
            # Здесь вы можете обработать ошибку скачивания
            print(f"Ошибка: {e}")


class MinecraftLauncher(QMainWindow):
    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def __init__(self):
        super().__init__()
        self.downloader = Downloader()
        self.downloader.finished.connect(self.on_download_finished)        
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

        # Устанавливаем изображение в QLabel
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
        self.download_button.setGeometry(30, 319, 167, 35)
        self.download_button.clicked.connect(self.download_version_files)
        

        self.launch_button = QPushButton('Запустить игру', self)
        self.launch_button.setGeometry(207, 319, 167, 35)
        self.launch_button.setEnabled(False)
        self.launch_button.clicked.connect(self.launch_minecraft)

        self.connect_checkbox = QCheckBox(self)
        self.connect_checkbox.setGeometry(30, 261, 15, 15)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(30, 383, 404, 28)
        self.downloader.progress_updated.connect(self.update_progress)

        self.connect_checkbox_text = QLabel('Отключить автоподключение', self)
        self.connect_checkbox_text.setGeometry(55, 261, 244, 15)
        
        self.logo.setObjectName("logo")
        self.username_label.setObjectName("username_label")
        self.password_label.setObjectName("password_label")
        self.password_entry.setObjectName("password_entry")
        self.username_entry.setObjectName("username_entry")
        self.save_button.setObjectName("save_button")
        self.show_password_button.setObjectName("show_password_button")
        self.download_button.setObjectName("download_button")
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
                # Читаем содержимое файла
                credentials = json.load(file)

                # Извлекаем username и password из файла
                username = credentials.get("username")
                password = credentials.get("password")
                 #Вставляем считанные данные в поля ввода
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
            # Получаем текущие координаты окна
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Перемещаем окно на новые координаты
            self.move(self.pos() + event.pos() - self.offset)
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    def save_credentials(self):
        username = self.username_entry.text()
        password = self.password_entry.text()
        data = json.dumps({"agent":{"name":"Minecraft","version":1}, "username":username,"password":password})
        headers = {'Content-Type': 'application/json'}
        r = requests.post('****', data=data, headers=headers)
        # Получаем текущую директорию
        current_directory = os.getcwd()

        # Формируем путь к файлу, в который будем сохранять данные
        file_path = os.path.join(current_directory, "credentials.json")

        credentials = {
            "username": username,
            "password": password,
        }
        credentials["add_data"] = json.loads(r.text)
        # Открываем файл на запись (режим 'w') в формате JSON
        with open(file_path, 'w') as file:
        # Записываем данные в файл в формате JSON
            json.dump(credentials, file)




    def toggle_password_visibility(self):
        if self.show_password_button.isChecked():
            self.password_entry.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_button.setText('Скрыть пароль')
        else:
            self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_button.setText('Показать пароль')

    def download_version_files(self):
        self.download_button.setEnabled(False)
        self.download_thread = QThread()
        self.downloader.moveToThread(self.download_thread)
        self.download_thread.started.connect(self.downloader.download_files)
        self.download_thread.start()
    def on_download_finished(self):
        QMessageBox.information(None, "Успех", f"Файлы Minecraft успешно скачаны.")
        self.launch_button.setEnabled(True)
        self.download_button.setEnabled(True)
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
            # Если папка существует и не пуста, активируем кнопку
            self.launch_button.setEnabled(True)

if __name__ == '__main__':

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    ex = MinecraftLauncher()
    with loop:
        sys.exit(loop.run_forever())

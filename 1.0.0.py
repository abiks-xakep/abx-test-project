import os
import sys
import json
import subprocess
import zipfile
import requests
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox, QProgressBar
from qasync import QEventLoop, QApplication
import asyncio
from threading import Thread
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
def check_for_updates():
    # URL, где содержится версия приложения
    version_url = "*****"

    try:
        # Отправляем GET-запрос к веб-серверу
        response = requests.get(version_url)
        
        # Проверяем успешность запроса
        if response.status_code == 200:
            # Получаем версию из ответа
            server_version = response.text.strip()

            # Текущая версия вашего приложения
            app_version = "1.0.0"

            # Проверяем, совпадает ли версия
            if server_version == app_version:
                QMessageBox.information(None, "Обновления", "Последняя версия программы.")
            else:
                QMessageBox.warning(None, "Обновления", "Обнаружена новая версия программы. Свяжитесь с администратором для получения информации")
        else:
            QMessageBox.critical(None, "Ошибка", f"Ошибка при получении версии: {response.status_code}")
    except Exception as e:
        QMessageBox.critical(None, "Ошибка", f"Ошибка: {e}")

def main():
    script_directory = os.getcwd()
    check_for_updates()



class Downloader(QObject):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal()
    
    
    @pyqtSlot()
    def download_files(self):
        try:
            script_directory = os.getcwd()
            url = "********"
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


class MinecraftLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.downloader = Downloader()
        self.downloader.finished.connect(self.on_download_finished)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Minecraft Launcher')
        self.setGeometry(100, 100, 500, 500)
        

        self.username_label = QLabel('Игровое имя:', self)
        self.username_label.move(20, 20)

        self.password_label = QLabel('Пароль:', self)
        self.password_label.move(200, 20)

        self.password_entry = QLineEdit(self)
        self.password_entry.move(200, 50)
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)

        self.username_entry = QLineEdit(self)
        self.username_entry.move(20, 50)   

        self.save_button = QPushButton('Сохранить изменения', self)
        self.save_button.move(20, 80)
        self.save_button.clicked.connect(self.save_credentials)


        self.show_password_button = QPushButton('Показать пароль', self)
        self.show_password_button.move(200, 80)
        self.show_password_button.setCheckable(True)
        self.show_password_button.clicked.connect(self.toggle_password_visibility)

        self.download_button = QPushButton('Скачать файлы', self)
        self.download_button.move(20, 150)
        self.download_button.clicked.connect(self.download_version_files)

        self.launch_button = QPushButton('Запустить игру', self)
        self.launch_button.move(20, 180)
        self.launch_button.setEnabled(False)
        self.launch_button.clicked.connect(self.launch_minecraft)

        self.connect_checkbox = QCheckBox('Подключаться автоматически к серверу.', self)
        self.connect_checkbox.move(20, 110)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(20, 220, 460, 20)

        self.downloader.progress_updated.connect(self.update_progress)

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
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    def save_credentials(self):
        username = self.username_entry.text()
        password = self.password_entry.text()
        data = json.dumps({"agent":{"name":"Minecraft","version":1}, "username":username,"password":password})
        headers = {'Content-Type': 'application/json'}
        r = requests.post('*********', data=data, headers=headers)
        # Получаем текущую директорию
        current_directory = os.getcwd()

        # Формируем путь к файлу, в который будем сохранять данные
        file_path = os.path.join(current_directory, "credentials.json")

        credentials = {
            "username": username,
            "password": password,
            # Предполагается, что r.text у вас имеет нужный формат
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
        self.download_thread = QThread()
        self.downloader.moveToThread(self.download_thread)
        self.download_thread.started.connect(self.downloader.download_files)
        self.download_thread.start()
    def on_download_finished(self):
        QMessageBox.information(None, "Успех", f"Файлы Minecraft успешно скачаны.")
        self.launch_button.setEnabled(True)
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

        # Запуск Minecraft с установленной версией и никнеймом

        #generated_uuid = str(uuid.uuid4()).replace("-", "")
        script_directory = os.getcwd()
        minecraft_path = script_directory  # Используем текущую директорию скрипта
        connect_to_server = self.connect_checkbox.isChecked()
        if connect_to_server:
            os.environ['USERNAME'] = credentials['add_data']['selectedProfile']['name']
            os.environ['UUID'] = credentials['add_data']['selectedProfile']['id']
            os.environ['clientId'] = credentials['add_data']['clientToken']
            os.environ['accessToken'] = credentials['add_data']['accessToken']
            os.environ['server'] = "--server *********"
            command = [r"start.bat"]
            subprocess.run(command, shell=True, cwd=script_directory)
        else:
            os.environ['USERNAME'] = credentials['add_data']['selectedProfile']['name']
            os.environ['UUID'] = credentials['add_data']['selectedProfile']['id']
            os.environ['clientId'] = credentials['add_data']['clientToken']
            os.environ['accessToken'] = credentials['add_data']['accessToken']
            command = [r"start.bat"]
            subprocess.run(command, shell=True, cwd=script_directory)
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
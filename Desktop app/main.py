from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QApplication, QGridLayout,
    QVBoxLayout, QStackedWidget, QComboBox, QLabel, QHBoxLayout, QProgressBar, QInputDialog
)
from PySide6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QUrl
from qasync import QEventLoop, asyncSlot
import asyncio
from bleak import BleakScanner, BleakClient
import json
from PySide6.QtGui import QIcon
import os
import time
import datetime
from PySide6.QtMultimedia import QSoundEffect

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart mat")

        self.timer_duration = 45 * 60  # Default timer duration in seconds (45 minutes)
        self.remaining_time = self.timer_duration
        self.countdown_timer = QTimer()
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self.update_timer)
        self.timer_end_time = None
        self.is_timer_running = False
        self.animation = None

        self.daily_goal = 2500  # Default daily water consumption goal in milliliters
        self.current_water_intake = 0
        self.current_contribution = 0

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.create_view_setup())
        self.stacked_widget.addWidget(self.create_view_1())
        self.stacked_widget.addWidget(self.create_view_2())

        main_layout.addWidget(self.stacked_widget)

        self.saved_device = self.load_saved_device()
        self.ble_client = None
        self.load_water_data()

        self.showMinimized()

    def create_view_setup(self):
        view = QWidget()
        layout = QVBoxLayout(view)

        self.status_label = QLabel("Click 'Scan' to find BLE devices.")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.device_dropdown = QComboBox()
        layout.addWidget(self.device_dropdown)

        scan_button = QPushButton("Scan for Devices")
        scan_button.clicked.connect(self.scan_for_devices)
        layout.addWidget(scan_button)

        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.connect_to_device)
        layout.addWidget(connect_button)

        return view

    @asyncSlot()
    async def discover_devices(self):
        self.status_label.setText("Scanning for devices...")
        devices = await BleakScanner.discover()
        self.device_dropdown.clear()
        for device in devices:
            self.device_dropdown.addItem(f"{device.name} ({device.address})", device.address)
        self.status_label.setText("Select a device from the dropdown.")

    def scan_for_devices(self):
        self.discover_devices()

    @asyncSlot()
    async def connect_to_selected_device(self, address):
        self.status_label.setText(f"Connecting to {address}...")
        try:
            self.ble_client = BleakClient(address)
            await self.ble_client.connect()
            if self.ble_client.is_connected:
                self.status_label.setText(f"Connected to {address}")
                self.save_device(address)
                characteristic_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"
                try:
                    await self.ble_client.start_notify(characteristic_uuid, self.handle_notification)
                    self.status_label.setText("Notification subscription successful.")
                except Exception as e:
                    self.status_label.setText(f"Failed to subscribe to notifications: {str(e)}")
                self.switch_view(0)
        except Exception as e:
            self.status_label.setText(f"Failed to connect: {str(e)}")
            if self.ble_client:
                await self.ble_client.disconnect()
                self.ble_client = None

    def handle_notification(self, sender, data):
        try:
            received_text = data.decode("utf-8")
            self.status_label.setText(f"Received: {received_text}")
            if received_text.isdigit() and int(received_text) > 0:
                contribution = int(received_text)
                self.current_water_intake += contribution
                self.update_water_progress()
                self.save_water_data()
                self.status_label.setText(f"Received {contribution} mL. Water intake updated.")
                if self.is_timer_running:
                    self.remaining_time = self.timer_duration
                    self.timer_end_time = time.time() + self.remaining_time
                    self.countdown_timer.start()
                    self.timer_label.setText(self.format_time(self.remaining_time))
        except Exception as e:
            self.status_label.setText(f"Failed to process notification: {str(e)}")

    def disconnect_device(self):
        if self.ble_client and self.ble_client.is_connected:
            asyncio.create_task(self.ble_client.disconnect())
            self.ble_client = None
            self.status_label.setText("Disconnected from device.")
            self.switch_view(-1)

    def closeEvent(self, event):
        if self.ble_client and self.ble_client.is_connected:
            asyncio.create_task(self.ble_client.disconnect())
        super().closeEvent(event)

    @asyncSlot()
    async def send_text(self, address, text):
        if not self.is_valid_address(address):
            self.status_label.setText("Invalid device address.")
            return
        if not self.ble_client or not self.ble_client.is_connected:
            self.status_label.setText("Device is not connected.")
            return
        try:
            characteristic_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"
            await self.ble_client.write_gatt_char(characteristic_uuid, text.encode())
            self.status_label.setText(f"Sent: {text}")
        except Exception as e:
            self.status_label.setText(f"Failed to send text: {str(e)}")

    def connect_to_device(self):
        selected_index = self.device_dropdown.currentIndex()
        if selected_index == -1:
            self.status_label.setText("No device selected.")
            return
        address = self.device_dropdown.currentData()
        if not address:
            self.status_label.setText("Invalid device address.")
            return
        self.connect_to_selected_device(address)

    def create_view_1(self):
        view = QWidget()
        layout = QVBoxLayout(view)

        self.timer_label = QLabel(self.format_time(self.remaining_time))
        self.timer_label.setObjectName("timer_label")
        self.timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timer_label)

        self.pause_play_button = QPushButton()
        self.pause_play_button.setObjectName("pause_play_button")
        self.pause_play_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "play.png")))
        self.pause_play_button.setIconSize(QSize(26, 26))
        self.pause_play_button.setFixedSize(64, 64)
        self.pause_play_button.clicked.connect(self.toggle_timer)
        layout.addWidget(self.pause_play_button, alignment=Qt.AlignCenter)

        progress_layout = QHBoxLayout()
        self.water_progress = QProgressBar()
        self.water_progress.setRange(0, self.daily_goal)
        self.water_progress.setValue(self.current_water_intake)
        self.water_progress.setTextVisible(True)
        self.water_progress.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.water_progress)

        self.percentage_label = QLabel(f"{self.calculate_percentage()}%")
        progress_layout.addWidget(self.percentage_label)

        layout.addLayout(progress_layout)

        icons_path = os.path.join(os.path.dirname(__file__), "icons")
        services = [
            ("Reset", os.path.join(icons_path, "reset.png"), "Reset Message"),
            ("Daily Intake", os.path.join(icons_path, "water.png"), "Daily Intake Message"),
            ("Settings", os.path.join(icons_path, "clock.png"), None),
        ]

        grid = QGridLayout()
        for i, (text, icon_path, message) in enumerate(services):
            button = QPushButton()
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(64, 64))
            button.setText(text)
            if text == "Reset":
                button.setMinimumSize(300, 100)
                button.clicked.connect(self.reset_action)
                grid.addWidget(button, 0, 0, 1, 2)  # Span two columns
            else:
                button.setMinimumSize(150, 100)
                if text == "Settings":
                    button.clicked.connect(lambda: self.switch_view(1))
                elif text == "Daily Intake":
                    button.clicked.connect(self.set_daily_goal)
                else:
                    button.clicked.connect(lambda _, msg=message: self.send_serial_message(msg))
                grid.addWidget(button, 1, i % 2)

        layout.addLayout(grid)
        layout.setAlignment(Qt.AlignTop)
        return view

    def calculate_percentage(self):
        if self.daily_goal == 0:
            return 0
        return int((self.current_water_intake / self.daily_goal) * 100)

    def update_water_progress(self):
        self.water_progress.setValue(self.current_water_intake)
        self.water_progress.setFormat(f"{self.current_water_intake} / {self.daily_goal} mL")
        self.percentage_label.setText(f"{self.calculate_percentage()}%")

    def set_daily_goal(self):
        self.load_water_data()
        new_goal, ok = QInputDialog.getInt(
            self,
            "Set Daily Goal",
            "Enter your daily water goal (mL):",
            self.daily_goal,
            1,
            10000,
        )
        if ok:
            self.daily_goal = new_goal
            self.water_progress.setRange(0, self.daily_goal)
            self.update_water_progress()
            self.save_water_data()
            self.status_label.setText(f"Daily goal set to {self.daily_goal} mL.")

    def load_water_data(self):
        try:
            if not os.path.exists("data.json"):
                self.save_water_data()
                return
            with open("data.json", "r") as file:
                data = json.load(file)
                saved_date = data.get("date", None)
                current_date = datetime.date.today().isoformat()
                if saved_date != current_date:
                    self.current_water_intake = 0
                    self.current_contribution = 0
                else:
                    self.current_water_intake = data.get("current_water_intake", self.current_water_intake)
                    self.current_contribution = data.get("current_contribution", self.current_contribution)
                self.daily_goal = data.get("daily_goal", self.daily_goal)
                self.timer_duration = data.get("timer_duration", self.timer_duration)
                self.remaining_time = self.timer_duration
                self.water_progress.setRange(0, self.daily_goal)
                self.water_progress.setValue(self.current_water_intake)
                self.update_water_progress()
                self.timer_label.setText(self.format_time(self.remaining_time))
        except Exception as e:
            print(f"Failed to load water data: {str(e)}")

    def save_water_data(self):
        try:
            data = {}
            if os.path.exists("data.json"):
                with open("data.json", "r") as file:
                    data = json.load(file)
            data["daily_goal"] = self.daily_goal
            data["current_water_intake"] = self.current_water_intake
            data["current_contribution"] = self.current_contribution
            data["timer_duration"] = self.timer_duration
            data["date"] = datetime.date.today().isoformat()
            with open("data.json", "w") as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print(f"Failed to save water data: {str(e)}")

    def send_serial_message(self, message):
        if not self.saved_device:
            self.status_label.setText("No device connected.")
            return
        if not self.is_valid_address(self.saved_device):
            self.status_label.setText("Invalid saved device address.")
            return
        asyncio.create_task(self.send_text(self.saved_device, message))

    def timer_action(self):
        self.status_label.setText("Timer service selected.")

    def heat_action(self):
        self.status_label.setText("Heat service selected.")

    def daily_intake_action(self):
        self.status_label.setText("Daily Intake service selected.")

    def reset_action(self):
        self.remaining_time = self.timer_duration
        self.timer_end_time = None
        self.timer_label.setText(self.format_time(self.remaining_time))
        self.countdown_timer.stop()
        self.is_timer_running = False
        self.pause_play_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "play.png")))
        self.status_label.setText("Timer reset.")

    def is_valid_address(self, address):
        return isinstance(address, str) and len(address) > 0

    def create_view_2(self):
        view = QWidget()
        layout = QVBoxLayout(view)

        back_button = QPushButton("Back")
        back_button.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        back_button.clicked.connect(lambda: self.switch_view(0))
        layout.addWidget(back_button, alignment=Qt.AlignLeft)

        timer_label = QLabel("Set Timer Duration:")
        timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d2d77;")
        timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(timer_label)

        timer_input_layout = QHBoxLayout()

        self.hours_dropdown = QComboBox()
        self.hours_dropdown.setEditable(True)
        self.hours_dropdown.addItems([f"{i:02}" for i in range(24)])
        self.hours_dropdown.setCurrentText("01")
        self.hours_dropdown.setStyleSheet("font-size: 14px; padding: 5px; min-width: 60px;")
        timer_input_layout.addWidget(self.hours_dropdown)

        colon_label_1 = QLabel(":")
        colon_label_1.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d2d77; padding: 0 10px;")
        timer_input_layout.addWidget(colon_label_1)

        self.minutes_dropdown = QComboBox()
        self.minutes_dropdown.setEditable(True)
        self.minutes_dropdown.addItems([f"{i:02}" for i in range(60)])
        self.minutes_dropdown.setCurrentText("00")
        self.minutes_dropdown.setStyleSheet("font-size: 14px; padding: 5px; min-width: 60px;")
        timer_input_layout.addWidget(self.minutes_dropdown)

        colon_label_2 = QLabel(":")
        colon_label_2.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d2d77; padding: 0 10px;")
        timer_input_layout.addWidget(colon_label_2)

        self.seconds_dropdown = QComboBox()
        self.seconds_dropdown.setEditable(True)
        self.seconds_dropdown.addItems([f"{i:02}" for i in range(60)])
        self.seconds_dropdown.setCurrentText("00")
        self.seconds_dropdown.setStyleSheet("font-size: 14px; padding: 5px; min-width: 60px;")
        timer_input_layout.addWidget(self.seconds_dropdown)

        timer_input_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(timer_input_layout)

        update_timer_button = QPushButton("Update Timer")
        update_timer_button.clicked.connect(self.update_timer_duration)
        layout.addWidget(update_timer_button, alignment=Qt.AlignCenter)

        forget_button = QPushButton("Forget Device")
        forget_button.clicked.connect(self.forget_device)
        layout.addWidget(forget_button, alignment=Qt.AlignCenter)

        layout.setAlignment(Qt.AlignTop)
        return view
    
    def set_timer_dropdown_values(self):
        hours = self.timer_duration // 3600
        minutes = (self.timer_duration % 3600) // 60
        seconds = self.timer_duration % 60

        self.hours_dropdown.setCurrentText(f"{hours:02}")
        self.minutes_dropdown.setCurrentText(f"{minutes:02}")
        self.seconds_dropdown.setCurrentText(f"{seconds:02}")

    def update_timer_duration(self):
        try:
            hours = int(self.hours_dropdown.currentText())
            minutes = int(self.minutes_dropdown.currentText())
            seconds = int(self.seconds_dropdown.currentText())
            if hours < 0 or minutes < 0 or seconds < 0 or minutes >= 60 or seconds >= 60:
                raise ValueError("Invalid time values.")
            self.timer_duration = hours * 3600 + minutes * 60 + seconds
            self.remaining_time = self.timer_duration
            self.timer_label.setText(self.format_time(self.remaining_time))
            self.status_label.setText("Timer duration updated.")
            self.save_water_data()
        except ValueError:
            self.status_label.setText("Invalid input. Please select valid numbers.")

    def start_timer(self):
        if self.remaining_time > 0:
            self.timer_end_time = time.time() + self.remaining_time + 1
            self.countdown_timer.start()
            self.timer_label.setText(self.format_time(self.remaining_time))
            self.status_label.setText("Timer started.")
        else:
            self.status_label.setText("Set a valid timer duration before starting.")

    def update_timer(self):
        if self.timer_end_time:
            self.remaining_time = max(0, int(self.timer_end_time - time.time()))
            self.timer_label.setText(self.format_time(self.remaining_time))
            if self.remaining_time == 0:
                self.countdown_timer.stop()
                self.timer_label.setText("00:00:00")
                self.status_label.setText("Time's up!")
                self.play_alarm()  # Play alarm when timer ends
                self.pause_play_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "play.png")))  # Set play icon
                self.is_timer_running = False  # Ensure timer is marked as not running
        else:
            self.countdown_timer.stop()
            self.status_label.setText("Timer not running.")

    def play_alarm(self):
        alarm_sound_path = os.path.join(os.path.dirname(__file__), "alarm.wav")
        if os.path.exists(alarm_sound_path):
            self.alarm_sound = QSoundEffect(self)
            self.alarm_sound.setSource(QUrl.fromLocalFile(alarm_sound_path))
            self.alarm_sound.setLoopCount(1)  # Play the sound only once
            self.alarm_sound.setVolume(0.5)  # Set volume (0.0 to 1.0)
            self.alarm_sound.play()
        else:
            self.status_label.setText("Alarm sound file not found.")

    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def save_device(self, address):
        try:
            data = {}
            if os.path.exists("data.json"):
                with open("data.json", "r") as file:
                    data = json.load(file)
            data["address"] = address
            with open("data.json", "w") as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            self.status_label.setText(f"Failed to save device: {str(e)}")

    def load_saved_device(self):
        try:
            with open("data.json", "r") as file:
                data = json.load(file)
                return data.get("address")
        except FileNotFoundError:
            return None
        except Exception as e:
            self.status_label.setText(f"Failed to load device: {str(e)}")
            return None

    def forget_device(self):
        try:
            if os.path.exists("data.json"):
                with open("data.json", "r") as file:
                    data = json.load(file)
                data.pop("address", None)
                with open("data.json", "w") as file:
                    json.dump(data, file)
                self.saved_device = None
                self.status_label.setText("Device forgotten.")
                self.switch_view(-1)
            else:
                self.status_label.setText("No device to forget.")
        except Exception as e:
            self.status_label.setText(f"Failed to forget device: {str(e)}")

    async def auto_connect_to_saved_device(self):
        if self.saved_device:
            if not self.is_valid_address(self.saved_device):
                self.status_label.setText("Invalid saved device address.")
                return
            self.status_label.setText(f"Auto-connecting to {self.saved_device}...")
            await self.connect_to_selected_device(self.saved_device)

    def switch_view(self, index):
        self.stacked_widget.setCurrentIndex(index + 1)
        if index == 1:
            self.set_timer_dropdown_values()

    def toggle_timer(self):
        if self.is_timer_running:
            self.countdown_timer.stop()
            self.animate_icon_transition("pause.png", "play.png")
            self.status_label.setText("Timer paused.")
        else:
            self.start_timer()
            self.animate_icon_transition("play.png", "pause.png")
            self.status_label.setText("Timer resumed.")
        self.is_timer_running = not self.is_timer_running

    def animate_icon_transition(self, from_icon, to_icon):
        if self.animation:
            self.animation.stop()

        self.animation = QPropertyAnimation(self.pause_play_button, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.pause_play_button.geometry())
        self.animation.setEndValue(self.pause_play_button.geometry())
        self.animation.start()

        self.animation.finished.connect(lambda: self.pause_play_button.setIcon(
            QIcon(os.path.join(os.path.dirname(__file__), "icons", to_icon))
        ))


if __name__ == "__main__":
    app = QApplication([])

    app.setStyleSheet("QMainWindow { background-color: #e8eaf6; }")

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    try:
        qss_path = os.path.join(os.path.dirname(__file__), "style.qss")
        with open(qss_path, "r") as file:
            app.setStyleSheet(file.read())
    except FileNotFoundError:
        print("QSS file not found. Using default styles.")

    window = MainWindow()
    window.show()

    def start_auto_connect():
        asyncio.run_coroutine_threadsafe(window.auto_connect_to_saved_device(), loop)

    QTimer.singleShot(0, start_auto_connect)

    with loop:
        loop.run_forever()
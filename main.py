from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QApplication, QGridLayout,
    QVBoxLayout, QStackedWidget, QComboBox, QLabel, QCheckBox, QLineEdit, QHBoxLayout, QProgressBar, QInputDialog  # Add QProgressBar and QInputDialog
)
from PySide6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QRect  # Add QSize, QPropertyAnimation, and QRect to the imports
from PySide6.QtCore import QTimer as QCountdownTimer  # Add QTimer for countdown functionality
from qasync import QEventLoop, asyncSlot
import asyncio
from bleak import BleakScanner, BleakClient
import json  # Added for saving/loading device information
from PySide6.QtGui import QIcon
import os  # Add import for os
import time  # Add import for time library

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart mat companion")

        # Initialize timer variables before creating views
        self.timer_duration = 60 * 60  # Default timer duration in seconds (60 minutes)
        self.remaining_time = self.timer_duration
        self.countdown_timer = QTimer()  # Use QTimer directly
        self.countdown_timer.setInterval(1000)  # Set interval to 1 second
        self.countdown_timer.timeout.connect(self.update_timer)  # Ensure connection
        self.timer_end_time = None  # Store the end time for the countdown
        self.is_timer_running = False  # Track the state of the timer (paused or running)
        self.animation = None  # Store the animation object for the pause/play button

        self.daily_goal = 2000  # Default daily water consumption goal in milliliters
        self.current_water_intake = 0  # Track the current water intake
        self.load_water_data()  # Load water data from the JSON file

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)

        # Commented out the dropdown menu for switching views
        # self.dropdown = QComboBox()
        # self.dropdown.addItems(["Buttons", "Settings"])  # Correctly map dropdown options
        # self.dropdown.currentIndexChanged.connect(self.switch_view)  # Connect to view switching
        # self.dropdown.hide()  # Initially hide the dropdown menu

        # Create a stacked widget to hold multiple views
        self.stacked_widget = QStackedWidget()

        # Add views to the stacked widget
        self.stacked_widget.addWidget(self.create_view_setup())  # Setup View
        self.stacked_widget.addWidget(self.create_view_1())  # Buttons View
        self.stacked_widget.addWidget(self.create_view_2())  # Settings View

        # Commented out adding the dropdown to the main layout
        # main_layout.addWidget(self.dropdown)
        main_layout.addWidget(self.stacked_widget)

        # Load saved device information
        self.saved_device = self.load_saved_device()
        self.ble_client = None  # Store the BleakClient instance

    def create_view_setup(self):
        """Create the setup view for BLE connection."""
        view = QWidget()
        layout = QVBoxLayout(view)

        # Label to display instructions
        self.status_label = QLabel("Click 'Scan' to find BLE devices.")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Dropdown to list discovered devices
        self.device_dropdown = QComboBox()
        layout.addWidget(self.device_dropdown)

        # Button to scan for devices
        scan_button = QPushButton("Scan for Devices")
        scan_button.clicked.connect(self.scan_for_devices)
        layout.addWidget(scan_button)

        # Button to connect to the selected device
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.connect_to_device)
        layout.addWidget(connect_button)

        return view

    @asyncSlot()
    async def discover_devices(self):
        """Discover BLE devices asynchronously."""
        self.status_label.setText("Scanning for devices...")
        devices = await BleakScanner.discover()
        self.device_dropdown.clear()
        for device in devices:
            self.device_dropdown.addItem(f"{device.name} ({device.address})", device.address)
        self.status_label.setText("Select a device from the dropdown.")

    def scan_for_devices(self):
        """Scan for BLE devices."""
        self.discover_devices()  # Call the coroutine directly

    @asyncSlot()
    async def connect_to_selected_device(self, address):
        """Connect to the selected BLE device and save its address."""
        self.status_label.setText(f"Connecting to {address}...")
        try:
            self.ble_client = BleakClient(address)
            await self.ble_client.connect()
            if self.ble_client.is_connected:
                self.status_label.setText(f"Connected to {address}")
                self.save_device(address)  # Save the connected device
                # Subscribe to notifications
                characteristic_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"  # Replace with the correct UUID
                try:
                    await self.ble_client.start_notify(characteristic_uuid, self.handle_notification)
                    self.status_label.setText("Notification subscription successful.")
                except Exception as e:
                    self.status_label.setText(f"Failed to subscribe to notifications: {str(e)}")
                    print(f"Notification subscription error: {str(e)}")
                self.switch_view(0)  # Automatically switch to Buttons View
        except Exception as e:
            self.status_label.setText(f"Failed to connect: {str(e)}")
            print(f"Connection error: {str(e)}")
            if self.ble_client:
                await self.ble_client.disconnect()
                self.ble_client = None

    def handle_notification(self, sender, data):
        """Handle incoming data from the BLE device."""
        try:
            received_text = data.decode("utf-8")  # Decode the received bytes to a string
            self.status_label.setText(f"Received: {received_text}")
            print(f"Notification from {sender}: {received_text}")

            # Decode messages with specific prefixes
            if received_text.startswith("WATER:"):
                # Extract the number after the prefix
                water_amount = int(received_text.split(":")[1])
                self.current_water_intake += water_amount
                self.update_water_progress()  # Update the progress bar
                self.save_water_data()  # Save the updated water data
                self.status_label.setText(f"Updated water intake: {self.current_water_intake} ml")
                print(f"Water intake updated: {self.current_water_intake} ml")
        except Exception as e:
            self.status_label.setText(f"Failed to process notification: {str(e)}")
            print(f"Notification handling error: {str(e)}")

    def disconnect_device(self):
        """Disconnect from the BLE device and clean up."""
        if self.ble_client and self.ble_client.is_connected:
            asyncio.create_task(self.ble_client.disconnect())
            self.ble_client = None
            self.status_label.setText("Disconnected from device.")
            self.switch_view(-1)  # Switch to Setup View
            self.status_label.setText("Bluetooth connection lost. Please reconnect.")

    def closeEvent(self, event):
        """Handle the window close event to clean up BLE resources."""
        if self.ble_client and self.ble_client.is_connected:
            asyncio.run(self.ble_client.disconnect())
        super().closeEvent(event)

    @asyncSlot()
    async def send_text(self, address, text):
        """Send text to the connected BLE device."""
        if not self.is_valid_address(address):
            self.status_label.setText("Invalid device address.")
            return

        if not self.ble_client or not self.ble_client.is_connected:
            self.status_label.setText("Device is not connected.")
            return

        try:
            # Replace with the UUID of the writable characteristic
            characteristic_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"
            await self.ble_client.write_gatt_char(characteristic_uuid, text.encode())
            print(f"Sent: {text}")
            self.status_label.setText(f"Sent: {text}")
        except Exception as e:
            self.status_label.setText(f"Failed to send text: {str(e)}")
            print(f"Failed to send text: {str(e)}")

    def connect_to_device(self):
        """Connect to the selected device from the dropdown."""
        selected_index = self.device_dropdown.currentIndex()
        if (selected_index == -1):
            self.status_label.setText("No device selected.")
            return
        address = self.device_dropdown.currentData()
        if not address:
            self.status_label.setText("Invalid device address.")
            return
        self.connect_to_selected_device(address)  # Call the coroutine directly

    def create_view_1(self):
        """Create the main view with a countdown timer, buttons, and water goal progress."""
        view = QWidget()
        layout = QVBoxLayout(view)

        # Add a countdown timer label
        self.timer_label = QLabel(self.format_time(self.remaining_time))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #2d2d77; margin-bottom: 20px;")
        layout.addWidget(self.timer_label)

        # Add a universal pause/play button
        self.pause_play_button = QPushButton()
        self.pause_play_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "play.png")))
        self.pause_play_button.setIconSize(QSize(26, 26))  # Icon size remains the same
        self.pause_play_button.setStyleSheet(f"""
            QPushButton {{
                border: none;
                border-radius: 32px;  /* Make the button circular */
                background-color: #2d2d77;  /* Match the purplish font color */
            }}
            QPushButton:hover {{
                background-color: #24245c;  /* Slightly darker shade for hover effect */
            }}
        """)
        self.pause_play_button.setFixedSize(64, 64)  # Ensure the button is circular
        self.pause_play_button.clicked.connect(self.toggle_timer)
        layout.addWidget(self.pause_play_button, alignment=Qt.AlignCenter)

        # Add a progress bar for water consumption
        self.water_progress = QProgressBar()
        self.water_progress.setRange(0, self.daily_goal)
        self.water_progress.setValue(self.current_water_intake)
        self.water_progress.setTextVisible(True)
        self.water_progress.setAlignment(Qt.AlignCenter)
        self.water_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2d2d77;
                border-radius: 10px;
                text-align: center;
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;  /* White text for better contrast */
                background-color: #c5cae9;  /* Light purple background */
            }
            QProgressBar::chunk {
                background-color: #2d2d77;  /* Darker purple for the progress */
            }
        """)
        layout.addWidget(self.water_progress, alignment=Qt.AlignCenter)

        # Define buttons with their corresponding icons and labels
        icons_path = os.path.join(os.path.dirname(__file__), "icons")  # Absolute path to icons folder
        services = [
            ("Timer", os.path.join(icons_path, "clock.png"), None),  # Redirect to Settings View
            ("Heat", os.path.join(icons_path, "air.png"), "Heat Message"),
            ("Daily Intake", os.path.join(icons_path, "water.png"), "Daily Intake Message"),
            ("Reset", os.path.join(icons_path, "reset.png"), "Reset Message"),
        ]

        # Create a grid layout for buttons
        grid = QGridLayout()
        for i, (text, icon_path, message) in enumerate(services):
            button = QPushButton()
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(64, 64))  # Adjust icon size
            button.setText(text)
            button.setStyleSheet("text-align: center; font-size: 14px; font-weight: bold;")
            button.setMinimumSize(150, 150)
            if text == "Timer":
                button.clicked.connect(lambda: self.switch_view(1))  # Redirect to Settings View
            elif text == "Reset":
                button.clicked.connect(self.reset_action)  # Reset the timer
            elif text == "Daily Intake":
                button.clicked.connect(self.set_daily_goal)  # Set daily water goal
            else:
                button.clicked.connect(lambda _, msg=message: self.send_serial_message(msg))  # Send message on click
            grid.addWidget(button, i // 2, i % 2)  # Arrange buttons in a 2x2 grid

        layout.addLayout(grid)
        layout.setAlignment(Qt.AlignTop)  # Align buttons to the top
        return view

    def set_daily_goal(self):
        """Prompt the user to set a daily water consumption goal."""
        goal, ok = QInputDialog.getInt(self, "Set Daily Goal", "Enter your daily water goal (ml):", self.daily_goal, 1)
        if ok:
            self.daily_goal = goal
            self.water_progress.setRange(0, self.daily_goal)
            self.update_water_progress()
            self.save_water_data()  # Save the updated goal
            self.status_label.setText(f"Daily goal set to {self.daily_goal} ml.")

    def update_water_progress(self):
        """Update the progress bar for water consumption."""
        self.water_progress.setValue(self.current_water_intake)
        self.water_progress.setFormat(f"{self.current_water_intake} / {self.daily_goal} ml")

    def load_water_data(self):
        """Load the daily goal and current water intake from the JSON file."""
        try:
            with open("saved_device.json", "r") as file:
                data = json.load(file)
                self.daily_goal = data.get("daily_goal", self.daily_goal)
                self.current_water_intake = data.get("current_water_intake", self.current_water_intake)
        except FileNotFoundError:
            pass  # File doesn't exist, use default values
        except Exception as e:
            print(f"Failed to load water data: {str(e)}")

    def save_water_data(self):
        """Save the daily goal and current water intake to the JSON file."""
        try:
            data = {}
            if os.path.exists("saved_device.json"):
                with open("saved_device.json", "r") as file:
                    data = json.load(file)
            data["daily_goal"] = self.daily_goal
            data["current_water_intake"] = self.current_water_intake
            with open("saved_device.json", "w") as file:
                json.dump(data, file)
        except Exception as e:
            print(f"Failed to save water data: {str(e)}")

    def send_serial_message(self, message):
        """Send a customized serial message to the connected BLE device."""
        if not self.saved_device:
            self.status_label.setText("No device connected.")
            return
        if not self.is_valid_address(self.saved_device):
            self.status_label.setText("Invalid saved device address.")
            return
        asyncio.create_task(self.send_text(self.saved_device, message))  # Call the coroutine
        print(f"Sending message: {message}")

    def timer_action(self):
        """Handle the Timer button action."""
        self.status_label.setText("Timer service selected.")

    def heat_action(self):
        """Handle the Heat button action."""
        self.status_label.setText("Heat service selected.")

    def daily_intake_action(self):
        """Handle the Daily Intake button action."""
        self.status_label.setText("Daily Intake service selected.")

    def reset_action(self):
        """Reset the timer to the defined timer duration."""
        self.remaining_time = self.timer_duration
        self.timer_end_time = None  # Clear the end time
        self.timer_label.setText(self.format_time(self.remaining_time))  # Reset the timer label
        self.countdown_timer.stop()
        self.is_timer_running = False  # Ensure the timer is marked as not running
        self.pause_play_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "play.png")))  # Update icon to play
        self.status_label.setText("Timer reset.")

    def is_valid_address(self, address):
        """Validate the BLE device address format."""
        # Example validation: Check if the address is a non-empty string
        return isinstance(address, str) and len(address) > 0

    def create_view_2(self):
        """Create the settings view with timer customization using dropdown menus."""
        view = QWidget()
        layout = QVBoxLayout(view)

        # Add a back button to return to the Buttons View
        back_button = QPushButton("Back")
        back_button.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        back_button.clicked.connect(lambda: self.switch_view(0))  # Return to Buttons View
        layout.addWidget(back_button, alignment=Qt.AlignLeft)

        # Add a label for timer customization
        timer_label = QLabel("Set Timer Duration:")
        timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d2d77;")
        timer_label.setAlignment(Qt.AlignCenter)  # Center the label horizontally
        layout.addWidget(timer_label)

        # Create a horizontal layout for the dropdown menus
        timer_input_layout = QHBoxLayout()

        # Add dropdown for hours
        self.hours_dropdown = QComboBox()
        self.hours_dropdown.setEditable(True)  # Allow text input
        self.hours_dropdown.addItems([f"{i:02}" for i in range(24)])  # 0 to 23, formatted as 2 digits
        self.hours_dropdown.setCurrentText("01")  # Default value set to 1 hour
        self.hours_dropdown.setStyleSheet("font-size: 14px; padding: 5px; min-width: 60px;")
        timer_input_layout.addWidget(self.hours_dropdown)

        # Add colon label
        colon_label_1 = QLabel(":")
        colon_label_1.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d2d77; padding: 0 10px;")
        timer_input_layout.addWidget(colon_label_1)

        # Add dropdown for minutes
        self.minutes_dropdown = QComboBox()
        self.minutes_dropdown.setEditable(True)  # Allow text input
        self.minutes_dropdown.addItems([f"{i:02}" for i in range(60)])  # 0 to 59, formatted as 2 digits
        self.minutes_dropdown.setCurrentText("00")  # Default value set to 0 minutes
        self.minutes_dropdown.setStyleSheet("font-size: 14px; padding: 5px; min-width: 60px;")
        timer_input_layout.addWidget(self.minutes_dropdown)

        # Add colon label
        colon_label_2 = QLabel(":")
        colon_label_2.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d2d77; padding: 0 10px;")
        timer_input_layout.addWidget(colon_label_2)

        # Add dropdown for seconds
        self.seconds_dropdown = QComboBox()
        self.seconds_dropdown.setEditable(True)  # Allow text input
        self.seconds_dropdown.addItems([f"{i:02}" for i in range(60)])  # 0 to 59, formatted as 2 digits
        self.seconds_dropdown.setCurrentText("00")  # Default value set to 0 seconds
        self.seconds_dropdown.setStyleSheet("font-size: 14px; padding: 5px; min-width: 60px;")
        timer_input_layout.addWidget(self.seconds_dropdown)

        timer_input_layout.setAlignment(Qt.AlignCenter)  # Center the dropdowns horizontally
        layout.addLayout(timer_input_layout)

        # Add a button to update the timer
        update_timer_button = QPushButton("Update Timer")
        update_timer_button.clicked.connect(self.update_timer_duration)
        layout.addWidget(update_timer_button, alignment=Qt.AlignCenter)

        # Add a "Forget Device" button
        forget_button = QPushButton("Forget Device")
        forget_button.clicked.connect(self.forget_device)
        layout.addWidget(forget_button, alignment=Qt.AlignCenter)

        layout.setAlignment(Qt.AlignTop)
        return view

    def update_timer_duration(self):
        """Update the timer duration based on the dropdown menu inputs."""
        try:
            hours = int(self.hours_dropdown.currentText())
            minutes = int(self.minutes_dropdown.currentText())
            seconds = int(self.seconds_dropdown.currentText())
            if hours < 0 or minutes < 0 or seconds < 0 or minutes >= 60 or seconds >= 60:
                raise ValueError("Invalid time values.")
            self.timer_duration = hours * 3600 + minutes * 60 + seconds
            self.remaining_time = self.timer_duration
            self.timer_label.setText(self.format_time(self.remaining_time))  # Update the timer label
            self.status_label.setText("Timer duration updated.")
            print(f"Timer duration updated to {self.timer_duration} seconds.")  # Debug print
        except ValueError:
            self.status_label.setText("Invalid input. Please select valid numbers.")
            print("Invalid timer input detected.")  # Debug print

    def start_timer(self):
        """Start the countdown timer."""
        if self.remaining_time > 0:
            self.timer_end_time = time.time() + self.remaining_time  # Calculate the end time
            self.countdown_timer.start()  # Start the QTimer
            self.status_label.setText("Timer started.")
            print(f"Timer started with {self.remaining_time} seconds remaining.")  # Debug print
        else:
            self.status_label.setText("Set a valid timer duration before starting.")

    def update_timer(self):
        """Update the countdown timer display."""
        if self.timer_end_time:
            self.remaining_time = max(0, int(self.timer_end_time - time.time()))  # Calculate remaining time
            self.timer_label.setText(self.format_time(self.remaining_time))  # Update the timer label
            QApplication.processEvents()  # Force UI update
            if self.remaining_time == 0:
                self.countdown_timer.stop()  # Stop the timer when it reaches 0
                self.timer_label.setText("00:00:00")  # Ensure it counts down to 00:00:00
                self.status_label.setText("Time's up!")
                print("Timer reached 00:00:00.")  # Debug print
        else:
            self.countdown_timer.stop()
            self.status_label.setText("Timer not running.")
            print("Timer stopped as end time is not set.")  # Debug print

    def format_time(self, seconds):
        """Format time in HH:MM:SS format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def save_device(self, address):
        """Save the connected device's address to a file."""
        try:
            with open("saved_device.json", "w") as file:
                json.dump({"address": address}, file)
        except Exception as e:
            self.status_label.setText(f"Failed to save device: {str(e)}")

    def load_saved_device(self):
        """Load the saved device's address from a file."""
        try:
            with open("saved_device.json", "r") as file:
                data = json.load(file)
                return data.get("address")
        except FileNotFoundError:
            return None
        except Exception as e:
            self.status_label.setText(f"Failed to load device: {str(e)}")
            return None

    def forget_device(self):
        """Forget the saved device by deleting the saved file."""
        try:
            import os
            if os.path.exists("saved_device.json"):
                os.remove("saved_device.json")
                self.saved_device = None
                self.status_label.setText("Device forgotten.")
                self.switch_view(-1)  # Switch to Setup View
            else:
                self.status_label.setText("No device to forget.")
        except Exception as e:
            self.status_label.setText(f"Failed to forget device: {str(e)}")

    async def auto_connect_to_saved_device(self):
        """Automatically connect to the saved device if available."""
        if self.saved_device:
            if not self.is_valid_address(self.saved_device):
                self.status_label.setText("Invalid saved device address.")
                return
            self.status_label.setText(f"Auto-connecting to {self.saved_device}...")
            await self.connect_to_selected_device(self.saved_device)

    def switch_view(self, index):
        """Switch to the selected view."""
        self.stacked_widget.setCurrentIndex(index + 1)  # Adjust index to match views (Buttons=1, Settings=2)
        # Commented out dropdown visibility logic
        # if index == -1:  # Hide dropdown in Setup View
        #     self.dropdown.hide()
        # else:  # Show dropdown in other views
        #     self.dropdown.show()
        #     self.dropdown.setCurrentIndex(index)  # Update dropdown selection to match the view

    def toggle_timer(self):
        """Toggle the timer between pause and play states with animation."""
        if self.is_timer_running:
            self.countdown_timer.stop()
            self.animate_icon_transition("pause.png", "play.png")  # Animate to play icon
            self.status_label.setText("Timer paused.")
        else:
            self.start_timer()
            self.animate_icon_transition("play.png", "pause.png")  # Animate to pause icon
            self.status_label.setText("Timer resumed.")
        self.is_timer_running = not self.is_timer_running

    def animate_icon_transition(self, from_icon, to_icon):
        """Animate the transition between pause and play icons."""
        if self.animation:
            self.animation.stop()  # Stop any ongoing animation

        # Create an animation for the button geometry
        self.animation = QPropertyAnimation(self.pause_play_button, b"geometry")
        self.animation.setDuration(300)  # Duration of the animation in milliseconds
        self.animation.setStartValue(self.pause_play_button.geometry())
        self.animation.setEndValue(self.pause_play_button.geometry())
        self.animation.start()

        # Update the icon after the animation completes
        self.animation.finished.connect(lambda: self.pause_play_button.setIcon(
            QIcon(os.path.join(os.path.dirname(__file__), "icons", to_icon))
        ))


if __name__ == "__main__":
    app = QApplication([])

    # Set the background color of the entire app
    app.setStyleSheet("QMainWindow { background-color: #e8eaf6; }")

    # Use QEventLoop to integrate asyncio with PySide6
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    try:
        with open("style.qss", "r") as file:
            app.setStyleSheet(file.read())
    except FileNotFoundError:
        print("QSS file not found. Using default styles.")

    window = MainWindow()
    window.show()

    # Schedule the auto-connect coroutine after the event loop starts
    def start_auto_connect():
        # Pass the coroutine object directly to run_coroutine_threadsafe
        asyncio.run_coroutine_threadsafe(window.auto_connect_to_saved_device(), loop)

    # Use a single-shot timer to schedule the coroutine after the event loop starts
    QTimer.singleShot(0, start_auto_connect)

    with loop:
        loop.run_forever()
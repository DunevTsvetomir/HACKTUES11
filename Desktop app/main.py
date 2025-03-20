from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QApplication, QGridLayout,
    QVBoxLayout, QStackedWidget, QComboBox, QLabel, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from qasync import QEventLoop, asyncSlot
import asyncio
from bleak import BleakScanner, BleakClient
import json  # Added for saving/loading device information

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App template")

        # Set the window size
        self.resize(800, 600)

        # Create the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)

        # Create a dropdown menu for switching views
        self.dropdown = QComboBox()
        self.dropdown.addItems(["Buttons", "Settings"])  # Correctly map dropdown options
        self.dropdown.currentIndexChanged.connect(self.switch_view)  # Connect to view switching
        self.dropdown.hide()  # Initially hide the dropdown menu

        # Create a stacked widget to hold multiple views
        self.stacked_widget = QStackedWidget()

        # Add views to the stacked widget
        self.stacked_widget.addWidget(self.create_view_setup())  # Setup View
        self.stacked_widget.addWidget(self.create_view_1())  # View 1
        self.stacked_widget.addWidget(self.create_view_2())  # View 2

        # Add the dropdown and stacked widget to the main layout
        main_layout.addWidget(self.dropdown)
        main_layout.addWidget(self.stacked_widget)

        # Load saved device information
        self.saved_device = self.load_saved_device()

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
        asyncio.create_task(self.discover_devices())

    @asyncSlot()
    async def connect_to_selected_device(self, address):
        """Connect to the selected BLE device and save its address."""
        self.status_label.setText(f"Connecting to {address}...")
        try:
            async with BleakClient(address) as client:
                if client.is_connected:
                    self.status_label.setText(f"Connected to {address}")
                    self.save_device(address)  # Save the connected device
                    self.switch_view(0)  # Automatically switch to Buttons View
        except Exception as e:
            self.status_label.setText(f"Failed to connect: {str(e)}")

    @asyncSlot()
    async def send_text(self, address, text):
        """Send text to the connected BLE device."""
        try:
            async with BleakClient(address) as client:
                if client.is_connected:
                    # Replace with the UUID of the writable characteristic
                    characteristic_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"
                    await client.write_gatt_char(characteristic_uuid, text.encode())
                    self.status_label.setText(f"Sent: {text}")
        except Exception as e:
            self.status_label.setText(f"Failed to send text: {str(e)}")

    def connect_to_device(self):
        """Connect to the selected device from the dropdown."""
        selected_index = self.device_dropdown.currentIndex()
        if selected_index == -1:
            self.status_label.setText("No device selected.")
            return
        address = self.device_dropdown.currentData()
        asyncio.create_task(self.connect_to_selected_device(address))

    def create_view_1(self):
        """Create the first view with a grid of buttons."""
        view = QWidget()
        grid = QGridLayout(view)

        buttons = [
            ('Button 1', 0, 0), ('Button 2', 0, 1), ('Button 3', 0, 2),
            ('Button 4', 1, 0), ('Button 5', 1, 1), ('Button 6', 1, 2),
            ('Button 7', 2, 0), ('Button 8', 2, 1), ('Button 9', 2, 2)
        ]

        for text, row, col in buttons:
            button = QPushButton(text)
            button.setMinimumSize(100, 100)
            button.setMaximumSize(300, 150)
            grid.addWidget(button, row, col)

        # Set stretch factors to ensure uniform resizing
        for i in range(3):  # 3 rows and 3 columns
            grid.setRowStretch(i, 1)
            grid.setColumnStretch(i, 1)

        grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        return view

    def create_view_2(self):
        """Create the second view with checkboxes and a forget button."""
        view = QWidget()
        layout = QVBoxLayout(view)
        checkboxes = [
            ('Checkbox 1',), ('Checkbox 2',), ('Checkbox 3',)
        ]
        for checkbox in checkboxes:
            layout.addWidget(QCheckBox(checkbox[0]))

        # Add a "Forget Device" button
        forget_button = QPushButton("Forget Device")
        forget_button.clicked.connect(self.forget_device)
        layout.addWidget(forget_button)

        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        return view

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

    @asyncSlot()
    async def auto_connect_to_saved_device(self):
        """Automatically connect to the saved device if available."""
        if self.saved_device:
            self.status_label.setText(f"Auto-connecting to {self.saved_device}...")
            await self.connect_to_selected_device(self.saved_device)

    def switch_view(self, index):
        """Switch to the selected view and hide/show the dropdown menu."""
        self.stacked_widget.setCurrentIndex(index + 1)  # Adjust index to match views (Buttons=1, Settings=2)
        if index == -1:  # Hide dropdown in Setup View
            self.dropdown.hide()
        else:  # Show dropdown in other views
            self.dropdown.show()
            self.dropdown.setCurrentIndex(index)  # Update dropdown selection to match the view


if __name__ == "__main__":
    app = QApplication([])

    # Use QEventLoop to integrate asyncio with PySide6
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    # Schedule the auto-connect coroutine after the event loop starts
    def start_auto_connect():
        asyncio.run_coroutine_threadsafe(window.auto_connect_to_saved_device(), loop)

    # Use a single-shot timer to schedule the coroutine after the event loop starts
    QTimer.singleShot(0, start_auto_connect)

    with loop:
        loop.run_forever()
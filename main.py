from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QApplication, QGridLayout,
    QVBoxLayout, QStackedWidget, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt


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
        self.dropdown.addItems(["Buttons", "Settings"])
        self.dropdown.currentIndexChanged.connect(self.switch_view)  # Connect to view switching

        # Create a stacked widget to hold multiple views
        self.stacked_widget = QStackedWidget()

        # Add views to the stacked widget
        self.stacked_widget.addWidget(self.create_view_1())  # View 1
        self.stacked_widget.addWidget(self.create_view_2())  # View 2

        # Add the dropdown and stacked widget to the main layout
        main_layout.addWidget(self.dropdown)
        main_layout.addWidget(self.stacked_widget)

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
            grid.addWidget(button, row, col)

        # Set stretch factors to ensure uniform resizing
        for i in range(3):  # 3 rows and 3 columns
            grid.setRowStretch(i, 1)
            grid.setColumnStretch(i, 1)

        grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        return view

    def create_view_2(self):
        """Create the second view with checkboxes."""
        view = QWidget()
        layout = QVBoxLayout(view)
        checkboxes = [
            ('Checkbox 1',), ('Checkbox 2',), ('Checkbox 3',)
        ]
        for checkbox in checkboxes:
            layout.addWidget(QCheckBox(checkbox[0]))
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        return view

    def switch_view(self, index):
        """Switch to the selected view."""
        self.stacked_widget.setCurrentIndex(index)


app = QApplication()

window = MainWindow()
window.show()

app.exec()
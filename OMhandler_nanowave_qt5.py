import sys
import time
import os
import glob
import pyautogui  # Import pyautogui for mouse control
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QTextEdit, QVBoxLayout, QGraphicsScene, QGraphicsView, \
    QHBoxLayout, QGridLayout, QFileDialog, QLabel, QLineEdit, QCheckBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QTextCursor
from PIL import Image  # Import Pillow for resizing
import keyboard  # Import keyboard for global key press detection

# Global point variable to store the clicked point
point = None


# Function to capture the screenshot when the button is clicked
def capture_screenshot():
    # Grab the full screen (screen coordinates: x1=0, y1=0, x2=screen width, y2=screen height)
    screenshot = pyautogui.screenshot()

    # Resize the screenshot to half size
    screenshot = screenshot.resize((screenshot.width // 2, screenshot.height // 2))

    return screenshot


# Worker thread for PyAutoGUI actions
class MouseWorker(QThread):
    # Define a signal to send back status or info
    click_done = pyqtSignal(str)

    def __init__(self, point):
        super().__init__()
        self.point = point

    def run(self):
        try:
            # Simulate the mouse click at the point
            pyautogui.moveTo(self.point[0], self.point[1])  # Move the mouse to the point
            pyautogui.mouseDown()  # Press the mouse down (click down)
            time.sleep(0.01)  # Hold the click for 10ms
            pyautogui.mouseUp()  # Release the mouse (click up)
            # Emit signal when click is done
            self.click_done.emit(f"Mouse clicked at {self.point}")
        except Exception as e:
            self.click_done.emit(f"Error during click: {e}")


# PyQt5 Application class
class OMHandlerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OMhandler Nanowave")
        self.setGeometry(100, 100, 500, 300)

        self.initUI()

    def initUI(self):
        # Create the layout manager for the entire window
        layout = QVBoxLayout()

        # Layout for folder selection
        folder_layout = QHBoxLayout()

        # Label to show selected directory
        self.folder_path_display = QLineEdit(self)
        self.folder_path_display.setReadOnly(True)
        self.folder_path_display.setPlaceholderText("No directory selected")
        folder_layout.addWidget(self.folder_path_display)

        # Button to assign directory
        self.select_folder_button = QPushButton("📁", self)
        self.select_folder_button.setFixedSize(30, 30)
        self.select_folder_button.clicked.connect(self.select_directory)
        folder_layout.addWidget(self.select_folder_button)

        layout.addLayout(folder_layout)
        # Create a scrollable log window (QTextEdit) to show actions and timestamps
        self.action_log = QTextEdit(self)
        self.action_log.setReadOnly(True)  # Make the log text view only (no editing)
        self.action_log.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Always show vertical scroll bar
        self.action_log.setPlaceholderText("Action log will appear here...")
        layout.addWidget(self.action_log)

        # Create a grid layout to arrange the buttons
        button_layout = QGridLayout()

        # Create the define point button
        self.define_button = QPushButton("Define Point", self)
        self.define_button.setFixedSize(150, 40)
        self.define_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        self.define_button.clicked.connect(self.open_screenshot_window)
        button_layout.addWidget(self.define_button, 0, 0)

        # Create a checkbox to control auto-focus
        self.focus_checkbox = QCheckBox("Auto-Focus", self)
        self.focus_checkbox.setChecked(True)
        button_layout.addWidget(self.focus_checkbox, 0, 1)

        # Create the shutter button
        self.shutter_button = QPushButton("Shutter", self)
        self.shutter_button.setFixedSize(150, 40)
        self.shutter_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 14px;")
        self.shutter_button.clicked.connect(self.simulate_click)
        button_layout.addWidget(self.shutter_button, 0, 2)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Create a new horizontal layout for the text and numerical inputs
        input_layout = QHBoxLayout()

        # Editable text box
        self.text_input = QTextEdit(self)
        self.text_input.setFixedHeight(30)
        self.text_input.setPlaceholderText("Enter label or comment")
        input_layout.addWidget(self.text_input)

        # Integer input boxes (QSpinBox)
        from PyQt5.QtWidgets import QSpinBox, QComboBox

        self.int_box1 = QSpinBox()
        self.int_box1.setRange(1, 100)
        input_layout.addWidget(self.int_box1)

        self.int_box2 = QSpinBox()
        self.int_box2.setRange(1, 100)
        input_layout.addWidget(self.int_box2)

        self.int_box3 = QSpinBox()
        self.int_box3.setRange(1, 100)
        input_layout.addWidget(self.int_box3)

        # The fourth box using QComboBox for fixed set {5, 10, 20, 50}
        self.combo_box = QComboBox()
        self.combo_box.addItems(["5", "10", "20", "50"])
        input_layout.addWidget(self.combo_box)
        self.combo_box.setCurrentText("50")

        layout.addLayout(input_layout)

        # Set the layout for the window
        self.setLayout(layout)

        # Make the window stay on top
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        # Timer to periodically ensure the window gets focus
        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self.ensure_window_focus)
        self.focus_timer.start(200)  # Set to 200ms to reduce CPU usage

    def open_screenshot_window(self):
        global point  # Make sure to modify the global point variable

        try:
            # Capture and resize the screenshot
            screenshot_image = capture_screenshot()

            # Convert screenshot to a format PyQt5 can display (QImage.Format_RGB888)
            screenshot_pixmap = QPixmap.fromImage(
                QImage(screenshot_image.tobytes(), screenshot_image.width, screenshot_image.height,
                       screenshot_image.width * 3, QImage.Format_RGB888))

            # Create a new window for showing the screenshot and handling point click
            self.screenshot_window = QWidget()
            self.screenshot_window.setWindowTitle("Click on Screenshot")
            self.screenshot_window.setGeometry(100, 100, screenshot_image.width, screenshot_image.height)

            scene = QGraphicsScene()
            view = QGraphicsView(scene, self.screenshot_window)

            scene.addPixmap(screenshot_pixmap)

            self.rect_item = None
            self.start_x, self.start_y = None, None
            self.point = None

            view.setRenderHint(QPainter.Antialiasing)
            view.setRenderHint(QPainter.SmoothPixmapTransform)
            view.setRenderHint(QPainter.TextAntialiasing)

            view.setGeometry(0, 0, screenshot_image.width, screenshot_image.height)

            # Create mouse event handler
            view.setMouseTracking(True)
            view.mousePressEvent = self.on_mouse_press

            self.screenshot_window.show()

        except Exception as e:
            print(f"An error occurred while opening the screenshot window: {e}")

    def on_mouse_press(self, event):
        global point
        # Capture the mouse click position, adjusting for the resized image
        point = (event.x() * 2, event.y() * 2)  # Double the coordinates to match original size
        timestamp = time.strftime("%H:%M:%S")  # Only show time (without date)
        action_info = f"{timestamp} - Target point defined at {point}"
        self.update_log(action_info)

        # Close the screenshot window after defining the point
        self.screenshot_window.close()

    def select_directory(self):
        """Open file dialog to select a folder and display the path"""
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            self.folder_path_display.setText(folder)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:  # If Enter key is pressed
            self.simulate_click()

    def simulate_click(self):
        global point

        if point:  # If the point is defined
            print(f"Simulated click at: {point}")

            # Run the mouse click in a separate thread
            self.mouse_worker = MouseWorker(point)
            self.mouse_worker.click_done.connect(self.on_click_done)  # Connect the signal
            self.mouse_worker.start()  # Start the worker thread

            # After the click is simulated, raise and focus the main window
            self.raise_()
            self.activateWindow()  # Bring the main window to the front and focus it

    def on_click_done(self, message):
        # Update action info and timestamp on the main window
        timestamp = time.strftime("%H:%M:%S")  # Only show time (without date)
        action_info = f"{timestamp} - {message}"
        self.update_log(action_info)

        # Attempt to rename latest EOSCapture image
        time.sleep(0.5)
        self.rename_latest_eos_capture()

    def ensure_window_focus(self):
        # Only refocus the window if the checkbox is checked
        if self.focus_checkbox.isChecked():
            if not self.hasFocus():
                self.activateWindow()


    def rename_latest_eos_capture(self):
        folder = self.folder_path_display.text()
        if not folder or not os.path.isdir(folder):
            self.update_log("No valid folder selected.")
            return

        # Only consider .jpg files
        jpg_files = glob.glob(os.path.join(folder, "*.jpg"))
        if not jpg_files:
            self.update_log("No .jpg files found in selected folder.")
            return

        # Get latest jpg file
        latest_file = max(jpg_files, key=os.path.getctime)
        basename = os.path.basename(latest_file)

        if basename.startswith("EOSCapture"):
            # Build new name
            text_value = self.text_input.toPlainText().strip().replace(" ", "_")
            val1 = self.int_box1.value()
            val2 = self.int_box2.value()
            val3 = self.int_box3.value()
            val4 = self.combo_box.currentText()

            name_parts = [text_value, str(val1), str(val2), str(val3), val4]
            new_filename = "_".join(name_parts) + ".jpg"
            new_path = os.path.join(folder, new_filename)

            try:
                os.rename(latest_file, new_path)
                self.update_log(f"Renamed: {basename} → {new_filename}")

                # Rotate combo box: 50 → 20 → 10 → 5 → 50
                rotation_order = ["50", "20", "10", "5"]
                current_index = rotation_order.index(val4)
                next_index = (current_index + 1) % len(rotation_order)
                self.combo_box.setCurrentText(rotation_order[next_index])

                # If rotating from 5 → 50, increment int_box3
                if val4 == "5":
                    self.int_box3.setValue(self.int_box3.value() + 1)

            except Exception as e:
                self.update_log(f"Rename failed: {e}")


    def update_log(self, message):
        """ Append new messages to the log and ensure it's scrollable """
        try:
            current_text = self.action_log.toPlainText()
            new_text = f"{current_text}\n{message}"  # Add a newline before the new message
            self.action_log.setPlainText(new_text)
            # Auto-scroll to the bottom of the text area
            cursor = self.action_log.textCursor()  # Get the cursor for the QTextEdit
            cursor.movePosition(QTextCursor.End)  # Move the cursor to the end
            self.action_log.setTextCursor(cursor)  # Set the cursor to the end of the text area
        except Exception as e:
            print(f"Error updating log: {e}")


# Main function to run the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    omhandler = OMHandlerApp()
    omhandler.show()
    sys.exit(app.exec())

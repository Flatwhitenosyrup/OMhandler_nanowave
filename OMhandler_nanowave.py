import sys
import time
import pyautogui  # Import pyautogui for mouse control
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QTextEdit, QVBoxLayout, QGraphicsScene, QGraphicsView, \
    QGridLayout
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap, QPainter, QTextCursor
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


# PyQt6 Application class
class OMHandlerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OMhandler Nanowave")
        self.setGeometry(100, 100, 500, 300)

        self.initUI()

    def initUI(self):
        # Create the layout manager for the entire window
        layout = QVBoxLayout()

        # Create a scrollable log window (QTextEdit) to show actions and timestamps
        self.action_log = QTextEdit(self)
        self.action_log.setReadOnly(True)  # Make the log text view only (no editing)
        self.action_log.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.action_log.setPlaceholderText("Action log will appear here...")
        layout.addWidget(self.action_log)

        # Create a grid layout to arrange the buttons
        button_layout = QGridLayout()

        # Create the define point button
        self.define_button = QPushButton("Define Point", self)
        self.define_button.setFixedSize(150, 40)  # Set a custom button size
        self.define_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        self.define_button.clicked.connect(self.open_screenshot_window)
        button_layout.addWidget(self.define_button, 0, 0)

        # Create the shutter button, which behaves exactly like pressing Enter
        self.shutter_button = QPushButton("Shutter", self)
        self.shutter_button.setFixedSize(150, 40)  # Set a custom button size
        self.shutter_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 14px;")
        self.shutter_button.clicked.connect(self.simulate_click)  # Connect it to simulate_click
        button_layout.addWidget(self.shutter_button, 0, 1)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Set the layout for the window
        self.setLayout(layout)

        # Make the window stay on top
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        # Timer to periodically ensure the window gets focus
        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self.ensure_window_focus)
        self.focus_timer.start(200)  # Set to 200ms to reduce CPU usage

    def open_screenshot_window(self):
        global point  # Make sure to modify the global point variable

        try:
            # Capture and resize the screenshot
            screenshot_image = capture_screenshot()

            # Convert screenshot to a format PyQt6 can display (QImage.Format_RGB888)
            screenshot_pixmap = QPixmap.fromImage(
                QImage(screenshot_image.tobytes(), screenshot_image.width, screenshot_image.height,
                       screenshot_image.width * 3, QImage.Format.Format_RGB888))

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

            view.setRenderHint(QPainter.RenderHint.Antialiasing)
            view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            view.setRenderHint(QPainter.RenderHint.TextAntialiasing)

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:  # If Enter key is pressed
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

    def ensure_window_focus(self):
        # Periodically check if the window is still focused, and activate if needed
        if not self.hasFocus():
            self.activateWindow()

    def update_log(self, message):
        """ Append new messages to the log and ensure it's scrollable """
        try:
            current_text = self.action_log.toPlainText()
            new_text = f"{current_text}\n{message}"  # Add a newline before the new message
            self.action_log.setPlainText(new_text)
            # Auto-scroll to the bottom of the text area
            cursor = self.action_log.textCursor()  # Get the cursor for the QTextEdit
            cursor.movePosition(QTextCursor.MoveOperation.End)  # Move the cursor to the end
            self.action_log.setTextCursor(cursor)  # Set the cursor to the end of the text area
        except Exception as e:
            print(f"Error updating log: {e}")


# Main function to run the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    omhandler = OMHandlerApp()
    omhandler.show()
    sys.exit(app.exec())

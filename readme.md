# OMhandler Nanowave

A PyQt5-based GUI tool for assisting with point definition, screen capture, and automated mouse interaction. Designed for image post-processing workflows involving Canon EOS cameras and file renaming.

---

## 🛠 Requirements

This application runs on Python 3.6+ and uses the following packages:

### ✅ Required Python Packages

| Package      | Purpose                                | Installation Command                             |
|--------------|----------------------------------------|--------------------------------------------------|
| `PyQt5`      | GUI framework                          | `pip install pyqt5`                              |
| `pyautogui`  | Mouse control and screen capture       | `pip install pyautogui`                          |
| `Pillow`     | Image resizing (used by pyautogui)     | `pip install pillow`                             |
| `keyboard`   | Global key press detection (Windows)   | `pip install keyboard`                           |

> ⚠️ On some systems, `pyautogui` may also require additional dependencies like `pygetwindow`, `pymsgbox`, etc. Install via `pip install pyautogui` and follow any errors if prompted.

---

## 🧪 Optional Notes

- Designed for Windows systems.
- Ensure the script is run with appropriate privileges if mouse/keyboard control fails.
- Works best with Canon EOS series cameras that output `.jpg` files named `EOSCapture...`.

---

## ▶️ How to Run

```bash
python OMhandler_nanowave_qt5.py

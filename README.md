# SmartSort AI Pro (v2.0) 🚀
**The Intelligent, Privacy-First File Manager for macOS.**

SmartSort AI isn't just a script anymore—it's a full **Desktop Application** that lives in your menu bar. It watches your Downloads folder in real-time and uses **Semantic Analysis** to read and organize your files instantly.

![SmartSort Banner](https://img.shields.io/badge/Status-Active-success) ![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey) ![License](https://img.shields.io/badge/License-MIT-blue)

## ✨ New Features in v2.0
- **🧠 Deep Scan Technology:** It reads the content of PDFs and Text files.
  - *Example:* A file named `scan_001.pdf` containing the word "Invoice" is automatically moved to `Financial/Invoices` and renamed with today's date.
- **🟦 System Tray App:** Runs silently in the background. Control it via the blue icon in your menu bar.
- **🏎️ Rename Detection:** Smart enough to catch files even if the browser changes the filename mid-download.
- **🛡️ 100% Offline:** No data leaves your device. All processing is local.

## 📥 Download
**[Download SmartSort Pro for Mac](https://github.com/a1k7/SmartSort-AI/releases/latest)**
*(Click "SmartSort.zip" under Assets)*

---

## 🍎 Installation Guide (Mac)

### 1. Install
1. Download **`SmartSort.zip`** and unzip it.
2. Drag **`SmartSort.app`** into your **Applications** folder.

### 2. First Run (Permissions)
Because this is an open-source tool (not from the App Store), macOS requires a one-time approval:
1. Double-click the app.
2. If you see a warning ("Unidentified Developer"), go to **System Settings > Privacy & Security**.
3. Scroll down and click **Open Anyway**.
4. Click **Allow** when asked to access the Downloads folder.

### 3. Make it Automatic ⚡
To have SmartSort clean your Mac every time you turn it on:
1. Go to **System Settings > General > Login Items**.
2. Click the **(+)** button.
3. Select **SmartSort** from your Applications folder.

---

## 🛠️ How it Works
The app uses the Python `watchdog` library to monitor file system events and `pypdf` for content extraction.

| Keyword Detected | Target Folder |
| :--- | :--- |
| "Invoice", "Receipt", "Bill" | `Financial/` |
| "Resume", "CV" | `HR/` |
| "Report" | `Work/Reports` |
| "Assignment", "Syllabus" | `University/` |
| *No Keyword?* | Sorts by Extension (Images, Archives, etc.) |

---

## 👨‍💻 For Developers
Want to run the raw code or build it yourself?

```bash
# 1. Install Dependencies
pip install watchdog pypdf pystray pillow

# 2. Run from Source
python3 main.py

# 3. Build .app Bundle
pyinstaller --windowed --onefile --hidden-import=pypdf --hidden-import=PIL --hidden-import=pystray --name "SmartSort" main.py

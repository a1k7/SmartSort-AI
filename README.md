# SmartSort AI (v2.2) 🚀
**The Intelligent, Privacy-First "Digital Janitor" for your Mac.**

SmartSort AI is a background automation utility that keeps your **Desktop** and **Downloads** folder perfectly organized. It uses **Semantic Content Analysis** to read inside your files and sorts them into a clean Vault, all while running silently in your System Tray.

![Status](https://img.shields.io/badge/Status-Active-success) ![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-blue) ![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ New in v2.2: Startup Cleanup
SmartSort doesn't just watch for *new* files anymore.
- **🧹 Startup Cleanup:** On launch, it instantly scans your Desktop & Downloads and organizes the existing mess.
- **🖥️ Dual-Monitor:** Now watches both **Desktop** and **Downloads** folders simultaneously.
- **📂 The Vault:** All files are moved to `Documents/SmartSort_Vault` to keep your workspace clutter-free.

## 🧠 Key Features
- **Deep Scan (OCR):** Reads the text inside PDFs and Docs.
  - *Example:* A file named `scan_004.pdf` containing the word "Invoice" is auto-moved to `Financial/Invoices` and renamed with the date.
- **Rename Protection:** Detects files even if the browser renames them mid-download (fixing the "Unknown" file bug).
- **System Tray App:** Runs in the background with a blue menu bar icon.
- **100% Offline:** No cloud uploads. Your private data never leaves your device.

---

## 📥 Download
**[Download Latest Version (v2.2)](https://github.com/a1k7/SmartSort-AI/releases/latest)**
*(Click `SmartSort.zip` under Assets)*

---

## 🍎 Installation Guide (Mac)

### 1. Install
1. Download **`SmartSort.zip`** and unzip it.
2. Drag **`SmartSort.app`** into your **Applications** folder.

### 2. Permissions (First Run)
Because this is an open-source tool, macOS requires a one-time approval:
1. Double-click the app.
2. If blocked ("Unidentified Developer"), go to **System Settings > Privacy & Security**.
3. Scroll down and click **Open Anyway**.
4. **Important:** Click **Allow** when asked to access Downloads/Desktop.

### 3. Enable Auto-Start ⚡
To have SmartSort clean your Mac automatically on every reboot:
1. Go to **System Settings > General > Login Items**.
2. Click the **(+)** button.
3. Select **SmartSort** from your Applications folder.

---

## 🤖 Sorting Logic
The "Brain" decides where files go based on **Content** first, then **File Extension**.

| If file contains text... | It goes to... |
| :--- | :--- |
| "Invoice", "Receipt", "Bill" | `SmartSort_Vault/Financial/` |
| "Resume", "CV" | `SmartSort_Vault/HR/` |
| "Report" | `SmartSort_Vault/Work/Reports/` |
| "Assignment", "Syllabus" | `SmartSort_Vault/University/` |

**Fallback (Extension) Rules:**
* **Images:** `.jpg`, `.png`, `.svg` → `Images/`
* **Docs:** `.pdf`, `.docx`, `.txt` → `Documents/`
* **Installers:** `.dmg`, `.zip`, `.exe` → `Installers/`

---

## 👨‍💻 For Developers: Build from Source
Want to modify the brain? Here is how to build the standalone app.

### Prerequisites
```bash
pip install watchdog pypdf pystray pillow pyinstaller

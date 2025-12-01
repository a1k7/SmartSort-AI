# SmartSort AI (v4.1) 🚀
**The Intelligent, Privacy-First "Digital Janitor" for macOS & Windows.**

SmartSort AI is a background automation utility that keeps your **Desktop** and **Downloads** folder perfectly organized. It uses **Generative AI (Google Gemini)** and **Local OCR** to read inside your files, rename them intelligently, and sort them into a clean Vault.

![Status](https://img.shields.io/badge/Status-Active-success) ![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-blue) ![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ New in v4.1: The AI Update
SmartSort just got a massive brain upgrade.
- **🤖 Generative AI Renaming:** Uses Google Gemini to analyze file content and generate perfect filenames.
  - *Before:* `scan_09923.pdf`
  - *After:* `Invoice_Amazon_MacBook_Dec2025.pdf`
- **⚡ Hybrid Brain:** Uses **Local Smart Logic** by default (Free & Fast) but switches to **Cloud AI** if you provide an API Key.
- **📊 Impact Dashboard:** Track how many files you've sorted and how much time you've saved.

## 🧠 Key Features
- **Deep Scan (OCR):** Reads the text inside PDFs and Docs to sort them by content (not just extension).
- **Startup Cleanup:** Instantly cleans your Desktop & Downloads the moment you log in.
- **System Tray App:** Runs silently in the background with a blue menu bar icon.
- **Visual Settings:** Toggle features and customize rules with a beautiful Dark Mode GUI.

---

## 📥 Download
**[Download Latest Version (v4.1)](https://github.com/a1k7/SmartSort-AI/releases/latest)**
*(Choose `SmartSort.zip` for Mac or `SmartSort.exe` for Windows)*

---

## 🍎 Installation Guide (macOS)

### 1. Install
1. Download **`SmartSort.zip`** and unzip it.
2. **Crucial:** Drag **`SmartSort.app`** into your **Applications** folder.

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

## 🪟 Installation Guide (Windows)

### 1. Install
1. Download **`SmartSort.exe`**.
2. Move it to a safe folder (e.g., your Documents folder).

### 2. Bypass SmartScreen
When you run it, Windows might say "Windows protected your PC":
1. Click **More Info**.
2. Click **Run Anyway**.

### 3. Enable Auto-Start ⚡
1. Press `Win + R` on your keyboard.
2. Type `shell:startup` and press Enter.
3. Drag `SmartSort.exe` into this folder.

---

## 🤖 How the "Hybrid Brain" Works

| Mode | Technology | Speed | Cost |
| :--- | :--- | :--- | :--- |
| **Standard (Default)** | Regex & Keyword Matching | Instant (0.1s) | **Free** |
| **Ultra (Optional)** | Google Gemini 1.5 Flash | Fast (1.5s) | **Free Key** |

**Sorting Logic:**
1.  **Read File:** Extracts text from PDF, DOCX, TXT, RTF.
2.  **Rename:** If enabled, renames file based on Date + Entity (e.g., `Receipt_Uber_2025-01-01.pdf`).
3.  **Sort:** Moves file to `Documents/SmartSort_Vault/Category`.

---

## 👨‍💻 For Developers: Build from Source

### Prerequisites
```bash
pip install watchdog pypdf pystray pillow pyinstaller customtkinter requests google-generativeai

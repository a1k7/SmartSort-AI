import os
import time
import shutil
import threading
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pypdf import PdfReader
from PIL import Image, ImageDraw
import pystray
import datetime

# --- CONFIGURATION ---
APP_NAME = "SmartSort AI"
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
TARGET_DIR = os.path.expanduser("~/Documents/SmartSort_Vault")
log_file = os.path.join(os.path.expanduser("~"), "smartsort_debug.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

# --- RULES ---
SEMANTIC_RULES = {
    "invoice": "Financial/Invoices",
    "receipt": "Financial/Receipts",
    "resume": "HR/Resumes",
    "report": "Work/Reports",  # Added this for your screenshot!
    "assignment": "University/Assignments"
}

EXTENSION_MAP = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"],
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".csv"],
    "Audio": [".mp3", ".wav", ".aac"],
    "Video": [".mp4", ".mkv", ".mov", ".avi"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Installers": [".exe", ".msi", ".dmg", ".pkg"]
}

class ContentBrain:
    def analyze(self, filepath, filename):
        ext = os.path.splitext(filepath)[1].lower()
        text = ""
        try:
            if ext == ".pdf":
                reader = PdfReader(filepath)
                text = "".join([page.extract_text() for page in reader.pages[:2]])
            elif ext in [".txt", ".md", ".csv"]:
                with open(filepath, "r", errors="ignore") as f: text = f.read(2000)
        except: pass
        text = text.lower()

        # Check Semantic Keywords
        for key, folder in SEMANTIC_RULES.items():
            if key in text or key in filename.lower():
                return folder, filename # Found a smart match!

        # Fallback: Extension Sort
        for folder, extensions in EXTENSION_MAP.items():
            if ext in extensions:
                return folder, filename
                
        return "Others", filename

class ProHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            threading.Thread(target=self.process, args=(event.src_path,)).start()

    # --- NEW: Catch Renamed Files (The Missing Link) ---
    def on_moved(self, event):
        if not event.is_directory:
            threading.Thread(target=self.process, args=(event.dest_path,)).start()

    def process(self, filepath):
        filename = os.path.basename(filepath)
        
        # 1. Ignore Temp Files
        if filename.startswith(".") or "crdownload" in filename or filename == "Unknown": 
            return

        # 2. Wait for file write to finish
        time.sleep(2)
        if not os.path.exists(filepath): return # File moved or deleted

        # 3. Analyze & Sort
        try:
            brain = ContentBrain()
            folder, new_name = brain.analyze(filepath, filename)
            
            dest = os.path.join(TARGET_DIR, folder)
            os.makedirs(dest, exist_ok=True)
            final_path = os.path.join(dest, new_name)
            
            # Duplicate Handling
            counter = 1
            base, ext = os.path.splitext(new_name)
            while os.path.exists(final_path):
                final_path = os.path.join(dest, f"{base}_{counter}{ext}")
                counter += 1
                
            shutil.move(filepath, final_path)
            logging.info(f"Sorted {filename} -> {folder}")
        except Exception as e:
            logging.error(f"Error sorting {filename}: {e}")

# --- GUI ---
def create_icon():
    image = Image.new('RGB', (64, 64), color=(0, 122, 204))
    d = ImageDraw.Draw(image)
    d.rectangle([20, 20, 44, 44], fill="white")
    return image

def run_app():
    observer = Observer()
    observer.schedule(ProHandler(), DOWNLOADS_DIR, recursive=False)
    observer.start()
    
    image = create_icon()
    menu = pystray.Menu(pystray.MenuItem("Quit", lambda icon, item: (observer.stop(), icon.stop())))
    icon = pystray.Icon("SmartSort", image, "SmartSort Running", menu)
    icon.run()

if __name__ == "__main__":
    run_app()

import os
import time
import shutil
import threading
import logging
import json
import subprocess
import platform
import sys
import customtkinter as ctk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pypdf import PdfReader
from PIL import Image, ImageDraw
import pystray
import datetime

# --- CONFIGURATION ---
APP_NAME = "SmartSort AI"
CONFIG_FILE = os.path.expanduser("~/smartsort_config.json")
LOG_FILE = os.path.expanduser("~/smartsort_debug.log")

# Default Config
DEFAULT_CONFIG = {
    "target_dir": os.path.expanduser("~/Documents/SmartSort_Vault"),
    "deep_scan": True,
    "startup_cleanup": True,
    "semantic_rules": {
        "invoice": "Financial/Invoices",
        "receipt": "Financial/Receipts",
        "resume": "HR/Resumes",
        "report": "Work/Reports",
        "assignment": "University/Assignments"
    },
    "extension_rules": {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"],
        "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".csv"],
        "Audio": [".mp3", ".wav", ".aac"],
        "Video": [".mp4", ".mkv", ".mov", ".avi"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "Installers": [".exe", ".msi", ".dmg", ".pkg"]
    }
}

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f: json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r') as f: return json.load(f)
    except:
        return DEFAULT_CONFIG

def save_config(new_config):
    with open(CONFIG_FILE, 'w') as f: json.dump(new_config, f, indent=4)

# --- THE BRAIN ---
class ContentBrain:
    def analyze(self, filepath, filename, config):
        ext = os.path.splitext(filepath)[1].lower()
        text = ""
        
        # Deep Scan
        if config.get("deep_scan", True):
            try:
                if ext == ".pdf":
                    reader = PdfReader(filepath)
                    text = "".join([page.extract_text() for page in reader.pages[:2]])
                elif ext in [".txt", ".md", ".csv"]:
                    with open(filepath, "r", errors="ignore") as f: text = f.read(2000)
            except: pass
        text = text.lower()

        # Semantic Rules
        for key, folder in config["semantic_rules"].items():
            if key in text or key in filename.lower():
                # Smart Rename for Financial
                if "financial" in folder.lower() and str(datetime.date.today()) not in filename:
                    name, ext = os.path.splitext(filename)
                    return folder, f"{key.title()}_{datetime.date.today()}_{name}{ext}"
                return folder, filename

        # Extension Rules
        for folder, extensions in config["extension_rules"].items():
            if ext in extensions:
                return folder, filename
                
        return "Others", filename

class ProHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory: threading.Thread(target=self.process, args=(event.src_path,)).start()
    
    def on_moved(self, event):
        if not event.is_directory: threading.Thread(target=self.process, args=(event.dest_path,)).start()

    def process(self, filepath):
        config = load_config()
        filename = os.path.basename(filepath)
        
        # Safety Checks
        if filename.startswith(".") or "crdownload" in filename or filename == "Unknown": return
        if filename in ["SmartSort.app", "SmartSort.zip", "SmartSort.exe"]: return

        time.sleep(2)
        if not os.path.exists(filepath): return

        try:
            brain = ContentBrain()
            folder, new_name = brain.analyze(filepath, filename, config)
            dest = os.path.join(config["target_dir"], folder)
            os.makedirs(dest, exist_ok=True)
            final_path = os.path.join(dest, new_name)
            
            counter = 1
            base, ext = os.path.splitext(new_name)
            while os.path.exists(final_path):
                final_path = os.path.join(dest, f"{base}_{counter}{ext}")
                counter += 1
                
            shutil.move(filepath, final_path)
            logging.info(f"Sorted {filename} -> {folder}")
        except Exception as e:
            logging.error(f"Error: {e}")

# --- GUI SETTINGS WINDOW ---
class SettingsWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SmartSort AI - Settings")
        self.geometry("600x500")
        self.config = load_config()
        
        ctk.CTkLabel(self, text="SmartSort Configuration", font=("Arial", 22, "bold")).pack(pady=20)

        self.var_deep = ctk.BooleanVar(value=self.config.get("deep_scan", True))
        self.var_cleanup = ctk.BooleanVar(value=self.config.get("startup_cleanup", True))
        
        switch_frame = ctk.CTkFrame(self)
        switch_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkSwitch(switch_frame, text="Enable Deep Scan", variable=self.var_deep).pack(side="left", padx=20, pady=10)
        ctk.CTkSwitch(switch_frame, text="Startup Cleanup", variable=self.var_cleanup).pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(self, text="Edit Rules (JSON):").pack(anchor="w", padx=25, pady=(15,0))
        self.text_area = ctk.CTkTextbox(self, height=200)
        self.text_area.pack(padx=20, pady=5, fill="both", expand=True)
        
        pretty_json = json.dumps(self.config["semantic_rules"], indent=4)
        self.text_area.insert("0.0", pretty_json)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Open Logs", command=self.open_logs, fg_color="#555").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Save & Close", command=self.save_and_close, fg_color="#2cc985", text_color="black").pack(side="left", padx=10)

    def open_logs(self):
        if platform.system() == "Darwin": subprocess.call(('open', LOG_FILE))
        else: os.startfile(LOG_FILE)

    def save_and_close(self):
        try:
            new_rules = json.loads(self.text_area.get("0.0", "end"))
            self.config["semantic_rules"] = new_rules
            self.config["deep_scan"] = self.var_deep.get()
            self.config["startup_cleanup"] = self.var_cleanup.get()
            save_config(self.config)
            self.destroy()
        except Exception as e:
            ctk.CTkLabel(self, text=f"Error: {e}", text_color="red").pack()

# --- SYSTEM TRAY ---
def create_icon():
    image = Image.new('RGB', (64, 64), color=(0, 122, 204))
    d = ImageDraw.Draw(image)
    d.rectangle([20, 20, 44, 44], fill="white")
    return image

def launch_settings(icon, item):
    # Launch Settings in a separate process to avoid Mac Thread conflicts
    if getattr(sys, 'frozen', False):
        subprocess.Popen([sys.executable, "--settings"])
    else:
        subprocess.Popen([sys.executable, __file__, "--settings"])

def run_tray():
    # 1. Startup Cleanup
    config = load_config()
    if config.get("startup_cleanup", True):
        handler = ProHandler()
        folders = [os.path.expanduser("~/Downloads"), os.path.expanduser("~/Desktop")]
        for f in folders:
            if os.path.exists(f):
                for file in os.listdir(f):
                    if os.path.isfile(os.path.join(f, file)): handler.process(os.path.join(f, file))

    # 2. Watcher
    observer = Observer()
    handler = ProHandler()
    observer.schedule(handler, os.path.expanduser("~/Downloads"), recursive=False)
    observer.schedule(handler, os.path.expanduser("~/Desktop"), recursive=False)
    observer.start()
    
    # 3. Tray Icon
    image = create_icon()
    menu = pystray.Menu(
        pystray.MenuItem("⚙️ Settings", launch_settings),
        pystray.MenuItem("Exit", lambda icon, item: (observer.stop(), icon.stop()))
    )
    icon = pystray.Icon("SmartSort", image, "SmartSort Running", menu)
    icon.run()

# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    if "--settings" in sys.argv:
        app = SettingsWindow()
        app.mainloop()
    else:
        run_tray()

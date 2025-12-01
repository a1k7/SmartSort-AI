import os
import time
import shutil
import threading
import logging
import json
import subprocess
import platform
import sys
import requests
import webbrowser
import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pypdf import PdfReader
from PIL import Image, ImageDraw
import pystray

# --- CONFIGURATION ---
APP_VERSION = "v3.1"
GITHUB_REPO = "a1k7/SmartSort-AI"
APP_NAME = "SmartSort AI"

CONFIG_FILE = os.path.expanduser("~/smartsort_config.json")
STATS_FILE = os.path.expanduser("~/smartsort_stats.json")
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
        "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".csv", ".rtf"],
        "Audio": [".mp3", ".wav", ".aac"],
        "Video": [".mp4", ".mkv", ".mov", ".avi"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "Installers": [".exe", ".msi", ".dmg", ".pkg"]
    }
}

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

# --- DATA MANAGER ---
def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f: json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r') as f: return json.load(f)
    except: return DEFAULT_CONFIG

def save_config(new_config):
    with open(CONFIG_FILE, 'w') as f: json.dump(new_config, f, indent=4)

def update_stats(count=1):
    data = {"files_sorted": 0, "time_saved_mins": 0}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f: data = json.load(f)
        except: pass
    
    data["files_sorted"] += count
    data["time_saved_mins"] += (count * 0.5) # Assume 30s saved per file
    
    with open(STATS_FILE, 'w') as f: json.dump(data, f)

def get_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f: return json.load(f)
        except: pass
    return {"files_sorted": 0, "time_saved_mins": 0}

# --- THE BRAIN ---
class ContentBrain:
    def analyze(self, filepath, filename, config):
        ext = os.path.splitext(filepath)[1].lower()
        text = ""
        
        if config.get("deep_scan", True):
            try:
                if ext == ".pdf":
                    reader = PdfReader(filepath)
                    text = "".join([page.extract_text() for page in reader.pages[:2]])
                elif ext in [".txt", ".md", ".csv", ".rtf"]:
                    with open(filepath, "r", errors="ignore") as f: text = f.read(2000)
            except: pass
        text = text.lower()

        for key, folder in config["semantic_rules"].items():
            if key in text or key in filename.lower():
                if "financial" in folder.lower() and str(datetime.date.today()) not in filename:
                    name, ext = os.path.splitext(filename)
                    return folder, f"{key.title()}_{datetime.date.today()}_{name}{ext}"
                return folder, filename

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
            update_stats() # TRACK STATS
            logging.info(f"Sorted {filename} -> {folder}")
        except Exception as e:
            logging.error(f"Error: {e}")

# --- GUI DASHBOARD ---
class DashboardWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"SmartSort AI {APP_VERSION}")
        self.geometry("700x550")
        self.config = load_config()
        
        # TABS
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_dash = self.tabview.add("Dashboard")
        self.tab_rules = self.tabview.add("Rules & Settings")
        
        self.build_dashboard()
        self.build_settings()

    def build_dashboard(self):
        stats = get_stats()
        
        # Header
        ctk.CTkLabel(self.tab_dash, text="Your Impact", font=("Arial", 24, "bold")).pack(pady=20)
        
        # Stats Cards
        frame = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        frame.pack(pady=10)
        
        self.create_stat_card(frame, "Files Sorted", str(stats["files_sorted"]), "#3b82f6")
        self.create_stat_card(frame, "Time Saved", f"{int(stats['time_saved_mins'])} min", "#10b981")

        # Update Checker
        ctk.CTkButton(self.tab_dash, text="Check for Updates", command=self.check_update).pack(pady=40)
        
        # Viral Loop
        ctk.CTkLabel(self.tab_dash, text="Share your setup with friends!", text_color="gray").pack()
        btn_frame = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Export Rules", command=self.export_rules, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Import Rules", command=self.import_rules, width=120, fg_color="#555").pack(side="left", padx=10)

    def create_stat_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, width=200, height=100, border_color=color, border_width=2)
        card.pack(side="left", padx=20)
        ctk.CTkLabel(card, text=value, font=("Arial", 32, "bold"), text_color=color).pack(pady=(20,0))
        ctk.CTkLabel(card, text=title, font=("Arial", 14)).pack(pady=(5,20))

    def build_settings(self):
        # Switches
        self.var_deep = ctk.BooleanVar(value=self.config.get("deep_scan", True))
        self.var_cleanup = ctk.BooleanVar(value=self.config.get("startup_cleanup", True))
        
        ctk.CTkSwitch(self.tab_rules, text="Enable Deep Scan", variable=self.var_deep).pack(pady=10)
        ctk.CTkSwitch(self.tab_rules, text="Startup Cleanup", variable=self.var_cleanup).pack(pady=10)

        # JSON Editor
        ctk.CTkLabel(self.tab_rules, text="Edit Rules (JSON):").pack(anchor="w", padx=20)
        self.text_area = ctk.CTkTextbox(self.tab_rules, height=200)
        self.text_area.pack(padx=20, pady=5, fill="both", expand=True)
        self.text_area.insert("0.0", json.dumps(self.config["semantic_rules"], indent=4))

        # Action Buttons
        btn_frame = ctk.CTkFrame(self.tab_rules, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Open Logs", command=self.open_logs, fg_color="#555").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Save & Restart", command=self.save_config, fg_color="#2cc985", text_color="black").pack(side="left", padx=10)

    # --- LOGIC METHODS ---
    def check_update(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(url, timeout=3).json()
            latest_tag = response.get("tag_name", APP_VERSION)
            
            if latest_tag != APP_VERSION:
                msg = f"Update Available!\n\nCurrent: {APP_VERSION}\nNew: {latest_tag}"
                if messagebox.askyesno("Update", msg + "\n\nDownload now?"):
                    webbrowser.open(f"https://github.com/{GITHUB_REPO}/releases/latest")
            else:
                messagebox.showinfo("Update", "You are up to date! 🚀")
        except:
            messagebox.showerror("Error", "Could not check for updates.")

    def export_rules(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            with open(path, 'w') as f: json.dump(self.config["semantic_rules"], f, indent=4)
            messagebox.showinfo("Success", "Rules exported successfully!")

    def import_rules(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            try:
                with open(path, 'r') as f: new_rules = json.load(f)
                self.config["semantic_rules"].update(new_rules)
                save_config(self.config)
                self.text_area.delete("0.0", "end")
                self.text_area.insert("0.0", json.dumps(self.config["semantic_rules"], indent=4))
                messagebox.showinfo("Success", "Rules imported! Click Save to apply.")
            except:
                messagebox.showerror("Error", "Invalid JSON file.")

    def open_logs(self):
        if platform.system() == "Darwin": subprocess.call(('open', LOG_FILE))
        else: os.startfile(LOG_FILE)

    def save_config(self):
        try:
            new_rules = json.loads(self.text_area.get("0.0", "end"))
            self.config["semantic_rules"] = new_rules
            self.config["deep_scan"] = self.var_deep.get()
            self.config["startup_cleanup"] = self.var_cleanup.get()
            save_config(self.config)
            self.destroy()
        except:
            messagebox.showerror("Error", "Invalid JSON format in rules.")

# --- SYSTEM TRAY ---
def create_icon():
    image = Image.new('RGB', (64, 64), color=(0, 122, 204))
    d = ImageDraw.Draw(image)
    d.rectangle([20, 20, 44, 44], fill="white")
    return image

def launch_dashboard(icon, item):
    if getattr(sys, 'frozen', False):
        subprocess.Popen([sys.executable, "--settings"])
    else:
        subprocess.Popen([sys.executable, __file__, "--settings"])

def run_tray():
    config = load_config()
    if config.get("startup_cleanup", True):
        handler = ProHandler()
        for f in [os.path.expanduser("~/Downloads"), os.path.expanduser("~/Desktop")]:
            if os.path.exists(f):
                for file in os.listdir(f):
                    if os.path.isfile(os.path.join(f, file)): handler.process(os.path.join(f, file))

    observer = Observer()
    handler = ProHandler()
    observer.schedule(handler, os.path.expanduser("~/Downloads"), recursive=False)
    observer.schedule(handler, os.path.expanduser("~/Desktop"), recursive=False)
    observer.start()
    
    image = create_icon()
    menu = pystray.Menu(
        pystray.MenuItem("📊 Dashboard & Settings", launch_dashboard),
        pystray.MenuItem("Exit", lambda icon, item: (observer.stop(), icon.stop()))
    )
    icon = pystray.Icon("SmartSort", image, "SmartSort Running", menu)
    icon.run()

if __name__ == "__main__":
    if "--settings" in sys.argv:
        app = DashboardWindow()
        app.mainloop()
    else:
        run_tray()

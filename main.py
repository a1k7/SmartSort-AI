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
import re
from tkinter import filedialog, messagebox
import customtkinter as ctk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pypdf import PdfReader
from PIL import Image, ImageDraw
import pystray
import google.generativeai as genai

# --- CONFIGURATION ---
APP_VERSION = "v4.1"
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
    "ai_renaming": False,
    "gemini_api_key": "",
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
    data = {"files_sorted": 0, "ai_renames": 0}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                data = json.load(f)
        except: pass
    
    data["files_sorted"] += count
    with open(STATS_FILE, 'w') as f: json.dump(data, f)

def get_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"files_sorted": 0, "ai_renames": 0}

# --- THE HYBRID BRAIN ---
class ContentBrain:
    def extract_date(self, text):
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{4}'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match: return match.group(0).replace("/", "-").replace(" ", "_")
        return str(datetime.date.today())

    def extract_entity(self, text):
        common_entities = ["Amazon", "Apple", "Google", "Netflix", "Spotify", "Uber", "Lyft", "Bank", "Hospital", "University"]
        for entity in common_entities:
            if entity.lower() in text.lower(): return entity
        return "Doc"

    def get_local_smart_name(self, text, original_name):
        if len(text) < 10: return original_name
        
        doc_type = "File"
        if "invoice" in text.lower(): doc_type = "Invoice"
        elif "receipt" in text.lower(): doc_type = "Receipt"
        elif "report" in text.lower(): doc_type = "Report"
        elif "resume" in text.lower(): doc_type = "Resume"
        else: return original_name

        entity = self.extract_entity(text)
        date_str = self.extract_date(text)
        ext = os.path.splitext(original_name)[1]
        
        new_name = f"{doc_type}_{entity}_{date_str}{ext}"
        logging.info(f"⚡ Local Smart Rename: {original_name} -> {new_name}")
        return new_name

    def get_ai_filename(self, text, original_name, api_key):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Rename this file concisely. Format: Type_Entity_Date.ext. Text: {text[:300]}"
            response = model.generate_content(prompt)
            clean = response.text.strip().replace(" ", "_")
            ext = os.path.splitext(original_name)[1]
            if not clean.endswith(ext): clean += ext
            return clean
        except: return original_name

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
        
        final_name = filename
        
        # Priority 1: AI API
        if config.get("ai_renaming", False) and config.get("gemini_api_key"):
            final_name = self.get_ai_filename(text, filename, config["gemini_api_key"])
        # Priority 2: Local Smart Logic
        elif config.get("deep_scan", True) and len(text) > 20:
            final_name = self.get_local_smart_name(text, filename)

        text_lower = text.lower()
        for key, folder in config["semantic_rules"].items():
            if key in text_lower or key in filename.lower():
                return folder, final_name

        for folder, extensions in config["extension_rules"].items():
            if ext in extensions:
                return folder, final_name
                
        return "Others", final_name

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
            update_stats()
            logging.info(f"Sorted {filename} -> {folder}/{new_name}")
        except Exception as e:
            logging.error(f"Error: {e}")

# --- GUI ---
class DashboardWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("700x600")
        self.config = load_config()
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        self.tab_dash = self.tabview.add("Dashboard")
        self.tab_rules = self.tabview.add("Settings")
        
        self.build_dashboard()
        self.build_settings()

    def build_dashboard(self):
        stats = get_stats()
        ctk.CTkLabel(self.tab_dash, text="Your Impact", font=("Arial", 24, "bold")).pack(pady=20)
        
        frame = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        frame.pack(pady=10)
        self.create_stat_card(frame, "Files Sorted", str(stats["files_sorted"]), "#3b82f6")
        
        ctk.CTkButton(self.tab_dash, text="Check for Updates", command=self.check_update).pack(pady=40)

    def create_stat_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, width=200, height=100, border_color=color, border_width=2)
        card.pack(side="left", padx=20)
        ctk.CTkLabel(card, text=value, font=("Arial", 32, "bold"), text_color=color).pack(pady=(20,0))
        ctk.CTkLabel(card, text=title, font=("Arial", 14)).pack(pady=(5,20))

    def build_settings(self):
        # AI Section
        ai_frame = ctk.CTkFrame(self.tab_rules)
        ai_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(ai_frame, text="✨ AI Power (Gemini)", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.var_ai = ctk.BooleanVar(value=self.config.get("ai_renaming", False))
        ctk.CTkSwitch(ai_frame, text="Enable AI Auto-Rename", variable=self.var_ai).pack(pady=5)
        
        self.entry_api = ctk.CTkEntry(ai_frame, placeholder_text="Paste Gemini API Key Here", width=300)
        self.entry_api.pack(pady=10)
        if self.config.get("gemini_api_key"): self.entry_api.insert(0, self.config["gemini_api_key"])
        
        ctk.CTkLabel(ai_frame, text="Get free key at aistudio.google.com", font=("Arial", 10), text_color="gray").pack(pady=5)

        # Standard Settings
        self.var_deep = ctk.BooleanVar(value=self.config.get("deep_scan", True))
        self.var_cleanup = ctk.BooleanVar(value=self.config.get("startup_cleanup", True))
        
        ctk.CTkSwitch(self.tab_rules, text="Deep Scan (PDF Reading)", variable=self.var_deep).pack(pady=5)
        ctk.CTkSwitch(self.tab_rules, text="Startup Cleanup", variable=self.var_cleanup).pack(pady=5)

        # Buttons
        ctk.CTkButton(self.tab_rules, text="Save & Apply", command=self.save_config, fg_color="#2cc985", text_color="black").pack(pady=20)

    def check_update(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(url, timeout=3).json()
            latest = response.get("tag_name", APP_VERSION)
            if latest != APP_VERSION:
                if messagebox.askyesno("Update", f"New version {latest} available!"):
                    webbrowser.open(f"https://github.com/{GITHUB_REPO}/releases/latest")
            else: messagebox.showinfo("Info", "Up to date!")
        except: messagebox.showerror("Error", "Check failed")

    def save_config(self):
        self.config["ai_renaming"] = self.var_ai.get()
        self.config["gemini_api_key"] = self.entry_api.get()
        self.config["deep_scan"] = self.var_deep.get()
        self.config["startup_cleanup"] = self.var_cleanup.get()
        save_config(self.config)
        self.destroy()

# --- TRAY ---
def create_icon():
    image = Image.new('RGB', (64, 64), color=(0, 122, 204))
    d = ImageDraw.Draw(image)
    d.rectangle([20, 20, 44, 44], fill="white")
    return image

def launch_dashboard(icon, item):
    if getattr(sys, 'frozen', False): subprocess.Popen([sys.executable, "--settings"])
    else: subprocess.Popen([sys.executable, __file__, "--settings"])

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
    
    icon = pystray.Icon("SmartSort", create_icon(), "SmartSort Running", menu=pystray.Menu(
        pystray.MenuItem("✨ AI Dashboard", launch_dashboard),
        pystray.MenuItem("Exit", lambda icon, item: (observer.stop(), icon.stop()))
    ))
    icon.run()

if __name__ == "__main__":
    if "--settings" in sys.argv:
        app = DashboardWindow()
        app.mainloop()
    else:
        run_tray()

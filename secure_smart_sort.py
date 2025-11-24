import os
import time
import shutil
import platform
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION ---
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
QUARANTINE_DIR = os.path.expanduser("~/Documents/Quarantine")

DESTINATIONS = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"],
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".csv"],
    "Audio": [".mp3", ".wav", ".aac"],
    "Video": [".mp4", ".mkv", ".mov", ".avi"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Installers": [".exe", ".msi", ".dmg", ".pkg"]
}

class SafeFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory: return
        self.process_file(event.src_path)

    def process_file(self, filepath):
        filename = os.path.basename(filepath)
        if filename.startswith(".") or "crdownload" in filename: return

        # Wait for download if it's new
        if not self.wait_for_download(filepath): return
        
        print(f"[+] Processing: {filename}")
        self.sort_file(filepath, filename)

    def wait_for_download(self, filepath):
        historical_size = -1
        for _ in range(30):
            try:
                current_size = os.path.getsize(filepath)
                if current_size == historical_size and current_size > 0: return True
                historical_size = current_size
                time.sleep(0.5)
            except: return False
        return False

    def sort_file(self, source, filename):
        ext = os.path.splitext(filename)[1].lower()
        target_folder = "Others"
        for folder, extensions in DESTINATIONS.items():
            if ext in extensions:
                target_folder = folder
                break
        
        dest_dir = os.path.join(DOWNLOADS_DIR, target_folder)
        os.makedirs(dest_dir, exist_ok=True)
        
        try:
            # Handle duplicates
            base, extension = os.path.splitext(filename)
            counter = 1
            new_name = filename
            while os.path.exists(os.path.join(dest_dir, new_name)):
                new_name = f"{base}_{counter}{extension}"
                counter += 1
                
            shutil.move(source, os.path.join(dest_dir, new_name))
            print(f"    -> Sorted into {target_folder}")
        except Exception as e:
            print(f"    -> Error: {e}")

def run_initial_cleanup():
    print("🧹 Running Startup Cleanup...")
    # Scan all files currently in Downloads
    for filename in os.listdir(DOWNLOADS_DIR):
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        
        # Skip folders and hidden files
        if os.path.isdir(filepath) or filename.startswith("."):
            continue
            
        # Manually process them
        handler = SafeFileHandler()
        handler.process_file(filepath)

if __name__ == "__main__":
    # 1. Clean up the mess FIRST
    run_initial_cleanup()
    
    # 2. Then start watching for new stuff
    observer = Observer()
    observer.schedule(SafeFileHandler(), DOWNLOADS_DIR, recursive=False)
    observer.start()
    print(f"--- SmartSort AI Watching: {DOWNLOADS_DIR} ---")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
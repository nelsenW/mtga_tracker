import os
import json
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MTGALogParser(FileSystemEventHandler):
    def __init__(self, log_path):
        self.log_path = Path(log_path)
        self.last_position = 0

    def parse_existing_logs(self):
        try:
            with open(self.log_path, 'r', encoding='utf-8') as file:
                for line in file:
                    self.process_line(line)
            
            self.last_position = self.log_path.stat().st_size

        except Exception as e:
            print(f"Error reading log file: {e}")
            return
    
    def on_modified(self, event):
        if event.src_path != str(self.log_path):
            return

        max_retries = 3
        for attempt in range(max_retries):
            try:
                with open(self.log_path, 'r', encoding='utf-8') as file:
                    file.seek(self.last_position)
                    for line in file:
                        self.process_line(line)
                    self.last_position = file.tell()
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
                else:
                    print(f"Failed to read log file after {max_retries} attempts: {e}")
                    break

    def process_line(self, line):
        line = line.strip()

        if '{' not in line:
            return
        
        try:
            json_start = line.index('{')
            json_str = line[json_start:]
            data = json.loads(json_str)

            self.handle_event(data)

        except (json.JSONDecodeError, ValueError):
            pass
    
    def handle_event(self, data):
        if 'matchGameRoomStateChangedEvent' in data:
            self.handle_match_event(data)
        elif 'DraftStatus' in data:
            self.handle_draft_event(data)
        elif 'PlayerInventory' in data:
            self.handle_collection_event(data)
        else:
            print(f"Unhandled event type: {data.keys()}")

    def handle_match_event(self, data):
        print(f"Match event: {json.dumps(data, indent=2)}")

    def handle_draft_event(self, data):
        print(f"Draft event: {json.dumps(data, indent=2)}")

    def handle_collection_event(self, data):
        print(f"Collection event: {json.dumps(data, indent=2)}")

def find_mtga_log():
    if os.path.exists('/proc/version'):
        with open('/proc/version', 'r') as f:
            if 'microsoft' in f.read().lower():
                import subprocess
                try:
                    result = subprocess.run(['cmd.exe', '/c', 'echo %USERNAME%'], 
                                          capture_output=True, text=True)
                    win_username = result.stdout.strip()
                    
                    possible_paths = [
                        Path(f'/mnt/c/Users/{win_username}/AppData/LocalLow/Wizards Of The Coast/MTGA/Player.log'),
                    ]
                    
                    for path in possible_paths:
                        if path.exists():
                            return path
                    return None
                    
                except Exception as e:
                    return None
    
    if os.name == 'nt':
        appdata = os.getenv('APPDATA')
        if not appdata:
            print("APPDATA environment variable not found")
            return None
            
        possible_paths = [
            Path(appdata).parent / 'LocalLow' / 'Wizards Of The Coast' / 'MTGA' / 'Player.log',
            Path.home() / 'AppData' / 'LocalLow' / 'Wizards Of The Coast' / 'MTGA' / 'Player.log',
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
    
    test_log = Path.home() / 'mtga_test.log'
    if test_log.exists():
        print(f"[Dev Mode] Using test log: {test_log}")
        return test_log
    
    return None

if __name__ == "__main__":
    log_path = find_mtga_log()

    if not log_path:
        print("Couldn't find MTGA log file, specify manually.")
        exit(1)
    
    print(f"Watching log file: {log_path}")
        
    parser = MTGALogParser(log_path)

    parser.parse_existing_logs()

    observer = Observer()
    observer.schedule(parser, str(log_path.parent), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


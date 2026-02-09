import subprocess
import sys
from pathlib import Path


def check_dependencies():
    try:
        import watchdog
        return True
    except ImportError:
        print(" Missing required package: watchdog")
        print("\nInstalling dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'watchdog'], check=True)
        print(" Dependencies installed")
        return True


def initialize_database():
    db_path = Path('mtga_tracker.db')
    
    if not db_path.exists():
        print("\n Initializing database...")
        subprocess.run([sys.executable, 'mtga_database.py'], check=True)
    else:
        print("\n Database already exists")


def show_menu():
    print("\n" + "=" * 60)
    print("MTGA TRACKER - QUICK START")
    print("=" * 60)
    print("\n1. Start Real-time Tracker (monitor new matches)")
    print("2. View Statistics")
    print("3. Import Historical Data")
    print("4. Reset Database (delete all data)")
    print("5. Exit")
    print("\n" + "=" * 60)


def main():
    print(" MTGA Tracker Setup")
    print("-" * 60)
    
    if not check_dependencies():
        print("\n Failed to install dependencies")
        return
    
    initialize_database()
    
    while True:
        show_menu()
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            print("\n Starting real-time tracker...")
            print("Press Ctrl+C to stop\n")
            try:
                subprocess.run([sys.executable, 'mtga_tracker.py'])
            except KeyboardInterrupt:
                print("\n Tracker stopped")
        
        elif choice == '2':
            print("\n Loading statistics...\n")
            subprocess.run([sys.executable, 'mtga_stats.py'])
            input("\nPress Enter to continue...")
        
        elif choice == '3':
            jsonl_file = input("\nEnter path to match_events.jsonl (or press Enter for default): ").strip()
            if not jsonl_file:
                jsonl_file = '/mnt/user-data/uploads/match_events.jsonl'
            
            if Path(jsonl_file).exists():
                print(f"\n Importing from {jsonl_file}...\n")
                subprocess.run([sys.executable, 'import_history.py', jsonl_file])
                input("\nPress Enter to continue...")
            else:
                print(f"\n File not found: {jsonl_file}")
                input("\nPress Enter to continue...")
        
        elif choice == '4':
            confirm = input("\n  Delete all tracked data? (yes/no): ").strip().lower()
            if confirm == 'yes':
                db_path = Path('mtga_tracker.db')
                if db_path.exists():
                    db_path.unlink()
                    print(" Database deleted")
                    initialize_database()
                else:
                    print("No database to delete")
            else:
                print(" Cancelled")
            input("\nPress Enter to continue...")
        
        elif choice == '5':
            print("\n Goodbye!")
            break
        
        else:
            print("\n Invalid choice. Please enter 1-5.")
            input("\nPress Enter to continue...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Goodbye!")
    except Exception as e:
        print(f"\n Error: {e}")
        sys.exit(1)

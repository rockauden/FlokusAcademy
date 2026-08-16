import sys
import os

# Ensure UTF-8 output formatting on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import database

def main():
    print("==================================================")
    print("🧹 Flokus Academy - Test Data Reset & Go-Live Prep")
    print("==================================================")
    
    confirm = input("⚠️ Are you sure you want to clear all test tasks, projects, chat, purchases, and reset Sparky & UFA expenses to baseline? (y/N): ")
    if confirm.strip().lower() in ['y', 'yes']:
        database.reset_all_test_data()
        print("✅ Success! Flokus Academy test data has been cleared and reset to production baseline.")
    else:
        print("❌ Reset cancelled.")

if __name__ == "__main__":
    main()

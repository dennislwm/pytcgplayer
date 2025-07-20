#!/usr/bin/env python3
"""
Demo script showing idempotent functionality.
"""
import sys
import os
import subprocess
from pathlib import Path

# Add parent directory to path so we can import from common
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.logger import AppLogger


def run_command(cmd: str, description: str):
    """Run a command and show its output"""
    print(f"\n🔄 {description}")
    print(f"Command: {cmd}")
    print("=" * 60)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # Show relevant log lines for duplicate detection
    if result.stdout:
        lines = result.stdout.split('\n')
        for line in lines:
            if 'duplicates' in line or 'total rows' in line or 'new)' in line:
                print(f"📊 {line.strip()}")
    
    return result.returncode == 0


def main():
    # Setup logging
    logger = AppLogger()
    logger.setup_logging(verbose=False, log_file="demo_idempotent.log")
    log = AppLogger.get_logger(__name__)
    
    print("🚀 Idempotent Application Demo")
    print("This demo shows how the application can be run multiple times")
    print("without creating duplicate entries in the output file.\n")
    
    # Clean up any existing demo file
    demo_file = Path("demo_idempotent.csv")
    if demo_file.exists():
        demo_file.unlink()
        print(f"🧹 Cleaned up existing {demo_file}")
    
    # Run 1: First execution (should create 30 new records)
    success1 = run_command(
        "cd .. && PYTHONPATH=. pipenv run python3 main.py data/input.csv demo/demo_idempotent.csv",
        "First Run - Creating new records"
    )
    
    if not success1:
        print("❌ First run failed")
        return 1
    
    # Check file after first run
    if demo_file.exists():
        row_count = len(demo_file.read_text().strip().split('\n'))
        print(f"✅ First run complete: {row_count} total lines (1 header + {row_count-1} data rows)")
    
    # Run 2: Second execution (should detect all as duplicates)
    success2 = run_command(
        "cd .. && PYTHONPATH=. pipenv run python3 main.py data/input.csv demo/demo_idempotent.csv",
        "Second Run - Testing idempotency (should find duplicates)"
    )
    
    if not success2:
        print("❌ Second run failed")
        return 1
    
    # Check file after second run
    if demo_file.exists():
        row_count_after = len(demo_file.read_text().strip().split('\n'))
        print(f"✅ Second run complete: {row_count_after} total lines (unchanged)")
        
        if row_count_after == row_count:
            print("🎯 SUCCESS: File size unchanged - application is idempotent!")
        else:
            print("❌ FAILED: File size changed - duplicates were not detected")
            return 1
    
    # Run 3: Third execution (should still detect all as duplicates)
    success3 = run_command(
        "cd .. && PYTHONPATH=. pipenv run python3 main.py data/input.csv demo/demo_idempotent.csv",
        "Third Run - Confirming idempotency"
    )
    
    if not success3:
        print("❌ Third run failed")
        return 1
    
    final_row_count = len(demo_file.read_text().strip().split('\n'))
    print(f"✅ Third run complete: {final_row_count} total lines (still unchanged)")
    
    print("\n🎉 Idempotent Demo Complete!")
    print("Key Benefits:")
    print("  ✓ Safe to run multiple times")
    print("  ✓ No duplicate data entries")
    print("  ✓ Consistent output regardless of run count")
    print("  ✓ Perfect for automated/scheduled tasks")
    
    log.info("Idempotent demo completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
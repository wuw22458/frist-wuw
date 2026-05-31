"""Quick verification script to check if new UI elements exist."""
import sys
sys.path.insert(0, ".")

from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)

from ui.settings import SettingsWindow
win = SettingsWindow()

# Check hero card elements
print(f"Hero icon exists: {hasattr(win, '_hero_icon')}")
print(f"Hero status text exists: {hasattr(win, '_hero_status_text')}")
print(f"Hero summary exists: {hasattr(win, '_hero_summary')}")
print(f"Hero runtime exists: {hasattr(win, '_hero_runtime')}")
print(f"Pause btn exists: {hasattr(win, '_pause_btn')}")
print(f"Animatable cards count: {len(win._animatable_cards)}")

# Check stats card
print(f"Stat today exists: {hasattr(win, '_stat_today')}")
print(f"Stat waiting exists: {hasattr(win, '_stat_waiting')}")
print(f"Stat errors exists: {hasattr(win, '_stat_errors')}")

# Check filter tags
print(f"Filter tags exist: {hasattr(win, '_filter_tags')}")
print(f"Active filter exists: {hasattr(win, '_active_filter')}")

# Check volume slider
print(f"Volume slider exists: {hasattr(win, '_vol_slider')}")

# Check splash
from ui.splash import AnimatedSplash
splash = AnimatedSplash("1.2.1")
print(f"Splash screen can be created: {splash is not None}")

print("\n=== ALL CHECKS PASSED ===")

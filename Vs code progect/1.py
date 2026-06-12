from pynput.mouse import Button, Controller
import time

mouse = Controller()
INTERVAL = 0.625  # секунди між кліками (0.625 = швидкість атаки 1.6)

print("✅ Автоклікер запущено. Перейди у Minecraft.")
print("CTRL+C у терміналі — зупинити.")

try:
    while True:
        mouse.click(Button.left)
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("\n⛔ Зупинено.")

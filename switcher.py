import threading
import time
import ctypes
import pyperclip
from PIL import Image, ImageDraw
import pystray

user32 = ctypes.windll.user32

# 1. Базовые буквы (строчные и заглавные)
ENG_LETTERS = "qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>"
RUS_LETTERS = "йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ"

# 2. Спецсимволы и цифровой ряд с зажатым Shift
# Обратите внимание: на английской раскладке Shift+2 это `@`, Shift+3 это `#`, Shift+4 это `$`, Shift+6 это `^`, Shift+7 это `&`
# На русской раскладке Shift+2 это `"`, Shift+3 это `№`, Shift+4 это `;`, Shift+6 это `:`, Shift+7 это `?`
ENG_SYMBOLS = "~`@#$^&|/?\\"
RUS_SYMBOLS = "Ёё\"№;:?|.,\\"

# Собираем полный словарь
ENG_FULL = ENG_LETTERS + ENG_SYMBOLS
RUS_FULL = RUS_LETTERS + RUS_SYMBOLS

ENG_TO_RUS = dict(zip(ENG_FULL, RUS_FULL))
RUS_TO_ENG = dict(zip(RUS_FULL, ENG_FULL))

# Дополнительные ручные правила для символов, которые не сошлись один к одному
# Например, английские слэши и точки, имеющие разные значения в раскладках
ADDITIONAL_ENG_TO_RUS = {'/': '.', '?': ',', ',': 'б', '.': 'ю', ';': 'ж', "'": 'э', '[': 'х', ']': 'ъ'}
ADDITIONAL_RUS_TO_ENG = {'.': '/', ',': '?', 'б': ',', 'ю': '.', 'ж': ';', 'э': "'", 'х': '[', 'ъ': ']'}

ENG_TO_RUS.update(ADDITIONAL_ENG_TO_RUS)
RUS_TO_ENG.update(ADDITIONAL_RUS_TO_ENG)

# Глобальные флаги управления
is_running = True
is_active = True
tray_icon = None


def convert_text(text):
    result = []
    for char in text:
        if char in ENG_TO_RUS:
            result.append(ENG_TO_RUS[char])
        elif char in RUS_TO_ENG:
            result.append(RUS_TO_ENG[char])
        else:
            result.append(char)  # Цифры (1, 2, 3...) и пробелы остаются как есть
    return "".join(result)


def clipboard_monitor():
    global is_running, is_active
    last_sequence = user32.GetClipboardSequenceNumber()
    last_copy_time = 0

    while is_running:
        if not is_active:
            time.sleep(0.5)
            continue

        try:
            current_sequence = user32.GetClipboardSequenceNumber()
            if current_sequence != last_sequence:
                current_time = time.time()

                if current_time - last_copy_time < 0.5:
                    current_text = pyperclip.paste()
                    if current_text:
                        converted = convert_text(current_text)
                        if converted != current_text:
                            pyperclip.copy(converted)
                            last_sequence = user32.GetClipboardSequenceNumber()
                            last_copy_time = 0
                            continue

                last_copy_time = current_time
                last_sequence = current_sequence
        except Exception:
            pass

        time.sleep(0.05)


def create_image():
    image = Image.new('RGB', (64, 64), color='#2c3e50')
    d = ImageDraw.Draw(image)
    d.rectangle([(16, 24), (48, 28)], fill='white')
    d.rectangle([(16, 36), (48, 40)], fill='white')
    return image


def on_toggle_action(icon, item):
    global is_active
    is_active = not is_active
    state = "Включен" if is_active else "На паузе"
    icon.title = f"Переводчик раскладки ({state})"


def on_quit_action(icon, item):
    global is_running
    is_running = False
    icon.stop()


def setup_tray():
    global tray_icon
    menu = pystray.Menu(
        pystray.MenuItem('Приостановить / Включить', on_toggle_action),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Выход', on_quit_action)
    )
    tray_icon = pystray.Icon("layout_switcher", create_image(), title="Переводчик раскладки (Включен)", menu=menu)
    tray_icon.run()


if __name__ == "__main__":
    monitor_thread = threading.Thread(target=clipboard_monitor, daemon=True)
    monitor_thread.start()
    setup_tray()

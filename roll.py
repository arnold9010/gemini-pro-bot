# roll.py

# Твой обновленный список ключей
API_KEYS = [
    "AIzaSyC0yW6Df_-poJ4hY6U46tmCWaVLijOxKBY",
    "AIzaSyDgTeuUXRW5PBwcPlbJvLGgYmgaHFCMLVM",
    "AIzaSyDDde0I4Ll8MFiaTR6wusZsxin5khP-eNM",
    "AIzaSyDes-0dhX_QcDiwbDsN429KeteGto-hSCU",
    "AIzaSyCu15npLP2z42eudEeCmLwfUaEegyPtxPM",
    "AIzaSyA_yDfcn8TsxEat966fqKE8g8007H_QCV4",
    "AIzaSyCz7oPoU38Fwe5OceE33AElnRlkHzeH1jc",
    "AIzaSyAd_5oTncxcATlVn_aKx3BEHJpIs7qwQTk"
]

_current_key_index = 0

def get_key():
    """Возвращает текущий активный ключ."""
    return API_KEYS[_current_key_index]

def next_key():
    """Переключает на следующий ключ в списке при ошибке (429 или лимит)."""
    global _current_key_index
    _current_key_index = (_current_key_index + 1) % len(API_KEYS)
    print(f"[*] Switched to API Key index: {_current_key_index}")
    return API_KEYS[_current_key_index]

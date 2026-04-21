# roll.py

# Твой свежий список ключей (вставлено 5 штук)
API_KEYS = [
    "AIzaSyBt_MY6YQGYqPx1ZhnulWmiH9krF5mZFr8",
    "AIzaSyBjg3Mk5Axj_odWRVpDvh0f5PDCYmNiFZ4",
    "AIzaSyAF8Ltfk2AHQbcr5thHB5ofCPH6hvA3gXA",
    "AIzaSyDh6M0V5JBw4_MbFx9smIu2KKOSpGhuUQA",
    "AIzaSyCaIZkgTtg_grZAX-Yt1EuRUkr6NEwCVwY"
]

_current_key_index = 0

def get_key():
    """Возвращает текущий активный ключ."""
    return API_KEYS[_current_key_index]

def next_key():
    """Переключает на следующий ключ в списке при ошибке (429 или 403)."""
    global _current_key_index
    _current_key_index = (_current_key_index + 1) % len(API_KEYS)
    print(f"[*] Switched to API Key index: {_current_key_index}")
    return API_KEYS[_current_key_index]

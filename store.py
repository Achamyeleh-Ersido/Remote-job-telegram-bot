import json
import os

DATA_DIR = os.path.join(os.getcwd(), "data")
STORE_FILE = os.path.join(DATA_DIR, "posted.json")
MAX_IDS = 5000  # keep the file from growing forever


def _ensure_store():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(STORE_FILE):
        with open(STORE_FILE, "w") as f:
            json.dump([], f)


def load_posted_ids() -> set:
    _ensure_store()
    try:
        with open(STORE_FILE, "r") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, FileNotFoundError):
        return set()


def save_posted_ids(ids: set) -> None:
    _ensure_store()
    id_list = list(ids)
    # Trim if it grows too large, keeping the most recently added ones isn't
    # guaranteed by set ordering, so we just cap the size to bound file growth.
    if len(id_list) > MAX_IDS:
        id_list = id_list[-MAX_IDS:]
    with open(STORE_FILE, "w") as f:
        json.dump(id_list, f, indent=2)

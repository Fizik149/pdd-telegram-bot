import json
import random
import string
from datetime import datetime

NUM_CODES = 10
CODES_FILE = "codes.json"

def generate_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

with open(CODES_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

for _ in range(NUM_CODES):
    code = generate_code()
    while code in data["codes"]:
        code = generate_code()
    data["codes"][code] = {
        "created": datetime.now().strftime("%Y-%m-%d"),
        "active": True,
        "used": False,
        "used_by": None,
        "used_at": None
    }

with open(CODES_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"✅ Сгенерировано {NUM_CODES} кодов.")

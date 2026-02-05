import json
from pathlib import Path
from config import DB_PATH


def save_appointment(
    user_id, procedure_id, specialist_id, salon_id,
    date, time, price_original, discount_percent,
    price_final, promo_code, source
):

    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    if "appointments" not in db:
        db["appointments"] = []

    appointment = {
        "id": f"app_{len(db['appointments']) + 1}",
        "client_telegram_id": user_id,
        "procedure_id": procedure_id,
        "specialist_id": specialist_id,
        "salon_id": salon_id,
        "date": date,
        "time": time,
        "source": source,
        "promo_code": promo_code,
        "price_original": price_original,
        "discount_percent": discount_percent,
        "price_final": price_final
    }

    db["appointments"].append(appointment)

    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

import json
from pathlib import Path
from decouple import config as env

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = Path(env("DB_PATH"))

with open(DB_PATH, "r", encoding="utf-8") as f:
    DB = json.load(f)

# быстрые алиасы
SALONS = DB["salons"]
PROCEDURES = DB["procedures"]
SPECIALISTS = DB["specialists"]
PROMOCODES = DB["promo_codes"]

PD_PDF_PATH = BASE_DIR / "data" / DB["meta"]["pd_agreement"]["pdf_file"]
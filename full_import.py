import os
import requests
from supabase import create_client

# =========================
# SUPABASE CONFIG
# =========================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "usom_threats"

# =========================
# USOM API
# =========================
USOM_API_URL = "https://www.usom.gov.tr/api/address/index"

# =========================
# FETCH DATA FROM USOM
# =========================
def fetch_usom():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(USOM_API_URL, headers=headers, timeout=60)
    r.raise_for_status()

    data = r.json()

    # API structure genelde:
    # {
    #   "models": [
    #       {"id":..., "url":"domain.com", "type":"domain"}
    #   ]
    # }

    models = data.get("models", [])

    results = []

    for item in models:
        value = item.get("url") or item.get("ip") or item.get("domain")

        if not value:
            continue

        results.append({
            "indicator": value.strip().lower(),
            "type": item.get("type"),
            "source": item.get("source"),
            "criticality": item.get("criticality"),
            "first_seen": item.get("date")
        })

    return results


# =========================
# UPSERT TO SUPABASE
# =========================
def insert_to_supabase(items):
    batch = []

    for item in items:
        batch.append(item)

        if len(batch) >= 500:
            supabase.table(TABLE_NAME).upsert(
                batch,
                on_conflict="indicator"
            ).execute()
            batch = []

    if batch:
        supabase.table(TABLE_NAME).upsert(
            batch,
            on_conflict="indicator"
        ).execute()


# =========================
# MAIN
# =========================
def main():
    print("USOM API çekiliyor...")

    items = fetch_usom()
    print(f"Toplam kayıt: {len(items)}")

    print("Supabase yazılıyor...")
    insert_to_supabase(items)

    print("Bitti")


if __name__ == "__main__":
    main()

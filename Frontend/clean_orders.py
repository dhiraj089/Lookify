import json
import os

DB_FILE = "d:/Lookify/Frontend/database/orders.json"

def clean_orders():
    if not os.path.exists(DB_FILE):
        print(f"Error: {DB_FILE} not found.")
        return

    with open(DB_FILE, "r") as f:
        try:
            orders = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

    cleaned_count = 0
    for order in orders:
        if "email" in order:
            original = order["email"]
            # Remove whitespace, newlines, and non-printable characters
            cleaned = "".join(original.split()).strip().lower()
            if cleaned != original:
                order["email"] = cleaned
                cleaned_count += 1
                print(f"Cleaned email: {repr(original)} -> {repr(cleaned)}")

    if cleaned_count > 0:
        with open(DB_FILE, "w") as f:
            json.dump(orders, f, indent=4)
        print(f"Successfully cleaned {cleaned_count} email entries in {DB_FILE}.")
    else:
        print("No corrupted email entries found.")

if __name__ == "__main__":
    clean_orders()

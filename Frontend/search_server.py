from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# ---------- PATHS ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
DATASET_CSV = os.path.join(PARENT_DIR, "styles.csv")
IMAGE_DIR = os.path.join(PARENT_DIR, "fashion-dataset", "images")

# ---------- LOAD DATA ----------
if os.path.exists(DATASET_CSV):
    df = pd.read_csv(DATASET_CSV, on_bad_lines='skip')
else:
    df = pd.DataFrame(columns=["id", "gender", "masterCategory", "subCategory", "articleType", "productDisplayName"])

TEXT_COLS = ["gender", "masterCategory", "subCategory", "articleType", "productDisplayName"]
for col in TEXT_COLS:
    if col in df.columns:
        df[col] = df[col].astype(str).str.lower()

# ---------- IMAGE ROUTE ----------
@app.route("/fashion-dataset/images/<path:filename>")
def images(filename):
    return send_from_directory(IMAGE_DIR, filename)

# ---------- SEARCH API ----------
@app.route("/api/search")
def search_products():
    query = request.args.get("q", "").lower().strip()
    if not query:
        return jsonify([])

    words = query.split()

    gender = None
    article = None

    # Gender detection
    if "men" in words or "mens" in words:
        gender = "men"
    elif "women" in words or "womens" in words:
        gender = "women"

    # Article detection
    if "tshirt" in words or "t-shirt" in words:
        article = "tshirts"
    elif "shirt" in words:
        article = "shirts"
    elif "jeans" in words:
        article = "jeans"
    elif "shoes" in words:
        article = "shoes"
    elif "bag" in words:
        article = "bags"

    results = df.copy()

    if gender:
        results = results[results["gender"].str.contains(gender)]

    if article:
        results = results[results["articleType"].str.contains(article)]

    # Fallback: name search
    if results.empty:
        results = df[df["productDisplayName"].str.contains(query)]

    results = results.head(24)

    output = []
    for _, row in results.iterrows():
        output.append({
            "id": int(row["id"]),
            "productDisplayName": row.get("productDisplayName", "").title(),
            "masterCategory": row.get("masterCategory", "").title(),
            "subCategory": row.get("subCategory", "").title(),
            "price": 2999,
            "image": f"/fashion-dataset/images/{row['id']}.jpg"
        })

    return jsonify(output)

# ---------- RUN ----------
if __name__ == "__main__":
    print("[OK] Search API running at http://127.0.0.1:8002")
    app.run(port=8002, debug=True)

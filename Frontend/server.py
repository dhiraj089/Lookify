import os
import json
import smtplib
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

import threading
from io import BytesIO
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
from dotenv import load_dotenv

# ReportLab Imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

load_dotenv() # Load environment variables from .env

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable Cross-Origin Resource Sharing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_LOGIN_DIR = BASE_DIR

# --- CONFIGURATION ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "lookify121@gmail.com"
SENDER_PASSWORD = "cxpd ptxv pngc ynfr" 
# Note: Reverted to these credentials because 'Lookifyfashion121@' was blocked by Google.

DB_FILE = os.path.join(BASE_DIR, "database", "orders.json")
USERS_FILE = os.path.join(BASE_DIR, "database", "users.json")

# Ensure database directory exists
os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)
for file in [DB_FILE, USERS_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f)

def verify_db():
    for file in [DB_FILE, USERS_FILE]:
        if not os.path.exists(file):
            with open(file, "w") as f:
                json.dump([], f)

# --- USER APIs ---

@app.route('/api/signup', methods=['POST'])
def signup():
    print("DEBUG: Received Signup request")
    try:
        data = request.json
        print(f"DEBUG: Signup Data: {data}")
        email = data.get('email', '').strip().lower()
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        data['email'] = email
        verify_db()
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
            
        if any(u['email'] == email for u in users):
            return jsonify({"error": "User already exists"}), 400
            
        users.append(data)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)
            
        return jsonify({"success": True, "message": "Account created successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    print("DEBUG: Received Login request")
    try:
        data = request.json
        print(f"DEBUG: Login Data: {data}")
        email = data.get('email', '').strip().lower()
        password = data.get('password')
        
        verify_db()
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
            
        user = next((u for u in users if u['email'] == email and u['password'] == password), None)
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401
            
        return jsonify({"success": True, "user": user})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/update_user', methods=['POST'])
def update_user():
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        if not email:
            return jsonify({"error": "Email is required"}), 400
            
        data['email'] = email
        verify_db()
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
            
        found = False
        for i, u in enumerate(users):
            if u['email'] == email:
                users[i].update(data)
                found = True
                break
        
        if not found:
            return jsonify({"error": "User not found"}), 404
            
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)
            
        return jsonify({"success": True, "message": "Profile updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ROUTES ---

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# NEW: Serve images from parent directory
@app.route('/fashion-dataset/<path:filename>')
def serve_images(filename):
    # Go up one level to 'Lookify/', then into 'fashion-dataset'
    # Current dir is 'Lookify/Frontend'
    # Parent is 'Lookify'
    parent_dir = os.path.dirname(BASE_DIR)
    folder = os.path.join(parent_dir, 'fashion-dataset')
    return send_from_directory(folder, filename)

@app.route('/checkout')
def checkout_page():
    # Only if checkout.html exists, otherwise redirect or error
    if os.path.exists(os.path.join(BASE_DIR, 'checkout.html')):
        return send_from_directory('.', 'checkout.html')
    return "Checkout page not found", 404

@app.route('/checkout/address')
def legacy_address_redirect():
    return redirect('/checkout')

# @app.route('/checkout/payment') - No longer needed, handled by SPA
# @app.route('/checkout/success') - No longer needed, handled by SPA

@app.route('/web_login/checkout.html')
def legacy_checkout_redirect():
    return redirect('/checkout')

@app.route('/payment.html')
@app.route('/web_login/payment.html')
def payment_page():
    return send_from_directory('.', 'payment.html')



# --- TEMP CART STORAGE (For Session Handoff) ---
TEMP_CARTS = {}

@app.route('/api/init_checkout', methods=['POST'])
def init_checkout():
    try:
        data = request.json
        import uuid
        token = str(uuid.uuid4())
        TEMP_CARTS[token] = data.get('cart', [])
        return jsonify({"success": True, "token": token})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_cart/<token>', methods=['GET'])
def get_cart(token):
    cart = TEMP_CARTS.get(token)
    if cart is None:
        return jsonify({"error": "Session expired or invalid"}), 404
    return jsonify(cart)


@app.route('/api/checkout', methods=['POST'])
def checkout():
    try:
        data = request.json
        user_email = data.get('email')

        cart_items = data.get('items', [])
        total_amount = data.get('total')
        address = data.get('address')
        payment_method = data.get('payment_method')
        
        if not user_email or not cart_items:
            return jsonify({"error": "Invalid data"}), 400

        # 1. Create Order Object
        order_id = f"ORD-{int(datetime.now().timestamp())}"
        order = {
            "order_id": order_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "email": user_email,
            "items": cart_items,
            "total": total_amount,
            "address": address,
            "payment": payment_method,
            "status": "Confirmed"
        }

        # 2. Save Order to Database (JSON)
        verify_db()
        with open(DB_FILE, "r") as f:
            orders = json.load(f)
        
        # Clean email before saving
        order['email'] = user_email.strip().lower()
        
        orders.append(order)
        with open(DB_FILE, "w") as f:
            json.dump(orders, f, indent=4)

        # 3. Send Email Invoice (Asynchronously to prevent timeout)
        threading.Thread(target=send_invoice_email, args=(user_email, order)).start()

        return jsonify({"success": True, "order_id": order_id})

    except Exception as e:
        print(f"Checkout Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    email = request.args.get('email')
    if not email:
        return jsonify([])
    
    verify_db()
    with open(DB_FILE, "r") as f:
        orders = json.load(f)
    
    search_email = email.strip().lower()
    user_orders = [o for o in orders if o.get('email', '').strip().lower() == search_email]
    return jsonify(user_orders)




@app.route('/api/search', methods=['GET'])
def search_products():
    try:
        query = request.args.get('q', '').lower().strip()
        if not query:
            return jsonify([])

        # Read styles.csv
        csv_path = os.path.join(os.path.dirname(BASE_DIR), 'styles.csv')
        if not os.path.exists(csv_path):
             csv_path = os.path.join(BASE_DIR, 'styles.csv')

        results = []
        if os.path.exists(csv_path):
            with open(csv_path, mode='r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                
                # Pre-process query tokens
                raw_tokens = query.split()
                tokens = []
                for t in raw_tokens:
                    # Simple normalization
                    if t in ['mens', 'men\'s']: t = 'men'
                    elif t in ['womens', 'women\'s']: t = 'women'
                    elif t in ['boys', 'boy\'s']: t = 'boy'
                    elif t in ['girls', 'girl\'s']: t = 'girl'
                    elif t.endswith('s') and len(t) > 3: # Simple singularization attempt for "bags" -> "bag"
                         # Very naive, but better than nothing for "tshirts" -> "tshirt" (which is still "tshirts" in csv?)
                         # Actually CSV says "Tshirts". Query "Tshirt". 
                         # So we should probably match substrings or check both.
                         pass
                    tokens.append(t)

                for row in reader:
                    # Construct a rich searchable string
                    searchable_text = f"{row['gender']} {row['masterCategory']} {row['subCategory']} {row['articleType']} {row['baseColour']} {row['usage']} {row['productDisplayName']}".lower()
                    
                    # Check if ALL tokens are in the searchable text
                    # We use a slightly fuzzy match: token just needs to be PART of a word in the text?
                    # or just strictly contained in the string.
                    match_count = 0
                    for token in tokens:
                        if token in searchable_text:
                            match_count += 1
                        else:
                            # Try singular/plural variations if direct match fails
                            if token.endswith('s') and token[:-1] in searchable_text: match_count += 1
                            elif (token + 's') in searchable_text: match_count += 1
                    
                    # Require ALL tokens to match (logic: AND)
                    if match_count == len(tokens):
                        row['image'] = f"/fashion-dataset/images/{row['id']}.jpg"
                        # Generate random price for search results
                        # User requested "shuffle minimum price", interpreting as random affordable prices.
                        import random
                        row['price'] = random.randint(3, 20) * 100 + 49 # e.g. 349, 449 ... 2049
                        results.append(row)
                        if len(results) >= 50: 
                            break
        
        return jsonify(results)
    except Exception as e:
        print(f"Search Error: {e}")
        return jsonify([])




@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    try:
        import csv
        import random
        
        seed_name = request.args.get('seed', '')
        
        # Read styles.csv
        csv_path = os.path.join(os.path.dirname(BASE_DIR), 'styles.csv')
        if not os.path.exists(csv_path):
             csv_path = os.path.join(BASE_DIR, 'styles.csv')

        items = []
        
        if os.path.exists(csv_path):
            with open(csv_path, mode='r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                all_rows = list(reader)
                
                seed_item = None
                if seed_name:
                    for row in all_rows:
                        if seed_name.strip().lower() in row['productDisplayName'].strip().lower():
                            seed_item = row
                            break
                
                # --- SMART SEED PARSING ---
                if not seed_item:
                    seed_lower = seed_name.lower()
                    
                    # Guess Gender
                    guessed_gender = 'Men' # Default
                    
                    women_keywords = ['women', 'girl', 'dress', 'skirt', 'saree', 'lehenga', 'kurti', 'gown', 'top', 'blouse', 'legging', 'churidar']
                    men_keywords = ['men', 'boy', 'shirt', 'tshirt', 'trouser', 'suit', 'sherwani']
                    
                    # Check for women first (prioritize 'top' as women's if ambiguous, though 'tank top' could be men)
                    if any(x in seed_lower for x in women_keywords): 
                        guessed_gender = 'Women'
                    elif any(x in seed_lower for x in men_keywords):
                        guessed_gender = 'Men'

                    
                    # Guess Category
                    guessed_sub_cat = 'Topwear' # Default
                    if any(x in seed_lower for x in ['jeans', 'trousers', 'pant', 'shorts', 'skirt', 'leggings']):
                        guessed_sub_cat = 'Bottomwear'
                    elif any(x in seed_lower for x in ['shoe', 'sandal', 'heel', 'flat', 'boot', 'sneaker']):
                        guessed_sub_cat = 'Shoes'
                        
                    seed_item = {
                        'gender': guessed_gender,
                        'masterCategory': 'Apparel' if guessed_sub_cat != 'Shoes' else 'Footwear',
                        'subCategory': guessed_sub_cat,
                        'articleType': 'Unknown',
                        'usage': 'Casual'
                    }

                # --- STRICT SETTINGS ---
                gender = seed_item['gender']
                master_cat = seed_item['masterCategory']
                sub_cat = seed_item['subCategory']
                
                # Normalize Gender for strict filtering
                target_gender_group = []
                if gender in ['Men', 'Boys']:
                    target_gender_group = ['Men', 'Boys'] # Strictly Men/Boys. NO Unisex to stay safe? Or include Unisex? User said "only suggest mens". Let's include Unisex as it's usually safe (e.g. watches).
                    target_gender_group.append('Unisex') 
                elif gender in ['Women', 'Girls']:
                    target_gender_group = ['Women', 'Girls'] # STRICT: "Women things only" requested. Excludes Unisex.
                else: 
                    target_gender_group = ['Men', 'Boys', 'Unisex'] # Default fallback
                    
                # Strict Categories
                MEN_BOTTOMS = ['Jeans', 'Trousers', 'Track Pants', 'Shorts', 'Tracksuits'] # 'Pants' is usually mostly Trousers/Track Pants in datasets
                MEN_TOPS = ['Tshirts', 'Shirts', 'Sweatshirts', 'Kurtas', 'Jackets']
                MEN_SHOES = ['Casual Shoes', 'Sports Shoes', 'Formal Shoes', 'Sandals', 'Flip Flops']
                MEN_WATCHES = ['Watches']
                MEN_ACCESSORIES = ['Belts', 'Wallets'] # "Accessories" requested (excluding watches)
                
                WOMEN_BOTTOMS = ['Jeans', 'Trousers', 'Leggings', 'Capris', 'Shorts', 'Skirts', 'Jeggings', 'Track Pants', 'Churidar', 'Salwar']
                WOMEN_TOPS = ['Tops', 'Tshirts', 'Shirts', 'Kurtas', 'Tunics', 'Sweatshirts']
                WOMEN_SHOES = ['Heels', 'Flats', 'Casual Shoes', 'Sports Shoes', 'Sandals']
                WOMEN_WATCHES = ['Watches']
                WOMEN_BAGS = ['Handbags', 'Clutches'] # Priority 1
                WOMEN_ACCESSORIES = ['Belts', 'Wallets'] # Priority 2
                
                # --- PRE-FILTER CANDIDATES ---
                candidates = {
                    'tops': [],
                    'bottoms': [],
                    'shoes': [],
                    'watches': [],
                    'accessories': [],
                    'bags': [] # New Bucket for Bags
                }
                
                for row in all_rows:
                    # 1. Strict Gender Filter
                    if row['gender'] not in target_gender_group:
                        continue
                        
                    # 2. Strict Category Map
                    rtype = row['articleType']
                    
                    if gender in ['Men', 'Boys']:
                        if rtype in MEN_TOPS: candidates['tops'].append(row)
                        elif rtype in MEN_BOTTOMS: candidates['bottoms'].append(row)
                        elif rtype in MEN_SHOES: candidates['shoes'].append(row)
                        elif rtype in MEN_WATCHES: candidates['watches'].append(row)
                        elif rtype in MEN_ACCESSORIES: candidates['accessories'].append(row)
                    else:
                        if rtype in WOMEN_TOPS: candidates['tops'].append(row)
                        elif rtype in WOMEN_BOTTOMS: candidates['bottoms'].append(row)
                        elif rtype in WOMEN_SHOES: candidates['shoes'].append(row)
                        elif rtype in WOMEN_WATCHES: candidates['watches'].append(row)
                        elif rtype in WOMEN_BAGS: candidates['bags'].append(row)
                        elif rtype in WOMEN_ACCESSORIES: candidates['accessories'].append(row)

                # --- SELECT 4 ITEMS ---
                final_selection = []
                
                def get_random(key):
                    if candidates.get(key):
                        return random.choice(candidates[key])
                    return None

                # Slot 1: Complementary Apparel 
                slot1 = None
                if sub_cat == 'Topwear':
                    slot1 = get_random('bottoms') 
                elif sub_cat == 'Bottomwear':
                    slot1 = get_random('tops') 
                else: 
                     # For Shoes/Accessories/Etc, suggest clothing based on gender
                     if gender in ['Men', 'Boys']: slot1 = get_random('tops')
                     else: slot1 = get_random('tops') # Default to top or dress
                
                if slot1: final_selection.append(slot1)
                
                # Slot 2: Shares
                slot2 = get_random('shoes')
                if slot2: final_selection.append(slot2)
                
                # Slot 3: Watch
                slot3 = get_random('watches')
                if slot3: final_selection.append(slot3)
                
                # Slot 4: Accessories (Ideally Bag for Women)
                slot4 = None
                if gender in ['Women', 'Girls']:
                     # Try Bags first
                     slot4 = get_random('bags')
                     if not slot4: slot4 = get_random('accessories')
                else:
                     slot4 = get_random('accessories')
                
                if slot4: final_selection.append(slot4)
                
                # Fallback: If any slot failed, fill with random unique items from valid categories
                if len(final_selection) < 4:
                    all_remaining = []
                    for k in candidates:
                        all_remaining.extend(candidates[k])
                    random.shuffle(all_remaining)
                    
                    for item in all_remaining:
                        if len(final_selection) >= 4: break
                        if item not in final_selection:
                            final_selection.append(item)

                random.shuffle(final_selection)
                
                for row in final_selection:
                    img_path = f"/fashion-dataset/images/{row['id']}.jpg"
                    price = random.randint(5, 30) * 100 + 99
                    items.append({
                        "id": row['id'],
                        "name": row['productDisplayName'],
                        "price": price,
                        "image": img_path,
                        "category": row['articleType'],
                        "subCategory": row['subCategory']
                    })
        
        return jsonify(items)
    except Exception as e:
        print(f"Suggestion Error: {e}")
        return jsonify([])

# --- HELPERS ---

def verify_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)

def generate_pdf_receipt(order):
    """
    Generate a PDF receipt for the order.
    Returns BytesIO object containing the PDF.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # --- STYLES ---
    styles = getSampleStyleSheet()
    
    # Custom Title Style
    title_style = ParagraphStyle(
        'LookifyTitle', parent=styles['Heading1'], fontSize=28, fontName='Helvetica-Bold', textColor=colors.black, spaceAfter=20, alignment=1
    )
    section_header = ParagraphStyle(
        'SectionHeader', parent=styles['Heading3'], fontSize=12, fontName='Helvetica-Bold', textColor=colors.black, spaceAfter=10, spaceBefore=20
    )
    
    # helper for bold text
    def bold(txt): return f"<b>{txt}</b>"

    # --- HEADER ---
    elements.append(Paragraph("RECEIPT", title_style))
    elements.append(Paragraph(f"Order Number: {order['order_id']}", styles['Normal']))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%d %b %Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # --- SHIPMENT SECTION ---
    elements.append(Paragraph(f"Shipment 1 of 1", section_header))
    
    # Prepare Image Paths
    # Current Dir: Frontend/
    # Images Dir: ../fashion-dataset/images/
    parent_dir = os.path.dirname(BASE_DIR)
    images_dir = os.path.join(parent_dir, 'fashion-dataset', 'images')
    
    data = []
    
    from reportlab.platypus import Image as RLImage
    
    subtotal = 0
    for item in order['items']:
        # Resolving Image Path
        img_filename = os.path.basename(item.get('image', ''))
        img_path = os.path.join(images_dir, img_filename)
        
        # Create Image Flowable
        img_obj = None
        if os.path.exists(img_path):
            try:
                img_obj = RLImage(img_path, width=1.2*inch, height=1.5*inch)
            except: pass
            
        if not img_obj:
            img_obj = "No Image"
            
        # Details Column
        details = [
            Paragraph(f"<b>{item['name']}</b>", styles['Normal']),
            Paragraph(f"Size: {item.get('size', 'N/A')}", styles['Normal']),
            Paragraph(f"Qty: 1", styles['Normal']), # Assuming qty 1 per line item for now
            Paragraph(f"<font color='red'>Rs. {item['price']}</font>", styles['Normal'])
        ]
        
        price_val = int(item['price'])
        subtotal += price_val
        
        data.append([img_obj, details, f"Rs. {price_val}"])
    
    # Table Style
    table = Table(data, colWidths=[1.5*inch, 3*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.2*inch))
    
    # --- PAYMENT DETAILS ---
    elements.append(Paragraph("Payment Details", section_header))
    
    shipping = 50
    discount = 0 
    taxes = round(subtotal * 0.05, 2) 
    grand_total = subtotal + shipping + taxes
    
    # Use Paragraph for bold text to avoid raw HTML tags
    grand_total_label = Paragraph("<b>Grand Total</b>", styles['Normal'])
    grand_total_val = Paragraph(f"<b>Rs. {grand_total}</b>", styles['Normal'])
    
    pay_data = [
        ["Subtotal", f"Rs. {subtotal}"],
        ["Shipping", f"Rs. {shipping}"],
        ["Taxes (5%)", f"Rs. {taxes}"],
        [grand_total_label, grand_total_val]
    ]
    
    pay_table = Table(pay_data, colWidths=[4*inch, 1.5*inch])
    pay_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
        ('padding', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Fallback style
    ]))
    elements.append(pay_table)
    
    # --- DELIVERY DETAILS ---
    elements.append(Paragraph("Delivery Details", section_header))
    
    address = order.get('address', {})
    if isinstance(address, dict):
        addr_text = f"{address.get('line1', '')}<br/>{address.get('city', '')} - {address.get('pincode', '')}"
    else:
        addr_text = str(address)
        
    elements.append(Paragraph("<b>Shipping Address</b>", styles['Normal']))
    elements.append(Paragraph(addr_text, styles['Normal']))
    
    # --- STATUS ---
    elements.append(Spacer(1, 0.3*inch))
    status_text = f"Payment Status: <font color='green'><b>PAID ({order.get('payment', 'Online').upper()})</b></font>"
    elements.append(Paragraph(status_text, styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def send_invoice_email(to_email, order):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("⚠️ Email credentials not found. Skipping email.")
        return

    subject = f"Lookify Order Receipt - {order['order_id']}"
    
    subject = f"Order Confirmation #{order['order_id']}"
    
    # HTML Email Body (Clean Light Theme)
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica', 'Arial', sans-serif; background-color: #f4f4f4; color: #333333; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border: 1px solid #e0e0e0; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
            .header {{ background-color: #000000; padding: 40px 20px; text-align: center; }}
            .logo {{ font-size: 32px; font-weight: 900; letter-spacing: 4px; color: #ffffff; text-decoration: none; }}
            .subtitle {{ color: #cccccc; font-size: 12px; letter-spacing: 2px; margin-top: 10px; text-transform: uppercase; }}
            .content {{ padding: 40px 30px; }}
            .greeting {{ font-size: 16px; margin-bottom: 20px; color: #000; font-weight: bold; }}
            .order-table {{ width: 100%; border-collapse: collapse; margin: 30px 0; }}
            .order-table th {{ text-align: left; padding: 12px; border-bottom: 2px solid #000; color: #000; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
            .order-table td {{ padding: 15px 12px; border-bottom: 1px solid #eee; color: #333; vertical-align: middle; }}
            .item-name {{ font-weight: bold; font-size: 14px; display: block; }}
            .item-meta {{ font-size: 12px; color: #666; }}
            .total-row td {{ border-top: 2px solid #000; border-bottom: none; font-size: 18px; font-weight: bold; color: #000; padding-top: 20px; }}
            .footer {{ background-color: #f9f9f9; padding: 20px; text-align: center; font-size: 12px; color: #888; border-top: 1px solid #eee; }}
        </style>
    </head>
    <body style="background-color: #f4f4f4;">
        <div class="container">
            <!-- HEADER -->
            <div class="header">
                <div class="logo">LOOKIFY</div>
                <div class="subtitle">Premium Fashion Studio</div>
            </div>

            <!-- CONTENT -->
            <div class="content">
                <p class="greeting">Dear Customer,</p>
                <p style="color: #555; line-height: 1.6;">Thank you for your purchase. Your order <b>#{order['order_id']}</b> has been confirmed.</p>
                
                <table class="order-table">
                    <thead>
                        <tr>
                            <th>Item Details</th>
                            <th style="text-align: right;">Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join([f'''
                        <tr>
                            <td>
                                <span class="item-name">{item["name"]}</span>
                                <span class="item-meta">Size: {item.get("size", "-")}</span>
                            </td>
                            <td style="text-align: right;">Rs. {item["price"]}</td>
                        </tr>
                        ''' for item in order['items']])}
                        <tr class="total-row">
                            <td>Total Amount</td>
                            <td style="text-align: right;">Rs. {order['total']}</td>
                        </tr>
                    </tbody>
                </table>

                <div style="text-align: center; margin-top: 40px;">
                    <p style="color: #666; font-size: 13px; margin-bottom: 20px;">A detailed PDF receipt is attached to this email.</p>
                </div>
            </div>

            <!-- FOOTER -->
            <div class="footer">
                &copy; 2026 Lookify Fashion. All rights reserved.<br>
                Mumbai, India
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    try:
        # Generate PDF
        pdf_buffer = generate_pdf_receipt(order)
        
        # Attach PDF
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf_buffer.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename=Invoice_{order['order_id']}.pdf")
        msg.attach(part)
        
        # Send Email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"✅ Invoice Email sent to {to_email}")
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        import traceback
        traceback.print_exc()

@app.route('/test-email')
def test_email_route():
    email = request.args.get('email')
    if not email:
        return "Please provide email param: /test-email?email=your@email.com"
    
    try:
        # Simple Test
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "Lookify Test Email"
        msg.attach(MIMEText("This is a test email from your Lookify Server.", 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1) # Show SMTP interaction in console
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        return f"✅ Email sent to {email}. Check server logs for details."
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == '__main__':
    print("Starting Flask Server on Port 8000...")
    app.run(host='0.0.0.0', port=8000, debug=True)
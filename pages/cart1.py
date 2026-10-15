import streamlit as st
import webbrowser
import urllib.parse
import json
import requests

# ---------------- PAGE ----------------
st.set_page_config(
    page_title="Lookify – Your Cart",
    page_icon="🛒",
    layout="wide"
)


# ---------------- SESSION STATE ----------------
if "cart" not in st.session_state:
    st.session_state.cart = []

# --- RESTORE CART FROM TOKEN (If session is empty) ---
try:
    params = st.query_params
    token = params.get("token")
    
    # Only restore if cart is empty and token is provided
    if token and not st.session_state.cart:
        res = requests.get(f"http://127.0.0.1:8000/api/get_cart/{token}")
        if res.status_code == 200:
            restored_data = res.json()
            # server returns [...] (list of items)
            # We need to map them back to our session state format if needed.
            
            # Check if it's a list (expected) or dict (error/wrapper)
            raw_items = []
            if isinstance(restored_data, list):
                raw_items = restored_data
            elif isinstance(restored_data, dict):
                 raw_items = restored_data.get("cart", [])

            for item in raw_items:
                # Reconstruct session item
                img_path = item.get("image") or item.get("img")
                if img_path and img_path.startswith("/"):
                    img_path = f"http://127.0.0.1:8000{img_path}"

                session_item = {
                    "name": item.get("name"),
                    "price": float(item.get("price", 0)),
                    "image": img_path,
                    "img": img_path,
                    "size": item.get("size", "M"),
                    "qty": 1, # Default to 1 as checkout payload flattened qtys
                    "category": "" # Category might be missing from checkout payload, harmless
                }
                
                # Check for duplicates in restoration (if flattened)
                exists = False
                for existing in st.session_state.cart:
                     if existing["name"] == session_item["name"] and existing["size"] == session_item["size"]:
                         existing["qty"] += 1
                         exists = True
                         break
                if not exists:
                    st.session_state.cart.append(session_item)
            
            if raw_items:
                st.toast("🛒 Cart Restored from Previous Session!")


except Exception as e:
    # silent fail or log
    print(f"Error restoring cart: {e}")


# --- QUERY PARAMS HANDLER ---
try:
    params = st.query_params
    
    # 1. Handle Multiple Items (JSON)
    if "add_items" in params:
        try:
            items_json = params.get("add_items")
            new_items = json.loads(items_json)
            
            for raw_item in new_items:
                item_to_add = {
                    "name": raw_item.get("name", "Unknown Item"),
                    "price": float(raw_item.get("price", 0)),
                    "image": raw_item.get("image", ""),
                    "img": raw_item.get("image", ""), # Compatibility key
                    "size": raw_item.get("size", "M"),
                    "qty": 1,
                    "category": raw_item.get("category", "")
                }
                
                # Fix relative paths
                if item_to_add["image"].startswith("/"):
                    full_url = f"http://127.0.0.1:8000{item_to_add['image']}"
                    item_to_add["image"] = full_url
                    item_to_add["img"] = full_url
                
                # Add to cart (check duplicates)
                exists = False
                for existing in st.session_state.cart:
                    if existing["name"] == item_to_add["name"] and existing["size"] == item_to_add["size"]:
                        existing["qty"] += 1
                        exists = True
                        break
                if not exists:
                    st.session_state.cart.append(item_to_add)
            
            st.toast(f"✅ Added {len(new_items)} items to Cart!")
            st.query_params.clear()
            st.rerun() # Refresh to clear params from URL
            
        except Exception as json_err:
            st.error(f"Error parsing items: {json_err}")

    # 2. Handle Single Item (Legacy support from bgAddToCart)
    elif "add_item" in params:
        new_item = {
            "name": params.get("name", "Unknown Item"),
            "price": float(params.get("price", 0)),
            "image": params.get("image", ""),
            "img": params.get("image", ""), # Compatibility key
            "size": params.get("size", "M"),
            "qty": 1,
            "category": params.get("category", "")
        }

        if new_item["image"].startswith("/"):
             full_url = f"http://127.0.0.1:8000{new_item['image']}"
             new_item["image"] = full_url
             new_item["img"] = full_url

        exists = False
        for item in st.session_state.cart:
            if item["name"] == new_item["name"] and item["size"] == new_item["size"]:
                item["qty"] += 1
                exists = True
                break
        
        if not exists:
            st.session_state.cart.append(new_item)
            
        st.toast(f"✅ Added {new_item['name']} to Cart!")
        st.query_params.clear()
        st.rerun()

except Exception as e:
    st.error(f"Error processing cart updates: {e}")


if "tryon_item" not in st.session_state:
    st.session_state.tryon_item = None

# Ensure quantity exists
for item in st.session_state.cart:
    if "qty" not in item:
        item["qty"] = 1

# ---------------- CSS & BRANDING ----------------
st.markdown("""
<style>
[data-testid="stToolbar"], header, footer {
    visibility: hidden;
    height: 0px;
}
html, body, [data-testid="stApp"] {
    background: #000;
    color: #fff;
    font-family: 'Montserrat', sans-serif;
}
.main .block-container {
    padding-top: 0rem !important;
}
.logo-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    width: 100%;
    cursor: pointer;
    transition: transform 0.3s;
    text-decoration: none;
    margin-top: -30px;
    margin-bottom: 1rem;
}
.logo-container:hover {
    transform: scale(1.05);
}
.logo-main {
    font-size: 38px;
    font-family: 'Montserrat', sans-serif;
    font-weight: 900;
    font-style: italic;
    letter-spacing: -2px;
    text-transform: uppercase;
    color: #fff;
    text-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
    position: relative;
    z-index: 2;
    display: inline-block;
}
.logo-main::after {
    content: '';
    position: absolute;
    top: 55%;
    left: -5%;
    width: 110%;
    height: 3px;
    background: repeating-linear-gradient(90deg, #E84A27 0, #E84A27 12px, transparent 12px, transparent 24px);
    transform: translateY(-50%) rotate(-3deg);
    z-index: 3;
    pointer-events: none;
}
.logo-main::before {
    content: '';
    position: absolute;
    right: 1px;
    top: 55%;
    width: 3px;
    height: 25px;
    background: #E84A27;
    transform: rotate(15deg);
    z-index: 3;
}
.cart-container {
    max-width: 1200px;
    margin: 40px auto 100px;
    padding: 0 50px;
}
.cart-title {
    text-align: center;
    font-size: 32px;
    margin-bottom: 40px;
}
.cart-card {
    background: #111;
    padding: 20px;
    border-radius: 18px;
    text-align: center;
    margin-bottom: 30px;
}
.cart-card img {
    width: 100%;
    border-radius: 12px;
    margin-bottom: 10px;
}
.stButton button {
    color: black !important;
}
</style>
<a href="http://127.0.0.1:8000/index.html" class="logo-container">
    <div class="logo-main">LOOKIFY</div>
</a>
""", unsafe_allow_html=True)

# ---------------- CART CONTENT ----------------
st.markdown("<div class='cart-container'>", unsafe_allow_html=True)
st.markdown("<h1 class='cart-title'>🛒 Your Selected Items</h1>", unsafe_allow_html=True)

if not st.session_state.cart:
    st.markdown(
        "<p style='opacity:0.6;text-align:center;'>Your cart is empty 😕</p>",
        unsafe_allow_html=True
    )
    if st.button("Go Back to Shop"):
        st.switch_page("app.py")
else:
    cols = st.columns(4)

    grand_total = 0

    for i, item in enumerate(st.session_state.cart):
        with cols[i % 4]:
            st.markdown("<div class='cart-card'>", unsafe_allow_html=True)

            img_src = item.get("img") or item.get("image")
            st.image(img_src, use_container_width=True)
            st.markdown(f"<h3>{item['name']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p>Size: {item['size']}</p>", unsafe_allow_html=True)

            # -------- QUANTITY --------
            q1, q2, q3 = st.columns([1, 2, 1])
            with q1:
                if st.button("➖", key=f"dec_{i}") and item["qty"] > 1:
                    item["qty"] -= 1
                    st.rerun()

            with q2:
                st.markdown(
                    f"<p style='text-align:center;'>Qty: {item['qty']}</p>",
                    unsafe_allow_html=True
                )

            with q3:
                if st.button("➕", key=f"inc_{i}"):
                    item["qty"] += 1
                    st.rerun()

            total_price = item["price"] * item["qty"]
            grand_total += total_price

            st.markdown(f"<h4>₹{total_price}</h4>", unsafe_allow_html=True)

            if st.button("👗 Try On", key=f"tryon_{i}", use_container_width=True):
                st.session_state.tryon_item = item
                st.switch_page("pages/tryon.py")

            if st.button("🗑️ Remove", key=f"del_{i}", use_container_width=True):
                st.session_state.cart.pop(i)
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- TOTAL + PAYMENT BUTTON ----------------
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        f"<h2 style='text-align:center;'>Total Amount: ₹{grand_total}</h2>",
        unsafe_allow_html=True
    )

    # BACKEND INTEGRATION: Prepare JSON Data
    cart_for_checkout = []
    for item in st.session_state.cart:
        for _ in range(item['qty']):
            cart_for_checkout.append({
                "name": item['name'],
                "id": item['name'],  # Explicitly sending ID (which is the name/filename)
                "price": int(item['price']),
                "size": item['size'],
                "image": item.get('img') or item.get('image')
            })

    # NEW LOGIC: Hybrid Fix (Localhost for Server, IP for You)
    checkoutUrl = "#"
    token = None # Initialize token

    try:
        # 1. Server talks to itself via Localhost (ALWAYS WORKS)
        # CHANGED: Port 8000 (Frontend/server.py)
        res = requests.post("http://127.0.0.1:8000/api/init_checkout", json={"cart": cart_for_checkout})
        
        if res.status_code == 200:
            token = res.json().get("token")
            # 2. Redirect Link uses Your IP (So other laptop can access it)
            # CHANGED: Point to Frontend/server.py on 8000
            checkoutUrl = f"http://127.0.0.1:8000/payment.html?token={token}"
        else:
            st.error("Failed to connect to checkout server.")
    except Exception as e:
        st.error(f"Error connecting to checkout: {e}")
        # Could provide a mailto link or fallback here if needed
        # But do NOT fallback to the long URL
    
    first_item_name = ""
    if st.session_state.cart:
        first_item_name = st.session_state.cart[0]['name']
    
    encoded_seed = urllib.parse.quote(first_item_name)
    suggestionUrl = f"http://127.0.0.1:8000/suggestions.html?seed={encoded_seed}"
    if token:
        suggestionUrl += f"&token={token}"

    st.markdown(f"""
        <div style="text-align: center; margin-top: 20px;">
            <a href="{checkoutUrl}" target="_self">
                <button style="
                    background: #fff; 
                    color: #000; 
                    border: none; 
                    padding: 15px 40px; 
                    font-size: 1.2rem; 
                    font-weight: 700; 
                    border-radius: 8px; 
                    cursor: pointer;
                    transition: 0.2s;
                    margin-bottom: 20px;
                ">
                    🛍️ PROCEED TO BUY
                </button>
            </a>
            <br>
            <a href="{suggestionUrl}" target="_blank">
                <button style="
                    background: transparent; 
                    color: #aaa; 
                    border: 1px solid #333; 
                    padding: 10px 30px; 
                    font-size: 0.9rem; 
                    font-weight: 500; 
                    border-radius: 30px; 
                    cursor: pointer;
                    transition: 0.3s;
                    letter-spacing: 1px;
                ">
                    ✨ COMPLETE YOUR LOOK
                </button>
            </a>
        </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
import numpy as np
import pandas as pd
import streamlit as st
try:
    import tensorflow as tf
    from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
    from tensorflow.keras.preprocessing import image
    from tensorflow.keras.layers import GlobalMaxPool2D
except ImportError:
    tf = None
from sklearn.neighbors import NearestNeighbors
import os, pickle as pkl
from numpy.linalg import norm
import warnings
warnings.filterwarnings("ignore")

# ---------------- PAGE ----------------
st.set_page_config(page_title="Fashion Recommender", page_icon="👗", layout="centered")

# ---------------- CUSTOM SIDEBAR ----------------
with st.sidebar:
    st.markdown("AI Fashion Recommender System")

# ---------------- SESSION STATE (CART) ----------------
if "cart" not in st.session_state:
    st.session_state.cart = []

# ---------------- CSS ----------------
st.markdown("""
<style>
[data-testid="stToolbar"], header, footer { visibility: hidden; height: 0px; }
html, body, [data-testid="stApp"] { background: #000000 !important; color: #ffffff; font-family: 'Montserrat', sans-serif; }
.main .block-container { max-width: 900px; padding-top: 0rem !important; }

/* BRANDING */
.logo-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: transform 0.3s;
    text-decoration: none;
    margin-top: -30px;
    margin-bottom: 1rem;
    width: 100%;
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

h1 { text-align: center; font-size: 2.4rem !important; font-weight: 800 !important; color: #fff !important; margin-bottom: 3rem !important; }
.upload-area { background: #0000; border: 2px dashed #e5e7eb; border-radius: 16px; padding: 3.5rem; text-align: center; }
.rec-title { text-align: center; font-size: 1.7rem; font-weight: 700; color: #ffffff; margin: 2rem 0 1.5rem 0; }
[data-testid="stImage"] img { border-radius: 14px; transition: transform 0.3s ease, box-shadow 0.3s ease; }
[data-testid="stImage"] img:hover { transform: scale(1.08); box-shadow: 0 12px 30px rgba(0,0,0,0.5); }
.price { color: #10b981; font-weight: 800; font-size: 1.15rem; text-align: center; margin-top: 6px; }
.cart-btn { background: linear-gradient(45deg, #10b981, #059669) !important; color: white !important; border-radius: 8px; font-weight: 700; border: none; width: 100%; padding: 0.5rem; }
.cart-btn:hover { background: linear-gradient(45deg, #059669, #047857) !important; }
[data-testid="stFileUploader"] button { color: black !important; }
.stButton button { color: black !important; }
</style>
""", unsafe_allow_html=True)

# ---------------- BRANDING ----------------
st.markdown("""
<a href="http://127.0.0.1:8000/index.html" class="logo-container">
    <div class="logo-main">LOOKIFY</div>
</a>
""", unsafe_allow_html=True)

st.title("Fashion Recommender System")

# ---------------- DATA FUNCTIONS (UNCHANGED) ----------------
@st.cache_data
def load_dataset():
    img_folder = "images"
    try:
        styles = pd.read_csv("styles.csv", on_bad_lines="skip")
    except:
        styles = pd.DataFrame()
    return img_folder, styles

@st.cache_resource
def load_model():
    if tf is None:
        return None
    base = ResNet50(weights="imagenet", include_top=False, input_shape=(224,224,3))
    model = tf.keras.Sequential([base, GlobalMaxPool2D()])
    model.trainable = False
    return model

def extract_feature(path, model):
    img = image.load_img(path, target_size=(224,224))
    arr = preprocess_input(np.expand_dims(image.img_to_array(img), 0))
    feat = model.predict(arr, verbose=0).flatten()
    return feat / norm(feat)

@st.cache_data
def get_features(folder):
    if os.path.exists("features.pkl") and os.path.exists("filenames.pkl"):
        return pkl.load(open("features.pkl","rb")), pkl.load(open("filenames.pkl","rb"))
    model = load_model()
    feats, names = [], []
    for f in os.listdir(folder):
        if f.lower().endswith((".jpg",".png",".jpeg")):
            p = os.path.join(folder,f)
            feats.append(extract_feature(p, model))
            names.append(p)
    feats = np.array(feats)
    pkl.dump(feats, open("features.pkl","wb"))
    pkl.dump(names, open("filenames.pkl","wb"))
    return feats, np.array(names)

# ---------------- UPLOAD UI ----------------
col1, col2 = st.columns([3.5, 1])
with col1:
    st.markdown('<div class="upload-area"><div style="font-size:3.5rem; color:#c7c7c7;">☁️</div></div>', unsafe_allow_html=True)
with col2:
    uploaded_file = st.file_uploader("Drag and drop file here", type=["jpg","png","jpeg"])

# ---------------- RECOMMEND + CART REDIRECT ----------------
if uploaded_file:
    os.makedirs("temp_upload", exist_ok=True)
    test_path = f"temp_upload/{uploaded_file.name}"
    with open(test_path,"wb") as f:
        f.write(uploaded_file.getbuffer())

    model = load_model()
    if model is None:
        st.warning("⚠️ TensorFlow is required for visual feature extraction. Please install TensorFlow to run visual recommendations.")
        st.stop()
    img_folder, _ = load_dataset()
    features, filenames = get_features(img_folder)

    q = extract_feature(test_path, model)
    knn = NearestNeighbors(n_neighbors=6, algorithm="brute")
    knn.fit(features)
    _, idx = knn.kneighbors([q])

    st.image(uploaded_file, width=350)
    st.markdown('<div class="rec-title">Top 5 Recommendations</div>', unsafe_allow_html=True)

    prices = np.array([650, 950, 1200, 850, 1100])
    np.random.shuffle(prices)

    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            img_path = filenames[idx[0][i+1]]
            st.image(img_path, use_container_width=True)

            size = st.selectbox("Size", ["S", "M", "L", "XL"], key=f"size_{i}")

            if st.button("🛒 Add to Cart", key=f"cart_{i}"):
                st.session_state.cart.append({
                    "img": img_path,
                    "price": prices[i],
                    "size": size,
                    "name": os.path.basename(img_path).split('.')[0]
                })
                st.switch_page("pages/cart1.py")

            st.markdown(f"<div class='price'>₹{prices[i]}</div>", unsafe_allow_html=True)
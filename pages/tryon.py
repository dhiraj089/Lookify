import streamlit as st
from gradio_client import Client, handle_file
import tempfile, os

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Lookify AI Studio | Try-On",
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= ITEM SELECTION (FIXED) =================
selected_item = st.session_state.get("tryon_item")

# fallback if user refreshed or direct open
if selected_item is None:
    if "cart" in st.session_state and len(st.session_state.cart) > 0:
        selected_item = st.session_state.cart[-1]
        st.session_state.tryon_item = selected_item
    else:
        st.warning("🛒 Your cart is empty. Add items first.")
        st.stop()

selected_garment_path = selected_item.get("img") or selected_item.get("image")

# ================= CSS =================
st.markdown("""
<style>
#MainMenu, footer { visibility: hidden; }

html, body, [data-testid="stApp"] {
    background: radial-gradient(circle at top, #0b0b0b, #000000);
    color: white;
    font-family: 'Montserrat', sans-serif;
}

.main .block-container {
    max-width: 1300px;
    padding-top: 3rem;
}

h1 {
    text-align: center;
    font-size: 46px !important;
    font-weight: 900 !important;
    letter-spacing: 2px;
    margin-bottom: 2.5rem !important;
}

# .card {
#     background: #ffffff;
#     border-radius: 18px;
#     padding: 2rem;
#     color: black;
# }



.stButton button {
    background: white !important;
    color: black !important;
    font-weight: 700;
    border-radius: 12px;
    padding: 0.7rem 1.4rem;
}

[data-testid="stImage"] img {
    border-radius: 18px;
}
</style>
""", unsafe_allow_html=True)

# ================= TITLE =================
st.markdown("""
<style>
[data-testid="stToolbar"], header, footer {
    visibility: hidden;
    height: 0px;
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
    margin-bottom: 15px;
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
</style>
<a href="http://127.0.0.1:8000/index.html" class="logo-container">
    <div class="logo-main">LOOKIFY</div>
</a>
""", unsafe_allow_html=True)

# ================= AI CLIENT =================
@st.cache_resource
def get_client(hf_token=None):
    return Client("yisol/IDM-VTON", token=hf_token)

client = get_client()

# ================= HELPERS =================
def resolve_local_path(path):
    """
    If the path is a localhost URL, resolve it to the absolute file path on disk.
    The remote AI server cannot reach back to http://127.0.0.1:8000.
    """
    if isinstance(path, str) and path.startswith("http://127.0.0.1:8000/fashion-dataset/"):
        # Rel: images/53759.jpg
        rel_part = path.replace("http://127.0.0.1:8000/fashion-dataset/", "").replace("/", os.sep)
        # Root is D:\Lookify (2 levels up from pages/tryon.py)
        # We use absolute paths for safety.
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_path = os.path.join(project_root, "fashion-dataset", rel_part)
        
        if os.path.exists(local_path):
            return local_path
    return path

def save_to_disk(file):
    if isinstance(file, str):
        return file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(file.getvalue())
        return tmp.name

# ================= SIDEBAR =================
with st.sidebar:
    st.header("⚙️ Configuration")

    hf_token = st.text_input(
        "Hugging Face Token (Optional)",
        type="password"
    )

    if hf_token:
        client = get_client(hf_token)
        st.success("✅ Token Connected")
    else:
        st.info("ℹ️ Running in Guest Mode")

    st.divider()
    st.header("🧺 Selected Garment")
    st.image(selected_garment_path, use_container_width=True)
    st.caption(f"{selected_item['name']} | Size: {selected_item['size']}")
    st.markdown(f"**₹{selected_item['price']}**")

    st.divider()
    person_img = st.file_uploader(
        "Upload Person Image",
        type=["jpg", "jpeg", "png"]
    )

# ================= MAIN UI =================
left, right = st.columns(2, gap="large")

with left:
    st.subheader("Source Canvas")
    st.markdown("<div class='upload-box'>", unsafe_allow_html=True)

    if person_img:
        st.image(person_img, caption="Person Image", use_container_width=True)

    st.image(
        selected_garment_path,
        caption="Garment (From Cart)",
        use_container_width=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.subheader("AI Transformation")
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    if st.button("🪄 Try-On", use_container_width=True):
        if not person_img:
            st.warning("Upload a person image first")
        else:
            with st.spinner("AI is stitching your look…"):
                p_path = save_to_disk(person_img)
                g_path = resolve_local_path(selected_garment_path)

                try:
                    result = client.predict(
                        dict={
                            "background": handle_file(p_path),
                            "layers": [],
                            "composite": None
                        },
                        garm_img=handle_file(g_path),
                        garment_des="a fashion garment",
                        is_checked=True,
                        is_checked_crop=False,
                        denoise_steps=30,
                        seed=42,
                        api_name="/tryon"
                    )

                    if result:
                        st.image(
                            result[0],
                            caption="✨ Lookify Result",
                            use_container_width=True
                        )
                        st.success("Transformation Complete")
                        st.balloons()
                    else:
                        st.error("AI returned empty output")

                except Exception as e:
                    st.error(f"Server Error: {e}")

                finally:
                    try:
                        os.remove(p_path)
                    except:
                        pass

    st.markdown("</div>", unsafe_allow_html=True)

# ================= FOOTER =================
st.divider()
st.caption("©️ 2026 LOOKIFY • AI Fashion Studio")

if st.button("⬅️ Back to Recommendations"):
    st.switch_page("app.py")
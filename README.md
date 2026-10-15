# 🖤 LOOKIFY: AI Fashion Studio

**Experience the future of fashion e-commerce with AI-driven personalized recommendations and high-fidelity virtual try-ons.**

---

## 🚀 Overview
Lookify is an end-to-end AI fashion ecosystem designed to bridge the gap between product discovery and personal visualization. By combining **Computer Vision**, **Deep Learning**, and **Personalized Recommendation Engines**, Lookify transforms the passive "browsing" experience into an interactive "AI Studio."

---

## 🛑 Limitations of Existing Systems (The Problem)
Standard e-commerce platforms suffer from archaic bottlenecks that Lookify successfully overcomes:

1.  **Static "Model-Centric" Visualization**
    *   *The Issue:* Reliance on generic studio photos that fail to reflect diverse, real-world user body types.
2.  **The "Fit-Uncertainty" Return Loop**
    *   *The Issue:* Lack of visualization leads to massive return rates (30-40%), causing logistical waste and high overheads.
3.  **Metadata-Restricted Search**
    *   *The Issue:* Discovery engines are limited to basic text tags (color, brand) rather than intelligent visual style compatibility.
4.  **Fragmented Decision Journey**
    *   *The Issue:* A disconnected flow between browsing and styling leads to high decision fatigue and cart abandonment.

---

## ✨ Key Features
*   **🪄 AI Virtual Try-On:** Upload your own photo and see how any garment fits you instantly using state-of-the-art Generative AI.
*   **👔 Intelligent Recommendations:** Discover fashion items based on visual features and aesthetic compatibility, not just keywords.
*   **🛒 Unified AI Studio:** A seamless interface that integrates discovery, cart management, and virtual styling in one unified workflow.
*   **⚡ Real-time Search:** Lightning-fast visual indexing of over 44,000 fashion products.

---

## 🛠️ Tech Stack
*   **Frontend:** Streamlit & HTML/CSS (Vanilla)
*   **Backend:** Python & Flask
*   **Database:** MySQL
*   **AI Models:** 
    *   Virtual Try-On: IDM-VTON (via Hugging Face)
    *   Recommendations: K-Nearest Neighbors (KNN) & Feature Extraction
*   **Tools:** Git LFS (for large model storage), Gradio Client

---

## 📦 Installation & Setup

### 1. Prerequisites
*   Python 3.10+
*   MySQL Server
*   Hugging Face Token (Recommended for Try-On)

### 2. Clone the Repository
```bash
git clone https://github.com/yashbhosale8105/Lookify.git
cd Lookify
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Database
Import the `schema.sql` file into your MySQL workbench to set up the users and orders tables.

### 5. Running the Application
```bash
python run_lookify.bat
```

---

## 📁 Directory Structure
*   `app.py` - Main Streamlit application entry.
*   `backend.py` - Flask API for authentication and database management.
*   `Frontend/` - Static web server files and UI components.
*   `pages/` - Multi-page Streamlit modules (Try-On & Cart).
*   `*.pkl` - Pre-trained AI feature maps and models (LFS).

---

## 🤝 Acknowledgments
*   Dataset: [Kaggle Fashion Product Images](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset)
*   AI Model: IDM-VTON by Yisol

---
*Created with 🖤 by Yash Bhosale*


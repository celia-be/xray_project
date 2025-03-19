import streamlit as st
import requests
import base64
from PIL import Image
import io
import os
import numpy as np
from openai import OpenAI
import time


# Init OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # pour tester en local mettre direct la clé client = OpenAI(api_key="")

# Streamlit settings
st.set_page_config(
    page_title="Fracture Detection",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# st.markdown("""
#     <style>
#     body {
#         background-color: #121212 !important;
#         color: #FAFAFA !important;
#     }
#     .stApp {
#         background-color: #121212 !important;
#     }
#     header, footer {
#         visibility: hidden;
#     }
#     .block-container {
#         padding-top: 2rem;
#     }
#     </style>
# """, unsafe_allow_html=True)


# # Custom CSS
# st.markdown("""
#     <style>
#     html, body, [class*="css"] {
#         background-color: #000000 !important;
#         color: #FAFAFA !important;
#     }
#     .uploadedFile {display: none;}
#     .stImage > img {
#         border-radius: 10px;
#         border: 1px solid #555;
#         width: 300px !important;
#     }
#     .green-box {
#         background-color: #003300;
#         color: #C8FACC;
#         padding: 1rem;
#         border-radius: 10px;
#         border: 1px solid #00cc44;
#         margin-bottom: 1rem;
#         text-align: center;
#         width: 400px;  /* 👈 correspond exactement à la largeur de l'image */

#     }
#     </style>
# """, unsafe_allow_html=True)

# Custom High-Tech Medical CSS
st.markdown("""
    <style>
    /* General dark background and white text */
    html, body, .stApp, [class*="css"] {
        background-color: #121212 !important;
        color: #ffffff !important;
    }

    /* Hide Streamlit header and footer */
    header, footer {
        visibility: hidden;
    }

    .block-container {
        padding-top: 2rem;
    }

    /* Hide uploaded file name */
    .uploadedFile {display: none;}

    /* Image styling */
    .stImage > img {
        border-radius: 10px;
        border: 1px solid #555;
        width: 300px !important;
    }

    /* Prediction result box */
    .green-box {
        background-color: #003300;
        color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #00cc44;
        margin-bottom: 1rem;
        text-align: center;
        width: 400px;  /* Same width as image */
    }

    /* Title and subtitle */
    .stApp h1, .stApp h2 {
        text-align: center;
        color: #2b6ea7;
    }

    /* 🔘 Custom style for the Streamlit button */
    div.stButton > button {
        background-color: #4a4a4a;
        color: white;
        border: 1px solid #888;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        font-weight: bold;
        transition: background-color 0.2s ease;
    }

    div.stButton > button:hover {
        background-color: #6a6a6a;
        border-color: #aaa;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)



st.title("Xray Vision Solutions")
st.write("Upload a radiograph to receive classification and explanation.")

uploaded_file = st.file_uploader("Upload Radiograph", type=["jpg", "jpeg", "png", "webp", "avif"], label_visibility="collapsed")

col1, col2 = st.columns([1, 1.2])

if uploaded_file:
    try:
        image = Image.open(uploaded_file).convert("RGB")  # ← ici on vérifie déjà si c’est lisible
    except Exception as e:
        st.error(f"⚠️ Failed to load the image: {e}")
        st.stop()
    #image = Image.open(uploaded_file).convert("RGB")
    resized = image.resize((400, 400))
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    buffered.seek(0)
    files = {"file": ("image.png", buffered, "image/png")}

    # URLS vers les deux endpoints FastAPI
    url_yolo = "https://finalproject-306051821410.europe-west1.run.app/predict-yolo"
    url_shap = "https://finalproject-306051821410.europe-west1.run.app/predict-shap"
    #url_yolo="http://127.0.0.1:8000/predict-yolo"  #local
    #url_shap="http://127.0.0.1:8000/predict-shap"  #local

    with col1:
        result_placeholder = st.empty()
        button_placeholder = st.empty()
        img_placeholder = st.image(resized)

    with col2:
        if button_placeholder.button("Analyze Image"):
            # Create separate buffers
            buffer_yolo = io.BytesIO()
            image.save(buffer_yolo, format="PNG")
            buffer_yolo.seek(0)
            files_yolo = {"file": ("image.png", buffer_yolo, "image/png")}

            buffer_shap = io.BytesIO()
            image.save(buffer_shap, format="PNG")
            buffer_shap.seek(0)
            files_shap = {"file": ("image.png", buffer_shap, "image/png")}

            # ---- YOLO Prediction ----
            try:
                with st.spinner("Predicting..."):
                    response = requests.post(url_yolo, files=files_yolo)
                    response.raise_for_status()
                    data = response.json()

                    predicted_class = data.get("class")
                    confidence = data.get("confidence")

                # Display prediction result (after spinner ends)
                button_placeholder.empty()
                result_placeholder.markdown(
                    f"""
                    <div class="green-box">
                        <h4>Prediction: {predicted_class}</h4>
                        <p>Confidence: {confidence:.2%}</p>
                    </div>
                    """, unsafe_allow_html=True
                )

            except Exception as e:
                st.error(f"❌ YOLO prediction error: {e}")
                st.stop()

            # ---- OpenAI Recommendation (independent) ----
            if predicted_class.lower() == "fractured":
                try:
                    dots_placeholder = st.empty()
                    dots = ["", ".", "..", "..."]

                    # Animation "ChatGPT typing..."
                    for i in range(8):
                        dots_placeholder.markdown(f"**🧠 Medical AI is thinking{dots[i % 4]}**")
                        time.sleep(0.4)

                    prompt = f"""
                    A radiograph was classified as a bone fracture with {confidence:.2%} confidence.
                    Provide a theoretical explanation on fractures, keep it short.
                    """
                    completion = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a medical assistant specialized in radiology."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.4,
                        max_tokens=300
                    )

                    explanation = completion.choices[0].message.content
                    dots_placeholder.empty()

                    # Typing effect
                    full_text = ""
                    message_box = st.empty()
                    for char in explanation:
                        full_text += char
                        message_box.markdown(f"🧠 **AI Medical Assistant:**\n\n{full_text}")
                        time.sleep(0.01)

                except Exception as e:
                    st.warning(f"⚠️ Could not generate explanation: {e}")

            # ---- SHAP Interpretation (independent) ----
            if predicted_class.lower() == "fractured":
                try:
                    with st.spinner("Graphical localization..."):
                        shap_response = requests.post(url_shap, files=files_shap)
                        shap_response.raise_for_status()
                        shap_data = shap_response.json()
                        base64_img = shap_data.get("image")

                        if base64_img:
                            img_bytes = base64.b64decode(base64_img.split(",")[1])
                            result_image = Image.open(io.BytesIO(img_bytes))
                            img_placeholder.image(result_image)
                except Exception as e:
                    st.warning(f"⚠️ Could not load SHAP image: {e}")





# note
# 1 cd frontend
# 2 git init
# 3 gh repo create -> follow instruction
# 4 git add commit push

# if push (please make sure you have the correct repository rights)

# git remote add origin SSH_URL (find it in github)
# check with: git remote -v

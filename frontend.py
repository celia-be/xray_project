import streamlit as st
import requests
import base64
from PIL import Image
import io
import os
import numpy as np
from openai import OpenAI

# Init OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # pour tester en local mettre direct la clé client = OpenAI(api_key="")

# Streamlit settings
st.set_page_config(
    page_title="Fracture Detection",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    html, body, [class*="css"] {
        background-color: #121212 !important;
        color: #FAFAFA !important;
    }
    .uploadedFile {display: none;}
    .stImage > img {
        border-radius: 8px;
        border: 1px solid #555;
        width: 300px !important;
    }
    .green-box {
        background-color: #003300;
        color: #C8FACC;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #00cc44;
        margin-bottom: 1rem;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Xray Advisor Solutions")
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
                with st.spinner("🧠 Predicting with YOLO..."):
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
                    with st.spinner("Generating medical recommendation..."):
                        prompt = f"""
                        A radiograph was classified as a bone fracture with {confidence:.2%} confidence.
                        Provide a short and sarcastical joke about the confidence. Then, give a medical recommendation and theoretical explanation on fractures.
                        """
                        completion = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a medical assistant specialized in radiology."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.4,
                            max_tokens=300
                        )
                        explanation = completion.choices[0].message.content
                        # Juste avant le bloc HTML
                        explanation_html = explanation.replace("\n", "<br>")

                        # Puis dans le markdown HTML
                        st.markdown("### AI Medical Assistant")
                        st.markdown(
                            f"""
                            <div style="display: flex; align-items: flex-start; margin-top: 1rem;">
                                <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png"
                                    style="width: 40px; height: 40px; border-radius: 50%; margin-right: 0.75rem;"
                                    alt="AI Avatar">
                                <div style="
                                    background-color: #1f1f1f;
                                    border: 1px solid #333;
                                    padding: 1rem;
                                    border-radius: 10px;
                                    font-family: 'Courier New', monospace;
                                    font-size: 0.9rem;
                                    color: #fafafa;
                                    max-width: 600px;
                                    line-height: 1.5;
                                ">
                                    {explanation_html}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )



                except Exception as e:
                    st.warning(f"⚠️ Could not generate explanation: {e}")

            # ---- SHAP Interpretation (independent) ----
            if predicted_class.lower() == "fractured":
                try:
                    with st.spinner("📷 Loading SHAP interpretation..."):
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

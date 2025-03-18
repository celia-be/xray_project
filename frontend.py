import streamlit as st
import requests
import base64
from PIL import Image
import io
import os
import numpy as np
from openai import OpenAI

# Init OpenAI client
client = OpenAI(api_key="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")  # ⬅️ Remplace par ta vraie clé API OpenAI

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

st.title("Fracture Detection Interface")
st.write("Upload a radiograph to receive classification and explanation.")

uploaded_file = st.file_uploader("Upload Radiograph", type=["jpg", "jpeg", "png", "webp", "avif"], label_visibility="collapsed")

# Layout
col1, col2 = st.columns([1, 1.2])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    resized = image.resize((400, 400))
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    buffered.seek(0)
    files = {"file": ("image.png", buffered, "image/png")}
    url = "https://finalproject-306051821410.europe-west1.run.app/predict-image"

    with col1:
        # Zone pour le bouton et les résultats au-dessus de l'image
        result_placeholder = st.empty()
        button_placeholder = st.empty()
        img_placeholder = st.image(resized)

    with col2:
        if button_placeholder.button("Analyze Image"):
            with st.spinner("Running analysis..."):
                try:
                    response = requests.post(url, files=files)
                    response.raise_for_status()
                    data = response.json()

                    predicted_class = data.get("class")
                    confidence = data.get("confidence")
                    base64_img = data.get("image")

                    # Remplacer bouton par résultat
                    button_placeholder.empty()
                    result_placeholder.markdown(
                        f"""
                        <div class="green-box">
                            <h4>Prediction: {predicted_class}</h4>
                            <p>Confidence: {confidence:.2%}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Affichage de la nouvelle image si fracture
                    if predicted_class.lower() == "fractured" and base64_img:
                        img_bytes = base64.b64decode(base64_img.split(",")[1])
                        result_image = Image.open(io.BytesIO(img_bytes))
                        img_placeholder.image(result_image)

                    # Recommandation médicale
                    if predicted_class.lower() == "fractured":
                        with st.spinner("Generating medical explanation..."):
                            prompt = f"""
                            A radiograph was classified as a bone fracture with {confidence:.2%} confidence.
                            Provide a short and sarcastical joke about the confidence. And provide a short medical recommandation and theoritical recall on fractures.
                            Write everything as a text.
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
                            st.markdown("### Medical Recommendation")
                            st.info(explanation)

                except Exception as e:
                    st.error(f"Error during prediction: {e}")

# note
# 1 cd frontend
# 2 git init
# 3 gh repo create -> follow instruction
# 4 git add commit push

# if push (please make sure you have the correct repository rights)

# git remote add origin SSH_URL (find it in github)
# check with: git remote -v

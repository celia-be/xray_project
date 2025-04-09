import streamlit as st
import requests
import io
import base64
from PIL import Image
import pandas as pd
import zipfile
import csv

st.set_page_config(page_title="Medical Image Batch Anonymizer", layout="wide", page_icon="🩺")
# === INIT upload key ===
if "uploader_key_images" not in st.session_state:
    st.session_state.uploader_key_images = "images_default"
if "uploader_key_reports" not in st.session_state:
    st.session_state.uploader_key_reports = "reports_default"


# === INIT template ===

# 🌑 Medical dark theme styling
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #0E1117;
            color: white;
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        .stButton>button {
            color: white;
            background-color: #1f2e40;
            border-radius: 8px;
            border: 1px solid #1a1a1a;
        }
        .stButton>button:hover {
            background-color: #2e3e55;
        }
        .stSelectbox label, .stSlider label, .stFileUploader label {
            font-weight: bold;
            color: #E0E0E0;
        }
        .stRadio label {
            color: #CCCCCC;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Data Processing")

# === SECTION 1: Uploads ===
with st.container():
    st.subheader("Upload Images and Reports")
    col1, col2 = st.columns(2)

    with col1:
        uploaded_files = st.file_uploader("Medical Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key=st.session_state.uploader_key_images)

    with col2:
        uploaded_reports = st.file_uploader("Consultation Reports", type=["txt", "pdf", "docx"], accept_multiple_files=True, key=st.session_state.uploader_key_reports)

# === INIT STATES ===
if "image_to_report" not in st.session_state:
    st.session_state.image_to_report = {}
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "anonymized" not in st.session_state:
    st.session_state.anonymized = {}

# === SECTION 2: Sidebar Navigation ===
if uploaded_files:
    with st.sidebar:
        st.subheader("⚙️ Batch Actions")

        if st.button("⚡ Anonymize All Images"):
            with st.spinner("Batch anonymization in progress..."):
                for i, f in enumerate(uploaded_files):
                    if f.name not in st.session_state.anonymized:
                        files = {"file": (f.name, f.getvalue(), f.type)}
                        response = requests.post("http://localhost:8000/anonymize-image", files=files)
                        if response.status_code == 200:
                            img_base64 = response.json()["image"]
                            img_data = img_base64.split(",")[1]
                            result_bytes = io.BytesIO(base64.b64decode(img_data))
                            anonymized_image = Image.open(result_bytes)
                            anonymized_image.thumbnail((400, 400))
                            st.session_state.anonymized[f.name] = anonymized_image
                        else:
                            st.warning(f"❌ Failed to anonymize image: {f.name}")
                    st.sidebar.progress((i + 1) / len(uploaded_files), text=f"Processing {f.name}")
            st.success("🎉 All images have been anonymized!")

        if uploaded_reports:
            st.markdown("### 🪄 Assign a Report to All Images")
            report_names = [r.name for r in uploaded_reports]
            selected_global_report = st.selectbox("Choose a report", report_names, key="global_report_sidebar")
            if st.button("Apply report to all images", key="apply_all_reports"):
                for f in uploaded_files:
                    st.session_state.image_to_report[f.name] = selected_global_report
                st.success(f"Report '{selected_global_report}' has been assigned to all images.")

        if len(st.session_state.anonymized) > 0:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for filename, img in st.session_state.anonymized.items():
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    zip_file.writestr(f"images/{filename.rsplit('.', 1)[0]}_anonymized.png", img_bytes.getvalue())
                if uploaded_reports:
                    for report in uploaded_reports:
                        zip_file.writestr(f"reports/{report.name}", report.getvalue())
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(["index", "image_filename", "report_filename"])
                for idx, (img_name, _) in enumerate(st.session_state.anonymized.items()):
                    report_name = st.session_state.image_to_report.get(img_name, "")
                    writer.writerow([idx, img_name, report_name])
                zip_file.writestr("associations.csv", csv_buffer.getvalue())
            zip_buffer.seek(0)
            st.download_button(
                label="📥 Download ZIP (images + reports + CSV)",
                data=zip_buffer,
                file_name="anonymized_dataset.zip",
                mime="application/zip"
            )

        # st.markdown("### Select an image")
        filenames = [f.name for f in uploaded_files]
        # selected_filename = st.radio(
        #     "Select an image",
        #     filenames,
        #     index=st.session_state.current_index,
        #     format_func=lambda name: f"✅ {name}" if name in st.session_state.anonymized else f"❌ {name}"
        # )

        st.markdown("---")
        st.markdown(f"✅ **{len(st.session_state.anonymized)} / {len(filenames)}** images anonymized")

        st.markdown("---")
        if st.button("♻️ Reset Session"):
            st.session_state.clear()
            st.session_state.uploader_key_images = str(hash(str(pd.Timestamp.now()))) + "_img"
            st.session_state.uploader_key_reports = str(hash(str(pd.Timestamp.now()))) + "_rep"
            st.rerun()



# === SECTION 3: Main Panel Display ===
if uploaded_files:
    # Titre centré
    st.markdown("<div style='text-align:center; padding-top: 10px;'>", unsafe_allow_html=True)
    st.subheader("Image Preview")

    filenames = [f.name for f in uploaded_files]

    # 🧭 Navigation entre les images
    col_nav1, col_nav2, col_nav3 = st.columns([1, 6, 1])
    with col_nav1:
        if st.button("Prev", key="prev_image") and st.session_state.current_index > 0:
            st.session_state.current_index -= 1
    with col_nav3:
        if st.button("Next", key="next_image") and st.session_state.current_index < len(filenames) - 1:
            st.session_state.current_index += 1

    # Mise à jour de l'image sélectionnée
    selected_filename = filenames[st.session_state.current_index]
    selected_file = next((f for f in uploaded_files if f.name == selected_filename), None)

    if selected_file:
        st.markdown("</div>", unsafe_allow_html=True)
        # st.markdown(
        #     f"<h5 style='color:white; text-align:center;'>Image {st.session_state.current_index + 1} of {len(filenames)} — {selected_filename}</h5>",
        #     unsafe_allow_html=True
        # )

        # Chargement de l'image
        image_bytes = selected_file.getvalue()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image.thumbnail((400, 400))

        # === Affichage image + association côte à côte ===
        col_img, col_assoc = st.columns([3, 4], gap="large")

        with col_img:
            st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)

            # Affichage de l’image
            if selected_file.name in st.session_state.anonymized:
                st.image(
                    st.session_state.anonymized[selected_file.name],
                    use_container_width=False
                )
            else:
                st.image(image, use_container_width=False)

            # ➕ Légende stylisée en dessous
            max_name_length = 60  # Limite de caractères
            display_name = selected_filename if len(selected_filename) <= max_name_length else selected_filename[:max_name_length] + "..."
            st.markdown(
                f"<p style='text-align:center; font-size:14px; color:#CCCCCC;'>"
                f"Image {st.session_state.current_index + 1} of {len(filenames)} — {display_name}</p>",
                unsafe_allow_html=True
            )

            st.markdown("</div>", unsafe_allow_html=True)


        with col_assoc:
            #st.markdown("")

            col_sel, col_or, col_input = st.columns([3, 1, 3])
            with col_sel:
                st.markdown("#### <span style='color:white;'>Select report file</span>", unsafe_allow_html=True)
                selected_report = st.selectbox(
                    label="",
                    options=["None"] + [r.name for r in uploaded_reports],
                    index=0,
                    key=f"select_{selected_file.name}"
                )

            with col_or:
                st.markdown("<div style='text-align:center; padding-top: 35px; font-weight:bold; color:white;'>or</div>", unsafe_allow_html=True)

            with col_input:
                st.markdown("#### <span style='color:white;'>Type custom label</span>", unsafe_allow_html=True)
                manual_label = st.text_input(
                    label="",
                    value=st.session_state.image_to_report.get(selected_file.name, ""),
                    key=f"text_{selected_file.name}"
                )

            # 💾 Save button
            if st.button("Save report association", key=f"save_{selected_file.name}"):
                if manual_label.strip():
                    st.session_state.image_to_report[selected_file.name] = manual_label.strip()
                    st.success(f"Label '{manual_label.strip()}' saved for image.")
                    st.rerun()
                elif selected_report != "None":
                    st.session_state.image_to_report[selected_file.name] = selected_report
                    st.success(f"Report '{selected_report}' assigned to image.")
                    st.rerun()
                else:
                    st.warning("No report or label assigned.")

# === SECTION 4: Table of associations ===
if uploaded_files and len(st.session_state.image_to_report) > 0:
    with st.expander("📋 Image / Report Associations"):
        assoc_data = [
            {
                "Image": img,
                "Linked Report": st.session_state.image_to_report.get(img, "None")
            }
            for img in [f.name for f in uploaded_files]
        ]
        df_assoc = pd.DataFrame(assoc_data)
        st.dataframe(df_assoc, use_container_width=True)

        if st.button("♻️ Reset all associations"):
            st.session_state.image_to_report.clear()
            st.success("All associations have been cleared.")

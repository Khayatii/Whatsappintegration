import streamlit as st  # type: ignore
import cv2
from ultralytics import YOLO
import requests  # type: ignore
from PIL import Image
import os
from glob import glob
from numpy import random
import io

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = '7843011691:AAG99Q1KGx70DKBb6r8EF__9_vBsSlj1e6c'  # Replace with your bot token
CHAT_ID = '6723260132'  # Replace with your chat ID

# Function to load the YOLO model
@st.cache_resource
def load_model(model_path):
    model = YOLO(model_path)
    return model

# Function to predict objects in the image
def predict_image(model, image, conf_threshold, iou_threshold):
    res = model.predict(
        image,
        conf=conf_threshold,
        iou=iou_threshold,
        device='cpu',
    )
    
    class_name = model.model.names
    classes = res[0].boxes.cls
    class_counts = {}
    
    # Count occurrences of each class
    for c in classes:
        c = int(c)
        class_counts[class_name[c]] = class_counts.get(class_name[c], 0) + 1

    # Generate prediction text
    prediction_text = 'Predicted '
    for k, v in sorted(class_counts.items(), key=lambda item: item[1], reverse=True):
        prediction_text += f'{v} {k}'
        if v > 1:
            prediction_text += 's'
        prediction_text += ', '

    prediction_text = prediction_text[:-2] if class_counts else "No objects detected"

    # Calculate inference latency
    latency = round(sum(res[0].speed.values()) / 1000, 2)
    prediction_text += f' in {latency} seconds.'

    # Convert result image to RGB
    res_image = res[0].plot()
    res_image = cv2.cvtColor(res_image, cv2.COLOR_BGR2RGB)
    
    return res_image, prediction_text

# Function to send image via Telegram
def send_to_telegram(image, caption, bot_token, chat_id):
    url = f'https://api.telegram.org/bot{bot_token}/sendPhoto'
    
    # Convert image to bytes
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    
    # Create the payload for the Telegram request
    files = {'photo': ('image.png', image_bytes, 'image/png')}
    data = {'chat_id': chat_id, 'caption': caption}
    
    try:
        response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            st.success("Image sent to Telegram successfully!")
        else:
            st.error(f"Failed to send image to Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error sending image to Telegram: {e}")

def main():
    # Set Streamlit page configuration
    st.set_page_config(
        page_title="Wildfire Detection",
        page_icon="🔥",
        initial_sidebar_state="collapsed",
    )
    
    # Sidebar information
    st.sidebar.markdown("Developed by Alim Tleuliyev")
    st.sidebar.markdown("LinkedIn: [Profile](https://www.linkedin.com/in/alimtleuliyev/)")
    st.sidebar.markdown("GitHub: [Repo](https://github.com/AlimTleuliyev/wildfire-detection)")
    st.sidebar.markdown("Email: [alim.tleuliyev@nu.edu.kz](mailto:alim.tleuliyev@nu.edu.kz)")
    st.sidebar.markdown("Telegram: [@nativealim](https://t.me/nativealim)")

    # Set custom CSS styles
    st.markdown(
        """
        <style>
        .container {
            max-width: 800px;
        }
        .title {
            text-align: center;
            font-size: 35px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .description {
            margin-bottom: 30px;
        }
        .instructions {
            margin-bottom: 20px;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # App title
    st.markdown("<div class='title'>Wildfire Detection</div>", unsafe_allow_html=True)

    # Logo and description
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.write("")
    with col2:
        logos = glob('dalle-logos/*.png')
        logo = random.choice(logos)
        st.image(logo, use_column_width=True, caption="Generated by DALL-E")
    with col3:
        st.write("")

    st.sidebar.image(logo, use_column_width=True, caption="Generated by DALL-E")

    # Description
    st.markdown(
    """
    <div style='text-align: center;'>
        <h2>🔥 <strong>Wildfire Detection App</strong></h2>
        <p>Welcome to our Wildfire Detection App! Powered by the <a href='https://github.com/ultralytics/ultralytics'>YOLOv8</a> detection model trained on the <a href='https://github.com/gaiasd/DFireDataset'>D-Fire: an image dataset for fire and smoke detection</a>.</p>
        <h3>🌍 <strong>Preventing Wildfires with Computer Vision</strong></h3>
        <p>Our goal is to prevent wildfires by detecting fire and smoke in images with high accuracy and speed.</p>
        <h3>📸 <strong>Try It Out!</strong></h3>
        <p>Experience the effectiveness of our detection model by uploading an image or providing a URL.</p>
    </div>
    """,
    unsafe_allow_html=True
    )

    # Add a separator
    st.markdown("---")

    # Model selection
    col1, col2 = st.columns(2)
    with col1:
        model_type = st.radio("Select Model Type", ("Fire Detection", "General"), index=0)

    models_dir = "general-models" if model_type == "General" else "fire-models"
    model_files = [f.replace(".pt", "") for f in os.listdir(models_dir) if f.endswith(".pt")]
    
    with col2:
        selected_model = st.selectbox("Select Model Size", sorted(model_files), index=2)

    # Load the selected model
    model_path = os.path.join(models_dir, selected_model + ".pt")  # type: ignore
    model = load_model(model_path)

    # Add a section divider
    st.markdown("---")

    # Set confidence and IOU thresholds
    col1, col2 = st.columns(2)
    with col2:
        conf_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.20, 0.05)
        with st.expander("What is Confidence Threshold?"):
            st.caption("The Confidence Threshold is a value between 0 and 1.")
            st.caption("It determines the minimum confidence level required for an object detection.")
            st.caption("If the confidence of a detected object is below this threshold, it will be ignored.")
            st.caption("You can adjust this threshold to control the number of detected objects.")
            st.caption("Lower values make the detection more strict, while higher values allow more detections.")
    with col1:
        iou_threshold = st.slider("IOU Threshold", 0.0, 1.0, 0.5, 0.05)
        with st.expander("What is IOU Threshold?"):
            st.caption("The IOU (Intersection over Union) Threshold is a value between 0 and 1.")
            st.caption("It determines the minimum overlap required between the predicted bounding box")
            st.caption("and the ground truth box for them to be considered a match.")
            st.caption("You can adjust this threshold to control the precision and recall of the detections.")
            st.caption("Higher values make the matching more strict, while lower values allow more matches.")

    # Add a section divider
    st.markdown("---")

    # Image selection
    image = None
    image_source = st.radio("Select image source:", ("Enter URL", "Upload from Computer"))
    if image_source == "Upload from Computer":
        uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)

    # Analyze the image and send to Telegram
    if image:
        if st.button("Analyze Image"):
            res_image, prediction_text = predict_image(model, image, conf_threshold, iou_threshold)
            st.image(res_image, caption="Detection Results", use_column_width=True)
            st.success(prediction_text)

            # New button to send to Telegram
            if st.button("Send to Telegram"):
                st.write("Sending image to Telegram...")
                st.write(f"Caption: {prediction_text}")
                send_to_telegram(res_image, prediction

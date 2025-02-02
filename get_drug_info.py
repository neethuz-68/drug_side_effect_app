import streamlit as st
import google.generativeai as genai
import json
import re
from PIL import Image
import io
import base64
# Configure the API Key for Google Generative AI
genai.configure(api_key="AIzaSyC4r9sfRtfuK3k4XelwMx01payjcSmNxzw")

# Initialize the Generative AI model (Correct way)
model = genai.GenerativeModel("gemini-2.0-flash-exp")  # Initialize ONCE, outside the function


def get_drug_info_from_image(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        # Prepare image for Gemini API
        img_data = {
            "mime_type": "image/jpeg",  # Or image/png, etc. Adjust as needed
            "data": image_bytes
        }

        prompt = """
        You are an AI assistant that identifies medicines from images and provides information about them.

        1. Identify the medicine in the given image.  If multiple items are present, just identify the first one you are reasonably confident about.
        2. Return a JSON object with the following keys:
            - "drug_name": The name of the identified drug.  If you are unsure, set this to "Unknown".
            - "usage": A brief description of what the drug is used for. If the drug is unknown, set this to "Drug not identified".
            - "side_effects": An object where the keys are "side effect 1", "side effect 2", etc., and the values are the corresponding side effects. If the drug is unknown, set this to "Side effects not available".
        """

        response = model.generate_content(contents=[img_data, prompt])
        text = response.text

        

        try:
            drug_info_json = json.loads(text)
            return drug_info_json
        except json.JSONDecodeError:
            st.warning("Warning: Model output was not valid JSON. Attempting to parse with regex.")
            drug_info = {}
            drug_name_match = re.search(r'"drug_name":\s*"([^"]*)"', text)
            usage_match = re.search(r'"usage":\s*"([^"]*)"', text)
            side_effects_matches = re.findall(r'"side effect (\d+)":\s*"([^"]*)"', text)

            if drug_name_match:
                drug_info["drug_name"] = drug_name_match.group(1)
            if usage_match:
                drug_info["usage"] = usage_match.group(1)
            if side_effects_matches:
                drug_info["side_effects"] = {f"side effect {m[0]}": m[1] for m in side_effects_matches}

            return drug_info if drug_info else None


        response = model.generate_content(  # Correct way to call generate_content
            contents=[img_data, prompt]
        )

        text = response.text

        

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None
# Streamlit UI
st.title("Drug Information Finder from Image")

uploaded_file = st.file_uploader("Upload an image of a medicine:", type=["jpg", "jpeg", "png"])  # Accept image uploads

if uploaded_file is not None:
    image_bytes = uploaded_file.read()  # Read the uploaded file as bytes
    image = Image.open(io.BytesIO(image_bytes)) # Display the uploaded image
    st.image(image, caption="Uploaded Medicine Image", use_container_width=True)

    if st.button("Get Drug Information from Image"):
        with st.spinner("Identifying drug and fetching information..."):
            drug_info = get_drug_info_from_image(image_bytes)

            if drug_info:
                drug_name = drug_info.get("drug_name", "Unknown Drug")
                st.write(f"### **Identified Drug:** {drug_name}")

                st.write(f"### **What is {drug_name} used for?**")
                st.write(drug_info.get("usage", "Usage information not found."))

                st.write("### **Side Effects:**")
                side_effects = drug_info.get("side_effects", {})
                if side_effects:
                    for key, value in side_effects.items():
                        st.write(f"- {value}")
                else:
                    st.write("No side effects found.")
            else:
                st.error("Could not retrieve drug information from the image.")
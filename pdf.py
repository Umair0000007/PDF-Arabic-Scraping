import streamlit as st
import fitz
import tempfile
import os
from PIL import Image
import io
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import json

# Load environment variables and configure Gemini
load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    st.error("Please set the GOOGLE_API_KEY in your .env file")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_data_from_image(image):
    """Extract data from image using Gemini API"""
    try:
        
        prompt = """
        Extract and rewrite all data in image in english. Donot summarise, only translate it into english in a structured way.
        }"""


        # Get response from Gemini
        
        response = model.generate_content([prompt, image])
        JSON_data = response.text
        return JSON_data

    except Exception as e:
        st.error(f"Error extracting data: {str(e)}")
        return None

        

def convert_pdf_to_images(pdf_file):
    """Convert PDF to list of PIL Images"""
    try:
        with tempfile.TemporaryDirectory() as path:
            pdf_path = os.path.join(path, "uploaded_pdf.pdf")
            with open(pdf_path, "wb") as f:
                f.write(pdf_file.getbuffer())

            pdf_document = fitz.open(pdf_path)
            images = []

            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))
                images.append(img)

            pdf_document.close()
            return images
    except Exception as e:
        st.error(f"Error converting PDF: {str(e)}")
        return []

# Set page config
st.set_page_config(page_title="PDF Data Extractor", layout="wide")

# Add title
st.title("PDF Data Extractor")

# Create sidebar
with st.sidebar:
    st.header("Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    # Add reset button
    if st.button("Reset All Data"):
        st.session_state.all_data = []
        st.experimental_rerun()


# Main content area
if uploaded_file is not None:
    try:
        with st.spinner("Converting PDF to images..."):
            images = convert_pdf_to_images(uploaded_file)

            if not images:
                st.error("No images were extracted from the PDF")
                st.stop()

            progress_bar = st.progress(0)

            all_json = []  # Store DataFrames for all pages
            for i, image in enumerate(images):
                st.text(f"Processing page {i+1} of {len(images)}...")
                jsons = extract_data_from_image(image)
                if jsons is not None:
                    all_json.append(jsons)
                    st.write(jsons) 
                progress_bar.progress((i + 1) / len(images))

            if not all_dataframes:
                st.warning("No data was extracted from the PDF")
                st.stop()

            # Concatenate DataFrames from all pages
            final_df = pd.concat(all_dataframes, ignore_index=True)

            # Display the final DataFrame
            st.header("Extracted Data")
            st.dataframe(final_df)

            # Add download button
            st.header("Download Data")
            csv = final_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="extracted_data.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

else:
    st.info("Please upload a PDF file using the sidebar")

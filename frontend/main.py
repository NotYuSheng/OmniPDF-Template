from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
from io import BytesIO
from PIL import Image
import pandas as pd
import requests
import base64
import json
import time
import os

# local imports
from utils import pdf_check

# Page configuration
st.set_page_config(
    page_title="OmniPDF",
    page_icon="🦸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://omnipdf-backend:8003")

# QOL configs
sidebar = ""

def check_file(uploaded_file):
    # Check file
    if not uploaded_file:
        st.warning("Please upload a PDF file to get started.")
    if not pdf_check(uploaded_file):
        st.warning("Magic numbers not found. Please upload a PDF file.")
    
    return True

def translate_file(uploaded_file):
    pass

def generate_metadata(uploaded_file):
    pass

def check_backend():
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        st.error(f"Error checking backend: {e}")
        return False

def upload_pdf_UI():
    st.header("📁 Upload PDF")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF file to process"
    )
    
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        
        # Processing options
        st.subheader("Processing Options")
        target_language = st.selectbox(
            "Target Language",
            ["English", "Spanish", "French", "German", "Chinese", "Japanese"]
        )
        
        extract_images = st.checkbox("Extract Images", value=True)
        generate_metadata = st.checkbox("Generate Metadata", value=True)
        enable_rag = st.checkbox("Enable RAG Chat", value=True)
        
        if st.button("🚀 Process PDF", type="primary"):
            with st.spinner("Processing PDF..."):
                st.session_state.processed_data = process_pdf(uploaded_file)
            st.success("Processing completed!")
            st.rerun()

def start_chat_UI():
    st.header("Chat")
    st.markdown("💬 Ask questions about the document content")


    
    # Chat interface
    chat_container = st.container(height=350)
    
    
    if "chat_history" in st.session_state:
        with chat_container:
            # Display chat history
            for i, (question, answer) in enumerate(st.session_state.chat_history):
                st.markdown(f'<div class="chat-container">', unsafe_allow_html=True)
                st.markdown(f"**You:** {question}")
                st.markdown(f"**Assistant:** {answer}")
                st.markdown('</div>', unsafe_allow_html=True)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_question = st.text_input("Ask a question about the document:", placeholder="What is this document about?")
        submit_button = st.form_submit_button("Send")
        
        if submit_button and user_question:
            # Generate response
            response = simulate_rag_response(user_question, "document content")
            
            # Add to chat history
            st.session_state.chat_history.append((user_question, response))
            st.rerun()

def translate_UI():
    st.write("📄 Translate Content")

def extract_images_UI():
    st.write("🖼️ Image Extraction")

def metadata_UI():
    st.write("📊 PDF Metadata")

def wordcloud_UI():
    st.write("☁️ Word Cloud")


def main():
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        
        .image-container {
            border: 2px solid #e6e6e6;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .chat-container {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-header">🦸 OmniPDF</h1>', unsafe_allow_html=True)

    # Full list of tab labels and corresponding keys
    tab_map = {
        "📂 Upload": "upload",
        "📄 Translate": "translate",
        "🖼️ Extract Images": "extract_images",
        "📊 Metadata": "metadata",
        "☁️ Word Cloud": "wordcloud",
        "💬 Chat": "chat",
        "⚙️": "settings"
    }

    # Initialize session state for sidebar-only tab selection
    if "sidebar_tab" not in st.session_state:
        st.session_state.sidebar_tab = "📂 Upload"  # default

    # Generate list of tabs excluding the selected sidebar-only one (except ⚙️ Settings)
    visible_tab_labels = [
        label for label in tab_map.keys()
        if label != st.session_state.sidebar_tab
    ]

    # Create Streamlit tabs
    tabs = st.tabs(visible_tab_labels)

    # Sidebar content (only show the selected one)
    with st.sidebar:
        selected_key = tab_map[st.session_state.sidebar_tab]
        st.markdown(f"### Sidebar: {st.session_state.sidebar_tab}")
        if selected_key == "chat":
            start_chat_UI()
        elif selected_key == "upload":
            upload_pdf_UI()
        # Add other sidebar-only functions here

    # Render each tab
    for tab, label in zip(tabs, visible_tab_labels):
        key = tab_map[label]
        with tab:
            if key == "translate":
                translate_UI()
            elif key == "extract_images":
                extract_images_UI()
            elif key == "metadata":
                metadata_UI()
            elif key == "wordcloud":
                wordcloud_UI()
            elif key == "settings":
                st.markdown("### ⚙️ Settings")
                # Move the selectbox here
                selected = st.selectbox(
                    "Choose which tab should appear only in the sidebar:",
                    options=[label for label in tab_map.keys() if label != "⚙️"],
                    index=[label for label in tab_map].index(st.session_state.sidebar_tab),
                    key="sidebar_tab"  # binds directly to session_state
                )

    
if __name__ == "__main__":
    main()

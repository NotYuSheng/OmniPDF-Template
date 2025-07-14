from wordcloud import WordCloud
import matplotlib as plt
import os
import requests
import streamlit as st

# Check if the uploaded file is a valid PDF by checking the magic number
def is_pdf(file_obj):
    try:
        file_obj.seek(0)
        header = file_obj.read(5)
        file_obj.seek(0)
        return header == b"%PDF-"
    except Exception:
        return False


def generate_wordcloud(text_data):
    """Generate word cloud from text data"""
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='white',
        colormap='viridis'
    ).generate(' '.join(text_data))
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig


def display_pdf(file):
    """Display PDF in an iframe on Streamlit."""
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")

    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    return pdf_display


def check_backend():
    """
    Check the health of specific backend services.
    Returns a dictionary with service names and their health status.
    """
    try:
        # Define the services to check
        services = {
            "PDF Processor": os.getenv("PDF_PROCESSOR_URL", "http://localhost:8080/pdf_processor"),
            "PDF Extractor": os.getenv("PDF_EXTRACTOR_URL", "http://localhost:8080/pdf_extraction"),
            "Chat Service": os.getenv("CHAT_URL", "http://localhost:8080/chat"),
            "Translation Service": os.getenv("DOCLING_TRANSLATION_URL", "http://localhost:8080/docling_translation"),
            "Embedder Service": os.getenv("EMBEDDER_URL", "http://localhost:8080/embedder")
        }
        
        backend_check_results = {}
        
        for service_name, url in services.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    backend_check_results[service_name] = {"status": "Healthy", "url": url}
                else:
                    backend_check_results[service_name] = {"status": f"HTTP {response.status_code}", "url": url}
            except requests.exceptions.ConnectionError:
                backend_check_results[service_name] = {"status": "Connection Error", "url": url}
            except requests.exceptions.Timeout:
                backend_check_results[service_name] = {"status": "Timeout", "url": url}
            except Exception as e:
                backend_check_results[service_name] = {"status": f"Error: {str(e)}", "url": url}
        
        return backend_check_results
        
    except Exception as e:
        st.error(f"Error checking backend services: {e}")
        return {}


def display_backend_status():
    """
    Display the status of backend services in Streamlit.
    """
    st.subheader("🔧 Backend Services Status")
    
    backend_status = check_backend()
    
    if not backend_status:
        st.error("Unable to check backend services")
        return
    
    # Create columns for better layout
    cols = st.columns(2)
    
    for i, (service_name, status_info) in enumerate(backend_status.items()):
        col = cols[i % 2]
        
        with col:
            if status_info["status"] == "Healthy":
                st.success(f"✅ {service_name}")
                st.caption(f"Status: {status_info['status']}")
            else:
                st.error(f"❌ {service_name}")
                st.caption(f"Status: {status_info['status']}")
                st.caption(f"URL: {status_info['url']}")


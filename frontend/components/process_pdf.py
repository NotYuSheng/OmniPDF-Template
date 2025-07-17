from wordcloud import WordCloud
import matplotlib as plt
import os
import requests
import streamlit as st
import httpx
import asyncio
import base64

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


async def check_backend():
    """
    Check the health of specific backend services asynchronously.
    Returns a dictionary with service names and their health status.m
    """
    services = {
        "PDF Processor": os.getenv("PDF_PROCESSOR_URL", "http://localhost:8080/pdf_processor"),
        "PDF Extractor": os.getenv("PDF_EXTRACTOR_URL", "http://localhost:8080/pdf_extraction"),
        "Chat Service": os.getenv("CHAT_URL", "http://localhost:8080/chat"),
        "Translation Service": os.getenv("DOCLING_TRANSLATION_URL", "http://localhost:8080/docling_translation"),
        "Embedder Service": os.getenv("EMBEDDER_URL", "http://localhost:8080/embedder")
    }

    async def check_service(service_name, url):
        health_url = f"{url}/health"
        try:
            async with httpx.AsyncClient(timeout=1) as client:
                response = await client.get(health_url)
                if response.status_code == 200:
                    return service_name, {"status": "Healthy", "url": url}
                else:
                    return service_name, {"status": f"HTTP {response.status_code}", "url": url}
        except httpx.ConnectError:
            return service_name, {"status": "Connection Error", "url": url}
        except httpx.TimeoutException:
            return service_name, {"status": "Timeout", "url": url}
        except Exception as e:
            return service_name, {"status": f"Error: {str(e)}", "url": url}

    try:
        results = await asyncio.gather(*(check_service(name, url) for name, url in services.items()))
        return {name: status for name, status in results}
    except Exception as e:
        print(f"Error checking backend services: {e}")
        return {}



def display_backend_status():
    """
    Display the status of backend services in Streamlit.
    """
    st.subheader("🔧 Backend Services Status")
    
    backend_status = asyncio.run(check_backend())
    
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


def DocumentUploadResponse(doc_id: str, filename: str, download_url: str):
    return {
        "doc_id": doc_id,
        "filename": filename,
        "download_url": download_url
    }
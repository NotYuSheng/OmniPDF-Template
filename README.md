# OmniPDF

OmniPDF is a PDF analyzer capable of translation, summarization, captioning and conversational capabilities through Retrieval-Augmented-Generation (RAG). 

## Port Assignments

The following port mappings are used across the OmniPDF microservices **for development and testing purposes only**. Ports for some core services are defined in the `docker-compose.yml` file, while other services listed are common components in the development setup (potentially run separately or via other configurations). This table aims to ensure clarity and avoid conflicts during local deployment.

> **Note:** These port numbers are **not** intended for production. Actual port exposure should be handled by Kubernetes Ingress, OpenShift Routes, or a reverse proxy in secured environments.

| Service                   | Description                                            | Port  |
|---------------------------|--------------------------------------------------------|--------|
| Streamlit Frontend        | Web UI for user interaction                            | 8501   |
| Nginx API Gateway         | Proxies file uploads to PDF Processor                  | 8080   |
| PDF Processor Service     | Main coordinator for processing and routing            | 8000   |
| Text Extraction Service   | Extracts layout-aware text and language info           | 8001   |
| PDF Extraction Service    | Extracts tables and images from PDFs                   | 8002   |
| Table Translation Service | Translates Docling JSON table content                  | 8003   |
| PDF Renderer Service      | Renders preview images with overlay annotations        | 8004   |
| Embedder Service          | Chunks + embeds PDF text and stores in ChromaDB        | 8005   |
| Chat Service              | Retrieves context chunks and queries LLM               | 8006   |
| Translation Service       | Translates non-table text and image captions           | 8007   |
| vLLM LLM Server           | LLM backend for chat, translation, captions, summaries | 1234   |
| Redis                     | In-memory session store                                | 6379   |
| ChromaDB                  | Temporary in-memory vector store                       | 5100   |
| S3-Compatible Store       | Object storage (e.g., MinIO S3 API)                    | 9000   |
| MinIO Console             | MinIO web-based Admin UI                               | 9001   |

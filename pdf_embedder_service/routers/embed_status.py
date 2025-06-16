from fastapi import APIRouter

router = APIRouter()


@router.get("/status/{doc_id}")
async def embedding_check(doc_id: str):
    return {"status": f"{doc_id} embedded"}


# RAGGING (part of chat service)
# def rag(chunks, collection_name):
#     # Load all data chunks into ChromaDB
#     vectorstore = Chroma.from_documents(
#         documents=documents,
#         collection_name=collection_name,
#         # embedding=Embeddings.ollama.OllamaEmbeddings(model='nomic-embed-text'),
#         embedding=Embeddings,
#     )
#     # To check ChromaDB
#     retriever = vectorstore.as_retriever()

#     prompt_template = """Answer the question based only on the following context:
#     {context}
#     Question: {question}
#     """
#     prompt = ChatPromptTemplate.from_template(prompt_template)

#     chain = (
#         {"context": retriever, "question": RunnablePassthrough()}
#         | prompt
#         | local_llm
#         | StrOutputParser()
#     )

#     # User prompt
#     result = chain.invoke("What is the use of Text Splitting?")
#     print(result)

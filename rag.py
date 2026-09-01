from pathlib import Path
from typing import List
from dotenv import load_dotenv
import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import docx2txt


load_dotenv()
Path("chroma_vector_storage").mkdir(exist_ok=True)

embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

vectorstore = Chroma(
    collection_name="documents",
    embedding_function=embeddings,
    persist_directory="chroma_vector_storage"
)

def read_file_text(file_path: str) -> str:
    """
    Reads the text content from a file based on its extension.
    Supports .pdf, .docx, .txt, .md, .py, .csv, and .json files.
    """
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text
    elif file_path.endswith(".docx"):
        return docx2txt.process(file_path)
    elif file_path.endswith((".txt", ".md", ".py", ".csv", ".json")):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

def add_doc_to_rag(file_path: str, thread_id: str) -> str:
    """
    Adds a document to the RAG (Retrieval-Augmented Generation) system.
    Reads the file, splits it into chunks, and adds it to the vector store.
    Returns a message indicating the success or failure of the operation.
    If successful, it returns the number of chunks added to the RAG.
    """
    try:
        text = read_file_text(file_path)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
            # length_function=len
        )
        chunks = text_splitter.split_text(text)
        documents = [Document(page_content=chunk, metadata={"source": file_path, "thread_id": thread_id}) for chunk in chunks]
        vectorstore.add_documents(documents)
        return f"Document '{file_path}' added to RAG successfully with {len(chunks)} chunks."
    except Exception as e:
        return f"Error adding document to RAG: {e}"

def retrieve_from_rag(query: str, thread_id: str, top_k: int = 5) -> str:
    """
    Retrieves relevant documents from the RAG system based on a query.
    Returns a string containing the top_k relevant documents' content, separated by two newlines.
    Includes the source of each document in the output.
    If no relevant documents are found, it returns a message indicating that.
    If an error occurs during retrieval, it returns an error message.
    """ 
    try:
        results = vectorstore.similarity_search(query, k=top_k, filter={"thread_id": thread_id})
        if not results:
            return "No relevant documents found in RAG."
        return '\n\n'.join([f"Source {i}: {result.metadata.get('source', 'Unknown')}\n{result.page_content}" for i, result in enumerate(results, start=1)])
    except Exception as e:
        return f"Error retrieving documents from RAG: {e}"
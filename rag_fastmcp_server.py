"""
RAG System for PCB Assembly Process Documentation - FastMCP Server

This module implements a Retrieval-Augmented Generation system using:
- Ollama qwen3-embedding:0.6b for embeddings
- ChromaDB for vector storage
- LangChain for document loading and retrieval
- FastMCP for Model Context Protocol server
"""

import os
from pathlib import Path
from typing import List, Dict, Any

from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv
load_dotenv()


class ProcessRAG:
    """RAG system for retrieving PCB assembly process information"""
    
    def __init__(
        self,
        # documents_dir: str = "documents",
        documents_dir: str = os.getenv("DOCUMENTS_DIR", "documents"),
        ollama_base_url: str = "http://localhost:11434",
        # embedding_model: str = "qwen3-embedding:4b",
        embedding_model: str = "qwen3-embedding:0.6b",
        persist_directory: str = os.getenv("CHROMA_PERSIST_DIR", "database/chroma_db")
    ):
        """
        Initialize the RAG system.
        
        Args:
            documents_dir: Directory containing process documentation markdown files
            ollama_base_url: Base URL for Ollama API
            embedding_model: Ollama embedding model name
            persist_directory: Directory to persist ChromaDB data
        """
        self.documents_dir = Path(documents_dir)
        self.ollama_base_url = ollama_base_url
        self.embedding_model = embedding_model
        self.persist_directory = persist_directory
        
        if not os.path.exists(self.documents_dir):
            raise FileNotFoundError(f"Documents directory '{self.documents_dir}' does not exist.")
        
        
        # Initialize embeddings
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=ollama_base_url
        )
        
        # Initialize or load vector store
        self.vector_store = None
        self.retriever = None
        
    def load_documents(self) -> List[Document]:
        """
        Load all markdown documents from the documents directory.
        
        Returns:
            List of Document objects
        """
        # print(f"Loading documents from {self.documents_dir}...")
        
        # Load all markdown files
        loader = DirectoryLoader(
            str(self.documents_dir),
            glob="*.md",
            loader_cls=UnstructuredMarkdownLoader,
            show_progress=False
        )
        
        documents = loader.load()
        # print(f"Loaded {len(documents)} documents")
        
        return documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks. Uses full document strategy for comprehensive context.
        
        Args:
            documents: List of documents to chunk
            
        Returns:
            List of chunked documents
        """
        # print("Processing documents...")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=250,
            length_function=len,
        )

        # Process each document to extract metadata before chunking
        all_chunks = []
        for i, doc in enumerate(documents):
            # Extract metadata from original document
            filename = Path(doc.metadata.get('source', '')).stem
            
            # Extract process name from content
            line = doc.page_content.split('\n')[0]
            process_name = line.replace('# ', '').strip()
            
            # Split the document into chunks
            chunks = text_splitter.split_documents([doc])
            
            # Add metadata to all chunks from this document
            for chunk in chunks:
                chunk.metadata['doc_id'] = i
                chunk.metadata['filename'] = filename
                chunk.metadata['process_name'] = process_name
            
            for chunk in chunks:
                all_chunks.append(chunk)
        
        return all_chunks
    
    def create_vector_store(self, documents: List[Document]) -> Chroma:
        """
        Create ChromaDB vector store from documents.
        
        Args:
            documents: List of documents to store
            
        Returns:
            Chroma vector store instance
        """
        # print("Creating vector store with ChromaDB...")
        
        # Create persist directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Create vector store
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
            collection_name="pcb_processes"
        )
        
        # print(f"Vector store created with {len(documents)} documents")
        return vector_store
    
    def initialize(self, force_reload: bool = False):
        """
        Initialize the RAG system by loading documents and creating vector store.
        
        Args:
            force_reload: If True, reload documents even if vector store exists
        """
        # Check if vector store already exists
        if os.path.exists(self.persist_directory) and not force_reload:
            # # print("Loading existing vector store...") # Gives error while loading in claude over stdio
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name="pcb_processes"
            )
        else:
            # if persist_directory exists, delete it
            # if os.path.exists(self.persist_directory):
            #     import shutil
            #     shutil.rmtree(self.persist_directory)
            # Gives error while loading in claude over stdio
            # Todo : Fix this
            # Load and process documents
            documents = self.load_documents()
            chunked_docs = self.chunk_documents(documents)
            
            # Create vector store
            self.vector_store = self.create_vector_store(chunked_docs)
        
        # Create retriever
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 2}
        )
        
        # # print("RAG system initialized successfully") ## Gives error while loading in claude over stdio
    
    def retrieve(self, query: str, k: int = 2) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        if self.retriever is None:
            raise RuntimeError("RAG system not initialized. Call initialize() first.")
        
        # Update retriever with custom k
        self.retriever.search_kwargs = {"k": k}
        results = self.retriever.invoke(query)
        return results
    
    def format_results(self, documents: List[Document]) -> str:
        if not documents:
            return "No relevant process documentation found."
        
        formatted = "\nInformation\n"
        
        for i, doc in enumerate(documents, 1):
            process_name = doc.metadata.get('process_name', 'Unknown Process')
            formatted += f"Process: {process_name}\n"
            page_content = doc.page_content.replace('\n\n', '\n')
            formatted += f"{page_content}\n"
        
        return formatted
    
    def search(self, query: str, k: int = 2) -> str:
        """
        Search for relevant information.
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            Formatted search results
        """
        documents = self.retrieve(query, k=k)
        return self.format_results(documents)
    
    def search_company(self, company_name: str, k: int = 3) -> str:
        """
        Search for information about a specific company.
        
        Args:
            company_name: Name of the company to search for
            k: Number of documents to retrieve
            
        Returns:
            Formatted search results about the company
        """
        query = f"Invented by {company_name}"
        documents = self.retrieve(query, k=k)
        return self.format_results(documents)
    
    def search_process(self, process_name: str, k: int = 3) -> str:
        """
        Search for information about a specific process.
        
        Args:
            process_name: Name of the process to search for
            k: Number of documents to retrieve
            
        Returns:
            Formatted search results about the process
        """
        query = f"{process_name}"
        documents = self.retrieve(query, k=k)
        return self.format_results(documents)


# Global RAG instance
_rag_instance: ProcessRAG | None = None


def get_rag_instance(
    ollama_base_url: str = "http://localhost:11434",
    force_reload: bool = False
) -> ProcessRAG:
    """
    Get or create the global RAG instance.
    
    Args:
        ollama_base_url: Base URL for Ollama API
        force_reload: If True, reload documents even if vector store exists
        
    Returns:
        ProcessRAG instance
    """
    global _rag_instance
    
    if _rag_instance is None:
        _rag_instance = ProcessRAG(ollama_base_url=ollama_base_url)
        _rag_instance.initialize(force_reload=force_reload)
    
    return _rag_instance


# Initialize FastMCP server
mcp = FastMCP("PCB Process RAG Server", host="127.0.0.1", port=8001)


@mcp.tool()
def get_query_rag(query: str) -> str:
    """
    Search the RAG system for general information about PCB assembly processes.
    
    Args:
        query: The search query about PCB processes, materials, or techniques
        
    Returns:
        Relevant information from the documentation
    """
    rag = get_rag_instance()
    return rag.search(query, k=2)


# @mcp.tool()
# def get_company_data_rag(company_name: str) -> str:
#     """
#     Look up information about a specific company from the documentation.
    
#     Args:
#         company_name: Name of the company to search for
        
#     Returns:
#         Information about the company including products, services, and contact details
#     """
#     rag = get_rag_instance()
#     return rag.search_company(company_name, k=3)


# @mcp.tool()
# def get_process_data_rag(process_name: str) -> str:
#     """
#     Look up detailed information about a specific PCB assembly process.
    
#     Args:
#         process_name: Name of the process (e.g., "reflow soldering", "wave soldering")
        
#     Returns:
#         Detailed information about the process including specifications and requirements
#     """
#     rag = get_rag_instance()
#     return rag.search_process(process_name, k=3)


if __name__ == "__main__":
    
    # default to false
    import argparse
    parser = argparse.ArgumentParser(description="RAG FastMCP Server for PCB Process Documentation")    
    parser.add_argument("--force-reload", action="store_true", help="Force reload documents and recreate vector store")
    parser.add_argument("--transport", type=str, default="stdio", choices=["stdio", "http"], help="Transport protocol (default: stdio)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="HTTP host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8001, help="HTTP port (default: 8000)")
    args = parser.parse_args()
    # print(f"Chroma force reload set to: {args.force_reload}")
    # print(f"Transport: {args.transport}")
    
    # print("Initializing RAG system...")
    # get_rag_instance(force_reload=args.force_reload)
    get_rag_instance(force_reload=False)
    
    # print("RAG system initialized successfully")
    
    if args.transport == "http":
        print(f"Starting HTTP server on {args.host}:{args.port}")
        # mcp.run(transport="streamable-http", host=args.host, port=args.port)
        mcp.run(transport="streamable-http")
        
    else:
        print("Starting stdio server")
        mcp.run(transport="stdio")

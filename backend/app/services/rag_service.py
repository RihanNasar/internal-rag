from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from typing import List
from app.config import get_settings
import os
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class RAGService:
    """Service for managing document retrieval with RAG"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.is_initialized = False
    
    def load_documents(self, documents_path: str = "documents") -> int:
        """
        Load and process team member documents
        
        Args:
            documents_path: Path to directory containing text documents
            
        Returns:
            Number of document chunks processed
        """
        try:
            docs = []
            
            if not os.path.exists(documents_path):
                logger.warning(f"Documents path {documents_path} does not exist")
                return 0
            
            # Load all text files
            for filename in os.listdir(documents_path):
                if filename.endswith('.txt') or filename.endswith('.md'):
                    filepath = os.path.join(documents_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            docs.append(Document(
                                page_content=content,
                                metadata={
                                    "source": filename,
                                    "filepath": filepath
                                }
                            ))
                        logger.info(f"Loaded document: {filename}")
                    except Exception as e:
                        logger.error(f"Error loading {filename}: {e}")
            
            if not docs:
                logger.warning("No documents loaded")
                return 0
            
            # Split documents into chunks
            split_docs = self.text_splitter.split_documents(docs)
            logger.info(f"Split {len(docs)} documents into {len(split_docs)} chunks")
            
            # Create vector store
            self.vector_store = Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                persist_directory="./chroma_db",
                collection_name="team_roles"
            )
            
            self.is_initialized = True
            logger.info(f"Vector store initialized with {len(split_docs)} chunks")
            
            return len(split_docs)
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            raise
    
    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """
        Search for relevant team member information
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        if not self.is_initialized or not self.vector_store:
            raise ValueError("Vector store not initialized. Call load_documents first.")
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            logger.debug(f"Found {len(results)} results for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return []
    
    def get_relevant_context(self, task_description: str, k: int = 3) -> str:
        """
        Get relevant context for task assignment
        
        Args:
            task_description: Description of the task
            k: Number of documents to retrieve
            
        Returns:
            Concatenated context from relevant documents
        """
        if not self.is_initialized or not self.vector_store:
            logger.warning("RAG service not initialized, returning empty context")
            return ""
        
        try:
            docs = self.similarity_search(task_description, k=k)
            if not docs:
                logger.info("No relevant documents found in knowledge base")
                return ""
            
            context = "\n\n".join([
                f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
                for doc in docs
            ])
            logger.info(f"Retrieved {len(docs)} relevant document chunks")
            return context
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return ""
    
    def reload_documents(self, documents_path: str = "documents") -> int:
        """Reload documents and reinitialize vector store"""
        logger.info("Reloading documents...")
        self.vector_store = None
        self.is_initialized = False
        return self.load_documents(documents_path)
    
    def add_document(self, content: str, metadata: dict = None) -> str:
        """
        Add a new document to the knowledge base
        
        Args:
            content: Document text content
            metadata: Optional metadata dictionary
            
        Returns:
            Document ID
        """
        try:
            if metadata is None:
                metadata = {}
            
            # Create document
            doc = Document(
                page_content=content,
                metadata=metadata
            )
            
            # Split into chunks
            split_docs = self.text_splitter.split_documents([doc])
            logger.info(f"Split document into {len(split_docs)} chunks")
            
            # Initialize vector store if needed
            if not self.is_initialized or not self.vector_store:
                self.vector_store = Chroma(
                    embedding_function=self.embeddings,
                    persist_directory="./chroma_db",
                    collection_name="team_roles"
                )
                self.is_initialized = True
            
            # Add to vector store
            ids = self.vector_store.add_documents(split_docs)
            
            logger.info(f"Added document to knowledge base: {metadata.get('filename', 'unknown')}")
            return ids[0] if ids else "unknown"
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    def get_stats(self) -> dict:
        """Get knowledge base statistics"""
        try:
            if not self.is_initialized or not self.vector_store:
                return {
                    "initialized": False,
                    "total_chunks": 0,
                    "collection_name": "team_roles"
                }
            
            # Get collection info
            collection = self.vector_store._collection
            count = collection.count()
            
            return {
                "initialized": True,
                "total_chunks": count,
                "collection_name": "team_roles",
                "persist_directory": "./chroma_db"
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "initialized": False,
                "total_chunks": 0,
                "error": str(e)
            }
    
    def clear_knowledge_base(self):
        """Clear all documents from the knowledge base"""
        try:
            if self.vector_store:
                # Delete the collection
                self.vector_store.delete_collection()
                logger.info("Knowledge base cleared")
            
            # Reinitialize
            self.vector_store = None
            self.is_initialized = False
            
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")
            raise


# Global singleton instance
rag_service = RAGService()

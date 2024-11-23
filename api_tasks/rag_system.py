from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import os

class RAGSystem:
    def __init__(self, openai_api_key):
        """Initialize the RAG system with OpenAI API key."""
        self.openai_api_key = openai_api_key
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.embeddings = OpenAIEmbeddings()
        self.llm = OpenAI(temperature=0)
        self.vector_store = None

    def load_documents(self, file_path):
        """Load and split documents into chunks."""
        # Load document
        loader = TextLoader(file_path)
        documents = loader.load()
        
        # Split text into chunks
        text_splitter = CharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separator="\n"
        )
        texts = text_splitter.split_documents(documents)
        return texts

    def create_vector_store(self, texts):
        """Create vector store from document chunks."""
        self.vector_store = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings
        )

    def query(self, question):
        """Query the RAG system."""
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Please load documents first.")
        
        # Create retrieval chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever()
        )
        
        # Get response
        response = qa_chain.run(question)
        return response

# Example usage
def main():
    # Initialize RAG system
    from api_tasks.basic_poligon_u import load_from_json, post_request
    
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]

    rag = RAGSystem(open_ai_api_key)
    
    # Load and process documents
    texts = rag.load_documents("path/to/your/document.txt")
    rag.create_vector_store(texts)
    
    # Query the system
    question = "What does the document say about X?"
    response = rag.query(question)
    print(f"Question: {question}")
    print(f"Answer: {response}")

if __name__ == "__main__":
    main()
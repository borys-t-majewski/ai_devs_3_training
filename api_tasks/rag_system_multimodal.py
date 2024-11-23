from langchain.document_loaders import (
    TextLoader,
    CSVLoader,
    UnstructuredURLLoader,
    PyPDFLoader,
    DirectoryLoader
)
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from typing import List, Dict, Optional
import os
from pathlib import Path

class RAGSystem:
    def __init__(self, openai_api_key: str, chunk_size: int = 1000, chunk_overlap: int = 200, temperature =0):
        """
        Initialize the RAG system with OpenAI API key and chunking parameters.
        
        Args:
            openai_api_key (str): OpenAI API key
            chunk_size (int): Size of text chunks for splitting documents
            chunk_overlap (int): Overlap between chunks to maintain context
        """
        self.openai_api_key = openai_api_key
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.embeddings = OpenAIEmbeddings()
        self.llm = OpenAI(temperature=temperature)
        self.vector_store = None
        self.nr_of_docs = 0
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Map file extensions to appropriate loaders
        self.loader_map = {
            '.txt': TextLoader,
            '.pdf': PyPDFLoader,
            '.csv': CSVLoader,
        }

    def get_loader_for_file(self, file_path: str):
        """
        Get appropriate document loader based on file extension.
        
        Args:
            file_path (str): Path to the document
            
        Returns:
            Loader class appropriate for the file type
        """
        ext = Path(file_path).suffix.lower()
        loader_class = self.loader_map.get(ext)
        if loader_class is None:
            raise ValueError(f"Unsupported file type: {ext}")
        if ext == '.txt':
            return loader_class(file_path,encoding="utf-8")
        else:
            return loader_class(file_path)
        

    def load_documents(self, sources: List[str], is_directory: bool = False):
        """
        Load multiple documents from various sources.
        
        Args:
            sources (List[str]): List of file paths or URLs
            is_directory (bool): If True, treat sources as directories and load all supported files
            
        Returns:
            List of processed document chunks
        """
        all_documents = []
        
        for source in sources:
            try:
                if is_directory:
                    # Load all supported files from directory
                    loader = DirectoryLoader(
                        source,
                        glob="**/*.*",  # Load all files
                        loader_cls=UnstructuredURLLoader  # Default loader for unknown types
                    )
                    documents = loader.load()
                else:
                    if source.startswith(('http://', 'https://')):
                        loader = UnstructuredURLLoader([source])
                    else:
                        loader = self.get_loader_for_file(source)
                    documents = loader.load()
                
                all_documents.extend(documents)
                print(f"Successfully loaded: {source}")
                
            except Exception as e:
                print(f"Error loading {source}: {str(e)}")
                continue
        
        # Split all documents into chunks
        text_splitter = CharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separator="\n"
        )
        
        return text_splitter.split_documents(all_documents)

    def create_vector_store(self, texts, persist_directory: Optional[str] = None):
        """
        Create or update vector store from document chunks.
        
        Args:
            texts: Document chunks to add to the vector store
            persist_directory (Optional[str]): Directory to persist the vector store
        """
        if persist_directory:
            self.vector_store = Chroma.from_documents(
                documents=texts,
                embedding=self.embeddings,
                persist_directory=persist_directory
            )
            self.vector_store.persist()
        else:
            self.vector_store = Chroma.from_documents(
                documents=texts,
                embedding=self.embeddings
            )
            self.nr_of_docs = len(texts)

    def customize_retrieval_chain(self, 
                                chain_type: str = "stuff",
                                custom_prompt: Optional[str] = None,
                                search_kwargs: Dict = None):
        """
        Create a customized retrieval chain.
        
        Args:
            chain_type (str): Type of chain to use ("stuff", "map_reduce", "refine", or "map_rerank")
            custom_prompt (Optional[str]): Custom prompt template
            search_kwargs (Dict): Arguments for retriever search (e.g., k=number of documents)
            
        Returns:
            RetrievalQA chain
        """
        # Default search arguments
        search_kwargs = search_kwargs or {"k": 4}
        
        # Create retriever with search configuration
        retriever = self.vector_store.as_retriever(
            search_kwargs=search_kwargs
        )
        
        # Set up custom prompt if provided
        if custom_prompt:
            prompt = PromptTemplate(
                template=custom_prompt,
                input_variables=["context", "question"]
            )
            
            return RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type=chain_type,
                retriever=retriever,
                chain_type_kwargs={"prompt": prompt}
            )
        
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type=chain_type,
            retriever=retriever
        )

    def query(self, 
              question: str,
              custom_prompt: Optional[str] = None,
              chain_type: str = "stuff",
              search_kwargs: Dict = None) -> str:
        """
        Query the RAG system with customization options.
        
        Args:
            question (str): Question to ask
            custom_prompt (Optional[str]): Custom prompt template
            chain_type (str): Type of chain to use
            search_kwargs (Dict): Arguments for retriever search
            
        Returns:
            str: Response from the model
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Please load documents first.")
        
        qa_chain = self.customize_retrieval_chain(
            chain_type=chain_type,
            custom_prompt=custom_prompt,
            search_kwargs=search_kwargs
        )
        
        return qa_chain.run(question)

    def get_document_count(self) -> int:
        """Get total number of documents in vector store"""
        if hasattr(self, 'nr_of_docs'):
            return self.nr_of_docs
        else:
            raise NotImplementedError("Unable to determine document count method for this vector store")


# Example usage
def main():
    # Initialize RAG system
    from basic_poligon_u import load_from_json, post_request
    import os
    import sys
    
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\..\config.json')
    
    open_ai_api_key = json_secrets["open_ai_api_key"]

    rag = RAGSystem(open_ai_api_key)
    
    # Load multiple documents
    sources = [
        r"C:\Projects\AI_DEVS_3\s_3_01_files\2024-11-12_report-00-sektor_C4.txt",
        r"C:\Projects\AI_DEVS_3\s_3_01_files\2024-11-12_report-05-sektor_C1.txt"
    ]
    
    # Load and process documents
    texts = rag.load_documents(sources)
    
    # Create vector store with persistence
    # rag.create_vector_store(texts, persist_directory="./vector_store",persist_directory=False)

    rag.create_vector_store(texts, persist_directory=None)
    # documents = rag.get()
    # for d in documents:
    #     print(d)
    #     print('--')
    # Example of custom prompt
    custom_prompt = """
    Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    Context: {context}
    
    Question: {question}
    
    Answer:"""
    
    # Query with customization
    print(os.path.dirname(sys.executable))

    question = "What are the main points discussed in the documents?"
    response = rag.query(
        question,
        custom_prompt=custom_prompt,
        chain_type="stuff",
        search_kwargs={"k": 4}
    )
    
    print(f"Question: {question}")
    print(f"Answer: {response}")

    # sim_score = rag.vector_store.similarity_search_with_score('Aleksander Ragowski',k=20)
    # sim_score = rag.vector_store(persist_directory=False).similarity_search_with_score('Wykryto  niepokjace detektory ruchu kurwa',k=2)

    sim_score = rag.vector_store.similarity_search_with_score('osobnik Aleksander Ragowski przedstawił się biometryczny',k=4)
    print(type(sim_score))
    print(len(sim_score))
    
    for s in sim_score:
        print(s)

if __name__ == "__main__":
    main()


#     (Document(metadata={'source': 'C:\\Projects\\AI_DEVS_3\\s_3_01_files\\2024-11-12_report-00-sektor_C4.txt'}, page_content='Godzina 22:43. Wykryto jednostkÄ™ organicznÄ… w pobliÅ¼u pÃ³Å‚nocnego skrzydÅ‚a fabryki. Osobnik przedstawiÅ‚ siÄ™ jako Aleksander Ragowski. Przeprowadzono skan biometryczny, 
# zgodnoÅ›Ä‡ z bazÄ… danych potwierdzona. Jednostka przekazana do dziaÅ‚u kontroli. Patrol kontynuowany.'), 0.2763340175151825)
# (Document(metadata={'source': 'C:\\Projects\\AI_DEVS_3\\s_3_01_files\\2024-11-12_report-05-sektor_C1.txt'}, page_content='Godzina 04:02. Bez wykrycia aktywnoÅ›ci organicznej lub technologicznej. Sensor dÅºwiÄ™kowy i detektory ruchu w peÅ‚nej gotowoÅ›ci. Bez niepokojÄ…cych sygnaÅ‚Ã³w w trakcie patrolu. KontynuujÄ™ monitorowanie.'), 0.39878755807876587)
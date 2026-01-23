import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import ChatOllama,OllamaEmbeddings


class RAGEngine:
    def __init__(self, persist_directory="chroma_db", pdf_path="testPDFinput.pdf"):
        load_dotenv()
        self.persist_directory = persist_directory
        self.pdf_path = pdf_path

        # 1. Initialize Models (Done once)
        # self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
        self.embedding_model = OllamaEmbeddings(model="embeddinggemma")

        # This is where we would query OpenAI for a response
        #self.llm = ChatOpenAI(model_name="gpt-5-mini", temperature=0)

        #This is the method to run the model locally
        self.llm = ChatOllama(model="gemma3:4b", temperature=0)

        # 2. Load/Create Vectorstore (Done once)
        self.vectorstore = self._setup_vectorstore()

        # 3. Set up the Chain (Done once)
        # self.rag_chain = self._setup_chain()

    def _setup_vectorstore(self):
        if os.path.exists(self.persist_directory):
            return Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_model
            )
        else:
            loader = PyPDFLoader(self.pdf_path)
            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            splits = text_splitter.split_documents(docs)
            return Chroma.from_documents(
                documents=splits,
                embedding=self.embedding_model,
                persist_directory=self.persist_directory
            )

    def query(self, question: str, user_id: str):  # Accept user_id
        # Create a filtered retriever for this specific query
        # This prevents User A from ever 'seeing' User B's documents
        retriever = self.vectorstore.as_retriever(
            search_kwargs={'filter': {'user_id': user_id}}
        )

        template = """
        You are a helpful assistant. Answer the question based only on the following context. You should give references in the format [document_name, page_number] for every bit of information that you use.
        Context: {context}
        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)

        # Build and invoke the chain
        chain = (
                {"context": retriever, "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
        )
        return chain.invoke(question)

import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import ChatOllama,OllamaEmbeddings
from sympy.multipledispatch.dispatcher import source


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

    def format_chroma_docs(self, docs):
        """Formats Chroma docs into a single string with metadata headers"""
        formatted_chunks = []

        for doc in docs:
            # Get Metadata directly from chromaDB results
            source_name = doc.metadata.get("document_name", "Unknown Source")
            page_number = doc.metadata.get("page_number", "Unknown Page")

            #Create a clearly marked header, so that the LLM can clearly understand it
            header = f"--- SOURCE: [{source_name}, Page {page_number}] ---"
            content = f"{header}\n{doc.page_content}"
            formatted_chunks.append(content)

        return "\n\n".join(formatted_chunks)

    def query(self, question: str, user_id: str):  # Accept user_id
        # Create a filtered retriever for this specific query
        # This prevents User A from ever 'seeing' User B's documents
        retriever = self.vectorstore.as_retriever(
            search_kwargs={'filter': {'user_id': user_id}}
        )

        # template = """
        # You are a helpful assistant. Answer the question based only on the following context. You should give references in the format [document_name, page_number] for every bit of information that you use.
        # Context: {context}
        # Question: {question}
        # """

        template = """
        You are a helpful assistant that answers questions strictly using the provided context. 

        RULES:
        1. Every claim you make must be followed by a reference in the format: [document_name, page_number].
        2. If the context doesn't contain the answer, say you don't know.
        3. The source information is provided at the start of each context block as 'SOURCE: [name, page]'.

        Example:
        Context: 
        --- SOURCE: [Manual.pdf, 12] ---
        The battery lasts for 10 hours.
        Question: How long is the battery life?
        Answer: The battery lasts for 10 hours [Manual.pdf, 12].

        Context: {context}
        Question: {question}
        Answer:
        """

        prompt = ChatPromptTemplate.from_template(template)

        # Build and invoke the chain
        chain = (
                {"context": retriever | RunnableLambda(self.format_chroma_docs),
                 "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
        )

        # print(chain.context)

        return chain.invoke(question)

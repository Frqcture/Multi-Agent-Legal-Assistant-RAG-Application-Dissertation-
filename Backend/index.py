import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import ChatOllama, OllamaEmbeddings


class RAGEngine:
    def __init__(
        self, persistDirectory: str = "chroma_db", pdfPath: str = "testPDFinput.pdf"
    ):
        load_dotenv()
        self.persistDirectory = persistDirectory
        self.pdfPath = pdfPath
        self.embeddingModel = OllamaEmbeddings(model="embeddinggemma")
        self.llm = ChatOllama(model="gemma3:4b", temperature=0)
        self.vectorstore = self._setupVectorstore()

    def _setupVectorstore(self):
        """Load existing vectorstore or create new one from PDF."""
        if os.path.exists(self.persistDirectory):
            return Chroma(
                persist_directory=self.persistDirectory,
                embedding_function=self.embeddingModel,
            )

        loader = PyPDFLoader(self.pdfPath)
        docs = loader.load()
        from langchain_text_splitters import NLTKTextSplitter
        
        # Natural Language Context Chunking - Splits on sentences instead of arbitrary characters
        textSplitter = NLTKTextSplitter(
            chunk_size=600, chunk_overlap=50
        )
        splits = textSplitter.split_documents(docs)
        return Chroma.from_documents(
            documents=splits,
            embedding=self.embeddingModel,
            persist_directory=self.persistDirectory,
        )

    def formatChromaDocs(self, docs):
        """Format documents with source headers for LLM context."""
        formattedChunks = []
        for doc in docs:
            sourceName = doc.metadata.get("document_name", "Unknown Source")
            pageNumber = doc.metadata.get("page_number", "Unknown Page")
            header = f"--- SOURCE: [{sourceName}, Page {pageNumber}] ---"
            formattedChunks.append(f"{header}\n{doc.page_content}")
        return "\n\n".join(formattedChunks)

    def query(self, question: str, userId: str):
        """Query RAG engine with user isolation via metadata filtering."""
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"filter": {"user_id": userId}}
        )

        template = """You are a helpful assistant that answers questions strictly using provided context.

RULES:
1. Every claim must be followed by a reference: [document_name, page_number].
2. If context doesn't answer the question, say you don't know.
3. Source info appears at the start of each context block as 'SOURCE: [name, page]'.

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
        chain = (
            {
                "context": retriever | RunnableLambda(self.formatChromaDocs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return chain.invoke(question)

    def listUserFiles(self, userId: str):
        """Get unique filenames uploaded by user."""
        results = self.vectorstore.get(where={"user_id": userId}, include=["metadatas"])
        filenames = {
            meta["document_name"]
            for meta in results["metadatas"]
            if "document_name" in meta
        }
        return list(filenames)

    def deleteFile(self, userId: str, filename: str):
        """Delete all chunks for a user's file."""
        results = self.vectorstore.get(
            where={"$and": [{"user_id": userId}, {"document_name": filename}]}
        )

        if results["ids"]:
            self.vectorstore.delete(ids=results["ids"])
            return True
        return False

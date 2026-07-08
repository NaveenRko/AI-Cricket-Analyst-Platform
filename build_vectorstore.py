from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import TextLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.vectorstores import FAISS

# ==================================
# LOAD ALL TXT FILES RECURSIVELY
# ==================================

loader = DirectoryLoader(
    "rag/rag_data",
    glob="**/*.txt",
    loader_cls=TextLoader
)

docs = loader.load()

print(f"Loaded {len(docs)} documents")

if len(docs) == 0:
    raise ValueError(
        "No txt files found inside rag/rag_data"
    )

# ==================================
# CHUNKING
# ==================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.split_documents(docs)

print(f"Created {len(chunks)} chunks")

# ==================================
# EMBEDDINGS
# ==================================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ==================================
# FAISS
# ==================================

vectorstore = FAISS.from_documents(
    chunks,
    embeddings
)

vectorstore.save_local(
    "rag/faiss_index"
)

print("Vectorstore Saved")
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = FAISS.load_local(
    "rag/faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

retriever = db.as_retriever(
    search_kwargs={"k": 3}
)

RAG_PROMPT = """
You are a senior IPL historian and cricket analyst.

Use ONLY the retrieved context.

Rules:

1. Answer directly.
2. Never invent facts.
3. Mention important achievements.
4. Explain why the player/team/match is important.
5. Use professional cricket language.
6. If information is unavailable say:
Information not available in knowledge base.

Context:
{context}

Question:
{question}

Answer:
"""


def get_rag_answer(llm, question):

    docs = retriever.invoke(question)

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    rag_sources = [
        doc.metadata.get("source", "")
        for doc in docs
    ]

    prompt = PromptTemplate(
        template=RAG_PROMPT,
        input_variables=["context", "question"]
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "context": context,
            "question": question
        }
    )

    return {
        "answer": response.content,
        "rag_docs": rag_sources
    }
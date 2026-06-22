import groq
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.rag.vectordb import VectorDBEngine
from app.core.logger import logger
from app.core.config import settings

# 1. VectorDBEngine ka global instance
_vector_db = VectorDBEngine()


def ask_question(question: str, db: Session, doc_id: Optional[int] = None, source_type: Any = None, top_k: int = 6) -> dict:
    """
    RAG query: specific doc_id (single document) aur/ya source_type
    (document, youtube, website, github, etc.) ke sath filter hota hai.
    """
    logger.info(f"Triggering query processing engine for: '{question}' | doc_id={doc_id} | source_type={source_type}")
    try:
        # ChromaDB se similarity search (doc_id + source_type filter ke sath)
        raw_results = _vector_db.query_similarity(
            question,
            top_k=top_k,
            doc_id=doc_id,
            source_type=source_type,
        )

        documents = raw_results.get("documents", [[]])[0] if raw_results.get("documents") else []
        metadatas = raw_results.get("metadatas", [[]])[0] if raw_results.get("metadatas") else []

        if not documents:
            logger.warning(f"No relevant context found for doc_id={doc_id} | source_type={source_type}")
            return {
                "answer": "I could not find any relevant information in the selected database.",
                "sources": [],
                "status": "empty_database"
            }

        # 2. Context Aggregation — har chunk ke saath uska source label bhi dete hain,
        # taaki LLM ko pata chale kaunsa context kis source (youtube/website/github) se aaya
        context_parts = []
        for doc, meta in zip(documents, metadatas):
            src = meta.get("source", "Unknown Source") if meta else "Unknown Source"
            stype = meta.get("source_type", "unknown") if meta else "unknown"
            context_parts.append(f"[Source: {src} | Type: {stype}]\n{doc}")
        context = "\n---\n".join(context_parts)

        # 3. Sources Filtering
        sources = list(set([
            meta.get("source", "Unknown Source")
            for meta in metadatas
            if meta
        ]))

        # 4. System Prompt: Force Roman Script
        system_prompt = (
            "You are an expert AI platform assistant. Answer the user's question based strictly on the provided context.\n"
            "The context below may come from multiple sources (YouTube video transcripts, websites, GitHub code, "
            "or uploaded documents) — each chunk is labeled with its Source and Type.\n"
            "CRITICAL RESPONSE RULES:\n"
            "1. Match the language style of the user's question.\n"
            "2. ALWAYS use the English/Latin alphabet (Roman script) only. NEVER use Devanagari/Hindi script.\n"
            "3. If a chunk's Type is 'youtube', treat its content as the spoken transcript of that video — "
            "answer video-related questions (e.g. 'what is inside the video', 'what does the video say') "
            "using that chunk's content directly, even if the word 'video' itself doesn't appear in the transcript.\n"
            "4. Give a direct, confident answer if the context discusses the topic, even if it doesn't contain a "
            "formal dictionary-style definition. Synthesize the answer from how the topic is discussed in the "
            "context, rather than saying you can't find a definition.\n"
            "5. Only say you don't know if the context truly has no relevant discussion of the topic at all.\n\n"
            f"Context:\n{context}"
        )

        # 5. Groq API Call
        client = groq.Groq(api_key=settings.GROQ_API_KEY)

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3
        )

        answer = chat_completion.choices[0].message.content
        logger.info("Successfully fetched synthesis model answer from Groq LLM.")

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Critical breakdown inside query processing service: {str(e)}")
        raise Exception(f"Query Pipeline Collapse Error: {str(e)}")
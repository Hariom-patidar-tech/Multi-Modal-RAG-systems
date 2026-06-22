import groq
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.rag.vectordb import VectorDBEngine
from app.core.logger import logger
from app.core.config import settings

# 1. VectorDBEngine ka global instance
_vector_db = VectorDBEngine()

# source_type parameter add kiya hai taaki filtering kaam kare
def ask_question(question: str, db: Session, doc_id: int = None, source_type=None) -> dict:
    """
    RAG query: Ab specific source_type (document, web, github, etc.) ke sath filter hota hai.
    """
    logger.info(f"Triggering query processing engine for: '{question}' | Filter: {source_type}")
    try:
        # ChromaDB se similarity search (Filter ke sath)
        raw_results = _vector_db.query_similarity(question, top_k=4, doc_id=doc_id, source_type=source_type)
        
        documents = raw_results.get("documents", [[]])[0] if raw_results.get("documents") else []
        metadatas = raw_results.get("metadatas", [[]])[0] if raw_results.get("metadatas") else []
        
        if not documents:
            logger.warning(f"No relevant context found for filter: {source_type}")
            return {
                "answer": "I could not find any relevant information in the selected database.",
                "sources": [],
                "status": "empty_database"
            }
            
        # 2. Context Aggregation
        context = "\n---\n".join(documents)
        
        # 3. Sources Filtering
        # Sirf wahi sources dikhayega jo filter se match karte hain
        sources = list(set([
            meta.get("source", "Unknown Source") 
            for meta in metadatas 
            if meta
        ]))

        # 4. System Prompt: Force Roman Script
        system_prompt = (
            "You are an expert AI platform assistant. Answer the user's question based strictly on the provided context.\n"
            "CRITICAL RESPONSE RULES:\n"
            "1. Match the language style of the user's question.\n"
            "2. ALWAYS use the English/Latin alphabet (Roman script) only. NEVER use Devanagari/Hindi script.\n"
            "3. If the context does not contain the answer, state clearly that you don't know.\n\n"
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
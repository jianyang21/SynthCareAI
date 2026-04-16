import os
import shutil
import uuid
from datetime import datetime
from pypdf import PdfReader
from pymongo import MongoClient, TEXT
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()
# ==========================================
# SETUP
# ==========================================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["synthcare"]

summaries_collection = mongo_db["patient_summaries"]
pages_collection = mongo_db["patient_pages"]

# Ensure the text index exists for the page index algorithm
pages_collection.create_index([("text", TEXT)])

# Using a standard LLM wrapper, but keeping the orchestration loop manual
summary_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# ==========================================
# INGESTION LOGIC
# ==========================================
def process_and_index_pdf(file_obj, filename: str, patient_id: int, doctor_id: int, record_type: str) -> dict:
    storage_dir = os.path.join(os.getcwd(), "local_storage", "pdfs")
    os.makedirs(storage_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{patient_id}_{timestamp}_{filename}"
    file_path = os.path.join(storage_dir, safe_filename)

    # Save to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file_obj, buffer)

    document_id = str(uuid.uuid4())

    try:
        reader = PdfReader(file_path)
        all_text_chunks = []
        page_documents = []

        # Read page by page
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if not page_text or not page_text.strip():
                continue
            
            all_text_chunks.append(page_text)
            page_documents.append({
                "document_id": document_id,
                "patient_id": patient_id,
                "page_number": page_num + 1,
                "text": page_text,
            })

        if not page_documents:
            raise ValueError("No readable text found in the PDF.")

        # Batch insert to build the text index
        pages_collection.insert_many(page_documents)

        # Generate global summary (truncated for safety limits)
        full_text = "\n".join(all_text_chunks)
        summary_prompt = [
            SystemMessage(content="Summarize this medical record concisely."),
            HumanMessage(content=f"Record text:\n{full_text[:15000]}")
        ]
        summary_response = summary_llm.invoke(summary_prompt)
        summary = summary_response.content.strip()

        # Save metadata
        mongo_document = {
            "document_id": document_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "record_type": record_type,
            "original_filename": filename,
            "disk_location": file_path,
            "summary": summary,
            "total_pages": len(reader.pages),
            "created_at": datetime.utcnow()
        }
        summaries_collection.insert_one(mongo_document)

        return {
            "status": "index_built",
            "document_id": document_id,
            "pages_indexed": len(page_documents),
            "summary": summary
        }

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e  # Let the router handle the HTTP exception

# ==========================================
# RETRIEVAL LOGIC
# ==========================================
def answer_pdf_question(document_id: str, question: str) -> dict:
    # 1. Search the index
    pipeline = [
        {
            "$match": {
                "document_id": document_id,
                "$text": {"$search": question}
            }
        },
        {"$addFields": {"score": {"$meta": "textScore"}}},
        {"$sort": {"score": -1}},
        {"$limit": 3}
    ]
    
    relevant_pages = list(pages_collection.aggregate(pipeline))

    if not relevant_pages:
        return {"answer": "I couldn't find any relevant keywords in this document.", "source_pages": []}

    # 2. Construct context
    context_blocks = []
    sources = []
    for page in relevant_pages:
        page_num = page.get("page_number", "?")
        text_chunk = page.get("text", "")
        context_blocks.append(f"--- Page {page_num} ---\n{text_chunk}")
        sources.append(page_num)

    compiled_context = "\n\n".join(context_blocks)

    # 3. Final generation
    prompt = f"""
    You are a medical assistant analyzing a patient's document.
    Answer the user's question based strictly on the provided document context below.
    If the context does not contain the answer, say "I cannot find the answer in this document."
    Cite the page numbers in your answer when relevant.

    [CONTEXT]
    {compiled_context}

    [QUESTION]
    {question}
    """

    messages = [
        SystemMessage(content="You are a precise, evidence-based medical assistant."),
        HumanMessage(content=prompt)
    ]

    response = summary_llm.invoke(messages)
    
    return {
        "answer": response.content.strip(),
        "source_pages": list(set(sources))
    }
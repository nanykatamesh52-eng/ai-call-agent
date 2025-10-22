import os
import re
import json
import pandas as pd
from langchain_community.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

_vector_db = None
_embedding_model = None
_llm = None

def parse_marketing_excel(file_path):
    df = pd.read_excel(file_path)
    docs = []
    for _, row in df.iterrows():
        questions = [q.strip() for q in str(row['Question Variants']).split('/')]
        docs.append({
            "questions": questions,
            "answer": row['Reply'],
            "intent": row['Intent']
        })
    return docs

def get_marketing_reply(query: str, language: str = "Arabic"):
    global _vector_db, _embedding_model, _llm

    if not query.strip():
        return {"reply": "من فضلك اسأل سؤالك.", "intent": "متابعة"}

    file_path = "marketing_info.xlsx"
    if not os.path.exists(file_path):
        return {"reply": "ملف قاعدة المعرفة غير موجود.", "intent": "إنهاء"}

    if _vector_db is None:
        docs_raw = parse_marketing_excel(file_path)
        docs_text = [f"سؤال: {' / '.join(d['questions'])}\nرد: {d['answer']}\nنية: {d['intent']}" for d in docs_raw]

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
        # Create simple document dicts expected by FAISS.from_documents
        docs_split = [{'page_content': t} for t in docs_text]

        _embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        # FAISS.from_documents expects Document objects; here we use the convenience method
        _vector_db = FAISS.from_documents(docs_split, _embedding_model)
        _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    results = _vector_db.similarity_search(query, k=3)
    context = "\n\n".join([r.page_content for r in results])

    prompt = f"""
أنت مساعد ذكي لشركة ماركت بلس لخدمات التسويق الإلكتروني.
استخدم المعلومات التالية للإجابة على العميل، وارجع الرد والنية فقط بصيغة JSON:

{context}

السؤال: {query}
"""

    response = _llm.invoke(prompt)
    match = re.search(r"\{.*\}", response.content.strip(), re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0).replace("'", '"'))
            return data
        except:
            pass

    return {"reply": response.content.strip(), "intent": "متابعة"}

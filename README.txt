AI Call Agent (Innocalls + RAG + ElevenLabs)
===========================================

Files included:
- .env.sample                 # edit and fill with real API keys
- marketing_info.txt          # knowledge base (also shipping an example XLSX)
- marketing_info.xlsx         # example knowledge base in Excel form
- contacts.xlsx               # example contact list
- marketing_rag_excel.py      # RAG code reading Excel and returning {reply,intent}
- innocalls_ws_client.py      # websocket client + upload helper (adjust for your API)
- webhook_stt.py              # FastAPI webhook that handles STT -> RAG -> TTS -> WS actions + logging
- call_launcher.py            # simple sequential launcher to trigger calls via Innocalls API
- test_call_flow.py           # local test script to simulate Innocalls webhook POST

Quick start:
1) Copy .env.sample to .env and fill keys (ElevenLabs + Innocalls tokens).
2) Install dependencies:
   pip install fastapi uvicorn pandas requests python-dotenv openpyxl websockets langchain langchain-openai langchain-community sentence-transformers faiss-cpu
3) Run webhook server:
   uvicorn webhook_stt:app --host 0.0.0.0 --port 8000
   still work 
   screen -S innocalls
   uvicorn webhook_stt:app --host 0.0.0.0 --port 8000
4) Run tests locally:
   python test_call_flow.py
5) To run call launcher (optional):
   python call_launcher.py

Notes:
- Update UPLOAD_URL / WS_URL to match your Innocalls account.
- The code uses ElevenLabs for TTS; adapt to another provider if preferred.
- Clean up temporary files (mp3) as needed.

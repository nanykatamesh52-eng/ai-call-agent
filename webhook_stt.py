import os, asyncio, hashlib
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from marketing_rag_excel import get_marketing_reply
from innocalls_ws_client import upload_audio_to_innocalls_local, ws_play_audio, ws_play_audio_then_hangup, ws_transfer_call
import pandas as pd
import requests

load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
HUMAN_AGENT_NUMBER = os.getenv("HUMAN_AGENT_NUMBER")
LANGUAGE = os.getenv("LANGUAGE", "Arabic")
LOG_FILE = "call_logs.xlsx"

app = FastAPI()

def ensure_log_file():
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame(columns=["Date/Time", "Call ID", "Phone", "Customer Speech", "AI Reply", "Intent", "Status"])
        df.to_excel(LOG_FILE, index=False)

def log_call(call_id, phone, speech, reply, intent, status):
    ensure_log_file()
    df = pd.read_excel(LOG_FILE)
    new_row = {
        "Date/Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Call ID": call_id,
        "Phone": phone,
        "Customer Speech": speech,
        "AI Reply": reply,
        "Intent": intent,
        "Status": status,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(LOG_FILE, index=False)
    print(f"Logged call {call_id}")

def elevenlabs_tts_save(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    body = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability":0.5,"similarity_boost":0.75}
    }
    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code == 200:
        name = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
        filename = f"tts_{name}.mp3"
        with open(filename, "wb") as f:
            f.write(resp.content)
        return filename
    else:
        print("ElevenLabs error:", resp.status_code, resp.text)
        return None

@app.post("/webhook")
async def innocalls_webhook(req: Request):
    data = await req.json()
    call_id = data.get("callId") or data.get("call_id") or data.get("callIdString")
    phone = data.get("phone") or data.get("from") or data.get("caller")
    speech_text = data.get("speech_text") or data.get("transcript") or data.get("speech") or ""

    if not call_id:
        call_id = phone or "unknown"

    print(f"Webhook call_id={call_id} phone={phone} speech='{speech_text[:80]}'")

    if not speech_text:
        reply_text = "لم أسمع ردًا واضحًا، هل يمكنك إعادة ذلك؟"
        filename = elevenlabs_tts_save(reply_text)
        if filename:
            file_url = upload_audio_to_innocalls_local(filename)
            try:
                os.remove(filename)
            except:
                pass
            if file_url:
                await ws_play_audio(call_id, file_url)
                return {"status":"ok","action":"speak"}
        raise HTTPException(status_code=500, detail="No speech and unable to respond")

    rag_out = get_marketing_reply(speech_text, LANGUAGE)
    reply_text = rag_out.get("reply", "عذرًا، لم أفهم سؤالك.")
    intent = rag_out.get("intent", "متابعة")
    print("RAG =>", rag_out)

    tts_file = elevenlabs_tts_save(reply_text)
    if tts_file is None:
        raise HTTPException(status_code=500, detail="TTS generation failed")

    file_url = upload_audio_to_innocalls_local(tts_file)
    try:
        os.remove(tts_file)
    except:
        pass
    if not file_url:
        raise HTTPException(status_code=500, detail="Upload to Innocalls failed")

    if intent == "تحويل_لبشري":
        await ws_transfer_call(call_id, HUMAN_AGENT_NUMBER)
        status = "Transferred"
    elif intent == "إنهاء":
        await ws_play_audio_then_hangup(call_id, file_url)
        status = "Ended"
    else:
        await ws_play_audio(call_id, file_url)
        status = "Replied"

    log_call(call_id, phone, speech_text, reply_text, intent, status)
    return {"status": "ok", "intent": intent, "action": status}

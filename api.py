import os
import glob
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AI_API")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    ticker: str
    date: str

def read_documents(directory_path: str) -> str:
    docs = []
    for filepath in glob.glob(os.path.join(directory_path, '*.md')):
        if os.path.basename(filepath).lower() == 'readme.md': 
            continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                docs.append(f"--- Document: {os.path.basename(filepath)} ---\n{f.read()}")
        except Exception as e:
            logger.warning(f"Could not read file {filepath}: {e}")
    return "\n\n".join(docs)

@app.post("/generate")
async def generate_brief(data: RequestData):
    load_dotenv()
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured in .env")

    client = Groq(api_key=api_key)
    
    try:
        with open('system_prompt.txt', 'r', encoding='utf-8') as f:
            system_instruction = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="system_prompt.txt not found")

    doc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    documents_text = read_documents(doc_dir)

    user_prompt = (
        f"Target Ticker: {data.ticker}\n"
        f"Current Date: {data.date}\n\n"
        f"Here are the retrieved documents:\n{documents_text}\n\n"
        f"Please generate the research brief based on the instructions."
    )

    models_to_try = ['openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'qwen/qwen3.8-27b', 'allam-2-7b']
    
    for model_name in models_to_try:
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                )
                return {"result": completion.choices[0].message.content}
            except Exception as e:
                if "429" in str(e) or "503" in str(e):
                    if attempt < max_attempts - 1:
                        time.sleep(2)
                    else:
                        break
                else:
                    logger.error(f"{model_name} failed: {e}")
                    break
    
    raise HTTPException(status_code=500, detail="Could not complete generation due to API constraints or Rate Limits")

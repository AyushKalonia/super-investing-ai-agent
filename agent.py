import os
import glob
import argparse
import time
import logging
from typing import List
from groq import Groq
from dotenv import load_dotenv

# Configure production-grade logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("AI_Agent")

def read_documents(directory_path: str) -> str:
    """
    Scans the provided directory for markdown documents and aggregates their contents.
    Excludes the instructions 'README.md' file to prevent contamination of the context.
    """
    docs: List[str] = []
    
    for filepath in glob.glob(os.path.join(directory_path, '*.md')):
        if os.path.basename(filepath).lower() == 'readme.md': 
            continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                docs.append(f"--- Document: {os.path.basename(filepath)} ---\n{f.read()}")
        except Exception as e:
            logger.warning(f"Could not read file {filepath}: {e}")
            
    return "\n\n".join(docs)


def run_agent(ticker: str, doc_dir: str, current_date: str) -> None:
    """
    Main orchestrator function for the AI Research Agent using Groq API.
    """
    load_dotenv()
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        logger.error("Please set your actual GROQ_API_KEY in the .env file.")
        return

    client = Groq(api_key=api_key)
    
    try:
        with open('system_prompt.txt', 'r', encoding='utf-8') as f:
            system_instruction = f.read()
    except FileNotFoundError:
        logger.error("system_prompt.txt not found. Make sure you are running this from the project root.")
        return

    if not os.path.exists(doc_dir):
        logger.error(f"Directory '{doc_dir}' does not exist.")
        return
        
    documents_text = read_documents(doc_dir)
    if not documents_text:
        logger.warning(f"No markdown documents found in '{doc_dir}'.")

    user_prompt = (
        f"Target Ticker: {ticker}\n"
        f"Current Date: {current_date}\n\n"
        f"Here are the retrieved documents:\n{documents_text}\n\n"
        f"Please generate the research brief based on the instructions."
    )

    models_to_try = ['openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'qwen/qwen3.8-27b', 'allam-2-7b']

    logger.info(f"Running research agent for {ticker}...")
    
    response = None
    for model_name in models_to_try:
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                logger.info(f"Invoking {model_name} (Attempt {attempt + 1})...")
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                )
                response = completion.choices[0].message.content
                logger.info(f"Success with {model_name}!")
                break # Break out of retry loop if successful
            except Exception as e:
                if "429" in str(e) or "503" in str(e):
                    if attempt < max_attempts - 1:
                        logger.warning(f"Server rate limited or busy. Retrying in 3 seconds...")
                        time.sleep(3)
                    else:
                        logger.error(f"{model_name} failed: Rate Limit Exceeded")
                        break
                else:
                    logger.error(f"{model_name} failed: {e}")
                    break # Break out of retry loop on generic errors
        
        if response:
            break # Break out of model fallback loop if we got a response

    if response:
        output_filename = f"{ticker.replace(':', '').replace(' ', '_').lower()}_brief.md"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(response)
        logger.info(f"Research brief successfully generated and saved to {output_filename}!")
    else:
        logger.error("Could not complete the generation. Please check your Groq API key quota.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Research Agent for Super Investing")
    parser.add_argument("--ticker", type=str, default="NSE: SRVCABLE", help="The target stock ticker (e.g., NSE: SRVCABLE)")
    default_doc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    parser.add_argument("--dir", type=str, default=default_doc_dir, help="Directory containing the research documents")
    parser.add_argument("--date", type=str, default="23 September 2026", help="The current date for the agent's temporal context")
    
    args = parser.parse_args()
    run_agent(args.ticker, args.dir, args.date)

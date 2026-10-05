import os
import glob
import argparse
import time
import logging
from typing import List
from google import genai
from google.genai import types
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
    
    Args:
        directory_path (str): The absolute or relative path to the directory containing documents.
        
    Returns:
        str: A concatenated string of all document contents, delimited with their filenames.
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
    Main orchestrator function for the AI Research Agent. 
    Loads API keys, reads documents, constructs the prompt, and fetches the brief from the Gemini API.
    
    Args:
        ticker (str): The stock ticker symbol (e.g., "NSE: SRVCABLE")
        doc_dir (str): Directory containing the scraped markdown files.
        current_date (str): Simulated or actual current date to provide temporal context to the AI.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Setup authentication
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.error("Please set your actual GEMINI_API_KEY in the .env file.")
        return

    client = genai.Client(api_key=api_key)
    
    # Load system prompt containing rules for conflict resolution and prompt injection
    try:
        with open('system_prompt.txt', 'r', encoding='utf-8') as f:
            system_instruction = f.read()
    except FileNotFoundError:
        logger.error("system_prompt.txt not found. Make sure you are running this from the project root.")
        return

    # Validate and load documents
    if not os.path.exists(doc_dir):
        logger.error(f"Directory '{doc_dir}' does not exist.")
        return
        
    documents_text = read_documents(doc_dir)
    if not documents_text:
        logger.warning(f"No markdown documents found in '{doc_dir}'.")

    # Construct the final user prompt dynamically
    user_prompt = (
        f"Target Ticker: {ticker}\n"
        f"Current Date: {current_date}\n\n"
        f"Here are the retrieved documents:\n{documents_text}\n\n"
        f"Please generate the research brief based on the instructions."
    )

    # Optimal models determined from API availability and free-tier quotas
    models_to_try = ['gemini-3.8-flash', 'gemini-flash-latest', 'gemini-3.5-flash']

    logger.info(f"Running research agent for {ticker}...")
    
    response = None
    for model_name in models_to_try:
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                logger.info(f"Invoking {model_name} (Attempt {attempt + 1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2, # Low temperature ensures factual consistency and prevents hallucinations
                    ),
                )
                logger.info(f"Success with {model_name}!")
                break # Break out of retry loop if successful
            except Exception as e:
                if "503" in str(e) and attempt < max_attempts - 1:
                    logger.warning(f"Server is experiencing high demand. Retrying in 3 seconds...")
                    time.sleep(3)
                else:
                    logger.error(f"{model_name} failed: {e}")
                    break # Break out of retry loop on non-503 or max attempts reached
        
        if response:
            break # Break out of model fallback loop if we got a response

    # Output the result using a dynamic filename based on the ticker
    if response:
        output_filename = f"{ticker.replace(':', '').replace(' ', '_').lower()}_brief.md"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info(f"Research brief successfully generated and saved to {output_filename}!")
    else:
        logger.error("Could not complete the generation. Please check your API key quota.")


if __name__ == "__main__":
    # Setup argparse to make the agent a fully functional CLI tool
    parser = argparse.ArgumentParser(description="AI Research Agent for Super Investing")
    
    parser.add_argument(
        "--ticker", 
        type=str, 
        default="NSE: SRVCABLE", 
        help="The target stock ticker (e.g., NSE: SRVCABLE)"
    )
    
    # Default path assumes the script is run from the 'project' folder and docs are in 'data'
    default_doc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    parser.add_argument(
        "--dir", 
        type=str, 
        default=default_doc_dir, 
        help="Directory containing the research documents"
    )
    
    parser.add_argument(
        "--date", 
        type=str, 
        default="23 September 2026", 
        help="The current date for the agent's temporal context"
    )
    
    args = parser.parse_args()
    run_agent(args.ticker, args.dir, args.date)

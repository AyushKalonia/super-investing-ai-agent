# Super Investing - AI Research Agent (Part B)

This project contains a Python-based AI research agent designed to generate a one-page research brief for a given NSE ticker based on a provided corpus of documents. 

The project features both a **Command Line Interface (CLI)** and a **Full-Stack Web Interface** (FastAPI + React).

## Design Highlights
*   **Active Sanitization:** The agent actively parses and sanitizes inputs by explicitly resolving entity name mismatches (e.g. ignoring 'Sarvottam Cable Network' when researching 'Sarvottam Cables'), prioritizing temporally relevant data, and highlighting conflicting financial figures rather than hallucinating averages.
*   **Security (Prompt Injection Defense):** The system prompt is engineered to neutralize hidden prompt injection attacks (like those found in unregulated blog sources) to guarantee safe and objective outputs.
*   **Production-Grade Reliability:** The agent implements a resilient `503` retry-loop with cascading model fallbacks to guarantee uptime during high-demand API spikes.

## Project Structure
- `agent.py`: The dynamic CLI tool for generating briefs via terminal.
- `api.py`: A lightning-fast FastAPI backend wrapper for the agent logic.
- `frontend/`: A premium React web application with dark-mode UI to interface with the agent.
- `data/`: Directory containing the test-case markdown documents.
- `system_prompt.txt`: The core instructions provided to the LLM to guide its behavior.
- `test_log.md`: Log of the iterations and testing process.
- `requirements.txt`: Python package dependencies.
- `.env.example`: Template file to store your API key locally (copy this to `.env` before running).

## How to Run Locally

### 1. Initial Setup
*   **Prerequisites**: Python 3.9+ and Node.js
*   **Setup Python Environment**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate      # Windows
    source venv/bin/activate    # Mac/Linux
    pip install -r requirements.txt
    ```
*   **Setup Node Environment**:
    ```bash
    cd frontend
    npm install
    ```
*   **API Key**: Copy `.env.example` to a new file named `.env`. Open `.env` and replace `your_gemini_api_key_here` with your actual Google Gemini API key.

---

### 2. Running the Web UI (Recommended)
You will need two terminal windows.
**Terminal 1 (Backend):**
```bash
# In the project root with your venv activated:
uvicorn api:app --reload
```
**Terminal 2 (Frontend):**
```bash
# In the frontend directory:
npm run dev
```
*Open `http://localhost:5173` in your browser to use the premium dashboard.*

---

### 3. Running via CLI
If you prefer the command line, run:
```bash
python agent.py
```
*By default, this will run the test case for SRVCABLE using the provided assessment documents located in the `data/` folder.*

**To run dynamically on a different ticker/directory:**
```bash
python agent.py --ticker "NSE: RELIANCE" --dir "./path/to/docs" --date "24 September 2026"
```

## Model Choice
I designed the agent to use **Gemini 3.8 Flash / Gemini Flash Latest**.
*   **Reasoning Capability:** The Flash model series excels at complex reasoning, instruction following, and anomaly detection required to bypass the traps in the documents.
*   **Speed & Context:** The massive context window easily accommodates the entire research pack, while generating outputs at unparalleled speeds.

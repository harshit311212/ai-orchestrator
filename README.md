# AI Orchestrator

A modular, web-based AI assistant built with Streamlit and Groq. This application acts as a central "brain" that orchestrates LLM-driven conversations and dynamically triggers external tools.

## How It Works
- **Frontend Layer:** A responsive chat interface built entirely in Python using Streamlit, featuring custom CSS styling and dual-panel outputs.
- **Orchestration Layer:** The primary backend loop (`orchestrator.py`) handles conversational memory and intelligently determines when an action needs to be taken.
- **Tool Execution:** Instead of fragile API wrappers, the LLM outputs strict JSON commands which the backend parses. This triggers standalone Python scripts, such as a Web Scraper, and feeds the live data back into the conversation.
- **LLM Engine:** Powered natively by Groq's insanely fast open-source inference models (e.g., LLaMA 3).

## Development Stack & Technologies Used
- **Language:** Python 3.x
- **UI Framework:** Streamlit (with custom CSS injection)
- **AI Inference Engine:** Groq API

## Core Dependencies
These packages drive the core execution of the app via `requirements.txt`:
1. `streamlit`: Powers the reactive User Interface components.
2. `groq`: The official Python SDK for interacting with Groq's high-speed language models.
3. `beautifulsoup4` & `requests`: Drive the backend website scraping tool to extract HTML over the network.
4. `python-dotenv`: Manages sensitive environment variables (API Keys).
5. `pydantic`: Provides underlying data structure validation.

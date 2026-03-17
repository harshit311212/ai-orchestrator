import json
import logging
from groq import Groq
import os
from dotenv import load_dotenv
from tools.scraper import scrape_website

load_dotenv()
logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def format_meeting_transcript(transcript: str, target_model: str) -> str:
    """
    Pipeline 1: Automated Meeting Analyst
    Takes raw transcript and extracts keys decisions, action items, and blockers.
    """
    prompt = f"""
    You are an expert meeting analyst. Please analyze the following meeting transcript.
    Extract the information and structure it into Markdown with the following sections:
    - Executive Summary
    - Key Decisions
    - Action Items (with assignees if mentioned)
    - Blockers/Risks

    Transcript:
    {transcript}
    """
    
    response = client.chat.completions.create(
        model=target_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content


def process_conversation(messages: list, target_model: str):
    """
    Core Conversation router and tool executor.
    Takes the conversation history and processes the latest message.
    """
    try:
        # Enforce strict JSON output for tools instead of relying on broken SDK wrappers
        system_instruction = {
            "role": "system",
            "content": "You are a helpful AI Orchestrator. If a user asks you to check a website or link, you MUST ONLY output the following exact JSON format and NOTHING ELSE: ```json\n{\"tool\": \"scrape_website\", \"url\": \"<their_url_here>\"}\n```. If they ask a normal question, answer normally without JSON."
        }
        
        # We only want to prepend this if it isn't already there (keeps history clean)
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, system_instruction)

        # First call to see if model wants to use a tool
        response = client.chat.completions.create(
            model=target_model,
            messages=messages
        )
        
        response_message = response.choices[0].message
        content = response_message.content or ""

        # Check if model outputted our requested JSON tool trigger
        if '"tool"' in content and '"scrape_website"' in content:
            # We must append the assistant's request so the chat history tracks
            messages.append({"role": "assistant", "content": content})
            
            # Robust extraction logic to find the JSON dictionary inside the string
            try:
                # Find the first { and last }
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                
                if start_idx == -1 or end_idx == -1:
                    raise ValueError("Could not locate JSON brackets in response.")
                    
                json_str = content[start_idx:end_idx+1]
                args = json.loads(json_str)
                url_to_scrape = args.get("url")
                
                if not url_to_scrape:
                    raise ValueError("No url provided in the parsed JSON")
                
                logger.info(f"LLM triggered scrape_website tool for URL: {url_to_scrape}")
                
                # Execute tool
                scraped_text = scrape_website(url_to_scrape)
                
                # Truncate if too long
                if len(scraped_text) > 20000:
                    scraped_text = scraped_text[:20000] + "... [Text truncated]"
                    
                # We feed it back as a user system injection to trick the model
                messages.append({
                    "role": "user",
                    "content": f"[SYSTEM TOOL EXECUTION] Scraped Web Data for {url_to_scrape}:\n\n{scraped_text}\n\nBased on this tool data, please fulfill the user's initial request."
                })

                # Second call to get final response
                second_response = client.chat.completions.create(
                    model=target_model,
                    messages=messages
                )
                
                final_content = second_response.choices[0].message.content
                messages.append({"role": "assistant", "content": final_content})
                # True signals to Streamlit to display the custom 'Tool Executed' badge
                return final_content, True 
                
            except Exception as e:
                logger.error(f"Failed to parse or execute custom JSON tool schema: {e}")
                messages.append({"role": "assistant", "content": f"I tried to use a tool, but encountered an error: {e}. Output was: {content}"})
                return f"I tried to use a tool, but encountered an error: {e}", False
            
        else:
            # No tool matched, just standard chat text
            messages.append({"role": "assistant", "content": content})
            return content, False
            
    except Exception as e:
        logger.error(f"Error in orchestrator: {e}")
        return f"An error occurred: {str(e)}", False

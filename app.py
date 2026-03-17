import streamlit as st
import os
import time
from orchestrator import process_conversation, format_meeting_transcript
from tools.audio_processor import transcribe_audio

# Must be called first
st.set_page_config(
    page_title="AI Orchestrator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "static", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def initialize_session():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to the Orchestrator Hub. I can browse the web or analyze your audio files. What would you like to do?"}
        ]
    if "structured_doc" not in st.session_state:
        st.session_state.structured_doc = None
    if "system_status" not in st.session_state:
        st.session_state.system_status = "Ready"

def main():
    load_css()
    initialize_session()

    # --- LEFT SIDEBAR (Control Panel) ---
    with st.sidebar:
        st.title("Control Panel")
        
        st.markdown("### Configuration")
        active_model = st.selectbox(
            "Active LLM",
            options=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            index=0,
            help="Select the reasoning engine."
        )

        st.markdown("### Upload Zones")
        audio_file = st.file_uploader("Upload Meeting Audio", type=["mp3", "wav", "m4a"])
        
        if audio_file:
            if st.button("Process Audio Pipeline"):
                st.session_state.system_status = "Transcribing..."
                
                # Save temp
                temp_audio_path = f"temp_{audio_file.name}"
                with open(temp_audio_path, "wb") as f:
                    f.write(audio_file.getbuffer())
                
                with st.spinner("Transcribing..."):
                    transcript = transcribe_audio(temp_audio_path)
                    
                    if "Error" not in transcript:
                        st.session_state.system_status = "Synthesizing..."
                        with st.spinner("Synthesizing Meeting Notes..."):
                            doc = format_meeting_transcript(transcript, active_model)
                            st.session_state.structured_doc = doc
                            st.session_state.system_status = "Document Ready"
                            
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": "I have successfully transcribed and analyzed your audio. The Meeting Analyst document is available in the canvas panel."
                            })
                    else:
                        st.error(transcript)
                        st.session_state.system_status = "Ready - Error"
                        
                # Cleanup
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)

        st.markdown("---")
        st.markdown(f"**System Status:** `{st.session_state.system_status}`")


    # --- MAIN LAYOUT (Chat Hub & Canvas) ---
    st.title("AI Orchestrator Studio ⚡")
    
    # We use columns: 60% chat, 40% canvas
    if st.session_state.structured_doc:
        col_chat, col_canvas = st.columns([6, 4])
    else:
        # If no doc, chat takes full width
        col_chat, col_canvas = st.columns([1, 0.001]) # small dummy column

    # Center Panel (Chat Hub)
    with col_chat:
        st.header("Conversational Hub")
        chat_container = st.container(height=600)
        
        with chat_container:
            for msg in st.session_state.messages:
                # Highlight tool logs slightly differently
                if msg["role"] == "tool":
                    with st.expander(f"🛠️ Extracted Context ({msg['name']})"):
                        st.markdown(f"<span class='tool-badge'>Scraped Web Data</span>\n\n{msg['content'][:1000]}...", unsafe_allow_html=True)
                elif msg["role"] != "system":
                    avatar = "👤" if msg["role"] == "user" else "🤖"
                    with st.chat_message(msg["role"], avatar=avatar):
                        st.markdown(msg["content"])
        
        # Chat input buffer
        prompt = st.chat_input("Enter your command (e.g., 'Scrape the URL https://example.com and summarize it')")
        
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(prompt)
                    
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Routing..."):
                        response_content, used_tool = process_conversation(
                            st.session_state.messages, 
                            active_model
                        )
                    
                    if used_tool:
                        st.markdown(f"<span class='tool-badge'>Executed Scraper Tool</span>", unsafe_allow_html=True)
                        time.sleep(0.5)
                        
                    st.markdown(response_content)
                    
            st.rerun()

    # Right Panel (The Canvas)
    if st.session_state.structured_doc:
        with col_canvas:
            st.header("The Canvas 📄")
            with st.container(height=600, border=True):
                st.markdown(st.session_state.structured_doc)
                
            st.download_button(
                label="⬇️ Download as Markdown",
                data=st.session_state.structured_doc,
                file_name="generated_document.md",
                mime="text/markdown"
            )

if __name__ == "__main__":
    main()

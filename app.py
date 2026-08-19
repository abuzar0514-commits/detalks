import streamlit as st
import re
from mistralai import Mistral
from deep_translator import GoogleTranslator

st.set_page_config(page_title="DeTalks: Immersion Tutor", page_icon="🇩🇪", layout="centered")

st.title("🇩🇪 DeTalks: German Immersion Tutor")

# Sidebar Configuration
st.sidebar.header("⚙️ Settings")
api_key = st.sidebar.text_input("Mistral API Key", type="password", help="Enter your key to start")
level = st.sidebar.selectbox("Language Level", ["Beginner", "Intermediate", "Advanced"])
mode = st.sidebar.selectbox("Hover Translation Mode", ["Word", "Sentence", "Both"])

if st.sidebar.button("🔄 Reset Chat"):
    st.session_state.messages = []
    st.rerun()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if not api_key:
    st.info("👈 Please enter your Mistral API Key in the sidebar to begin.")
    st.stop()

# Initialize Client
client = Mistral(api_key=api_key.strip())

@st.cache_data(show_spinner=False)
def translate_text(text, source="de", target="en"):
    try:
        return GoogleTranslator(source=source, target=target).translate(text)
    except Exception:
        return "Translation error"

def render_interactive_text(text, trans_mode):
    words = text.split()
    sentence_trans = translate_text(text) if trans_mode in ["Sentence", "Both"] else ""
    
    formatted_spans = []
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word)
        word_trans = translate_text(clean_word) if (trans_mode in ["Word", "Both"] and clean_word) else ""
        
        if trans_mode == "Word":
            tooltip = f"Word: {word_trans}"
        elif trans_mode == "Sentence":
            tooltip = f"Sentence: {sentence_trans}"
        else:
            tooltip = f"Word: {word_trans} | Sentence: {sentence_trans}"
            
        formatted_spans.append(
            f'<span title="{tooltip}" style="background-color: #e2e8f0; padding: 2px 5px; '
            f'border-radius: 4px; cursor: help; border-bottom: 1px dashed #4a5568;">{word}</span>'
        )
    return " ".join(formatted_spans)

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(render_interactive_text(msg["content"], mode), unsafe_allow_html=True)
        else:
            st.write(msg["content"])

# Start Conversation Trigger
if not st.session_state.messages:
    if st.button("🚀 Start Chat", type="primary"):
        prompt = f"Start a German conversation. Level: {level}. Use only German. Ask me one opening question."
        try:
            resp = client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "system", "content": "Speak ONLY German."}, {"role": "user", "content": prompt}]
            )
            ai_text = resp.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
            st.rerun()
        except Exception as e:
            st.error(f"API Error: {e}")

# Handle User Input
if user_input := st.chat_input("Senden Sie eine Nachricht..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    instr = f"Tutor ({level}). German only. Format: Korrektur: [Correction]. Antwort: [Response]."
    api_msgs = [{"role": "system", "content": instr}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]
    
    try:
        resp = client.chat.complete(model="mistral-small-latest", messages=api_msgs)
        ai_text = resp.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
        st.rerun()
    except Exception as e:
        st.error(f"API Error: {e}")

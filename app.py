import streamlit as st
import ollama as ol
from voice import record_voice
import datetime
import json

st.set_page_config(page_title="🎙️ Voice Bot", layout="wide")
st.sidebar.title("TEST DEMO")


def log_interaction(action, data):
    timestamp = datetime.datetime.now().isoformat()
    log = {"timestamp": timestamp, "action": action, "data": data}
    with open("user_interactions_log.json", "a") as logfile:
        logfile.write(json.dumps(log) + "\n")


def app_mode_selector():
    return st.sidebar.selectbox("Select Mode", ["语音识别", "文本纠错", "对话"])


def language_selector():
    lang_options = ["ar", "de", "en", "es", "fr", "it", "ja", "nl", "pl", "pt", "ru", "zh"]
    with st.sidebar:
        return st.selectbox("Speech Language", ["en"] + lang_options)


def llm_selector():
    ollama_models = [m['name'] for m in ol.list()['models']]
    with st.sidebar:
        return st.selectbox("LLM", ollama_models)


def system_prompt_input(default_prompt):
    return st.sidebar.text_area("System Prompt", value=default_prompt, height=100)


def print_txt(text):
    if any("\u0600" <= c <= "\u06FF" for c in text):  # check if text contains Arabic characters
        text = f"<p style='direction: rtl; text-align: right;'>{text}</p>"
    st.markdown(text, unsafe_allow_html=True)


def print_chat_message(message):
    text = message["content"]
    if message["role"] == "user":
        with st.chat_message("user", avatar="🎙️"):
            print_txt(text)
    elif message["role"] == "assistant":
        with st.chat_message("assistant", avatar="🦙"):
            print_txt(text)


def init_chat_history(key, system_prompt):
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    if key not in st.session_state.chat_history:
        st.session_state.chat_history[key] = [{"role": "system", "content": system_prompt}]


def get_chat_history(key):
    return st.session_state.chat_history[key]


def main():
    app_mode = app_mode_selector()  # Get the selected application mode
    title_mapping = {
        "语音识别": "🎙 语音识别",
        "文本纠错": "📝 文本纠错",
        "对话": "💬 对话模式"
    }
    st.title(title_mapping[app_mode])
    
    model = llm_selector()
    chat_key = f"{app_mode}_chat_history_{model}"  # Unique key for each mode and model
    default_prompt = {
        "语音识别": "你是一名语音识别助手，请把语音识别出的文字加上标点符号输出，不得改变原文。",
        "文本纠错": "你是一名文本纠错助手，请修改文本中的错别字并输出结果",
        "对话": "你是一位有用的助手"
    }[app_mode]
    
    system_prompt = system_prompt_input(default_prompt)
    init_chat_history(chat_key, system_prompt)
    chat_history = get_chat_history(chat_key)
    for message in chat_history:
        print_chat_message(message)
    
    question = None
    if app_mode == "语音识别":
        with st.sidebar:
            question = record_voice(language=language_selector())
    elif app_mode == "对话":
        question = st.chat_input()
    elif app_mode == "文本纠错":
        question = st.text_input("Enter text for correction")
    
    debug_mode = st.sidebar.checkbox("Debug Mode", value=True)
    log_interaction("User input", {"mode": app_mode, "question": question})
    
    # Processing the conversation
    if question:
        user_message = {"role": "user", "content": question}
        # if app_mode == "语音识别":
        print_chat_message(user_message)
        chat_history.append(user_message)
        response = ol.chat(model=model, messages=chat_history)
        answer = response['message']['content']
        ai_message = {"role": "assistant", "content": answer}
        print_chat_message(ai_message)
        chat_history.append(ai_message)
        debug_info = {"messages": chat_history, "response": response}
        
        if debug_mode:
            st.write("Debug Info: Complete Prompt Interaction")
            st.json(debug_info)
        
        # truncate chat history to keep 20 messages max
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
        
        # update chat history
        st.session_state.chat_history[chat_key] = chat_history


if __name__ == "__main__":
    main()

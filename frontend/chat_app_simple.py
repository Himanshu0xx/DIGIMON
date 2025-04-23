import streamlit as st
import base64

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Chat UI", layout="wide")

# ---------- HELPER FUNCTION ----------
def get_base64_image(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# ---------- LOAD IMAGES ----------
bg_base64 = get_base64_image("background.png")
girl_base64 = get_base64_image("girl.png")

# ---------- STYLING ----------
st.markdown(f"""
    <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bg_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        .girl-img {{
            position: fixed;
            bottom: 58px;
            left: 20px;
            width: 80px;
            z-index: 9999;
        }}
        .message {{
            padding: 10px 16px;
            border-radius: 20px;
            margin: 5px 10px;
            max-width: 70%;
            font-size: 15px;
            font-family: monospace;
            word-wrap: break-word;
            display: inline-block;
        }}
        .user-message {{
            background-color: #0077cc;
            color: white;
            margin-left: auto;
            text-align: right;
            border-bottom-right-radius: 5px;
        }}
        .bot-message {{
            background-color: #f1f1f1;
            color: black;
            margin-right: auto;
            text-align: left;
            border-bottom-left-radius: 5px;
        }}
        section[data-testid="stChatInput"] {{
            background-color: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            height: auto !important;
        }}
        section[data-testid="stChatInput"] > div:first-child {{
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            height: auto !important;
        }}
        div[data-testid="stChatInput"] textarea {{
            min-height: 36px !important;
            height: 36px !important;
            padding: 6px 12px !important;
            font-size: 14px;
            border-radius: 20px;
            background-color: #1e1e1e;
            color: white;
            border: 1px solid #444;
        }}
        #MainMenu, header, footer {{
            visibility: hidden;
        }}
    </style>
    <img src="data:image/png;base64,{girl_base64}" class="girl-img">
""", unsafe_allow_html=True)

# ---------- CHAT STATE ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------- SIMPLE BOT REPLY FUNCTION ----------
def simple_bot_reply(message):
    # Simple responses based on message
    if "hello" in message.lower():
        return "Hello! How can I assist you today?"
    elif "how are you" in message.lower():
        return "I'm doing great, thank you! How about you?"
    elif "bye" in message.lower():
        return "Goodbye! Have a great day!"
    else:
        return "Sorry, I didn't understand that. Can you please rephrase?"

# ---------- DISPLAY MESSAGES ----------
for chat in st.session_state.chat_history:
    role = chat["role"]
    css_class = "user-message" if role == "user" else "bot-message"
    st.markdown(f"<div class='message {css_class}'>{chat['message']}</div>", unsafe_allow_html=True)

# ---------- CHAT INPUT ----------
user_input = st.chat_input("Type your message...")

# ---------- ON SUBMIT ----------
if user_input:
    st.session_state.chat_history.append({"role": "user", "message": user_input})
    reply = simple_bot_reply(user_input)
    st.session_state.chat_history.append({"role": "bot", "message": reply})

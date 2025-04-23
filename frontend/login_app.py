# login_app.py
import streamlit as st
import base64
import os
import time

# --- Page Configuration ---
st.set_page_config(page_title="FundMate Login", page_icon="🌐")

# --- Define the URL of your second Streamlit app ---
# !!! IMPORTANT: CHANGE THIS URL to where your second app (chat_app_simple.py) will run !!!
SECOND_APP_URL = "http://localhost:8502" # Example port for the second app

# --- Helper Functions ---
def load_logo_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        st.error(f"Logo file not found at: {path}")
        return None

def get_base64_gif(path):
    try:
        with open(path, "rb") as f:
            gif_data = f.read()
        return base64.b64encode(gif_data).decode()
    except FileNotFoundError:
        st.error(f"GIF file not found at: {path}")
        return None

# --- Add FundMate Logo ---
# Assumes logo is in the same folder as script. Adjust path if needed.
logo_path = "FundMate Landscape.png"
if os.path.exists(logo_path):
    logo_b64 = load_logo_base64(logo_path)
    if logo_b64:
        st.markdown(
            f"""
            <style>
                .top-right-logo {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    width: 180px; /* Adjust size as needed */
                    z-index: 100;
                }}
            </style>
            <img src="data:image/png;base64,{logo_b64}" class="top-right-logo">
            """,
            unsafe_allow_html=True
        )
else:
    st.warning(f"Logo image not found at expected path: {logo_path}")


# --- Define GIF path ---
# Assumes GIF is in the same folder. Adjust path if needed.
gif_path = "Add_a_subheading.gif"

# --- Helper function to perform redirection ---
def redirect_to_app(url):
    """Injects JavaScript to redirect the browser."""
    st.markdown(f"""
        <meta http-equiv="refresh" content="0; url={url}">
        <script type="text/javascript">
            window.location.href = "{url}";
        </script>
        <p>Redirecting... If you are not redirected automatically, <a href="{url}">click here</a>.</p>
    """, unsafe_allow_html=True)
    time.sleep(0.5) # Small delay
    st.stop() # Stop script execution

# --- Main Layout ---
st.title("Welcome to FundMate!")
st.markdown("---")

col1, col2 = st.columns([1, 1]) # Adjust ratio if needed

with col1:
    if os.path.exists(gif_path):
        b64_gif = get_base64_gif(gif_path)
        if b64_gif:
            st.markdown(
                f"""
                <div style="text-align: center; max-width: 450px; margin: auto;">
                    <img src="data:image/gif;base64,{b64_gif}" width="100%"/>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.error(f"GIF not found at: {gif_path}")

with col2:
    mode = st.radio(
        "Choose an action:",
        ('Login', 'Sign Up'),
        horizontal=True,
        label_visibility='collapsed'
    )
    st.markdown("---")

    if mode == 'Login':
        st.subheader("Login")
        with st.form("login_form"):
            login_email = st.text_input("Email", placeholder="your@email.com")
            login_password = st.text_input("Password", type="password", placeholder="your password")
            login_submitted = st.form_submit_button("Login", use_container_width=True)

            if login_submitted:
                # Redirect immediately without validation
                st.info("Proceeding... Redirecting...")
                redirect_to_app(SECOND_APP_URL)

    elif mode == 'Sign Up':
        st.subheader("Create Account")
        with st.form("signup_form"):
            signup_email = st.text_input("Email", placeholder="you@example.com")
            signup_password = st.text_input("Choose Password", type="password", placeholder="********")
            signup_confirm_password = st.text_input("Confirm Password", type="password", placeholder="********")
            signup_submitted = st.form_submit_button("Sign Up", use_container_width=True)

            if signup_submitted:
                 # Redirect immediately without validation
                st.info("Proceeding... Redirecting...")
                redirect_to_app('http://192.168.1.9:8501')

# Footer
st.markdown("---")
st.caption("© 2025 FundMate.co")
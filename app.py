import streamlit as st
from openai import OpenAI
import base64
import os
import time
import stripe
import sqlite3
import hashlib

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Bisma.Ai", layout="wide")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    is_pro INTEGER DEFAULT 0
)
""")
conn.commit()

# ---------------- HELPERS ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "videos" not in st.session_state:
    st.session_state.videos = []

if "is_pro" not in st.session_state:
    st.session_state.is_pro = False

if "show_login" not in st.session_state:
    st.session_state.show_login = False

# ---------------- PAYMENT SUCCESS ----------------
params = st.query_params
if "user" in params:
    username = params["user"]
    c.execute("UPDATE users SET is_pro=1 WHERE username=?", (username,))
    conn.commit()
    st.session_state.is_pro = True

# ---------------- PREMIUM UI ----------------
st.markdown("""
<style>
body { background-color: #0f172a; }

section[data-testid="stSidebar"] {
    background-color: #020617;
    border-right: 1px solid #1e293b;
}

[data-testid="stChatMessage"] {
    background-color: #111827;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 10px;
}

.stButton>button {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: white;
    border-radius: 12px;
    height: 3em;
    border: none;
}

.stTextInput input {
    background-color: #020617;
    color: white;
}

h1, h2, h3 {
    color: #22c55e;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LANDING ----------------
def landing_page():
    st.title("🌱 Bisma.Ai")
    st.subheader("Create. Imagine. Automate.")

    col1, col2, col3 = st.columns(3)
    col1.info("💬 AI Chat")
    col2.info("🎨 Image Generator")
    col3.info("🎬 Video Creator (Pro)")

    if st.button("Get Started"):
        st.session_state.show_login = True

# ---------------- LOGIN ----------------
def login_signup():
    st.title("🔐 Login / Sign Up")

    choice = st.radio("Choose", ["Login", "Sign Up"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if choice == "Sign Up":
        if st.button("Create Account"):
            try:
                c.execute(
                    "INSERT INTO users VALUES (?, ?, 0)",
                    (username, hash_password(password))
                )
                conn.commit()
                st.success("Account created!")
            except:
                st.error("User exists")

    if choice == "Login":
        if st.button("Login"):
            c.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, hash_password(password))
            )
            user = c.fetchone()

            if user:
                st.session_state.user = username
                st.session_state.is_pro = bool(user[2])
                st.success("Welcome!")
                st.rerun()
            else:
                st.error("Invalid login")

# ---------------- LOGOUT ----------------
def logout():
    st.session_state.user = None
    st.session_state.is_pro = False
    st.rerun()

# ---------------- STRIPE ----------------
def create_checkout_session(username):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": os.getenv("STRIPE_PRICE_ID"),
            "quantity": 1,
        }],
        mode="subscription",
        success_url=f"https://bisma-ai.onrender.com/?user={username}",
        cancel_url="https://bisma-ai.onrender.com/",
    )
    return session.url

# ---------------- MAIN APP ----------------
def main_app():

    st.title("🌱 Bisma.Ai")

    # Sidebar
    st.sidebar.write(f"👤 {st.session_state.user}")

    if st.session_state.is_pro:
        st.sidebar.success("💎 Pro")
    else:
        st.sidebar.warning("Free Plan")

    if st.sidebar.button("Logout"):
        logout()

    # Payment
    if st.sidebar.button("Upgrade to Pro"):
        url = create_checkout_session(st.session_state.user)
        st.sidebar.markdown(f"[👉 Pay here]({url})")

    tool = st.sidebar.selectbox(
        "Tool",
        ["Chatbot", "Image Generator", "Image → Video"]
    )

    # ---------------- CHAT ----------------
    if tool == "Chatbot":

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        user_input = st.chat_input("Ask anything...")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages
            )

            reply = response.choices[0].message.content

            placeholder = st.chat_message("assistant")
            full = ""

            for word in reply.split():
                full += word + " "
                time.sleep(0.02)
                placeholder.write(full)

            st.session_state.messages.append({"role": "assistant", "content": reply})

        if st.button("Clear Chat"):
            st.session_state.messages = []

    # ---------------- IMAGE ----------------
    elif tool == "Image Generator":

        prompt = st.text_input("Describe image")

        if st.button("Generate"):
            if prompt:
                result = client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt,
                    size="1024x1024"
                )

                image = base64.b64decode(result.data[0].b64_json)
                st.image(image)

    # ---------------- VIDEO ----------------
    elif tool == "Image → Video":

        if not st.session_state.is_pro:
            st.warning("🔒 Pro only")

            if st.button("Upgrade"):
                url = create_checkout_session(st.session_state.user)
                st.markdown(f"[👉 Pay here]({url})")

            st.stop()

        uploaded = st.file_uploader("Upload image", type=["png", "jpg"])

        if uploaded:
            st.image(uploaded)

        if st.button("Generate Video"):
            if uploaded:
                with st.spinner("Generating..."):
                    progress = st.progress(0)
                    for i in range(100):
                        time.sleep(0.02)
                        progress.progress(i + 1)

                demo = "https://www.w3schools.com/html/mov_bbb.mp4"
                st.session_state.videos.append(demo)

                st.video(demo)

                st.download_button(
                    "Download",
                    data=b"demo",
                    file_name="video.mp4"
                )

    # Gallery
    if st.session_state.videos:
        st.subheader("🎬 Gallery")
        for v in st.session_state.videos[::-1]:
            st.video(v)

# ---------------- ROUTER ----------------
if not st.session_state.user:
    if not st.session_state.show_login:
        landing_page()
    else:
        login_signup()
else:
    main_app()
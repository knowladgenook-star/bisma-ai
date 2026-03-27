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

# ---------------- STYLE ----------------
st.markdown("""
<style>
body { background-color: #0e1117; }
section[data-testid="stSidebar"] { background-color: #111827; }
.stButton>button {
    background-color: #10b981;
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
}
h1 { color: #10b981; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ---------------- LANDING PAGE ----------------
def landing_page():
    st.markdown("""
    <h1 style='text-align:center;'>🌱 Bisma.Ai</h1>
    <h3 style='text-align:center;'>Create. Imagine. Automate.</h3>
    """, unsafe_allow_html=True)

    st.write("")

    col1, col2, col3 = st.columns(3)

    col1.info("💬 AI Chat")
    col2.info("🎨 Image Generator")
    col3.info("🎬 Video Creator (Pro)")

    st.write("")

    if st.button("Get Started"):
        st.session_state.show_login = True

# ---------------- LOGIN + SIGNUP ----------------
def login_signup():

    st.title("🔐 Login / Sign Up")

    menu = st.radio("Choose", ["Login", "Sign Up"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if menu == "Sign Up":
        if st.button("Create Account"):
            hashed = hash_password(password)

            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
                conn.commit()
                st.success("Account created! Please login.")
            except:
                st.error("User already exists")

    elif menu == "Login":
        if st.button("Login"):
            hashed = hash_password(password)

            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed))
            user = c.fetchone()

            if user:
                st.session_state.user = username
                st.session_state.is_pro = bool(user[2])
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")

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
    st.caption("Empowering ideas. Creating the future with AI.")

    # Sidebar
    st.sidebar.write(f"👤 {st.session_state.user}")

    if st.session_state.is_pro:
        st.sidebar.success("💎 Pro User")
    else:
        st.sidebar.warning("Free Plan")

    if st.sidebar.button("Logout"):
        logout()

    # Payment
    st.sidebar.markdown("## 💎 Upgrade")

    if st.sidebar.button("Upgrade to Pro"):
        url = create_checkout_session(st.session_state.user)
        st.sidebar.markdown(f"[👉 Pay here]({url})")

    tool = st.sidebar.selectbox(
        "Choose Tool",
        ["Chatbot", "Image Generator", "Image → Video"]
    )

    # ---------------- CHAT ----------------
    if tool == "Chatbot":
        st.subheader("💬 Chat")

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

            st.chat_message("assistant").write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

        if st.button("🗑 Clear Chat"):
            st.session_state.messages = []
            st.rerun()

    # ---------------- IMAGE ----------------
    elif tool == "Image Generator":
        st.subheader("🎨 Image Generator")

        prompt = st.text_input("Describe your image")

        if st.button("Generate Image"):
            if prompt:
                result = client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt,
                    size="1024x1024"
                )

                image = base64.b64decode(result.data[0].b64_json)
                st.image(image)
            else:
                st.warning("Enter prompt")

    # ---------------- VIDEO ----------------
    elif tool == "Image → Video":

        if not st.session_state.is_pro:
            st.warning("🔒 Pro feature only")

            if st.button("Upgrade to Pro"):
                url = create_checkout_session(st.session_state.user)
                st.markdown(f"[👉 Pay here]({url})")

            st.stop()

        st.subheader("🎬 Image to Video")

        uploaded_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
        prompt = st.text_input("Describe motion")

        if uploaded_file:
            st.image(uploaded_file)

        if st.button("Generate Video"):
            if uploaded_file:

                with st.spinner("Creating video..."):
                    progress = st.progress(0)

                    for i in range(100):
                        time.sleep(0.03)
                        progress.progress(i + 1)

                demo_video = "https://www.w3schools.com/html/mov_bbb.mp4"

                st.session_state.videos.append(demo_video)

                st.video(demo_video)

                st.download_button(
                    "Download Video",
                    data=b"demo",
                    file_name="video.mp4"
                )

    # ---------------- GALLERY ----------------
    if st.session_state.videos:
        st.markdown("## 🎬 Video Gallery")

        for v in reversed(st.session_state.videos):
            st.video(v)

# ---------------- ROUTER ----------------
if not st.session_state.user:
    if not st.session_state.show_login:
        landing_page()
    else:
        login_signup()
else:
    main_app()
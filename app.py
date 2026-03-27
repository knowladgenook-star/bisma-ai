import streamlit as st
from openai import OpenAI
import base64
import os
import time
import stripe

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Bisma.Ai", layout="wide")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "videos" not in st.session_state:
    st.session_state.videos = []

if "is_pro" not in st.session_state:
    st.session_state.is_pro = False

# ---------------- PAYMENT SUCCESS DETECTION ----------------
query_params = st.query_params

if "success" in query_params:
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

# ---------------- LOGIN ----------------
def login():
    st.title("🔐 Login to Bisma.Ai")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state.user = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

# ---------------- LOGOUT ----------------
def logout():
    st.session_state.user = None
    st.rerun()

# ---------------- STRIPE ----------------
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": os.getenv("STRIPE_PRICE_ID"),
                "quantity": 1,
            }],
            mode="subscription",
            success_url="https://bisma-ai.onrender.com/?success=true",
            cancel_url="https://bisma-ai.onrender.com/?canceled=true",
        )
        return session.url
    except Exception as e:
        return str(e)

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

    # 💳 PAYMENT BUTTON
    st.sidebar.markdown("## 💎 Upgrade")

    if st.sidebar.button("Upgrade to Pro"):
        checkout_url = create_checkout_session()
        st.sidebar.markdown(f"[👉 Click here to pay]({checkout_url})")

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

    # ---------------- IMAGE GENERATOR ----------------
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
                st.warning("Please enter a prompt")

    # ---------------- IMAGE → VIDEO (LOCKED FEATURE) ----------------
    elif tool == "Image → Video":

        # 🔒 LOCK FOR FREE USERS
        if not st.session_state.is_pro:
            st.subheader("🎬 Image to Video 🔒")

            st.warning("This feature is available for Pro users only")

            if st.button("Upgrade to Pro"):
                checkout_url = create_checkout_session()
                st.markdown(f"[👉 Click here to pay]({checkout_url})")

            st.stop()

        # ✅ PRO USERS ACCESS
        st.subheader("🎬 Image to Video")

        uploaded_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
        prompt = st.text_input("Describe motion")

        if uploaded_file:
            st.image(uploaded_file, caption="Preview", use_container_width=True)

        if st.button("Generate Video"):
            if uploaded_file:

                # Demo generation (stable)
                with st.spinner("Generating cinematic video... 🎥"):
                    progress = st.progress(0)

                    for i in range(100):
                        time.sleep(0.03)
                        progress.progress(i + 1)

                demo_video = "https://www.w3schools.com/html/mov_bbb.mp4"

                st.session_state.videos.append(demo_video)

                st.video(demo_video)
                st.success("✅ Video ready!")

                st.download_button(
                    "📥 Download Video",
                    data=b"demo",
                    file_name="bisma_video.mp4"
                )

            else:
                st.warning("Please upload an image!")

        # ---------------- VIDEO GALLERY ----------------
        if st.session_state.videos:
            st.markdown("## 🎬 Video Gallery")

            for vid in reversed(st.session_state.videos):
                st.video(vid)

            if st.button("🗑 Clear Gallery"):
                st.session_state.videos = []
                st.rerun()

# ---------------- ROUTER ----------------
if st.session_state.user:
    main_app()
else:
    login()
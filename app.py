import streamlit as st
from openai import OpenAI
import base64
import os
import requests
import time

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Bisma.Ai", layout="wide")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- SESSION INIT ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "videos" not in st.session_state:
    st.session_state.videos = []

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

# ---------------- LOGIN SYSTEM ----------------
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

# ---------------- MAIN APP ----------------
def main_app():

    # HEADER
    st.title("🌱 Bisma.Ai")
    st.caption("Empowering ideas. Creating the future with AI.")

    # SIDEBAR
    st.sidebar.write(f"👤 Logged in as: {st.session_state.user}")
    if st.sidebar.button("Logout"):
        logout()

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

    # ---------------- VIDEO ----------------
    elif tool == "Image → Video":
        st.subheader("🎬 Image to Video")

        uploaded_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
        prompt = st.text_input("Describe motion")

        if st.button("Generate Video"):
            if uploaded_file:

                api_token = os.getenv("REPLICATE_API_TOKEN")

                files = {
                    "file": (uploaded_file.name, uploaded_file.read(), uploaded_file.type)
                }

                upload = requests.post(
                    "https://api.replicate.com/v1/files",
                    headers={"Authorization": f"Token {api_token}"},
                    files=files
                )

                file_url = upload.json()["urls"]["get"]

                headers = {
                    "Authorization": f"Token {api_token}",
                    "Content-Type": "application/json"
                }

                data = {
                    "version": "7836b0c54b5f3a4f0b9b51d6d5d9c0c1f1a6d5c7a6d4f8c1b0a5c6d7e8f9g0",
                    "input": {
                        "image": file_url,
                        "prompt": prompt if prompt else "cinematic motion"
                    }
                }

                prediction = requests.post(
                    "https://api.replicate.com/v1/predictions",
                    headers=headers,
                    json=data
                ).json()

                status_url = prediction["urls"]["get"]

                with st.spinner("Generating video..."):
                    while True:
                        result = requests.get(status_url, headers=headers).json()

                        if result["status"] == "succeeded":
                            video_url = result["output"]

                            st.session_state.videos.append(video_url)

                            st.video(video_url)

                            video_bytes = requests.get(video_url).content

                            st.download_button(
                                "📥 Download",
                                data=video_bytes,
                                file_name="video.mp4"
                            )

                            break

                        elif result["status"] == "failed":
                            st.error("Failed")
                            break

                        time.sleep(3)

        # GALLERY
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
import streamlit as st
from openai import OpenAI
import base64
import os
import requests
import time

# ---------------- API CLIENT ----------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Bisma.Ai", layout="wide")

# ---------------- CUSTOM STYLING ----------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
}

.block-container {
    padding-top: 2rem;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

.stButton>button {
    background-color: #10b981;
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-weight: bold;
}

.stTextInput>div>div>input {
    border-radius: 10px;
}

[data-testid="stChatMessage"] {
    background-color: #1f2937;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
}

h1, h2, h3 {
    color: #10b981;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<h1 style='text-align: center;'>🌱 Bisma.Ai</h1>
<p style='text-align: center; color: gray;'>
Empowering ideas. Creating the future with AI.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ---------------- SIDEBAR ----------------
st.sidebar.title("🌱 Bisma.Ai")

tool = st.sidebar.selectbox(
    "Choose Tool",
    ["Chatbot", "Image Generator", "Image → Video"]
)

# ---------------- CHATBOT ----------------
if tool == "Chatbot":
    st.subheader("💬 AI Chat Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

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


# ---------------- IMAGE GENERATOR ----------------
elif tool == "Image Generator":
    st.subheader("🎨 AI Image Generator")

    prompt = st.text_input("Describe your image")

    if st.button("Generate Image"):
        if prompt:
            result = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024"
            )

            image_base64 = result.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)

            st.image(image_bytes, use_container_width=True)
        else:
            st.warning("Please enter a prompt!")


# ---------------- IMAGE → VIDEO ----------------
elif tool == "Image → Video":
    st.subheader("🎬 Image to Video Generator")

    image_url = st.text_input("Enter Image URL")

    if st.button("Generate Video"):
        if image_url:

            api_token = os.getenv("REPLICATE_API_TOKEN")

            headers = {
                "Authorization": f"Token {api_token}",
                "Content-Type": "application/json"
            }

            data = {
                "version": "7836b0c54b5f3a4f0b9b51d6d5d9c0c1f1a6d5c7a6d4f8c1b0a5c6d7e8f9g0",
                "input": {
                    "image": image_url
                }
            }

            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers=headers,
                json=data
            )

            prediction = response.json()

            if "urls" not in prediction:
                st.error("Error starting video generation")
            else:
                status_url = prediction["urls"]["get"]

                with st.spinner("Generating video... please wait ⏳"):
                    while True:
                        result = requests.get(status_url, headers=headers).json()

                        if result["status"] == "succeeded":
                            video_url = result["output"]
                            st.video(video_url)
                            break

                        elif result["status"] == "failed":
                            st.error("Video generation failed")
                            break

                        time.sleep(3)
        else:
            st.warning("Please enter an image URL")

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("© 2026 Bisma.Ai — Built with AI")
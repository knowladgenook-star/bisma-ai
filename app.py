import streamlit as st
from openai import OpenAI
import base64
import os

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Page config
st.set_page_config(page_title="Bisma.Ai", layout="wide")

# ---------------- HEADER ----------------
st.title("🌱 Bisma.Ai")
st.subheader("Empowering ideas. Creating the future with AI.")
st.write("Welcome to Bisma.Ai — your all-in-one AI assistant for creativity, productivity, and innovation.")

st.markdown("---")

# ---------------- SIDEBAR ----------------
st.sidebar.title("🌱 Bisma.Ai")

tool = st.sidebar.selectbox(
    "Choose Tool",
    ["Chatbot", "Image Generator"]
)

# ---------------- CHATBOT ----------------
if tool == "Chatbot":
    st.subheader("💬 AI Chat Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show chat history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # User input
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

            # Decode base64 image
            image_base64 = result.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)

            st.image(image_bytes)
        else:
            st.warning("Please enter a prompt!")

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("© 2026 Bisma.Ai — Built with AI")
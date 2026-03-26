import streamlit as st
from openai import OpenAI
import base64
import os

# Add your API key here
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
st.set_page_config(page_title="Bisma.Ai", layout="wide")

st.title("🌱 Bisma.Ai")
st.subheader("Empowering ideas. Creating the future with AI.")
st.write("Welcome to Bisma.Ai — your all-in-one AI assistant for creativity, productivity, and innovation.")

# Sidebar
tool = st.sidebar.selectbox(
    "Choose Tool",
    ["Chat", "Image Generator"]
)

# ---------------- CHAT ----------------
if tool == "Chat":

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Input box
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

    prompt = st.text_input("Describe your image")

    if st.button("Generate Image"):
        if prompt:
            result = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024"
            )

            # FIX: decode base64 image
            image_base64 = result.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)

            st.image(image_bytes)
        else:
            st.warning("Please enter a prompt!")
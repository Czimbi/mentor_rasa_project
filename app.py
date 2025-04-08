import streamlit as st
import requests
from streamlit_chat import message

# Set the title of your Streamlit app
st.title("Rasa Chatbot")
bot_msg = 0
human_msg = 0
# Function to send the user message to the Rasa REST endpoint and retrieve the response
def get_bot_response(user_input):
    url = "http://localhost:5005/webhooks/rest/webhook"  # Adjust if your Rasa server URL is different
    payload = {"sender": "streamlit_user", "message": user_input}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        responses = response.json()
        # Combine responses if there are multiple messages from Rasa
        bot_message = "\n".join([r["text"] for r in responses if "text" in r])
        return bot_message
    else:
        return f"Error: {response.status_code}"

# Initialize session state to store conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_value" not in st.session_state:
    st.session_state.input_value = ""

# Create a container for the chat history
chat_container = st.container()

# Display conversation history using streamlit-chat's message component
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "bot":
            message(msg["content"], is_user=False, key=f"bot_{bot_msg}")
            bot_msg += 1
        else:
            message(msg["content"], is_user=True, key=f"user_{human_msg}")
            human_msg += 1

# Create a form for the input and send button
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", value=st.session_state.input_value, key="input", placeholder="Type your message here...", on_change=None)
    col1, col2 = st.columns([1, 1])
    with col1:
        send_button = st.form_submit_button("Send", use_container_width=True)
    with col2:
        clear_button = st.form_submit_button("Clear", use_container_width=True)

# Handle form submissions
if clear_button:
    st.session_state.messages = []
    st.session_state.input_value = ""
    st.rerun()
elif send_button and user_input:
    # Append user's message
    st.session_state.messages.append({"role": "user", "content": user_input})
    # Get bot response and append it
    bot_response = get_bot_response(user_input)
    st.session_state.messages.append({"role": "bot", "content": bot_response})
    # Clear the input value
    st.session_state.input_value = ""
    st.rerun()

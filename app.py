import streamlit as st
from google import genai
from google.genai import types
import smtplib
from email.mime.text import MIMEText

from prompts import SYSTEM_PROMPT


st.set_page_config(
    page_title="Snap & Study",
    page_icon="📚",
    layout="centered"
)


GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

MODEL_NAME = "gemini-3.5-flash-lite"


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


def ask_gemini(parts):
    try:
        response = st.session_state.chat.send_message(parts)
        return response.text

    except Exception as error:
        return f"Sorry, something went wrong: {error}"


def send_email(to_address, subject, body):

    gmail_address = st.secrets["GMAIL_ADDRESS"]
    gmail_app_password = st.secrets["GMAIL_APP_PASSWORD"]

    message = MIMEText(body)

    message["Subject"] = subject
    message["From"] = gmail_address
    message["To"] = to_address

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_app_password)
        server.send_message(message)


def add_message(role, kind, content):

    st.session_state.messages.append({
        "role": role,
        "kind": kind,
        "content": content
    })


def render_message(message):

    with st.chat_message(message["role"]):

        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


if "onboarded" not in st.session_state:
    st.session_state.onboarded = False


if not st.session_state.onboarded:

    st.title("📚 Snap & Study")

    st.subheader(
        "Snap it. Understand it. Study it. 🚀"
    )

    st.write(
        "Upload a photo of a question, diagram, or notes "
        "and let AI explain it in simple language."
    )

    with st.form("onboarding_form"):

        name = st.text_input("Your name")

        email = st.text_input(
            "Your email address",
            placeholder="student@gmail.com"
        )

        submitted = st.form_submit_button(
            "Let's Study 🚀"
        )

        if submitted:

            if not name.strip() or not email.strip():

                st.warning(
                    "Please enter your name and email."
                )

            else:

                st.session_state.name = name.strip()
                st.session_state.email = email.strip()

                st.session_state.chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    )
                )

                st.session_state.messages = []

                st.session_state.onboarded = True

                st.rerun()

    st.stop()


st.title("📚 Snap & Study")

st.write(
    f"Welcome, {st.session_state.name}! 👋"
)

st.info(
    "📸 Upload a question, diagram or notes, "
    "or type your question below."
)


# Display previous messages

for message in st.session_state.messages:
    render_message(message)


# Chat input

user_input = st.chat_input(
    "Ask a question, or attach a photo 📸",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"]
)


if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []

    if photo is not None:

        photo_bytes = photo.getvalue()

        add_message(
            "user",
            "image",
            photo_bytes
        )

        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type
            )
        )

    if text:

        add_message(
            "user",
            "text",
            text
        )

        parts.append(text)

    elif photo is not None:

        parts.append(
            "Explain this question, diagram, "
            "or study material in simple language."
        )

    with st.spinner(
        "🤖 Understanding your question..."
    ):

        answer = ask_gemini(parts)

    add_message(
        "assistant",
        "text",
        answer
    )

    st.rerun()


# Email section

st.divider()

st.subheader("📧 Save Your Study Summary")


if st.button(
    "📧 Send Study Summary to Email",
    use_container_width=True
):

    if len(st.session_state.messages) == 0:

        st.warning(
            "Please ask at least one question first."
        )

    else:

        with st.spinner(
            "Preparing your study summary..."
        ):

            summary = ask_gemini([
                """
                Summarize the important explanations and
                answers from our conversation into one
                email-friendly study message.

                Include the main concepts, important points,
                and useful steps to remember.

                Keep it simple and easy to read.
                Use plain text.
                """
            ])


        try:

            send_email(
                st.session_state.email,
                "Snap & Study - Your Study Summary",
                summary
            )

            st.success(
                "Study summary sent successfully! 📧"
            )

        except Exception as error:

            st.error(
                f"Could not send email: {error}"
            )
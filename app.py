import streamlit as st

st.set_page_config(
    page_title="SmartClass Response",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 SmartClass Response")
st.subheader("Interactive Classroom Discussion System")

st.success("Stage 1 is working successfully!")

st.write(
    "This application will allow instructors to create classroom "
    "questions and students to respond using a QR code."
)

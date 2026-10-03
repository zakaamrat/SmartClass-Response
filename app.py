import streamlit as st
import qrcode
import io
import secrets
import string
from datetime import datetime

# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="SmartClass Response",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# RESPONSIVE DESIGN
# =========================================================

st.markdown("""
<style>

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.main-title {
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 800;
    text-align: center;
}

.subtitle {
    text-align: center;
    color: #667085;
    font-size: 1.1rem;
    margin-bottom: 30px;
}

.info-card {
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #e6e8ec;
    background: white;
    margin-bottom: 15px;
}

.session-code {
    font-size: 28px;
    font-weight: 800;
    text-align: center;
    padding: 15px;
    border-radius: 15px;
    background: #f2f6ff;
}

.stButton > button {
    width: 100%;
    min-height: 48px;
    border-radius: 12px;
    font-weight: 700;
}

@media (max-width: 600px) {

    .block-container {
        padding: 1rem;
    }

    .info-card {
        padding: 15px;
    }

}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "activity" not in st.session_state:
    st.session_state.activity = None


# =========================================================
# FUNCTIONS
# =========================================================

def create_session_code(length=6):

    characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    return "".join(
        secrets.choice(characters)
        for _ in range(length)
    )


def create_qr(url):

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(url)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    return buffer.getvalue()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="main-title">
        🎓 SmartClass Response
    </div>

    <div class="subtitle">
        Interactive Classroom Discussion System
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# INSTRUCTOR LOGIN
# =========================================================

if not st.session_state.authenticated:

    left, middle, right = st.columns([1, 2, 1])

    with middle:

        st.subheader("👨‍🏫 Instructor Login")

        st.write(
            "Login to create a classroom activity."
        )

        password = st.text_input(
            "Instructor Password",
            type="password"
        )

        if st.button(
            "Login",
            type="primary"
        ):

            if password == st.secrets["INSTRUCTOR_PASSWORD"]:

                st.session_state.authenticated = True

                st.rerun()

            else:

                st.error(
                    "Incorrect instructor password."
                )

    st.stop()


# =========================================================
# INSTRUCTOR AREA
# =========================================================

top1, top2 = st.columns([5, 1])

with top1:

    st.subheader(
        "👨‍🏫 Instructor Dashboard"
    )

with top2:

    if st.button("Logout"):

        st.session_state.authenticated = False
        st.session_state.activity = None

        st.rerun()


st.divider()


# =========================================================
# CREATE ACTIVITY
# =========================================================

if st.session_state.activity is None:

    st.header(
        "➕ Create Classroom Activity"
    )

    st.write(
        "Select the course and semester, "
        "then enter your classroom question."
    )

    # -----------------------------------------
    # COURSE LIST
    # -----------------------------------------

    courses = [

        "Computer System Internals and Linux",

        "Object-Oriented Programming Languages",

        "Database Systems",

        "Information Systems and Retrieval",

        "Dependable Software Engineering",

        "Other"
    ]

    semesters = [

        "Semester 1 - 2026/2027",

        "Semester 2 - 2026/2027",

        "Summer - 2026/2027"
    ]

    with st.form("activity_form"):

        col1, col2 = st.columns(2)

        with col1:

            course = st.selectbox(
                "Course",
                courses
            )

        with col2:

            semester = st.selectbox(
                "Semester",
                semesters
            )


        # -----------------------------------------
        # OTHER COURSE
        # -----------------------------------------

        custom_course = ""

        if course == "Other":

            custom_course = st.text_input(
                "Enter Course Title"
            )


        activity_title = st.text_input(
            "Activity Title",
            placeholder=
            "Example: Linux Security Discussion"
        )


        question = st.text_area(
            "Question / Discussion Task",
            placeholder=
            "Enter the question students should discuss...",
            height=160
        )


        instructions = st.text_area(
            "Instructions (optional)",
            placeholder=
            "Example: Explain your answer and give one example.",
            height=90
        )


        st.markdown(
            "#### Student response options"
        )

        c1, c2 = st.columns(2)

        with c1:

            allow_email = st.checkbox(
                "Optional student email",
                value=True
            )

            allow_document = st.checkbox(
                "Document upload",
                value=True
            )

        with c2:

            allow_image = st.checkbox(
                "Image upload",
                value=True
            )

            allow_video = st.checkbox(
                "Short video upload",
                value=False
            )


        submitted = st.form_submit_button(
            "🚀 Generate Activity & QR Code",
            type="primary",
            use_container_width=True
        )


    # =====================================================
    # PROCESS FORM
    # =====================================================

    if submitted:

        selected_course = (
            custom_course.strip()
            if course == "Other"
            else course
        )

        if not selected_course:

            st.error(
                "Please enter the course title."
            )

        elif not activity_title.strip():

            st.error(
                "Please enter an activity title."
            )

        elif not question.strip():

            st.error(
                "Please enter a question."
            )

        else:

            now = datetime.now()

            session_code = create_session_code()

            app_url = st.secrets["APP_URL"]

            student_url = (
                f"{app_url}/?session={session_code}"
            )


            st.session_state.activity = {

                "course": selected_course,

                "semester": semester,

                "activity_title":
                    activity_title.strip(),

                "question":
                    question.strip(),

                "instructions":
                    instructions.strip(),

                "date":
                    now.strftime("%d %B %Y"),

                "time":
                    now.strftime("%I:%M %p"),

                "session":
                    session_code,

                "student_url":
                    student_url,

                "allow_email":
                    allow_email,

                "allow_document":
                    allow_document,

                "allow_image":
                    allow_image,

                "allow_video":
                    allow_video
            }

            st.rerun()


# =========================================================
# SHOW CREATED ACTIVITY
# =========================================================

else:

    activity = st.session_state.activity

    st.success(
        "Activity created successfully!"
    )

    left, right = st.columns([1.5, 1])


    # -----------------------------------------------------
    # ACTIVITY DETAILS
    # -----------------------------------------------------

    with left:

        st.header(
            activity["activity_title"]
        )

        st.markdown(
            f"""
            <div class="info-card">

            <b>📚 Course</b><br>
            {activity["course"]}

            <br><br>

            <b>🎓 Semester</b><br>
            {activity["semester"]}

            <br><br>

            <b>📅 Date</b><br>
            {activity["date"]}

            <br><br>

            <b>⏰ Time</b><br>
            {activity["time"]}

            </div>
            """,
            unsafe_allow_html=True
        )


        st.subheader(
            "💬 Discussion Question"
        )

        st.info(
            activity["question"]
        )


        if activity["instructions"]:

            st.write(
                "**Instructions:**"
            )

            st.write(
                activity["instructions"]
            )


    # -----------------------------------------------------
    # QR AREA
    # -----------------------------------------------------

    with right:

        st.subheader(
            "📱 Student Access"
        )

        st.write(
            "Students scan this QR code "
            "to access this activity."
        )


        st.markdown(
            f"""
            <div class="session-code">
                {activity["session"]}
            </div>
            """,
            unsafe_allow_html=True
        )


        qr_image = create_qr(
            activity["student_url"]
        )


        st.image(
            qr_image,
            width=280
        )


        st.caption(
            activity["student_url"]
        )


        st.download_button(
            "⬇️ Download QR Code",
            qr_image,
            file_name=
            f"{activity['session']}_QR.png",
            mime="image/png",
            use_container_width=True
        )


    st.divider()


    # -----------------------------------------------------
    # RESPONSE SETTINGS
    # -----------------------------------------------------

    st.subheader(
        "⚙️ Activity Settings"
    )

    s1, s2, s3, s4 = st.columns(4)

    s1.metric(
        "Email",
        "Optional"
        if activity["allow_email"]
        else "Disabled"
    )

    s2.metric(
        "Documents",
        "Allowed"
        if activity["allow_document"]
        else "Disabled"
    )

    s3.metric(
        "Images",
        "Allowed"
        if activity["allow_image"]
        else "Disabled"
    )

    s4.metric(
        "Videos",
        "Allowed"
        if activity["allow_video"]
        else "Disabled"
    )


    st.divider()


    if st.button(
        "➕ Create Another Activity",
        type="primary"
    ):

        st.session_state.activity = None

        st.rerun()

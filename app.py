import streamlit as st
import qrcode
import io
import secrets
import requests
import base64
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
import base64

with open("ibrahim44.gif", "rb") as f:
    gif_data = base64.b64encode(f.read()).decode()

st.markdown(
    f'<img src="data:image/gif;base64,{gif_data}" width="200">',
    unsafe_allow_html=True
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

.student-card {
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #e6e8ec;
    background: white;
    margin-bottom: 18px;
}

.session-code {
    font-size: 28px;
    font-weight: 800;
    text-align: center;
    padding: 15px;
    border-radius: 15px;
    background: #f2f6ff;
}

.activity-count {
    padding: 15px;
    border-radius: 12px;
    background: #f7f9fc;
    margin-bottom: 20px;
}

.student-question {
    padding: 22px;
    border-radius: 18px;
    background: #f7f9fc;
    border: 1px solid #e6e8ec;
    margin-bottom: 20px;
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

    .info-card,
    .student-card,
    .student-question {
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

if "student_submitted" not in st.session_state:
    st.session_state.student_submitted = False

if "student_submission_session" not in st.session_state:
    st.session_state.student_submission_session = None


# =========================================================
# GENERAL FUNCTIONS
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
# GOOGLE — SAVE ACTIVITY
# =========================================================

def save_activity_to_google(activity):

    payload = {

        "action":
            "create_activity",

        "session_id":
            activity["session"],

        "course":
            activity["course"],

        "semester":
            activity["semester"],

        "activity_title":
            activity["activity_title"],

        "question":
            activity["question"],

        "instructions":
            activity["instructions"],

        "created_date":
            activity["date"],

        "created_time":
            activity["time"],

        "allow_email":
            activity["allow_email"],

        "allow_document":
            activity["allow_document"],

        "allow_image":
            activity["allow_image"],

        "allow_video":
            activity["allow_video"]
    }

    try:

        response = requests.post(
            st.secrets["GOOGLE_SCRIPT_URL"],
            json=payload,
            timeout=20
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "Google connection timed out."
        }

    except requests.exceptions.RequestException as error:

        return {
            "success": False,
            "error": f"Google connection error: {error}"
        }

    except ValueError:

        return {
            "success": False,
            "error": "Google returned an invalid response."
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error)
        }


# =========================================================
# GOOGLE — GET ALL ACTIVITIES
# =========================================================

def get_all_activities():

    try:

        response = requests.get(
            st.secrets["GOOGLE_SCRIPT_URL"],
            params={
                "action": "get_activities"
            },
            timeout=20
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "Google connection timed out.",
            "activities": []
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error),
            "activities": []
        }


# =========================================================
# GOOGLE — GET ONE ACTIVITY
# =========================================================

def get_activity_from_google(session_id):

    try:

        response = requests.get(
            st.secrets["GOOGLE_SCRIPT_URL"],
            params={
                "action": "get_activity",
                "session_id": session_id
            },
            timeout=20
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "Google connection timed out."
        }

    except requests.exceptions.RequestException as error:

        return {
            "success": False,
            "error": f"Google connection error: {error}"
        }

    except ValueError:

        return {
            "success": False,
            "error": "Google returned an invalid response."
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error)
        }


# =========================================================
# GOOGLE — SUBMIT STUDENT RESPONSE
# =========================================================

def submit_student_response(
    session_id,
    student_email,
    answer,
    attachments=None
):

    now = datetime.now()
    attachments = attachments or []

    payload = {
        "action": "submit_response",
        "session_id": session_id,
        "submitted_date": now.strftime("%d %B %Y"),
        "submitted_time": now.strftime("%I:%M %p"),
        "student_email": student_email.strip(),
        "answer": answer.strip(),
        "attachments": attachments
    }

    try:
        # Base64 makes the JSON request larger than the original file bytes,
        # so uploads are given a longer timeout than text-only responses.
        response = requests.post(
            st.secrets["GOOGLE_SCRIPT_URL"],
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Submission timed out. Please try again with smaller files."
        }
    except requests.exceptions.RequestException as error:
        return {
            "success": False,
            "error": f"Connection error: {error}"
        }
    except ValueError:
        return {
            "success": False,
            "error": "Google returned an invalid response."
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }


def uploaded_file_to_attachment(uploaded_file, category):
    """Convert one Streamlit UploadedFile to the JSON format expected by Apps Script."""
    file_bytes = uploaded_file.getvalue()
    return {
        "category": category,
        "name": uploaded_file.name,
        "mime_type": uploaded_file.type or "application/octet-stream",
        "base64": base64.b64encode(file_bytes).decode("utf-8")
    }


def setting_enabled(value):
    """Handle either real booleans or TRUE/FALSE values returned by Google Sheets."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


# =========================================================
# GOOGLE — GET STUDENT RESPONSES
# =========================================================

def get_student_responses(session_id):
    try:
        response = requests.get(
            st.secrets["GOOGLE_SCRIPT_URL"],
            params={
                "action": "get_responses",
                "session_id": session_id
            },
            timeout=20
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Google connection timed out.", "responses": []}
    except requests.exceptions.RequestException as error:
        return {"success": False, "error": f"Google connection error: {error}", "responses": []}
    except ValueError:
        return {"success": False, "error": "Google returned an invalid response.", "responses": []}
    except Exception as error:
        return {"success": False, "error": str(error), "responses": []}


# =========================================================
# CHECK URL FOR STUDENT SESSION
# =========================================================
#
# THIS MUST COME BEFORE INSTRUCTOR LOGIN.
#
# Example:
#
# https://your-app.streamlit.app/?session=ABC123
#
# =========================================================

student_session_id = st.query_params.get("session")


# =========================================================
# STUDENT MODE
# =========================================================

if student_session_id:

    student_session_id = str(
        student_session_id
    ).strip()


    # Reset success state if another QR/session is opened

    if (
        st.session_state.student_submission_session
        != student_session_id
    ):

        st.session_state.student_submitted = False

        st.session_state.student_submission_session = (
            student_session_id
        )


    # -----------------------------------------------------
    # STUDENT HEADER
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="main-title">
            🎓 SmartClass Response
        </div>

        <div class="subtitle">
            Classroom Discussion
        </div>
        """,
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # LOAD ACTIVITY
    # -----------------------------------------------------

    with st.spinner(
        "Loading classroom activity..."
    ):

        activity_result = (
            get_activity_from_google(
                student_session_id
            )
        )


    # -----------------------------------------------------
    # ACTIVITY NOT FOUND
    # -----------------------------------------------------

    if not activity_result.get("success"):

        st.error(
            "❌ This classroom activity could not be found."
        )

        st.write(
            "Please scan the QR code again or ask your instructor."
        )

        with st.expander(
            "Technical information"
        ):

            st.write(
                activity_result.get(
                    "error",
                    "Unknown error."
                )
            )

        st.stop()


    student_activity = (
        activity_result.get(
            "activity",
            {}
        )
    )


    # -----------------------------------------------------
    # CHECK STATUS
    # -----------------------------------------------------

    activity_status = str(
        student_activity.get(
            "status",
            "Active"
        )
    ).strip()


    if activity_status.lower() != "active":

        st.warning(
            "🔒 This classroom activity is currently closed."
        )

        st.write(
            "Please contact your instructor if you believe "
            "the activity should still be available."
        )

        st.stop()


    # -----------------------------------------------------
    # COURSE INFORMATION
    # -----------------------------------------------------

    st.header(
        student_activity.get(
            "activity_title",
            "Classroom Activity"
        )
    )


    st.markdown(
        f"""
        <div class="student-card">

        <b>📚 Course</b><br>
        {student_activity.get("course", "")}

        <br><br>

        <b>🎓 Semester</b><br>
        {student_activity.get("semester", "")}

        <br><br>

        <b>🔑 Session</b><br>
        {student_session_id}

        </div>
        """,
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # QUESTION
    # -----------------------------------------------------

    st.subheader(
        "💬 Discussion Question"
    )


    st.info(
        student_activity.get(
            "question",
            ""
        )
    )


    # -----------------------------------------------------
    # INSTRUCTIONS
    # -----------------------------------------------------

    instructions = str(
        student_activity.get(
            "instructions",
            ""
        )
    ).strip()


    if instructions:

        st.write(
            "**📌 Instructions**"
        )

        st.write(
            instructions
        )


    st.divider()


    # =====================================================
    # SUBMISSION SUCCESS PAGE
    # =====================================================

    if st.session_state.student_submitted:

        st.success(
            "✅ Your response has been submitted successfully!"
        )

        st.markdown(
            """
            ### Thank you for participating

            Your response has been received by your instructor.
            """
        )

        st.info(
            "You may now close this page."
        )

        st.stop()


    # =====================================================
    # STUDENT RESPONSE FORM
    # =====================================================

    st.subheader(
        "✍️ Your Response"
    )


    st.write(
        "Write your response below and press "
        "**Submit Response** when finished."
    )


    with st.form(
        "student_response_form"
    ):


        # -------------------------------------------------
        # OPTIONAL EMAIL
        # -------------------------------------------------

        student_email = ""


        allow_email = student_activity.get(
            "allow_email",
            False
        )


        if allow_email:

            student_email = st.text_input(

                "Email (optional)",

                placeholder=
                    "You may leave this blank"
            )


            st.caption(
                "Your email is optional and will only "
                "be visible to the instructor."
            )


        # -------------------------------------------------
        # ANSWER
        # -------------------------------------------------

        answer = st.text_area(

            "Your Answer",

            placeholder=
                "Write your answer, explanation or "
                "classroom comment here...",

            height=220
        )


        # -------------------------------------------------
        # OPTIONAL ATTACHMENTS
        # -------------------------------------------------

        allow_document = setting_enabled(
            student_activity.get("allow_document", False)
        )
        allow_image = setting_enabled(
            student_activity.get("allow_image", False)
        )
        allow_video = setting_enabled(
            student_activity.get("allow_video", False)
        )

        document_files = []
        image_files = []
        video_files = []

        if allow_document or allow_image or allow_video:
            st.markdown("**📎 Attachments (optional)**")
            st.caption(
                "You can attach up to 5 files in total. "
                "Documents/images: max 5 MB each; short videos: max 8 MB; "
                "combined maximum: 12 MB."
            )

        if allow_document:
            document_files = st.file_uploader(
                "📄 Upload Document",
                type=["pdf", "doc", "docx", "ppt", "pptx",
                      "xls", "xlsx", "txt", "csv"],
                accept_multiple_files=True,
                key=f"student_documents_{student_session_id}"
            )

        if allow_image:
            image_files = st.file_uploader(
                "🖼️ Upload Image",
                type=["jpg", "jpeg", "png", "webp"],
                accept_multiple_files=True,
                key=f"student_images_{student_session_id}"
            )

        if allow_video:
            video_files = st.file_uploader(
                "🎥 Upload Short Video",
                type=["mp4", "mov", "webm"],
                accept_multiple_files=True,
                key=f"student_videos_{student_session_id}"
            )


        # -------------------------------------------------
        # SUBMIT BUTTON
        # -------------------------------------------------

        student_submit = (
            st.form_submit_button(

                "📤 Submit Response",

                type="primary",

                use_container_width=True
            )
        )


    # =====================================================
    # PROCESS STUDENT SUBMISSION
    # =====================================================

    if student_submit:


        if not answer.strip():

            st.error(
                "Please write your answer before submitting."
            )


        else:

            selected_files = (
                [(f, "document") for f in document_files]
                + [(f, "image") for f in image_files]
                + [(f, "video") for f in video_files]
            )

            if len(selected_files) > 5:
                st.error("Please upload a maximum of 5 attachments in total.")
                st.stop()

            attachments = []
            total_bytes = 0
            upload_error = None

            for uploaded_file, category in selected_files:
                file_size = len(uploaded_file.getvalue())
                total_bytes += file_size

                if category in {"document", "image"} and file_size > 5 * 1024 * 1024:
                    upload_error = f"{uploaded_file.name} is larger than 5 MB."
                    break

                if category == "video" and file_size > 8 * 1024 * 1024:
                    upload_error = f"{uploaded_file.name} is larger than 8 MB."
                    break

                attachments.append(
                    uploaded_file_to_attachment(uploaded_file, category)
                )

            if not upload_error and total_bytes > 12 * 1024 * 1024:
                upload_error = "The combined attachment size is larger than 12 MB."

            if upload_error:
                st.error(upload_error)
                st.stop()

            with st.spinner(
                "Uploading files and submitting your response..."
                if attachments else
                "Submitting your response..."
            ):

                submission_result = (
                    submit_student_response(
                        student_session_id,
                        student_email,
                        answer,
                        attachments
                    )
                )


            if submission_result.get(
                "success"
            ):

                st.session_state.student_submitted = True

                st.rerun()


            else:

                st.error(
                    "❌ Your response could not be submitted."
                )

                st.error(
                    submission_result.get(
                        "error",
                        "Unknown submission error."
                    )
                )


    # =====================================================
    # CRITICAL
    # =====================================================
    #
    # STOP HERE.
    #
    # A STUDENT MUST NEVER CONTINUE TO THE
    # INSTRUCTOR LOGIN SECTION.
    #
    # =====================================================

    st.stop()


# =========================================================
# INSTRUCTOR MODE
# =========================================================
#
# We reach this point ONLY when the URL does NOT contain
# ?session=...
#
# =========================================================


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

    left, middle, right = st.columns(
        [1, 2, 1]
    )


    with middle:

        st.subheader(
            "👨‍🏫 Instructor Login"
        )

        st.write(
            "Login to create and manage "
            "classroom activities."
        )


        password = st.text_input(
            "Instructor Password",
            type="password"
        )


        if st.button(
            "🔐 Login",
            type="primary",
            use_container_width=True
        ):

            if (
                password
                == st.secrets[
                    "INSTRUCTOR_PASSWORD"
                ]
            ):

                st.session_state.authenticated = True

                st.rerun()


            else:

                st.error(
                    "Incorrect instructor password."
                )


    st.stop()


# =========================================================
# INSTRUCTOR DASHBOARD HEADER
# =========================================================

top1, top2 = st.columns(
    [5, 1]
)


with top1:

    st.subheader(
        "👨‍🏫 Instructor Dashboard"
    )


with top2:

    if st.button(
        "Logout",
        use_container_width=True
    ):

        st.session_state.authenticated = False

        st.session_state.activity = None

        st.rerun()


st.divider()


# =========================================================
# DASHBOARD NAVIGATION
# =========================================================

dashboard_page = st.radio(

    "Instructor Menu",

    [
        "➕ Create Activity",
        "📚 My Activities",
        "📊 Student Responses"
    ],

    horizontal=True,

    label_visibility="collapsed"
)


st.divider()


# =========================================================
# PAGE 1 — CREATE ACTIVITY
# =========================================================

if dashboard_page == "➕ Create Activity":


    # =====================================================
    # NEW ACTIVITY FORM
    # =====================================================

    if st.session_state.activity is None:

        st.header(
            "➕ Create Classroom Activity"
        )


        st.write(
            "Select the course and semester, "
            "then enter your classroom question."
        )


        # -------------------------------------------------
        # COURSE LIST
        # -------------------------------------------------

        courses = [

            "Computer System Internals and Linux",

            "Information Security Management",

            "Database Systems",

            "Career Development",

            "Dependable Software Engineering",

            "Final Year Project",

            "Other"
        ]


        semesters = [

            "Semester 1 - 2026/2027",

            "Semester 2 - 2026/2027",

            "Summer - 2026/2027"
        ]


        # -------------------------------------------------
        # ACTIVITY FORM
        # -------------------------------------------------

        with st.form(
            "activity_form"
        ):


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


            # ---------------------------------------------
            # CUSTOM COURSE
            # ---------------------------------------------

            custom_course = ""


            if course == "Other":

                custom_course = st.text_input(
                    "Enter Course Title"
                )


            # ---------------------------------------------
            # ACTIVITY TITLE
            # ---------------------------------------------

            activity_title = st.text_input(

                "Activity Title",

                placeholder=
                    "Example: Linux Security Discussion"
            )


            # ---------------------------------------------
            # QUESTION
            # ---------------------------------------------

            question = st.text_area(

                "Question / Discussion Task",

                placeholder=
                    "Enter the question students "
                    "should discuss...",

                height=160
            )


            # ---------------------------------------------
            # INSTRUCTIONS
            # ---------------------------------------------

            instructions = st.text_area(

                "Instructions (optional)",

                placeholder=
                    "Example: Explain your answer "
                    "and give one example.",

                height=90
            )


            st.markdown(
                "#### Student Response Options"
            )


            option1, option2 = st.columns(2)


            with option1:

                allow_email = st.checkbox(
                    "Optional student email",
                    value=True
                )

                allow_document = st.checkbox(
                    "Document upload",
                    value=True
                )


            with option2:

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


        # =================================================
        # PROCESS NEW ACTIVITY
        # =================================================

        if submitted:


            selected_course = (

                custom_course.strip()

                if course == "Other"

                else course
            )


            # ---------------------------------------------
            # VALIDATION
            # ---------------------------------------------

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


                # -----------------------------------------
                # DATE & TIME
                # -----------------------------------------

                now = datetime.now()


                # -----------------------------------------
                # UNIQUE SESSION
                # -----------------------------------------

                session_code = (
                    create_session_code()
                )


                # -----------------------------------------
                # STUDENT URL
                # -----------------------------------------

                app_url = (
                    st.secrets["APP_URL"]
                    .rstrip("/")
                )


                student_url = (

                    f"{app_url}/"
                    f"?session={session_code}"
                )


                # -----------------------------------------
                # ACTIVITY DATA
                # -----------------------------------------

                activity = {

                    "course":
                        selected_course,

                    "semester":
                        semester,

                    "activity_title":
                        activity_title.strip(),

                    "question":
                        question.strip(),

                    "instructions":
                        instructions.strip(),

                    "date":
                        now.strftime(
                            "%d %B %Y"
                        ),

                    "time":
                        now.strftime(
                            "%I:%M %p"
                        ),

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


                # -----------------------------------------
                # SAVE TO GOOGLE
                # -----------------------------------------

                with st.spinner(
                    "Creating activity and saving "
                    "to Google Sheets and Drive..."
                ):

                    google_result = (
                        save_activity_to_google(
                            activity
                        )
                    )


                # -----------------------------------------
                # SUCCESS
                # -----------------------------------------

                if google_result.get(
                    "success"
                ):

                    activity[
                        "drive_folder_url"
                    ] = google_result.get(
                        "folder_url",
                        ""
                    )


                    st.session_state.activity = (
                        activity
                    )


                    st.rerun()


                # -----------------------------------------
                # FAILURE
                # -----------------------------------------

                else:

                    st.error(
                        "❌ The activity could not "
                        "be saved to Google."
                    )


                    st.error(
                        google_result.get(
                            "error",
                            "Unknown Google error."
                        )
                    )


    # =====================================================
    # SHOW JUST-CREATED ACTIVITY
    # =====================================================

    else:

        activity = (
            st.session_state.activity
        )


        st.success(
            "✅ Activity created and saved successfully!"
        )


        left, right = st.columns(
            [1.5, 1]
        )


        # -------------------------------------------------
        # ACTIVITY INFORMATION
        # -------------------------------------------------

        with left:


            st.header(
                activity[
                    "activity_title"
                ]
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
                    activity[
                        "instructions"
                    ]
                )


            if activity.get(
                "drive_folder_url"
            ):

                st.success(
                    "☁️ Google Drive activity "
                    "folder created successfully."
                )


                st.link_button(
                    "📁 Open Google Drive Folder",
                    activity[
                        "drive_folder_url"
                    ]
                )


        # -------------------------------------------------
        # QR CODE
        # -------------------------------------------------

        with right:


            st.subheader(
                "📱 Student Access"
            )


            st.write(
                "Students scan this QR code "
                "to answer this activity."
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
                activity[
                    "student_url"
                ]
            )


            st.image(
                qr_image,
                width=280
            )


            st.caption(
                activity[
                    "student_url"
                ]
            )


            st.download_button(

                "⬇️ Download QR Code",

                data=qr_image,

                file_name=
                    f"{activity['session']}_QR.png",

                mime="image/png",

                use_container_width=True
            )


        # -------------------------------------------------
        # RESPONSE SETTINGS
        # -------------------------------------------------

        st.divider()


        st.subheader(
            "⚙️ Activity Settings"
        )


        s1, s2, s3, s4 = (
            st.columns(4)
        )


        s1.metric(
            "Email",
            "Optional"
            if activity[
                "allow_email"
            ]
            else "Disabled"
        )


        s2.metric(
            "Documents",
            "Allowed"
            if activity[
                "allow_document"
            ]
            else "Disabled"
        )


        s3.metric(
            "Images",
            "Allowed"
            if activity[
                "allow_image"
            ]
            else "Disabled"
        )


        s4.metric(
            "Videos",
            "Allowed"
            if activity[
                "allow_video"
            ]
            else "Disabled"
        )


        st.divider()


        if st.button(
            "➕ Create Another Activity",
            type="primary"
        ):

            st.session_state.activity = None

            st.rerun()


# =========================================================
# PAGE 2 — MY ACTIVITIES
# =========================================================

elif dashboard_page == "📚 My Activities":


    st.header(
        "📚 My Activities"
    )


    st.write(
        "Find previous classroom activities, "
        "display their QR codes and share "
        "them with your students."
    )


    # -----------------------------------------------------
    # LOAD GOOGLE DATA
    # -----------------------------------------------------

    with st.spinner(
        "Loading activities from Google..."
    ):

        result = get_all_activities()


    # -----------------------------------------------------
    # LOAD ERROR
    # -----------------------------------------------------

    if not result.get(
        "success"
    ):

        st.error(
            "❌ Could not load activities."
        )

        st.error(
            result.get(
                "error",
                "Unknown Google error."
            )
        )

        st.stop()


    activities = result.get(
        "activities",
        []
    )


    # -----------------------------------------------------
    # NO ACTIVITIES
    # -----------------------------------------------------

    if not activities:

        st.info(
            "No activities have been created yet."
        )

        st.stop()


    # =====================================================
    # FILTERS
    # =====================================================

    st.subheader(
        "🔎 Find an Activity"
    )


    course_names = sorted(

        list(

            set(

                str(
                    activity.get(
                        "course",
                        ""
                    )
                )

                for activity
                in activities

                if activity.get(
                    "course"
                )
            )
        )
    )


    semester_names = sorted(

        list(

            set(

                str(
                    activity.get(
                        "semester",
                        ""
                    )
                )

                for activity
                in activities

                if activity.get(
                    "semester"
                )
            )
        )
    )


    filter1, filter2 = (
        st.columns(2)
    )


    with filter1:

        selected_course_filter = (
            st.selectbox(

                "Course",

                ["All Courses"]
                + course_names
            )
        )


    with filter2:

        selected_semester_filter = (
            st.selectbox(

                "Semester",

                ["All Semesters"]
                + semester_names
            )
        )


    search_text = st.text_input(

        "Search",

        placeholder=
            "Search activity title, "
            "question or session code..."
    )


    # =====================================================
    # APPLY FILTERS
    # =====================================================

    filtered_activities = []


    for item in activities:


        course_match = (

            selected_course_filter
            == "All Courses"

            or str(
                item.get(
                    "course",
                    ""
                )
            )
            == selected_course_filter
        )


        semester_match = (

            selected_semester_filter
            == "All Semesters"

            or str(
                item.get(
                    "semester",
                    ""
                )
            )
            == selected_semester_filter
        )


        searchable_text = (

            str(
                item.get(
                    "activity_title",
                    ""
                )
            )

            + " "

            + str(
                item.get(
                    "question",
                    ""
                )
            )

            + " "

            + str(
                item.get(
                    "session_id",
                    ""
                )
            )

        ).lower()


        search_match = (

            not search_text

            or search_text.lower()
            in searchable_text
        )


        if (
            course_match
            and semester_match
            and search_match
        ):

            filtered_activities.append(
                item
            )


    # =====================================================
    # ACTIVITY COUNT
    # =====================================================

    st.markdown(
        f"""
        <div class="activity-count">

        <b>
        {len(filtered_activities)}
        activity/activities found
        </b>

        </div>
        """,
        unsafe_allow_html=True
    )


    # =====================================================
    # DISPLAY ACTIVITIES
    # =====================================================

    if not filtered_activities:

        st.warning(
            "No activities match "
            "the selected filters."
        )


    for item in filtered_activities:


        title = str(
            item.get(
                "activity_title",
                "Untitled Activity"
            )
        )


        saved_session_id = str(
            item.get(
                "session_id",
                ""
            )
        )


        # -------------------------------------------------
        # ACTIVITY EXPANDER
        # -------------------------------------------------

        with st.expander(
            f"📘 {title} — {saved_session_id}"
        ):


            info1, info2, info3 = (
                st.columns(3)
            )


            # ---------------------------------------------
            # COURSE
            # ---------------------------------------------

            with info1:

                st.write(
                    "**📚 Course**"
                )

                st.write(
                    item.get(
                        "course",
                        ""
                    )
                )


            # ---------------------------------------------
            # SEMESTER
            # ---------------------------------------------

            with info2:

                st.write(
                    "**🎓 Semester**"
                )

                st.write(
                    item.get(
                        "semester",
                        ""
                    )
                )


            # ---------------------------------------------
            # DATE
            # ---------------------------------------------

            with info3:

                st.write(
                    "**📅 Date**"
                )

                st.write(
                    item.get(
                        "created_date",
                        ""
                    )
                )


            # ---------------------------------------------
            # QUESTION
            # ---------------------------------------------

            st.write(
                "**💬 Question**"
            )


            st.info(
                item.get(
                    "question",
                    ""
                )
            )


            # ---------------------------------------------
            # INSTRUCTIONS
            # ---------------------------------------------

            if item.get(
                "instructions"
            ):

                st.write(
                    "**Instructions:**"
                )

                st.write(
                    item.get(
                        "instructions"
                    )
                )


            # ---------------------------------------------
            # STATUS
            # ---------------------------------------------

            status = str(
                item.get(
                    "status",
                    "Active"
                )
            )


            st.write(
                f"**Status:** {status}"
            )


            # ---------------------------------------------
            # BUILD STUDENT URL
            # ---------------------------------------------

            app_url = (
                st.secrets[
                    "APP_URL"
                ]
                .rstrip("/")
            )


            student_url = (

                f"{app_url}/"
                f"?session={saved_session_id}"
            )


            # ---------------------------------------------
            # GENERATE QR
            # ---------------------------------------------

            qr_image = create_qr(
                student_url
            )


            qr_col, access_col = (
                st.columns(
                    [1, 2]
                )
            )


            # ---------------------------------------------
            # QR DISPLAY
            # ---------------------------------------------

            with qr_col:

                st.image(
                    qr_image,
                    width=230
                )


            # ---------------------------------------------
            # STUDENT ACCESS
            # ---------------------------------------------

            with access_col:


                st.markdown(
                    "### 📱 Student Access"
                )


                st.write(
                    "**Session Code:**"
                )


                st.code(
                    saved_session_id,
                    language=None
                )


                st.text_input(

                    "Student Link",

                    value=
                        student_url,

                    key=
                        f"url_{saved_session_id}"
                )


                st.download_button(

                    "⬇️ Download QR Code",

                    data=
                        qr_image,

                    file_name=
                        f"{saved_session_id}_QR.png",

                    mime=
                        "image/png",

                    key=
                        f"download_{saved_session_id}",

                    use_container_width=True
                )


                # -----------------------------------------
                # GOOGLE DRIVE
                # -----------------------------------------

                drive_url = str(
                    item.get(
                        "drive_folder_url",
                        ""
                    )
                )


                if drive_url:

                    st.link_button(

                        "📁 Open Google Drive Folder",

                        drive_url,

                        use_container_width=True
                    )

# =========================================================
# PAGE 3 — STUDENT RESPONSES
# =========================================================

elif dashboard_page == "📊 Student Responses":

    st.header("📊 Student Responses")
    st.write(
        "Select an activity to view student answers directly inside SmartClass."
    )

    with st.spinner("Loading activities from Google..."):
        activities_result = get_all_activities()

    if not activities_result.get("success"):
        st.error("❌ Could not load activities.")
        st.error(activities_result.get("error", "Unknown Google error."))
        st.stop()

    activities = activities_result.get("activities", [])

    if not activities:
        st.info("No activities have been created yet.")
        st.stop()

    course_names = sorted({
        str(item.get("course", "")).strip()
        for item in activities
        if str(item.get("course", "")).strip()
    })

    response_course = st.selectbox(
        "Course",
        course_names,
        key="responses_course"
    )

    course_activities = [
        item for item in activities
        if str(item.get("course", "")).strip() == response_course
    ]

    semester_names = sorted({
        str(item.get("semester", "")).strip()
        for item in course_activities
        if str(item.get("semester", "")).strip()
    })

    response_semester = st.selectbox(
        "Semester",
        semester_names,
        key="responses_semester"
    )

    matching_activities = [
        item for item in course_activities
        if str(item.get("semester", "")).strip() == response_semester
    ]

    if not matching_activities:
        st.info("No activities were found for this course and semester.")
        st.stop()

    activity_options = {}
    for item in matching_activities:
        session = str(item.get("session_id", "")).strip()
        title = str(item.get("activity_title", "Untitled Activity")).strip()
        date = str(item.get("created_date", "")).strip()
        label = f"{title} — {date} — {session}"
        activity_options[label] = item

    selected_activity_label = st.selectbox(
        "Activity",
        list(activity_options.keys()),
        key="responses_activity"
    )

    selected_activity = activity_options[selected_activity_label]
    selected_session = str(selected_activity.get("session_id", "")).strip()

    st.divider()
    st.subheader(selected_activity.get("activity_title", "Classroom Activity"))
    st.caption(
        f"{selected_activity.get('course', '')} • "
        f"{selected_activity.get('semester', '')} • "
        f"Session {selected_session}"
    )
    st.info(selected_activity.get("question", ""))

    control1, control2 = st.columns([1, 2])
    with control1:
        refresh = st.button(
            "🔄 Refresh Responses",
            use_container_width=True
        )
    with control2:
        presentation_mode = st.toggle(
            "🎥 Presentation Mode — hide student emails",
            value=False
        )

    # The button causes a normal Streamlit rerun, so responses are fetched fresh.
    with st.spinner("Loading student responses..."):
        responses_result = get_student_responses(selected_session)

    if not responses_result.get("success"):
        st.error("❌ Could not load student responses.")
        st.error(responses_result.get("error", "Unknown Google error."))
        st.stop()

    responses = responses_result.get("responses", [])

    total_responses = len(responses)
    responses_with_email = sum(
        1 for response in responses
        if str(response.get("student_email", "")).strip()
    )
    responses_with_attachment = sum(
        len(response.get("attachments", []) or [])
        if response.get("attachments")
        else (1 if str(response.get("attachment_url", "")).strip() else 0)
        for response in responses
    )

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Total Responses", total_responses)
    metric2.metric(
        "With Email",
        "Hidden" if presentation_mode else responses_with_email
    )
    metric3.metric("Attachments", responses_with_attachment)

    st.divider()

    if not responses:
        st.info(
            "No student responses have been submitted for this activity yet. "
            "Use Refresh Responses after students submit their answers."
        )
        st.stop()

    if presentation_mode:
        st.success(
            "🎥 Presentation Mode is active. Student emails are hidden."
        )

    for index, response in enumerate(responses, start=1):
        with st.container(border=True):
            heading_col, time_col = st.columns([3, 2])

            with heading_col:
                st.markdown(f"### 💬 Response {index}")

            with time_col:
                submitted_date = str(response.get("submitted_date", "")).strip()
                submitted_time = str(response.get("submitted_time", "")).strip()
                submitted_label = " • ".join(
                    part for part in [submitted_date, submitted_time] if part
                )
                if submitted_label:
                    st.caption(submitted_label)

            if not presentation_mode:
                student_email = str(response.get("student_email", "")).strip()
                if student_email:
                    st.write(f"**Student Email:** {student_email}")
                else:
                    st.caption("Student email: Not provided")

            answer_text = str(response.get("answer", "")).strip()
            st.write(answer_text if answer_text else "No written answer provided.")

            attachments = response.get("attachments", []) or []

            # Backward compatibility with responses created before multiple uploads.
            if not attachments:
                legacy_url = str(response.get("attachment_url", "")).strip()
                legacy_name = str(response.get("attachment_name", "")).strip()
                if legacy_url and not legacy_url.startswith("["):
                    attachments = [{
                        "name": legacy_name or "Attachment",
                        "url": legacy_url,
                        "type": str(response.get("attachment_type", "file"))
                    }]

            if attachments:
                st.markdown("**📎 Attachments**")
                for attachment_number, attachment in enumerate(attachments, start=1):
                    attachment_url = str(attachment.get("url", "")).strip()
                    attachment_name = str(attachment.get("name", "Attachment")).strip()
                    attachment_type = str(attachment.get("type", "file")).strip().lower()

                    if attachment_url:
                        icon = {
                            "image": "🖼️",
                            "document": "📄",
                            "video": "🎥"
                        }.get(attachment_type, "📎")

                        st.link_button(
                            f"{icon} Open {attachment_name}",
                            attachment_url,
                            key=(
                                f"attachment_{selected_session}_{index}_"
                                f"{attachment_number}"
                            )
                        )




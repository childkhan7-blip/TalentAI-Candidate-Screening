# import os
# import io
# import json

# from dotenv import load_dotenv
# from fastapi import FastAPI, UploadFile, File, HTTPException
# from pypdf import PdfReader
# from google import genai
# from pydantic import BaseModel
# from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# # =========================================================
# # LOAD ENVIRONMENT VARIABLES
# # =========================================================

# load_dotenv("backend/.env")


# # =========================================================
# # FASTAPI
# # =========================================================

# app = FastAPI(
#     title="HR Candidate Screening Agent"
# )


# # =========================================================
# # GEMINI
# # =========================================================

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# if not GEMINI_API_KEY:
#     raise ValueError(
#         "GEMINI_API_KEY is missing. "
#         "Check backend/.env"
#     )

# client = genai.Client(
#     api_key=GEMINI_API_KEY
# )

# # =========================================================
# # EMAIL CONFIGURATION
# # =========================================================

# conf = ConnectionConfig(
#     MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
#     MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
#     MAIL_FROM=os.getenv("MAIL_FROM"),
#     MAIL_PORT=587,
#     MAIL_SERVER="smtp.gmail.com",
#     MAIL_STARTTLS=True,
#     MAIL_SSL_TLS=False,
#     USE_CREDENTIALS=True
# )


# # =========================================================
# # INTERVIEW SCHEDULER
# # =========================================================

# class Interview(BaseModel):
#     candidate_name: str
#     candidate_email: str
#     interview_date: str
#     interview_time: str
#     position: str
# # =========================================================
# # HOME
# # =========================================================

# @app.get("/")
# def home():

#     return {
#         "message": "HR Candidate Screening Agent is running!"
#     }


# # =========================================================
# # CV UPLOAD + PDF PARSER
# # =========================================================

# @app.post("/upload-cv")
# async def upload_cv(
#     file: UploadFile = File(...)
# ):

#     # Check file type
#     if file.content_type != "application/pdf":

#         raise HTTPException(
#             status_code=400,
#             detail="Please upload a PDF CV."
#         )

#     # Read uploaded PDF
#     file_content = await file.read()

#     # Create PDF reader
#     pdf = PdfReader(
#         io.BytesIO(file_content)
#     )

#     # Extract text
#     cv_text = ""

#     for page in pdf.pages:

#         text = page.extract_text()

#         if text:
#             cv_text += text + "\n"

#     # Check extracted text
#     if not cv_text.strip():

#         raise HTTPException(
#             status_code=400,
#             detail="Could not extract text from this CV."
#         )

#     return {

#         "filename": file.filename,

#         "message":
#         "CV uploaded and parsed successfully!",

#         "cv_text": cv_text

#     }


# # =========================================================
# # AI CV SCORING
# # =========================================================

# @app.post("/score-cv")
# async def score_cv(

#     file: UploadFile = File(...),

#     job_requirements: str = ""

# ):

#     # -----------------------------------------------------
#     # Check PDF
#     # -----------------------------------------------------

#     if file.content_type != "application/pdf":

#         raise HTTPException(
#             status_code=400,
#             detail="Please upload a PDF CV."
#         )


#     # -----------------------------------------------------
#     # Read PDF
#     # -----------------------------------------------------

#     file_content = await file.read()

#     pdf = PdfReader(
#         io.BytesIO(file_content)
#     )


#     # -----------------------------------------------------
#     # Extract CV text
#     # -----------------------------------------------------

#     cv_text = ""

#     for page in pdf.pages:

#         text = page.extract_text()

#         if text:

#             cv_text += text + "\n"


#     # -----------------------------------------------------
#     # Check CV text
#     # -----------------------------------------------------

#     if not cv_text.strip():

#         raise HTTPException(
#             status_code=400,
#             detail="Could not extract text from CV."
#         )


#     # =====================================================
#     # GEMINI PROMPT
#     # =====================================================

#     prompt = f"""

# You are an HR Candidate Screening AI.

# Your job is to analyze a candidate's CV
# against the provided job requirements.

# JOB REQUIREMENTS:

# {job_requirements}


# CANDIDATE CV:

# {cv_text}


# Evaluate the candidate based on:

# 1. Skills match
# 2. Relevant experience
# 3. Education
# 4. Overall suitability


# Return ONLY valid JSON.

# Use exactly this structure:

# {{
#     "candidate_name": "candidate name",
#     "score": 85,
#     "matched_skills": [
#         "Python",
#         "FastAPI"
#     ],
#     "missing_skills": [
#         "Machine Learning"
#     ],
#     "experience_summary": "short summary",
#     "recommendation": "Interview"
# }}


# IMPORTANT:

# The score must be a number between 0 and 100.

# Recommendation must be exactly one of:

# "Interview"

# "Maybe"

# "Reject"

# """


#     # =====================================================
#     # CALL GEMINI
#     # =====================================================

#     response = client.models.generate_content(

#         model="gemini-2.5-flash",

#         contents=prompt

#     )


#     # =====================================================
#     # GET AI RESPONSE
#     # =====================================================

#     ai_text = response.text.strip()


#     # =====================================================
#     # REMOVE MARKDOWN JSON FENCES
#     # =====================================================

#     if ai_text.startswith("```"):

#         ai_text = ai_text.replace(
#             "```json",
#             ""
#         )

#         ai_text = ai_text.replace(
#             "```",
#             ""
#         )

#         ai_text = ai_text.strip()


#     # =====================================================
#     # PARSE JSON
#     # =====================================================

#     try:

#         result = json.loads(ai_text)

#     except json.JSONDecodeError:

#         raise HTTPException(

#             status_code=500,

#             detail="Gemini returned invalid JSON."

#         )


#     # =====================================================
#     # RETURN RESULT
#     # =====================================================

#     return {

#         "filename": file.filename,

#         "screening": result

#     }

# # =========================================================
# # CANDIDATE RANKING
# # =========================================================

# @app.post("/rank-candidates")
# def rank_candidates(candidates: list[dict]):

#     if not candidates:
#         raise HTTPException(
#             status_code=400,
#             detail="No candidates provided."
#         )

#     # Sort candidates by score
#     ranked_candidates = sorted(
#         candidates,
#         key=lambda candidate: candidate.get("score", 0),
#         reverse=True
#     )

#     # Add ranking position
#     for index, candidate in enumerate(
#         ranked_candidates,
#         start=1
#     ):
#         candidate["rank"] = index

#     return {
#         "total_candidates": len(ranked_candidates),
#         "ranked_candidates": ranked_candidates
#     }

# # =========================================================
# # SCHEDULE INTERVIEW
# # =========================================================

# # =========================================================
# # SCHEDULE INTERVIEW + SEND EMAIL
# # =========================================================

# @app.post("/schedule-interview")
# async def schedule_interview(interview: Interview):

#     message = MessageSchema(
#         subject="Interview Invitation - HR Candidate Screening",
#         recipients=[interview.candidate_email],
#         body=f"""
# Hello {interview.candidate_name},

# Congratulations!

# You have been selected for an interview for the position of:

# {interview.position}

# Interview Details:

# Date: {interview.interview_date}
# Time: {interview.interview_time}

# Please be available at the scheduled time.

# Best regards,
# HR Recruitment Team
# """,
#         subtype="plain"
#     )

#     fm = FastMail(conf)

#     await fm.send_message(message)

#     return {
#         "message": "Interview scheduled and invitation email sent successfully!",
#         "interview": {
#             "candidate_name": interview.candidate_name,
#             "candidate_email": interview.candidate_email,
#             "interview_date": interview.interview_date,
#             "interview_time": interview.interview_time,
#             "position": interview.position
#         }
#     }


import os
import io
import json

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from google import genai
from pydantic import BaseModel
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv("backend/.env")


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="HR Candidate Screening Agent",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# GEMINI
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing. "
        "Check backend/.env"
    )

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# EMAIL CONFIGURATION
# =========================================================

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)


# =========================================================
# INTERVIEW MODEL
# =========================================================

class Interview(BaseModel):

    candidate_name: str
    candidate_email: str
    interview_date: str
    interview_time: str
    position: str


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "HR Candidate Screening Agent is running!"
    }


# =========================================================
# UPLOAD CV + PDF PARSER
# =========================================================

@app.post("/upload-cv")
async def upload_cv(
    file: UploadFile = File(...)
):

    # Check file type
    if file.content_type != "application/pdf":

        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF CV."
        )

    # Read PDF
    file_content = await file.read()

    try:

        pdf = PdfReader(
            io.BytesIO(file_content)
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Could not read the PDF file."
        )

    # Extract text
    cv_text = ""

    for page in pdf.pages:

        text = page.extract_text()

        if text:

            cv_text += text + "\n"

    # Check extracted text
    if not cv_text.strip():

        raise HTTPException(
            status_code=400,
            detail="Could not extract text from this CV."
        )

    return {

        "filename": file.filename,

        "message":
        "CV uploaded and parsed successfully!",

        "cv_text": cv_text

    }


# =========================================================
# AI CV SCORING
# =========================================================

@app.post("/score-cv")
async def score_cv(

    file: UploadFile = File(...),

    job_requirements: str = ""

):

    # -----------------------------------------------------
    # Check PDF
    # -----------------------------------------------------

    if file.content_type != "application/pdf":

        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF CV."
        )


    # -----------------------------------------------------
    # Read PDF
    # -----------------------------------------------------

    file_content = await file.read()

    try:

        pdf = PdfReader(
            io.BytesIO(file_content)
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Could not read the PDF file."
        )


    # -----------------------------------------------------
    # Extract CV text
    # -----------------------------------------------------

    cv_text = ""

    for page in pdf.pages:

        text = page.extract_text()

        if text:

            cv_text += text + "\n"


    # -----------------------------------------------------
    # Check CV text
    # -----------------------------------------------------

    if not cv_text.strip():

        raise HTTPException(
            status_code=400,
            detail="Could not extract text from CV."
        )


    # =====================================================
    # GEMINI PROMPT
    # =====================================================

    prompt = f"""

You are an HR Candidate Screening AI.

Your job is to analyze a candidate's CV
against the provided job requirements.

JOB REQUIREMENTS:

{job_requirements}


CANDIDATE CV:

{cv_text}


Evaluate the candidate based on:

1. Skills match
2. Relevant experience
3. Education
4. Overall suitability


Return ONLY valid JSON.

Use exactly this structure:

{{
    "candidate_name": "candidate name",
    "score": 85,
    "matched_skills": [
        "Python",
        "FastAPI"
    ],
    "missing_skills": [
        "Machine Learning"
    ],
    "experience_summary": "short summary",
    "recommendation": "Interview"
}}


IMPORTANT:

The score must be a number between 0 and 100.

Recommendation must be exactly one of:

"Interview"

"Maybe"

"Reject"

"""


    # =====================================================
    # CALL GEMINI
    # =====================================================

    try:

        response = client.models.generate_content(

            model="gemini-2.5-flash",

            contents=prompt

        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Gemini API error: {str(e)}"

        )


    # =====================================================
    # GET AI RESPONSE
    # =====================================================

    ai_text = response.text.strip()


    # =====================================================
    # REMOVE MARKDOWN JSON FENCES
    # =====================================================

    if ai_text.startswith("```"):

        ai_text = ai_text.replace(
            "```json",
            ""
        )

        ai_text = ai_text.replace(
            "```",
            ""
        )

        ai_text = ai_text.strip()


    # =====================================================
    # PARSE JSON
    # =====================================================

    try:

        result = json.loads(ai_text)

    except json.JSONDecodeError:

        raise HTTPException(

            status_code=500,

            detail="Gemini returned invalid JSON."

        )


    # =====================================================
    # RETURN RESULT
    # =====================================================

    return {

        "filename": file.filename,

        "screening": result

    }


# =========================================================
# CANDIDATE RANKING
# =========================================================

@app.post("/rank-candidates")
def rank_candidates(
    candidates: list[dict]
):

    if not candidates:

        raise HTTPException(
            status_code=400,
            detail="No candidates provided."
        )


    # Sort candidates by score
    ranked_candidates = sorted(

        candidates,

        key=lambda candidate:
        candidate.get("score", 0),

        reverse=True

    )


    # Add ranking position
    for index, candidate in enumerate(

        ranked_candidates,

        start=1

    ):

        candidate["rank"] = index


    return {

        "total_candidates":
        len(ranked_candidates),

        "ranked_candidates":
        ranked_candidates

    }


# =========================================================
# SCHEDULE INTERVIEW + SEND EMAIL
# =========================================================

@app.post("/schedule-interview")
async def schedule_interview(
    interview: Interview
):

    try:

        message = MessageSchema(

            subject=
            "Interview Invitation - HR Candidate Screening",

            recipients=[
                interview.candidate_email
            ],

            body=f"""
Hello {interview.candidate_name},

Congratulations!

You have been selected for an interview for the position of:

{interview.position}

Interview Details:

Date: {interview.interview_date}
Time: {interview.interview_time}

Please be available at the scheduled time.

Best regards,
HR Recruitment Team
""",

            subtype="plain"

        )


        fm = FastMail(conf)

        await fm.send_message(message)


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Email sending failed: {str(e)}"

        )


    return {

        "message":
        "Interview scheduled and invitation email sent successfully!",

        "interview": {

            "candidate_name":
            interview.candidate_name,

            "candidate_email":
            interview.candidate_email,

            "interview_date":
            interview.interview_date,

            "interview_time":
            interview.interview_time,

            "position":
            interview.position

        }

    }

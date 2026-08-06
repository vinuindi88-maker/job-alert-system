# ============================================================
# JOB ALERT SYSTEM - GMAIL NOTIFICATION
# ============================================================

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv


# ------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ------------------------------------------------------------

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")


# ------------------------------------------------------------
# VALIDATE EMAIL CONFIGURATION
# ------------------------------------------------------------

def validate_email_config():

    missing = []

    if not GMAIL_ADDRESS:
        missing.append("GMAIL_ADDRESS")

    if not GMAIL_APP_PASSWORD:
        missing.append("GMAIL_APP_PASSWORD")

    if not ALERT_EMAIL:
        missing.append("ALERT_EMAIL")

    if missing:
        raise ValueError(
            "Missing .env variables: "
            + ", ".join(missing)
        )


# ------------------------------------------------------------
# CREATE JOB ALERT HTML
# ------------------------------------------------------------

def create_job_email(job, match_result):

    company = job.get("company", "Unknown Company")
    title = job.get("title", "Unknown Role")
    location = job.get("location", "Not specified")
    job_url = job.get("job_url", "")
    posted_date = job.get("posted_date", "Not specified")

    match_score = match_result.get(
        "match_score",
        0
    )

    skill_score = match_result.get(
        "skill_score",
        0
    )

    matched_skills = match_result.get(
        "matched_skills",
        []
    )

    missing_skills = match_result.get(
        "missing_skills",
        []
    )

    matched_text = (
        ", ".join(matched_skills)
        if matched_skills
        else "None detected"
    )

    missing_text = (
        ", ".join(missing_skills)
        if missing_skills
        else "None"
    )

    apply_button = ""

    if job_url:
        apply_button = f"""
        <p>
            <a href="{job_url}"
               style="
               display:inline-block;
               padding:12px 20px;
               background:#1a73e8;
               color:white;
               text-decoration:none;
               border-radius:6px;
               font-weight:bold;">
               APPLY NOW
            </a>
        </p>
        """

    html = f"""
    <html>

    <body style="
        font-family:Arial, sans-serif;
        background:#f5f5f5;
        padding:20px;
    ">

        <div style="
            max-width:650px;
            margin:auto;
            background:white;
            padding:25px;
            border-radius:10px;
        ">

            <h2>
                New Job Match Found
            </h2>

            <h3>
                {title}
            </h3>

            <p>
                <strong>Company:</strong>
                {company}
            </p>

            <p>
                <strong>Location:</strong>
                {location}
            </p>

            <p>
                <strong>Posted:</strong>
                {posted_date}
            </p>

            <hr>

            <h3>
                Resume Compatibility
            </h3>

            <p>
                <strong>Overall Match:</strong>
                {match_score}%
            </p>

            <p>
                <strong>Skill Match:</strong>
                {skill_score}%
            </p>

            <p>
                <strong>Matched Skills:</strong><br>
                {matched_text}
            </p>

            <p>
                <strong>Missing Skills:</strong><br>
                {missing_text}
            </p>

            {apply_button}

            <hr>

            <small>
                Automated Job Alert System
            </small>

        </div>

    </body>

    </html>
    """

    return html


# ------------------------------------------------------------
# SEND JOB ALERT
# ------------------------------------------------------------

def send_job_alert(job, match_result):

    validate_email_config()

    title = job.get(
        "title",
        "Job Opportunity"
    )

    company = job.get(
        "company",
        "Company"
    )

    score = match_result.get(
        "match_score",
        0
    )

    subject = (
        f"Job Alert: {title} | "
        f"{company} | "
        f"{score}% Match"
    )

    message = MIMEMultipart(
        "alternative"
    )

    message["From"] = GMAIL_ADDRESS
    message["To"] = ALERT_EMAIL
    message["Subject"] = subject

    html = create_job_email(
        job,
        match_result
    )

    message.attach(
        MIMEText(
            html,
            "html"
        )
    )

    try:

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as server:

            server.login(
                GMAIL_ADDRESS,
                GMAIL_APP_PASSWORD.replace(
                    " ",
                    ""
                )
            )

            server.sendmail(
                GMAIL_ADDRESS,
                ALERT_EMAIL,
                message.as_string()
            )

        print(
            f"EMAIL SENT: "
            f"{title} | {company}"
        )

        return True

    except Exception as error:

        print(
            "EMAIL ERROR:",
            error
        )

        return False


# ============================================================
# TEST EMAIL
# ============================================================

if __name__ == "__main__":

    test_job = {

        "company":
            "Test Company",

        "title":
            "Data Analyst",

        "location":
            "Bengaluru, India",

        "posted_date":
            "Today",

        "job_url":
            "https://example.com/job"
    }

    test_match = {

        "match_score":
            85.75,

        "skill_score":
            92.31,

        "matched_skills": [
            "SQL",
            "Python",
            "Power BI",
            "Excel",
            "Pandas"
        ],

        "missing_skills": [
            "Power Query"
        ]
    }

    print(
        "\nGMAIL TEST\n"
    )

    send_job_alert(
        test_job,
        test_match
    )
# ============================================================
# JOB ALERT SYSTEM - DATABASE MANAGER
# Seen Jobs + Processing + Match + Notification Tracking
# ============================================================

import sqlite3
import hashlib
import os
from datetime import datetime


# ============================================================
# DATABASE LOCATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "jobs.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    os.makedirs(
        os.path.dirname(DATABASE_PATH),
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    return connection


# ============================================================
# COLUMN MIGRATION HELPER
# ============================================================

def _add_column_if_missing(
    cursor,
    column_name,
    definition
):

    cursor.execute(
        "PRAGMA table_info(jobs)"
    )

    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    if column_name not in existing_columns:

        cursor.execute(
            f"""
            ALTER TABLE jobs
            ADD COLUMN {column_name} {definition}
            """
        )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # MAIN TABLE
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            job_key TEXT UNIQUE NOT NULL,

            company TEXT,

            title TEXT NOT NULL,

            location TEXT,

            source TEXT,

            job_url TEXT,

            job_id TEXT,

            posted_date TEXT,

            experience TEXT,

            match_score REAL,

            skill_score REAL,

            text_similarity REAL,

            matched_skills TEXT,

            missing_skills TEXT,

            notified INTEGER DEFAULT 0,

            processed INTEGER DEFAULT 0,

            basic_filter_passed INTEGER DEFAULT 0,

            experience_passed INTEGER DEFAULT 0,

            first_seen TEXT NOT NULL,

            last_seen TEXT
        )
        """
    )

    # --------------------------------------------------------
    # MIGRATE EXISTING DATABASE
    # --------------------------------------------------------

    _add_column_if_missing(
        cursor,
        "source",
        "TEXT"
    )

    _add_column_if_missing(
        cursor,
        "processed",
        "INTEGER DEFAULT 0"
    )

    _add_column_if_missing(
        cursor,
        "basic_filter_passed",
        "INTEGER DEFAULT 0"
    )

    _add_column_if_missing(
        cursor,
        "experience_passed",
        "INTEGER DEFAULT 0"
    )

    _add_column_if_missing(
        cursor,
        "last_seen",
        "TEXT"
    )

    # --------------------------------------------------------
    # INDEXES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_jobs_job_key
        ON jobs(job_key)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_jobs_processed
        ON jobs(processed)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_jobs_notified
        ON jobs(notified)
        """
    )

    connection.commit()
    connection.close()


# ============================================================
# GENERATE UNIQUE JOB KEY
# ============================================================

def generate_job_key(job):

    source = str(
        job.get("source", "")
    ).lower().strip()

    company = str(
        job.get("company", "")
    ).lower().strip()

    job_id = str(
        job.get("job_id", "")
    ).lower().strip()

    job_url = str(
        job.get(
            "job_url",
            job.get("url", "")
        )
    ).lower().strip()

    title = str(
        job.get("title", "")
    ).lower().strip()

    location = str(
        job.get("location", "")
    ).lower().strip()


    # --------------------------------------------------------
    # BEST IDENTIFIER
    # --------------------------------------------------------

    if job_id:

        raw_key = (
            f"{source}|"
            f"{company}|"
            f"{job_id}"
        )

    elif job_url:

        raw_key = (
            f"{source}|"
            f"{company}|"
            f"{job_url}"
        )

    else:

        raw_key = (
            f"{source}|"
            f"{company}|"
            f"{title}|"
            f"{location}"
        )


    return hashlib.sha256(
        raw_key.encode("utf-8")
    ).hexdigest()


# ============================================================
# CHECK IF JOB EXISTS
# ============================================================

def job_exists(job):

    job_key = generate_job_key(job)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM jobs
        WHERE job_key = ?
        LIMIT 1
        """,
        (job_key,)
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None


# ============================================================
# CHECK IF JOB ALREADY PROCESSED
# ============================================================

def job_already_processed(job):

    job_key = generate_job_key(job)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT processed
        FROM jobs
        WHERE job_key = ?
        LIMIT 1
        """,
        (job_key,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return False

    return result[0] == 1


# ============================================================
# REGISTER LIGHTWEIGHT JOB
# ============================================================

def register_job(job):

    job_key = generate_job_key(job)

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT OR IGNORE INTO jobs (

                job_key,
                company,
                title,
                location,
                source,
                job_url,
                job_id,
                posted_date,
                notified,
                processed,
                basic_filter_passed,
                experience_passed,
                first_seen,
                last_seen

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, ?, ?)
            """,

            (
                job_key,

                job.get(
                    "company",
                    ""
                ),

                job.get(
                    "title",
                    ""
                ),

                job.get(
                    "location",
                    ""
                ),

                job.get(
                    "source",
                    ""
                ),

                job.get(
                    "job_url",
                    job.get(
                        "url",
                        ""
                    )
                ),

                job.get(
                    "job_id",
                    ""
                ),

                job.get(
                    "posted_date",
                    job.get(
                        "posted_on",
                        job.get(
                            "released_date",
                            ""
                        )
                    )
                ),

                now,
                now,
            )
        )

        inserted = (
            cursor.rowcount > 0
        )

        connection.commit()

        return inserted

    finally:

        connection.close()


# ============================================================
# UPDATE LAST SEEN
# ============================================================

def update_last_seen(job):

    job_key = generate_job_key(job)

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE jobs
        SET last_seen = ?
        WHERE job_key = ?
        """,
        (
            now,
            job_key
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# MARK JOB PROCESSED
# ============================================================

def mark_processed(
    job,
    basic_filter_passed=False,
    experience_passed=False,
    match_result=None
):

    if match_result is None:
        match_result = {}

    job_key = generate_job_key(job)

    connection = get_connection()
    cursor = connection.cursor()

    matched_skills = match_result.get(
        "matched_skills",
        []
    )

    missing_skills = match_result.get(
        "missing_skills",
        []
    )

    if not isinstance(
        matched_skills,
        list
    ):
        matched_skills = []

    if not isinstance(
        missing_skills,
        list
    ):
        missing_skills = []


    cursor.execute(
        """
        UPDATE jobs

        SET
            processed = 1,

            basic_filter_passed = ?,

            experience_passed = ?,

            experience = ?,

            match_score = ?,

            skill_score = ?,

            text_similarity = ?,

            matched_skills = ?,

            missing_skills = ?

        WHERE job_key = ?
        """,

        (
            int(bool(
                basic_filter_passed
            )),

            int(bool(
                experience_passed
            )),

            job.get(
                "experience",
                ""
            ),

            match_result.get(
                "match_score"
            ),

            match_result.get(
                "skill_score"
            ),

            match_result.get(
                "text_similarity"
            ),

            ", ".join(
                matched_skills
            ),

            ", ".join(
                missing_skills
            ),

            job_key,
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# SAVE / UPDATE QUALIFIED JOB
# ============================================================

def save_job(
    job,
    match_result=None
):

    if match_result is None:
        match_result = {}

    if job_already_processed(job):

        return False

    register_job(job)

    mark_processed(
        job,
        basic_filter_passed=True,
        experience_passed=True,
        match_result=match_result
    )

    return True


# ============================================================
# MARK EMAIL AS SENT
# ============================================================

def mark_as_notified(job):

    job_key = generate_job_key(job)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE jobs

        SET notified = 1

        WHERE job_key = ?
        """,
        (job_key,)
    )

    connection.commit()
    connection.close()


# ============================================================
# CHECK NOTIFICATION STATUS
# ============================================================

def was_notified(job):

    job_key = generate_job_key(job)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT notified
        FROM jobs
        WHERE job_key = ?
        LIMIT 1
        """,
        (job_key,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return False

    return result[0] == 1


# ============================================================
# DATABASE STATS
# ============================================================

def get_database_stats():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

            COUNT(*) AS total,

            SUM(
                CASE
                    WHEN processed = 1
                    THEN 1
                    ELSE 0
                END
            ) AS processed,

            SUM(
                CASE
                    WHEN basic_filter_passed = 1
                    THEN 1
                    ELSE 0
                END
            ) AS basic_passed,

            SUM(
                CASE
                    WHEN experience_passed = 1
                    THEN 1
                    ELSE 0
                END
            ) AS experience_passed,

            SUM(
                CASE
                    WHEN match_score >= 80
                    THEN 1
                    ELSE 0
                END
            ) AS matches_80_plus,

            SUM(
                CASE
                    WHEN notified = 1
                    THEN 1
                    ELSE 0
                END
            ) AS notified

        FROM jobs
        """
    )

    row = cursor.fetchone()

    connection.close()

    return {
        "total": row[0] or 0,
        "processed": row[1] or 0,
        "basic_passed": row[2] or 0,
        "experience_passed": row[3] or 0,
        "matches_80_plus": row[4] or 0,
        "notified": row[5] or 0,
    }


# ============================================================
# DATABASE TEST
# ============================================================

if __name__ == "__main__":

    initialize_database()

    print(
        "\nDATABASE MANAGER READY\n"
    )

    print(
        f"Database: {DATABASE_PATH}"
    )

    print(
        "Seen-job tracking: ENABLED"
    )

    print(
        "Processed-job tracking: ENABLED"
    )

    print(
        "80%+ match tracking: ENABLED"
    )

    print(
        "Notification tracking: ENABLED"
    )

    print(
        "\nSTATS:"
    )

    print(
        get_database_stats()
    )
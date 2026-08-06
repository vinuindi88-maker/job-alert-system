# ============================================================
# JOB ALERT SYSTEM - DATABASE
# SQLite Job Tracking + Duplicate Protection
# ============================================================

import os
import sqlite3
import hashlib
from datetime import datetime


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_DIR = os.path.join(
    BASE_DIR,
    "database"
)

DATABASE_FILE = os.path.join(
    DATABASE_DIR,
    "jobs.db"
)


# ============================================================
# CONNECTION
# ============================================================

def get_connection():

    os.makedirs(
        DATABASE_DIR,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# CREATE DATABASE
# ============================================================

def init_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            job_key TEXT UNIQUE NOT NULL,

            company TEXT,

            title TEXT,

            location TEXT,

            source TEXT,

            job_url TEXT,

            first_seen TEXT NOT NULL,

            last_seen TEXT NOT NULL,

            processed INTEGER DEFAULT 0,

            basic_filter_passed INTEGER DEFAULT 0,

            experience_passed INTEGER DEFAULT 0,

            match_score REAL,

            alert_sent INTEGER DEFAULT 0
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_seen_jobs_job_key
        ON seen_jobs(job_key)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_seen_jobs_processed
        ON seen_jobs(processed)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_seen_jobs_alert_sent
        ON seen_jobs(alert_sent)
        """
    )

    connection.commit()

    connection.close()


# ============================================================
# GENERATE UNIQUE JOB KEY
# ============================================================

def generate_job_key(job):

    source = str(
        job.get(
            "source",
            ""
        )
    ).strip().lower()

    company = str(
        job.get(
            "company",
            ""
        )
    ).strip().lower()

    job_id = str(
        job.get(
            "job_id",
            ""
        )
    ).strip().lower()

    job_url = str(
        job.get(
            "job_url",
            job.get(
                "url",
                ""
            )
        )
    ).strip().lower()

    title = str(
        job.get(
            "title",
            ""
        )
    ).strip().lower()

    location = str(
        job.get(
            "location",
            ""
        )
    ).strip().lower()


    # Prefer ATS job ID when available.

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
        raw_key.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================
# CHECK IF JOB EXISTS
# ============================================================

def job_exists(job):

    job_key = generate_job_key(
        job
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM seen_jobs
        WHERE job_key = ?
        LIMIT 1
        """,
        (
            job_key,
        )
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None


# ============================================================
# REGISTER NEW JOB
# ============================================================

def register_job(job):

    job_key = generate_job_key(
        job
    )

    now = datetime.utcnow().isoformat()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO seen_jobs (
            job_key,
            company,
            title,
            location,
            source,
            job_url,
            first_seen,
            last_seen
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

            now,

            now,
        )
    )

    inserted = (
        cursor.rowcount > 0
    )

    connection.commit()

    connection.close()

    return inserted


# ============================================================
# UPDATE LAST SEEN
# ============================================================

def update_last_seen(job):

    job_key = generate_job_key(
        job
    )

    now = datetime.utcnow().isoformat()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE seen_jobs
        SET last_seen = ?
        WHERE job_key = ?
        """,
        (
            now,
            job_key,
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
    match_score=None
):

    job_key = generate_job_key(
        job
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE seen_jobs
        SET
            processed = 1,
            basic_filter_passed = ?,
            experience_passed = ?,
            match_score = ?
        WHERE job_key = ?
        """,
        (
            int(
                bool(
                    basic_filter_passed
                )
            ),

            int(
                bool(
                    experience_passed
                )
            ),

            match_score,

            job_key,
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# MARK ALERT SENT
# ============================================================

def mark_alert_sent(job):

    job_key = generate_job_key(
        job
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE seen_jobs
        SET alert_sent = 1
        WHERE job_key = ?
        """,
        (
            job_key,
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# CHECK ALERT STATUS
# ============================================================

def alert_already_sent(job):

    job_key = generate_job_key(
        job
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT alert_sent
        FROM seen_jobs
        WHERE job_key = ?
        LIMIT 1
        """,
        (
            job_key,
        )
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return False

    return bool(
        row["alert_sent"]
    )


# ============================================================
# GET DATABASE STATS
# ============================================================

def get_database_stats():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_jobs,

            SUM(
                CASE
                    WHEN processed = 1
                    THEN 1
                    ELSE 0
                END
            ) AS processed_jobs,

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
                    WHEN alert_sent = 1
                    THEN 1
                    ELSE 0
                END
            ) AS alerts_sent

        FROM seen_jobs
        """
    )

    row = cursor.fetchone()

    connection.close()

    return {
        "total_jobs":
            row["total_jobs"] or 0,

        "processed_jobs":
            row["processed_jobs"] or 0,

        "basic_passed":
            row["basic_passed"] or 0,

        "experience_passed":
            row["experience_passed"] or 0,

        "matches_80_plus":
            row["matches_80_plus"] or 0,

        "alerts_sent":
            row["alerts_sent"] or 0,
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    init_database()

    print(
        "\nDATABASE READY\n"
    )

    print(
        f"Database: {DATABASE_FILE}"
    )

    print(
        "Duplicate tracking: ENABLED"
    )

    print(
        "Processed-job tracking: ENABLED"
    )

    print(
        "80%+ match tracking: ENABLED"
    )

    print(
        "Alert tracking: ENABLED"
    )
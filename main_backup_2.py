# ============================================================
# JOB ALERT SYSTEM - FINAL PIPELINE WITH SAFE DRY RUN
# ============================================================

from scrapers.router import (
    scrape_all_companies,
    fetch_job_details,
)

from config.filters import basic_job_filter

from matcher.experience_filter import check_experience

from matcher.ats_match import (
    calculate_match,
    MIN_MATCH_SCORE,
)

from database.db_manager import (
    initialize_database,
    job_exists,
    save_job,
    mark_as_notified,
)

from notifications.gmail import send_job_alert


# ============================================================
# SETTINGS
# ============================================================

# IMPORTANT:
# True  = real jobs checked, NO EMAIL
# False = production mode, Gmail enabled

DRY_RUN = False


# ============================================================
# FETCH FULL JOB DESCRIPTION
# ============================================================

def load_full_job_details(job):

    company = job.get(
        "company",
        "Unknown Company"
    )

    title = job.get(
        "title",
        "Unknown Role"
    )

    try:

        detailed_job = fetch_job_details(
            job
        )

    except Exception as error:

        print(
            f"DETAIL FETCH ERROR: "
            f"{company} | {title} | {error}"
        )

        return None

    if not detailed_job:

        print(
            "REJECTED: Could not fetch job details"
        )

        return None

    description = detailed_job.get(
        "description",
        ""
    )

    if not description or not description.strip():

        print(
            "REJECTED: Job description missing"
        )

        return None

    return detailed_job


# ============================================================
# PROCESS ONE JOB
# ============================================================

def process_job(job):

    company = job.get(
        "company",
        "Unknown Company"
    )

    title = job.get(
        "title",
        "Unknown Role"
    )

    location = job.get(
        "location",
        ""
    )

    source = job.get(
        "source",
        "unknown"
    )

    print(
        "\n"
        "=========================================="
    )

    print(
        f"CHECKING: {company} | {title}"
    )

    print(
        f"LOCATION: {location}"
    )

    print(
        f"SOURCE: {source}"
    )


    # ========================================================
    # STEP 1 - STRICT BASIC FILTER
    #
    # Checks:
    # - <= 48 hours
    # - India
    # - relevant target role
    # - not senior
    # ========================================================

    try:

        basic_passed, basic_reason = (
            basic_job_filter(
                job
            )
        )

    except Exception as error:

        print(
            f"BASIC FILTER ERROR: {error}"
        )

        return {
            "status": "basic_rejected",
            "qualified": False
        }


    if not basic_passed:

        print(
            f"REJECTED BASIC: {basic_reason}"
        )

        return {
            "status": "basic_rejected",
            "qualified": False
        }


    print(
        f"PASSED BASIC: {basic_reason}"
    )


    # ========================================================
    # STEP 2 - FETCH FULL JD
    # ========================================================

    print(
        "FETCHING FULL JD..."
    )


    detailed_job = load_full_job_details(
        job
    )


    if detailed_job is None:

        return {
            "status": "detail_failed",
            "qualified": False
        }


    job = detailed_job


    description = job.get(
        "description",
        ""
    )


    print(
        "FULL JD: Loaded"
    )


    # ========================================================
    # STEP 3 - EXPERIENCE FILTER
    #
    # Desired:
    # Fresher / Entry level / 0-2 years
    #
    # Clearly >2 years = reject
    # Unclear requirement = allow
    # ========================================================

    try:

        experience_passed, experience_reason = (
            check_experience(
                description
            )
        )

    except Exception as error:

        print(
            f"EXPERIENCE FILTER ERROR: {error}"
        )

        return {
            "status": "experience_error",
            "qualified": False
        }


    if not experience_passed:

        print(
            f"REJECTED EXPERIENCE: "
            f"{experience_reason}"
        )

        return {
            "status": "experience_rejected",
            "qualified": False
        }


    print(
        f"PASSED EXPERIENCE: "
        f"{experience_reason}"
    )


    # ========================================================
    # STEP 4 - DUPLICATE CHECK
    # ========================================================

    try:

        already_exists = job_exists(
            job
        )

    except Exception as error:

        print(
            f"DATABASE CHECK ERROR: {error}"
        )

        return {
            "status": "database_error",
            "qualified": False
        }


    if already_exists:

        print(
            "SKIPPED: Job already processed"
        )

        return {
            "status": "duplicate",
            "qualified": False
        }


    # ========================================================
    # STEP 5 - RESUME/JD MATCH
    # ========================================================

    try:

        match_result = calculate_match(
            description
        )

    except Exception as error:

        print(
            f"RESUME MATCH ERROR: {error}"
        )

        return {
            "status": "match_error",
            "qualified": False
        }


    match_score = float(
        match_result.get(
            "match_score",
            0
        )
    )


    skill_score = float(
        match_result.get(
            "skill_score",
            0
        )
    )


    text_similarity = float(
        match_result.get(
            "text_similarity",
            0
        )
    )


    recognized_skills = int(
        match_result.get(
            "recognized_job_skill_count",
            0
        )
    )


    matched_skill_count = int(
        match_result.get(
            "matched_skill_count",
            0
        )
    )


    print(
        f"FINAL MATCH SCORE : "
        f"{match_score:.2f}%"
    )

    print(
        f"SKILL COVERAGE    : "
        f"{skill_score:.2f}%"
    )

    print(
        f"TEXT SIMILARITY   : "
        f"{text_similarity:.2f}%"
    )

    print(
        f"JD SKILLS FOUND   : "
        f"{recognized_skills}"
    )

    print(
        f"SKILLS MATCHED    : "
        f"{matched_skill_count}"
    )


    matched_skills = match_result.get(
        "matched_skills",
        []
    )


    missing_skills = match_result.get(
        "missing_skills",
        []
    )


    if matched_skills:

        print(
            "MATCHED SKILLS    : "
            + ", ".join(
                matched_skills
            )
        )


    if missing_skills:

        print(
            "MISSING SKILLS    : "
            + ", ".join(
                missing_skills
            )
        )


    # ========================================================
    # STEP 6 - STRICT 80% THRESHOLD
    # ========================================================

    if match_score < MIN_MATCH_SCORE:

        print(
            f"REJECTED MATCH: "
            f"{match_score:.2f}% < "
            f"{MIN_MATCH_SCORE}%"
        )

        return {
            "status": "match_rejected",
            "qualified": False
        }


    if not match_result.get(
        "passed",
        False
    ):

        print(
            "REJECTED MATCH: "
            "Matcher did not approve job"
        )

        return {
            "status": "match_rejected",
            "qualified": False
        }


    print(
        f"QUALIFIED: "
        f"{match_score:.2f}% >= "
        f"{MIN_MATCH_SCORE}%"
    )


    # ========================================================
    # STEP 7 - DRY RUN
    #
    # IMPORTANT:
    # No database save.
    # No Gmail.
    # No notified flag.
    # ========================================================

    if DRY_RUN:

        print(
            "DRY RUN: QUALIFIED JOB FOUND"
        )

        print(
            "DRY RUN: Gmail NOT sent"
        )

        print(
            "DRY RUN: Database NOT modified"
        )

        return {
            "status": "dry_run_qualified",
            "qualified": True
        }


    # ========================================================
    # STEP 8 - PRODUCTION DATABASE SAVE
    # ========================================================

    try:

        saved = save_job(
            job,
            match_result
        )

    except Exception as error:

        print(
            f"DATABASE SAVE ERROR: {error}"
        )

        return {
            "status": "database_error",
            "qualified": False
        }


    if not saved:

        print(
            "SKIPPED: Job already saved"
        )

        return {
            "status": "duplicate",
            "qualified": False
        }


    print(
        "DATABASE: Qualified job saved"
    )


    # ========================================================
    # STEP 9 - SEND GMAIL
    # ========================================================

    try:

        email_sent = send_job_alert(
            job,
            match_result
        )

    except Exception as error:

        print(
            f"EMAIL ERROR: {error}"
        )

        return {
            "status": "email_error",
            "qualified": True
        }


    if not email_sent:

        print(
            "WARNING: Job saved but Gmail not sent"
        )

        return {
            "status": "email_failed",
            "qualified": True
        }


    # ========================================================
    # STEP 10 - MARK NOTIFIED
    # ========================================================

    try:

        mark_as_notified(
            job
        )

    except Exception as error:

        print(
            f"NOTIFICATION DATABASE ERROR: "
            f"{error}"
        )

        return {
            "status": "notification_db_error",
            "qualified": True
        }


    print(
        "SUCCESS: Gmail alert sent"
    )


    return {
        "status": "email_sent",
        "qualified": True
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n"
        "=========================================="
    )

    print(
        "          JOB ALERT SYSTEM"
    )

    print(
        "=========================================="
    )


    if DRY_RUN:

        print(
            "MODE: DRY RUN"
        )

        print(
            "GMAIL: DISABLED"
        )

        print(
            "DATABASE WRITES: DISABLED"
        )

    else:

        print(
            "MODE: PRODUCTION"
        )

        print(
            "GMAIL: ENABLED"
        )

        print(
            "DATABASE WRITES: ENABLED"
        )


    # ========================================================
    # DATABASE INITIALIZATION
    # ========================================================

    try:

        initialize_database()

        print(
            "DATABASE: Ready"
        )

    except Exception as error:

        print(
            f"DATABASE INITIALIZATION ERROR: "
            f"{error}"
        )

        return


    # ========================================================
    # FETCH LIGHTWEIGHT JOBS
    # ========================================================

    print(
        "\nFetching lightweight jobs "
        "from official career systems...\n"
    )


    try:

        jobs = scrape_all_companies()

    except Exception as error:

        print(
            f"SCRAPER SYSTEM ERROR: {error}"
        )

        return


    if not jobs:

        print(
            "No jobs fetched."
        )

        return


    # ========================================================
    # COUNTERS
    # ========================================================

    total_jobs = len(
        jobs
    )

    checked = 0

    basic_passed_count = 0

    experience_passed_count = 0

    match_passed_count = 0

    alerts_sent = 0


    # ========================================================
    # PROCESS ALL JOBS
    # ========================================================

    for job in jobs:

        checked += 1


        print(
            "\n"
            "------------------------------------------"
        )

        print(
            f"JOB {checked}/{total_jobs}"
        )

        print(
            "------------------------------------------"
        )


        try:

            result = process_job(
                job
            )


            status = result.get(
                "status",
                ""
            )


            if status not in (
                "basic_rejected",
                "detail_failed"
            ):

                basic_passed_count += 1


            if status in (

                "match_rejected",
                "dry_run_qualified",
                "email_sent",
                "email_error",
                "email_failed",
                "notification_db_error",

            ):

                experience_passed_count += 1


            if result.get(
                "qualified",
                False
            ):

                match_passed_count += 1


            if status == "email_sent":

                alerts_sent += 1


        except KeyboardInterrupt:

            print(
                "\n\nSystem stopped by user."
            )

            return


        except Exception as error:

            print(
                f"UNEXPECTED JOB ERROR: "
                f"{error}"
            )

            continue


    # ========================================================
    # FINAL REPORT
    # ========================================================

    print(
        "\n"
        "=========================================="
    )

    print(
        "              RUN COMPLETE"
    )

    print(
        "=========================================="
    )

    print(
        f"Listings fetched       : "
        f"{total_jobs}"
    )

    print(
        f"Listings checked       : "
        f"{checked}"
    )

    print(
        f"Basic filter passed    : "
        f"{basic_passed_count}"
    )

    print(
        f"Experience passed      : "
        f"{experience_passed_count}"
    )

    print(
        f"80%+ matches           : "
        f"{match_passed_count}"
    )


    if DRY_RUN:

        print(
            "Gmail alerts sent      : 0 "
            "(DRY RUN)"
        )

    else:

        print(
            f"Gmail alerts sent      : "
            f"{alerts_sent}"
        )


    print(
        "==========================================\n"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
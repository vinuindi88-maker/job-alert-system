# ============================================================
# JOB ALERT SYSTEM - ASHBY SCRAPER
# Two-stage + Retry Protection + Duplicate Protection
# ============================================================

import html
import re
import requests

from scrapers.http_client import get


# ============================================================
# SETTINGS
# ============================================================

REQUEST_TIMEOUT = 30

ASHBY_API = "https://api.ashbyhq.com/posting-api/job-board"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


# ============================================================
# CLEAN HTML
# ============================================================

def clean_html(value):

    if not value:
        return ""

    value = html.unescape(str(value))

    value = re.sub(
        r"<br\s*/?>",
        "\n",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        r"</p>",
        "\n",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        r"<li[^>]*>",
        "\n- ",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        r"</li>",
        "",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        r"<[^>]+>",
        " ",
        value
    )

    value = re.sub(
        r"[ \t]+",
        " ",
        value
    )

    value = re.sub(
        r"\n\s*\n+",
        "\n",
        value
    )

    return value.strip()


# ============================================================
# BUILD BOARD URL
# ============================================================

def build_board_url(board_name):

    board_name = str(
        board_name
    ).strip().strip("/")

    return (
        f"{ASHBY_API}/"
        f"{board_name}"
    )


# ============================================================
# EXTRACT LOCATION
# ============================================================

def extract_location(posting):

    location = (
        posting.get("location")
        or ""
    )

    if isinstance(location, dict):

        location = (
            location.get("name")
            or location.get("text")
            or ""
        )

    if isinstance(location, list):

        location = ", ".join(
            str(item)
            for item in location
            if item
        )

    return str(location).strip()


# ============================================================
# FETCH LIGHTWEIGHT JOBS
# ============================================================

def fetch_ashby_jobs(
    company_name,
    board_name
):
    """
    Stage 1:
    Fetch lightweight Ashby listings.

    Ashby's board API may already return descriptions.
    We intentionally do NOT keep them during Stage 1.

    Full JD is obtained only after the job passes
    the broad title/location filter.
    """

    jobs = []

    if not board_name:

        print(
            f"[ASHBY CONFIG ERROR] "
            f"{company_name}: board_name missing"
        )

        return jobs


    url = build_board_url(
        board_name
    )


    try:

        response = get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            polite_delay=0.10
        )

        response.raise_for_status()

        data = response.json()


    except requests.RequestException as error:

        print(
            f"[ASHBY ERROR] "
            f"{company_name}: {error}"
        )

        return jobs


    except ValueError as error:

        print(
            f"[ASHBY JSON ERROR] "
            f"{company_name}: {error}"
        )

        return jobs


    postings = data.get(
        "jobs",
        []
    )


    if not isinstance(postings, list):

        print(
            f"[ASHBY ERROR] "
            f"{company_name}: unexpected API response"
        )

        return jobs


    seen_jobs = set()


    for posting in postings:

        if not isinstance(posting, dict):
            continue


        # ----------------------------------------------------
        # JOB ID
        # ----------------------------------------------------

        job_id = (
            posting.get("id")
            or posting.get("jobId")
            or ""
        )


        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = (
            posting.get("title")
            or ""
        ).strip()


        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        location = extract_location(
            posting
        )


        # ----------------------------------------------------
        # PUBLIC URL
        # ----------------------------------------------------

        public_url = (
            posting.get("jobUrl")
            or posting.get("applyUrl")
            or posting.get("url")
            or ""
        ).strip()


        # ----------------------------------------------------
        # DUPLICATE PROTECTION
        # ----------------------------------------------------

        unique_key = (
            str(job_id)
            if job_id
            else (
                f"{title}|"
                f"{location}|"
                f"{public_url}"
            )
        )


        if unique_key in seen_jobs:
            continue


        seen_jobs.add(
            unique_key
        )


        # ----------------------------------------------------
        # LIGHTWEIGHT JOB
        # ----------------------------------------------------

        jobs.append(
            {
                "company": company_name,

                "title": title,

                "location": location,

                "description": "",

                "url": public_url,

                "job_url": public_url,

                "source": "ashby",

                # Required for Stage 2
                "board_name": board_name,

                "job_id": job_id,

                # Useful lightweight metadata
                "department": (
                    posting.get("department")
                    or ""
                ),

                "team": (
                    posting.get("team")
                    or ""
                ),

                "employment_type": (
                    posting.get("employmentType")
                    or ""
                ),

                "workplace_type": (
                    posting.get("workplaceType")
                    or ""
                ),

                "published_at": (
                    posting.get("publishedAt")
                    or ""
                ),
            }
        )


    return jobs


# ============================================================
# FETCH FULL JOB DETAILS
# ============================================================

def fetch_ashby_job_details(job):
    """
    Stage 2:
    Fetch/recover full JD for ONE shortlisted Ashby job.

    Ashby's public board endpoint returns the board's jobs,
    so we request the board again and locate the selected
    job by ID or URL.
    """

    if not isinstance(job, dict):
        return job


    board_name = job.get(
        "board_name"
    )

    job_id = job.get(
        "job_id"
    )

    original_url = (
        job.get("url")
        or job.get("job_url")
        or ""
    )


    if not board_name:

        raise ValueError(
            "Ashby job is missing board_name."
        )


    url = build_board_url(
        board_name
    )


    try:

        response = get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            polite_delay=0.10
        )

        response.raise_for_status()

        data = response.json()


    except requests.RequestException as error:

        raise RuntimeError(
            f"Ashby detail request failed: {error}"
        )


    except ValueError as error:

        raise RuntimeError(
            f"Invalid Ashby detail response: {error}"
        )


    postings = data.get(
        "jobs",
        []
    )


    if not isinstance(postings, list):

        raise RuntimeError(
            "Unexpected Ashby detail response."
        )


    matched_posting = None


    # ========================================================
    # FIND SELECTED JOB
    # ========================================================

    for posting in postings:

        if not isinstance(posting, dict):
            continue


        posting_id = (
            posting.get("id")
            or posting.get("jobId")
            or ""
        )

        posting_url = (
            posting.get("jobUrl")
            or posting.get("applyUrl")
            or posting.get("url")
            or ""
        )


        if (
            job_id
            and str(posting_id) == str(job_id)
        ):

            matched_posting = posting
            break


        if (
            original_url
            and posting_url
            and posting_url == original_url
        ):

            matched_posting = posting
            break


    if matched_posting is None:

        raise RuntimeError(
            "Selected Ashby job was not found "
            "on the current job board."
        )


    # ========================================================
    # DESCRIPTION
    # ========================================================

    description = (
        matched_posting.get("descriptionHtml")
        or matched_posting.get("description")
        or matched_posting.get("jobDescription")
        or ""
    )


    description = clean_html(
        description
    )


    # ========================================================
    # TITLE
    # ========================================================

    title = (
        matched_posting.get("title")
        or job.get("title", "")
    )


    # ========================================================
    # LOCATION
    # ========================================================

    location = (
        extract_location(
            matched_posting
        )
        or job.get("location", "")
    )


    # ========================================================
    # URL
    # ========================================================

    public_url = (
        matched_posting.get("jobUrl")
        or matched_posting.get("applyUrl")
        or matched_posting.get("url")
        or original_url
    )


    # ========================================================
    # COPY + UPDATE
    # ========================================================

    detailed_job = dict(
        job
    )


    detailed_job.update(
        {
            "title": title,

            "location": location,

            "description": description,

            "url": public_url,

            "job_url": public_url,

            "source": "ashby",

            "job_id": (
                matched_posting.get("id")
                or matched_posting.get("jobId")
                or job_id
            ),

            "department": (
                matched_posting.get("department")
                or job.get("department", "")
            ),

            "team": (
                matched_posting.get("team")
                or job.get("team", "")
            ),

            "employment_type": (
                matched_posting.get("employmentType")
                or job.get("employment_type", "")
            ),

            "workplace_type": (
                matched_posting.get("workplaceType")
                or job.get("workplace_type", "")
            ),

            "published_at": (
                matched_posting.get("publishedAt")
                or job.get("published_at", "")
            ),
        }
    )


    return detailed_job


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\nASHBY SCRAPER READY\n"
    )

    print(
        "Two-stage Ashby scraper "
        "loaded successfully."
    )

    print(
        "Lightweight listings: ENABLED"
    )

    print(
        "Full JD on demand: ENABLED"
    )

    print(
        "HTTP retry/backoff: ENABLED"
    )

    print(
        "Duplicate protection: ENABLED"
    )
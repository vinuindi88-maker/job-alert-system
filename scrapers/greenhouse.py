# ============================================================
# JOB ALERT SYSTEM - GREENHOUSE SCRAPER
# Two-stage + Retry Protection
# ============================================================

import html
import re
import requests

from scrapers.http_client import get


# ============================================================
# SETTINGS
# ============================================================

REQUEST_TIMEOUT = 30

GREENHOUSE_API = (
    "https://boards-api.greenhouse.io/v1/boards"
)

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

    value = html.unescape(
        str(value)
    )

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

def build_board_url(board_token):

    board_token = str(
        board_token
    ).strip().strip("/")

    return (
        f"{GREENHOUSE_API}/"
        f"{board_token}/jobs"
    )


# ============================================================
# BUILD DETAIL URL
# ============================================================

def build_detail_url(
    board_token,
    job_id
):

    board_token = str(
        board_token
    ).strip().strip("/")

    return (
        f"{GREENHOUSE_API}/"
        f"{board_token}/jobs/"
        f"{job_id}"
    )


# ============================================================
# FETCH LIGHTWEIGHT JOBS
# ============================================================

def fetch_greenhouse_jobs(
    company_name,
    board_token
):
    """
    Stage 1

    Fetch Greenhouse job listings.

    Full descriptions are intentionally NOT requested.

    The full JD is downloaded only when the job passes
    the lightweight filters.
    """

    jobs = []

    if not board_token:

        print(
            f"[GREENHOUSE CONFIG ERROR] "
            f"{company_name}: board_token missing"
        )

        return jobs


    url = build_board_url(
        board_token
    )


    try:

        response = get(
            url,
            headers=HEADERS,
            params={
                "content": "false"
            },
            timeout=REQUEST_TIMEOUT,
            polite_delay=0.10
        )

        response.raise_for_status()

        data = response.json()


    except requests.RequestException as error:

        print(
            f"[GREENHOUSE ERROR] "
            f"{company_name}: {error}"
        )

        return jobs


    except ValueError as error:

        print(
            f"[GREENHOUSE JSON ERROR] "
            f"{company_name}: {error}"
        )

        return jobs


    postings = data.get(
        "jobs",
        []
    )


    if not isinstance(
        postings,
        list
    ):

        return jobs


    seen_ids = set()


    for posting in postings:

        job_id = posting.get(
            "id"
        )


        # ----------------------------------------------------
        # DUPLICATE PROTECTION
        # ----------------------------------------------------

        if job_id is not None:

            unique_key = str(
                job_id
            )

        else:

            unique_key = (
                f"{posting.get('title', '')}|"
                f"{posting.get('absolute_url', '')}"
            )


        if unique_key in seen_ids:
            continue


        seen_ids.add(
            unique_key
        )


        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = (
            posting.get(
                "title"
            )
            or ""
        ).strip()


        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        location_data = posting.get(
            "location",
            {}
        )


        if isinstance(
            location_data,
            dict
        ):

            location = (
                location_data.get(
                    "name"
                )
                or ""
            ).strip()

        else:

            location = str(
                location_data or ""
            ).strip()


        # ----------------------------------------------------
        # PUBLIC JOB URL
        # ----------------------------------------------------

        public_url = (
            posting.get(
                "absolute_url"
            )
            or ""
        ).strip()


        # ----------------------------------------------------
        # LIGHTWEIGHT JOB
        # ----------------------------------------------------

        jobs.append(
            {
                "company": company_name,

                "title": title,

                "location": location,

                # Stage 1:
                # intentionally empty.
                "description": "",

                "url": public_url,

                "job_url": public_url,

                "source": "greenhouse",

                # Required for Stage 2
                "board_token": board_token,

                "job_id": job_id,

                # Useful metadata
                "updated_at": (
                    posting.get(
                        "updated_at"
                    )
                    or ""
                ),
            }
        )


    return jobs


# ============================================================
# FETCH FULL JOB DETAILS
# ============================================================

def fetch_greenhouse_job_details(job):
    """
    Stage 2

    Fetch full Greenhouse JD for ONE shortlisted job.
    """

    if not isinstance(
        job,
        dict
    ):

        return job


    board_token = job.get(
        "board_token"
    )

    job_id = job.get(
        "job_id"
    )


    if not board_token or job_id is None:

        raise ValueError(
            "Greenhouse job is missing "
            "board_token or job_id."
        )


    url = build_detail_url(
        board_token,
        job_id
    )


    try:

        response = get(
            url,
            headers=HEADERS,
            params={
                "content": "true"
            },
            timeout=REQUEST_TIMEOUT,
            polite_delay=0.10
        )

        response.raise_for_status()

        data = response.json()


    except requests.RequestException as error:

        raise RuntimeError(
            f"Greenhouse detail request failed: "
            f"{error}"
        )


    except ValueError as error:

        raise RuntimeError(
            f"Invalid Greenhouse detail response: "
            f"{error}"
        )


    # ========================================================
    # DESCRIPTION
    # ========================================================

    description = clean_html(
        data.get(
            "content",
            ""
        )
    )


    # ========================================================
    # TITLE
    # ========================================================

    title = (
        data.get(
            "title"
        )
        or job.get(
            "title",
            ""
        )
    )


    # ========================================================
    # LOCATION
    # ========================================================

    location_data = data.get(
        "location",
        {}
    )


    if isinstance(
        location_data,
        dict
    ):

        location = (
            location_data.get(
                "name"
            )
            or job.get(
                "location",
                ""
            )
        )

    else:

        location = (
            str(
                location_data
            ).strip()
            or job.get(
                "location",
                ""
            )
        )


    # ========================================================
    # PUBLIC URL
    # ========================================================

    public_url = (
        data.get(
            "absolute_url"
        )
        or job.get(
            "url",
            ""
        )
    )


    # ========================================================
    # COPY ORIGINAL
    # ========================================================

    detailed_job = dict(
        job
    )


    # ========================================================
    # UPDATE
    # ========================================================

    detailed_job.update(
        {
            "title": title,

            "location": location,

            "description": description,

            "url": public_url,

            "job_url": public_url,

            "source": "greenhouse",

            "job_id": (
                data.get(
                    "id"
                )
                or job_id
            ),

            "updated_at": (
                data.get(
                    "updated_at"
                )
                or job.get(
                    "updated_at",
                    ""
                )
            ),
        }
    )


    # ========================================================
    # DEPARTMENTS
    # ========================================================

    departments = data.get(
        "departments",
        []
    )


    if isinstance(
        departments,
        list
    ):

        detailed_job[
            "departments"
        ] = [
            department.get(
                "name",
                ""
            )

            for department
            in departments

            if isinstance(
                department,
                dict
            )
        ]


    # ========================================================
    # OFFICES
    # ========================================================

    offices = data.get(
        "offices",
        []
    )


    if isinstance(
        offices,
        list
    ):

        detailed_job[
            "offices"
        ] = [
            office.get(
                "name",
                ""
            )

            for office
            in offices

            if isinstance(
                office,
                dict
            )
        ]


    return detailed_job


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\nGREENHOUSE SCRAPER READY\n"
    )

    print(
        "Two-stage Greenhouse scraper "
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
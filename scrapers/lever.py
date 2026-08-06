# ============================================================
# JOB ALERT SYSTEM - LEVER SCRAPER
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

LEVER_API = "https://api.lever.co/v0/postings"

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
# BUILD COMPANY API URL
# ============================================================

def build_company_url(company_slug):

    company_slug = str(
        company_slug
    ).strip().strip("/")

    return (
        f"{LEVER_API}/"
        f"{company_slug}"
    )


# ============================================================
# BUILD DETAIL API URL
# ============================================================

def build_detail_url(
    company_slug,
    job_id
):

    company_slug = str(
        company_slug
    ).strip().strip("/")

    job_id = str(
        job_id
    ).strip()

    return (
        f"{LEVER_API}/"
        f"{company_slug}/"
        f"{job_id}"
    )


# ============================================================
# EXTRACT LOCATION
# ============================================================

def extract_location(posting):

    categories = posting.get(
        "categories",
        {}
    )

    if not isinstance(
        categories,
        dict
    ):
        categories = {}


    location = (
        categories.get(
            "location"
        )
        or posting.get(
            "location"
        )
        or ""
    )


    if isinstance(
        location,
        list
    ):

        location = ", ".join(
            str(item)
            for item in location
            if item
        )


    return str(
        location
    ).strip()


# ============================================================
# FETCH LIGHTWEIGHT JOBS
# ============================================================

def fetch_lever_jobs(
    company_name,
    company_slug
):
    """
    Stage 1

    Fetch lightweight Lever listings.

    Full JD text is intentionally discarded at this stage.

    Lever's public postings endpoint may return job content
    in the listing response itself, but storing/processing it
    for every job would waste memory and CPU.

    Full details are fetched only for shortlisted jobs.
    """

    jobs = []


    if not company_slug:

        print(
            f"[LEVER CONFIG ERROR] "
            f"{company_name}: "
            f"company_slug missing"
        )

        return jobs


    url = build_company_url(
        company_slug
    )


    try:

        response = get(
            url,
            headers=HEADERS,
            params={
                "mode": "json"
            },
            timeout=REQUEST_TIMEOUT,
            polite_delay=0.10
        )

        response.raise_for_status()

        data = response.json()


    except requests.RequestException as error:

        print(
            f"[LEVER ERROR] "
            f"{company_name}: "
            f"{error}"
        )

        return jobs


    except ValueError as error:

        print(
            f"[LEVER JSON ERROR] "
            f"{company_name}: "
            f"{error}"
        )

        return jobs


    if not isinstance(
        data,
        list
    ):

        print(
            f"[LEVER ERROR] "
            f"{company_name}: "
            f"unexpected API response"
        )

        return jobs


    seen_jobs = set()


    for posting in data:

        if not isinstance(
            posting,
            dict
        ):
            continue


        # ----------------------------------------------------
        # JOB ID
        # ----------------------------------------------------

        job_id = (
            posting.get(
                "id"
            )
            or ""
        )


        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = (
            posting.get(
                "text"
            )
            or posting.get(
                "title"
            )
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
            posting.get(
                "hostedUrl"
            )
            or posting.get(
                "applyUrl"
            )
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
        # CATEGORIES
        # ----------------------------------------------------

        categories = posting.get(
            "categories",
            {}
        )

        if not isinstance(
            categories,
            dict
        ):
            categories = {}


        # ----------------------------------------------------
        # LIGHTWEIGHT JOB OBJECT
        # ----------------------------------------------------

        jobs.append(
            {
                "company": company_name,

                "title": title,

                "location": location,

                # Stage 1 intentionally empty
                "description": "",

                "url": public_url,

                "job_url": public_url,

                "source": "lever",

                # Required for Stage 2
                "company_slug": company_slug,

                "job_id": job_id,

                # Lightweight metadata
                "team": (
                    categories.get(
                        "team"
                    )
                    or ""
                ),

                "department": (
                    categories.get(
                        "department"
                    )
                    or ""
                ),

                "commitment": (
                    categories.get(
                        "commitment"
                    )
                    or ""
                ),

                "workplace_type": (
                    posting.get(
                        "workplaceType"
                    )
                    or ""
                ),

                "created_at": (
                    posting.get(
                        "createdAt"
                    )
                    or ""
                ),
            }
        )


    return jobs


# ============================================================
# FETCH FULL JOB DETAILS
# ============================================================

def fetch_lever_job_details(job):
    """
    Stage 2

    Fetch full JD for ONE shortlisted Lever job.
    """

    if not isinstance(
        job,
        dict
    ):

        return job


    company_slug = job.get(
        "company_slug"
    )

    job_id = job.get(
        "job_id"
    )


    if not company_slug or not job_id:

        raise ValueError(
            "Lever job is missing "
            "company_slug or job_id."
        )


    url = build_detail_url(
        company_slug,
        job_id
    )


    try:

        response = get(
            url,
            headers=HEADERS,
            params={
                "mode": "json"
            },
            timeout=REQUEST_TIMEOUT,
            polite_delay=0.10
        )

        response.raise_for_status()

        data = response.json()


    except requests.RequestException as error:

        raise RuntimeError(
            f"Lever detail request failed: "
            f"{error}"
        )


    except ValueError as error:

        raise RuntimeError(
            f"Invalid Lever detail response: "
            f"{error}"
        )


    if not isinstance(
        data,
        dict
    ):

        raise RuntimeError(
            "Unexpected Lever detail response."
        )


    # ========================================================
    # DESCRIPTION
    # ========================================================

    description_parts = []


    # Main description
    description = clean_html(
        data.get(
            "description",
            ""
        )
    )

    if description:

        description_parts.append(
            description
        )


    # Additional Lever sections
    lists = data.get(
        "lists",
        []
    )


    if isinstance(
        lists,
        list
    ):

        for section in lists:

            if not isinstance(
                section,
                dict
            ):
                continue


            section_title = clean_html(
                section.get(
                    "text",
                    ""
                )
            )


            section_content = clean_html(
                section.get(
                    "content",
                    ""
                )
            )


            if section_title:

                description_parts.append(
                    section_title
                )


            if section_content:

                description_parts.append(
                    section_content
                )


    # Closing / additional text
    additional = clean_html(
        data.get(
            "additional",
            ""
        )
    )


    if additional:

        description_parts.append(
            additional
        )


    full_description = "\n\n".join(
        part
        for part in description_parts
        if part
    ).strip()


    # ========================================================
    # TITLE
    # ========================================================

    title = (
        data.get(
            "text"
        )
        or data.get(
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

    location = (
        extract_location(
            data
        )
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
            "hostedUrl"
        )
        or data.get(
            "applyUrl"
        )
        or job.get(
            "url",
            ""
        )
    )


    # ========================================================
    # CATEGORIES
    # ========================================================

    categories = data.get(
        "categories",
        {}
    )


    if not isinstance(
        categories,
        dict
    ):

        categories = {}


    # ========================================================
    # COPY ORIGINAL JOB
    # ========================================================

    detailed_job = dict(
        job
    )


    # ========================================================
    # UPDATE FULL DETAILS
    # ========================================================

    detailed_job.update(
        {
            "title": title,

            "location": location,

            "description": full_description,

            "url": public_url,

            "job_url": public_url,

            "source": "lever",

            "job_id": (
                data.get(
                    "id"
                )
                or job_id
            ),

            "team": (
                categories.get(
                    "team"
                )
                or job.get(
                    "team",
                    ""
                )
            ),

            "department": (
                categories.get(
                    "department"
                )
                or job.get(
                    "department",
                    ""
                )
            ),

            "commitment": (
                categories.get(
                    "commitment"
                )
                or job.get(
                    "commitment",
                    ""
                )
            ),

            "workplace_type": (
                data.get(
                    "workplaceType"
                )
                or job.get(
                    "workplace_type",
                    ""
                )
            ),

            "created_at": (
                data.get(
                    "createdAt"
                )
                or job.get(
                    "created_at",
                    ""
                )
            ),
        }
    )


    return detailed_job


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\nLEVER SCRAPER READY\n"
    )

    print(
        "Two-stage Lever scraper "
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
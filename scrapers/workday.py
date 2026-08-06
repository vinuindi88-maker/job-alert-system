# ============================================================
# JOB ALERT SYSTEM - WORKDAY SCRAPER
# Two-stage + Full Pagination + Retry Protection
# ============================================================

import html
import re
import requests

from scrapers.http_client import get, post


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_LIMIT = 20
REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
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
# NORMALIZE BASE URL
# ============================================================

def normalize_base_url(base_url):

    if not base_url:
        return ""

    return base_url.rstrip("/")


# ============================================================
# BUILD LISTING API URL
# ============================================================

def build_jobs_api_url(
    base_url,
    tenant,
    site_name
):

    base_url = normalize_base_url(
        base_url
    )

    return (
        f"{base_url}/wday/cxs/"
        f"{tenant}/"
        f"{site_name}/jobs"
    )


# ============================================================
# BUILD PUBLIC JOB URL
# ============================================================

def build_public_job_url(
    base_url,
    site_name,
    external_path
):

    base_url = normalize_base_url(
        base_url
    )

    if not external_path:
        return ""

    if (
        external_path.startswith("http://")
        or external_path.startswith("https://")
    ):
        return external_path

    if not external_path.startswith("/"):
        external_path = "/" + external_path

    return (
        f"{base_url}/en-US/"
        f"{site_name}"
        f"{external_path}"
    )


# ============================================================
# BUILD DETAIL API URL
# ============================================================

def build_detail_api_url(
    base_url,
    tenant,
    site_name,
    external_path
):

    base_url = normalize_base_url(
        base_url
    )

    if not external_path:
        return ""

    path = str(
        external_path
    ).strip()

    # --------------------------------------------------------
    # FULL URL → EXTRACT /job/... PATH
    # --------------------------------------------------------

    if (
        path.startswith("http://")
        or path.startswith("https://")
    ):

        marker = f"/{site_name}/"

        if marker in path:

            path = path.split(
                marker,
                1
            )[1]

            path = "/" + path

        else:

            job_index = path.find(
                "/job/"
            )

            if job_index >= 0:

                path = path[
                    job_index:
                ]


    if not path.startswith("/"):
        path = "/" + path


    return (
        f"{base_url}/wday/cxs/"
        f"{tenant}/"
        f"{site_name}"
        f"{path}"
    )


# ============================================================
# FETCH LIGHTWEIGHT JOBS
# ============================================================

def fetch_workday_jobs(
    company_name,
    base_url,
    tenant,
    site_name,
    limit=DEFAULT_LIMIT,
    max_pages=None
):
    """
    Stage 1

    Fetch ALL lightweight Workday listings.

    Full descriptions are NOT fetched here.

    Important:
    Some Workday tenants return the real total only
    on offset=0 and return total=0 on later pages.

    Therefore we capture the first valid total and
    never overwrite it with later zero values.
    """

    jobs = []

    base_url = normalize_base_url(
        base_url
    )

    api_url = build_jobs_api_url(
        base_url,
        tenant,
        site_name
    )

    offset = 0
    page = 0

    total_jobs = None

    seen_jobs = set()


    while True:

        # ----------------------------------------------------
        # OPTIONAL PAGE LIMIT
        # ----------------------------------------------------

        if (
            max_pages is not None
            and page >= max_pages
        ):
            break


        # ----------------------------------------------------
        # REQUEST PAYLOAD
        # ----------------------------------------------------

        payload = {
            "appliedFacets": {},
            "limit": limit,
            "offset": offset,
            "searchText": "",
        }


        # ----------------------------------------------------
        # REQUEST WITH RETRY/BACKOFF
        # ----------------------------------------------------

        try:

            response = post(
                api_url,
                json=payload,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                polite_delay=0.15
            )

            response.raise_for_status()

            data = response.json()


        except requests.RequestException as error:

            print(
                f"[WORKDAY ERROR] "
                f"{company_name}: "
                f"{error}"
            )

            break


        except ValueError as error:

            print(
                f"[WORKDAY JSON ERROR] "
                f"{company_name}: "
                f"{error}"
            )

            break


        # ----------------------------------------------------
        # CAPTURE REAL TOTAL
        # ----------------------------------------------------

        current_total = data.get(
            "total"
        )


        if (
            total_jobs is None
            and isinstance(
                current_total,
                int
            )
            and current_total > 0
        ):

            total_jobs = current_total


        # ----------------------------------------------------
        # JOB POSTINGS
        # ----------------------------------------------------

        postings = data.get(
            "jobPostings",
            []
        )


        if not postings:
            break


        new_jobs_this_page = 0


        # ----------------------------------------------------
        # PROCESS LISTINGS
        # ----------------------------------------------------

        for posting in postings:

            title = (
                posting.get(
                    "title"
                )
                or ""
            ).strip()


            location = (
                posting.get(
                    "locationsText"
                )
                or ""
            ).strip()


            external_path = (
                posting.get(
                    "externalPath"
                )
                or ""
            ).strip()


            # ------------------------------------------------
            # DUPLICATE PROTECTION
            # ------------------------------------------------

            unique_key = (
                external_path
                or (
                    f"{title}|"
                    f"{location}"
                )
            )


            if unique_key in seen_jobs:
                continue


            seen_jobs.add(
                unique_key
            )

            new_jobs_this_page += 1


            # ------------------------------------------------
            # PUBLIC URL
            # ------------------------------------------------

            public_url = build_public_job_url(
                base_url,
                site_name,
                external_path
            )


            # ------------------------------------------------
            # LIGHTWEIGHT JOB OBJECT
            # ------------------------------------------------

            jobs.append(
                {
                    "company": company_name,

                    "title": title,

                    "location": location,

                    # Stage 1 intentionally empty
                    "description": "",

                    "url": public_url,

                    "job_url": public_url,

                    "source": "workday",

                    # Required by Stage 2
                    "base_url": base_url,

                    "tenant": tenant,

                    "site_name": site_name,

                    "external_path": external_path,

                    # Optional metadata
                    "posted_on": (
                        posting.get(
                            "postedOn"
                        )
                        or ""
                    ),

                    "bullet_fields": (
                        posting.get(
                            "bulletFields"
                        )
                        or []
                    ),
                }
            )


        # ----------------------------------------------------
        # PAGINATION
        # ----------------------------------------------------

        received_count = len(
            postings
        )

        offset += received_count

        page += 1


        # ----------------------------------------------------
        # DUPLICATE PAGE PROTECTION
        # ----------------------------------------------------

        if new_jobs_this_page == 0:

            print(
                f"[WORKDAY WARNING] "
                f"{company_name}: "
                f"duplicate page detected "
                f"at offset {offset}"
            )

            break


        # ----------------------------------------------------
        # REACHED REPORTED TOTAL
        # ----------------------------------------------------

        if (
            total_jobs is not None
            and offset >= total_jobs
        ):

            break


        # ----------------------------------------------------
        # FINAL PARTIAL PAGE
        # ----------------------------------------------------

        if received_count < limit:

            break


    return jobs


# ============================================================
# FETCH FULL JOB DETAILS
# ============================================================

def fetch_workday_job_details(job):
    """
    Stage 2

    Fetch the full JD for ONE shortlisted Workday job.

    This function is called only after the lightweight
    title/location filter passes.
    """

    if not isinstance(
        job,
        dict
    ):

        return job


    # --------------------------------------------------------
    # REQUIRED DATA
    # --------------------------------------------------------

    base_url = job.get(
        "base_url",
        ""
    )

    tenant = job.get(
        "tenant",
        ""
    )

    site_name = job.get(
        "site_name",
        ""
    )

    external_path = job.get(
        "external_path",
        ""
    )


    if (
        not base_url
        or not tenant
        or not site_name
        or not external_path
    ):

        raise ValueError(
            "Workday job is missing "
            "base_url, tenant, site_name "
            "or external_path."
        )


    # --------------------------------------------------------
    # DETAIL ENDPOINT
    # --------------------------------------------------------

    detail_url = build_detail_api_url(
        base_url,
        tenant,
        site_name,
        external_path
    )


    # --------------------------------------------------------
    # REQUEST WITH RETRY/BACKOFF
    # --------------------------------------------------------

    try:

        response = get(
            detail_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            polite_delay=0.15
        )

        response.raise_for_status()

        data = response.json()


    except requests.RequestException as error:

        raise RuntimeError(
            f"Workday detail request failed: "
            f"{error}"
        )


    except ValueError as error:

        raise RuntimeError(
            f"Invalid Workday detail response: "
            f"{error}"
        )


    # --------------------------------------------------------
    # JOB INFO
    # --------------------------------------------------------

    job_info = data.get(
        "jobInfo",
        {}
    )


    if not isinstance(
        job_info,
        dict
    ):

        job_info = {}


    posting_info = data.get(
        "jobPostingInfo",
        {}
    )


    if not isinstance(
        posting_info,
        dict
    ):

        posting_info = {}


    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = (
        posting_info.get(
            "jobDescription"
        )
        or job_info.get(
            "jobDescription"
        )
        or data.get(
            "jobDescription"
        )
        or ""
    )


    description = clean_html(
        description
    )


    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = (
        job_info.get(
            "title"
        )
        or posting_info.get(
            "title"
        )
        or job.get(
            "title",
            ""
        )
    )


    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    location = (
        job_info.get(
            "location"
        )
        or posting_info.get(
            "location"
        )
        or job.get(
            "location",
            ""
        )
    )


    # --------------------------------------------------------
    # PUBLIC URL
    # --------------------------------------------------------

    public_url = (
        job.get(
            "url"
        )
        or build_public_job_url(
            base_url,
            site_name,
            external_path
        )
    )


    # --------------------------------------------------------
    # COPY ORIGINAL JOB
    # --------------------------------------------------------

    detailed_job = dict(
        job
    )


    # --------------------------------------------------------
    # UPDATE FULL DETAILS
    # --------------------------------------------------------

    detailed_job.update(
        {
            "title": title,

            "location": location,

            "description": description,

            "url": public_url,

            "job_url": public_url,

            "source": "workday",
        }
    )


    # --------------------------------------------------------
    # JOB ID
    # --------------------------------------------------------

    detailed_job[
        "job_id"
    ] = (
        posting_info.get(
            "jobReqId"
        )
        or posting_info.get(
            "jobPostingId"
        )
        or detailed_job.get(
            "job_id",
            ""
        )
    )


    # --------------------------------------------------------
    # POSTED DATE
    # --------------------------------------------------------

    detailed_job[
        "posted_on"
    ] = (
        posting_info.get(
            "postedOn"
        )
        or detailed_job.get(
            "posted_on",
            ""
        )
    )


    return detailed_job


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\nWORKDAY SCRAPER READY\n"
    )

    print(
        "Two-stage Workday scraper loaded successfully."
    )

    print(
        "Full pagination: ENABLED"
    )

    print(
        "HTTP retry/backoff: ENABLED"
    )
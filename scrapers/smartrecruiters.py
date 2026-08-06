# ============================================================
# JOB ALERT SYSTEM - SMARTRECRUITERS SCRAPER
# Two-stage + Pagination + Retry + Duplicate Protection
# ============================================================

import html
import re
import requests

from scrapers.http_client import get


# ============================================================
# SETTINGS
# ============================================================

REQUEST_TIMEOUT = 30
DEFAULT_LIMIT = 100

SMARTRECRUITERS_API = (
    "https://api.smartrecruiters.com/v1/companies"
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
# BUILD JOB LIST URL
# ============================================================

def build_jobs_url(
    company_identifier
):

    company_identifier = str(
        company_identifier
    ).strip().strip("/")

    return (
        f"{SMARTRECRUITERS_API}/"
        f"{company_identifier}/postings"
    )


# ============================================================
# BUILD DETAIL URL
# ============================================================

def build_detail_url(
    company_identifier,
    job_id
):

    company_identifier = str(
        company_identifier
    ).strip().strip("/")

    job_id = str(
        job_id
    ).strip()

    return (
        f"{SMARTRECRUITERS_API}/"
        f"{company_identifier}/postings/"
        f"{job_id}"
    )


# ============================================================
# EXTRACT LOCATION
# ============================================================

def extract_location(posting):

    location = posting.get(
        "location",
        {}
    )

    if not isinstance(
        location,
        dict
    ):

        return str(
            location or ""
        ).strip()


    parts = []


    city = (
        location.get("city")
        or ""
    )

    region = (
        location.get("region")
        or ""
    )

    country = (
        location.get("country")
        or ""
    )


    for value in (
        city,
        region,
        country
    ):

        value = str(
            value
        ).strip()

        if (
            value
            and value not in parts
        ):

            parts.append(
                value
            )


    return ", ".join(
        parts
    )


# ============================================================
# EXTRACT PUBLIC URL
# ============================================================

def extract_public_url(
    posting
):

    # SmartRecruiters responses can expose
    # different URL fields.

    public_url = (
        posting.get("ref")
        or posting.get("jobAdUrl")
        or posting.get("url")
        or ""
    )


    return str(
        public_url
    ).strip()


# ============================================================
# FETCH LIGHTWEIGHT JOBS
# ============================================================

def fetch_smartrecruiters_jobs(
    company_name,
    company_identifier,
    limit=DEFAULT_LIMIT
):
    """
    Stage 1:
    Fetch ALL lightweight SmartRecruiters listings.

    Handles pagination using offset + limit.

    Full descriptions are NOT processed here.
    """

    jobs = []


    if not company_identifier:

        print(
            f"[SMARTRECRUITERS CONFIG ERROR] "
            f"{company_name}: "
            f"company_identifier missing"
        )

        return jobs


    url = build_jobs_url(
        company_identifier
    )


    offset = 0

    total_found = None

    seen_jobs = set()


    while True:

        params = {
            "limit": limit,
            "offset": offset,
        }


        try:

            response = get(
                url,
                headers=HEADERS,
                params=params,
                timeout=REQUEST_TIMEOUT,
                polite_delay=0.10
            )

            response.raise_for_status()

            data = response.json()


        except requests.RequestException as error:

            print(
                f"[SMARTRECRUITERS ERROR] "
                f"{company_name}: "
                f"{error}"
            )

            break


        except ValueError as error:

            print(
                f"[SMARTRECRUITERS JSON ERROR] "
                f"{company_name}: "
                f"{error}"
            )

            break


        # ----------------------------------------------------
        # TOTAL
        # ----------------------------------------------------

        current_total = data.get(
            "totalFound"
        )


        if (
            total_found is None
            and isinstance(
                current_total,
                int
            )
        ):

            total_found = current_total


        # ----------------------------------------------------
        # POSTINGS
        # ----------------------------------------------------

        postings = data.get(
            "content",
            []
        )


        if not isinstance(
            postings,
            list
        ):

            print(
                f"[SMARTRECRUITERS ERROR] "
                f"{company_name}: "
                f"unexpected API response"
            )

            break


        if not postings:
            break


        new_jobs_this_page = 0


        for posting in postings:

            if not isinstance(
                posting,
                dict
            ):
                continue


            # ------------------------------------------------
            # JOB ID
            # ------------------------------------------------

            job_id = (
                posting.get("id")
                or ""
            )


            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            title = (
                posting.get("name")
                or posting.get("title")
                or ""
            ).strip()


            # ------------------------------------------------
            # LOCATION
            # ------------------------------------------------

            location = extract_location(
                posting
            )


            # ------------------------------------------------
            # URL
            # ------------------------------------------------

            public_url = extract_public_url(
                posting
            )


            # ------------------------------------------------
            # DUPLICATE PROTECTION
            # ------------------------------------------------

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

            new_jobs_this_page += 1


            # ------------------------------------------------
            # LIGHTWEIGHT JOB
            # ------------------------------------------------

            jobs.append(
                {
                    "company": company_name,

                    "title": title,

                    "location": location,

                    "description": "",

                    "url": public_url,

                    "job_url": public_url,

                    "source": "smartrecruiters",

                    # Required for Stage 2
                    "company_identifier":
                        company_identifier,

                    "job_id": job_id,

                    # Useful metadata
                    "released_date": (
                        posting.get(
                            "releasedDate"
                        )
                        or ""
                    ),

                    "type_of_employment": (
                        posting.get(
                            "typeOfEmployment"
                        )
                        or ""
                    ),

                    "industry": (
                        posting.get(
                            "industry"
                        )
                        or ""
                    ),

                    "department": (
                        posting.get(
                            "department"
                        )
                        or ""
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


        # Prevent accidental infinite loop.

        if new_jobs_this_page == 0:

            print(
                f"[SMARTRECRUITERS WARNING] "
                f"{company_name}: "
                f"duplicate page detected."
            )

            break


        # Reached reported total.

        if (
            total_found is not None
            and offset >= total_found
        ):

            break


        # Partial page = last page.

        if received_count < limit:

            break


    return jobs


# ============================================================
# FETCH FULL JOB DETAILS
# ============================================================

def fetch_smartrecruiters_job_details(
    job
):
    """
    Stage 2:
    Fetch full JD for ONE shortlisted
    SmartRecruiters job.
    """

    if not isinstance(
        job,
        dict
    ):

        return job


    company_identifier = job.get(
        "company_identifier"
    )

    job_id = job.get(
        "job_id"
    )


    if (
        not company_identifier
        or not job_id
    ):

        raise ValueError(
            "SmartRecruiters job is missing "
            "company_identifier or job_id."
        )


    url = build_detail_url(
        company_identifier,
        job_id
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
            "SmartRecruiters detail "
            f"request failed: {error}"
        )


    except ValueError as error:

        raise RuntimeError(
            "Invalid SmartRecruiters "
            f"detail response: {error}"
        )


    if not isinstance(
        data,
        dict
    ):

        raise RuntimeError(
            "Unexpected SmartRecruiters "
            "detail response."
        )


    # ========================================================
    # DESCRIPTION
    # ========================================================

    description_parts = []


    job_ad = data.get(
        "jobAd",
        {}
    )


    if not isinstance(
        job_ad,
        dict
    ):

        job_ad = {}


    sections = job_ad.get(
        "sections",
        {}
    )


    if not isinstance(
        sections,
        dict
    ):

        sections = {}


    # Common SmartRecruiters sections.

    section_names = (
        "companyDescription",
        "jobDescription",
        "qualifications",
        "additionalInformation",
    )


    for section_name in section_names:

        section = sections.get(
            section_name,
            {}
        )


        if isinstance(
            section,
            dict
        ):

            section_title = clean_html(
                section.get(
                    "title",
                    ""
                )
            )

            section_text = clean_html(
                section.get(
                    "text",
                    ""
                )
            )


            if section_title:

                description_parts.append(
                    section_title
                )


            if section_text:

                description_parts.append(
                    section_text
                )


        elif section:

            section_text = clean_html(
                section
            )


            if section_text:

                description_parts.append(
                    section_text
                )


    # Fallback description fields.

    if not description_parts:

        fallback_description = clean_html(
            data.get(
                "description",
                ""
            )
        )


        if fallback_description:

            description_parts.append(
                fallback_description
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
        data.get("name")
        or data.get("title")
        or job.get("title", "")
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
        extract_public_url(
            data
        )
        or job.get(
            "url",
            ""
        )
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

            "description": full_description,

            "url": public_url,

            "job_url": public_url,

            "source": "smartrecruiters",

            "job_id": (
                data.get("id")
                or job_id
            ),

            "released_date": (
                data.get("releasedDate")
                or job.get(
                    "released_date",
                    ""
                )
            ),

            "type_of_employment": (
                data.get("typeOfEmployment")
                or job.get(
                    "type_of_employment",
                    ""
                )
            ),

            "industry": (
                data.get("industry")
                or job.get(
                    "industry",
                    ""
                )
            ),

            "department": (
                data.get("department")
                or job.get(
                    "department",
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
        "\nSMARTRECRUITERS SCRAPER READY\n"
    )

    print(
        "Two-stage SmartRecruiters scraper "
        "loaded successfully."
    )

    print(
        "Full pagination: ENABLED"
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
# ============================================================
# JOB ALERT SYSTEM - OPTIMIZED SCRAPER ROUTER
# ============================================================

import json
import os

# ------------------------------------------------------------
# SCRAPER IMPORTS
# ------------------------------------------------------------

from scrapers.greenhouse import (
    fetch_greenhouse_jobs,
    fetch_greenhouse_job_details,
)

from scrapers.workday import (
    fetch_workday_jobs,
    fetch_workday_job_details,
)

from scrapers.lever import (
    fetch_lever_jobs,
    fetch_lever_job_details,
)

from scrapers.ashby import (
    fetch_ashby_jobs,
    fetch_ashby_job_details,
)

from scrapers.smartrecruiters import (
    fetch_smartrecruiters_jobs,
    fetch_smartrecruiters_job_details,
)

# IMPORTANT:
# Same filter already tested for:
# - India
# - Last 48 hours
# - Relevant roles
# - Senior-role rejection
from config.filters import basic_job_filter


# ============================================================
# CONFIG
# ============================================================

COMPANIES_FILE = os.path.join(
    "companies",
    "companies.json"
)


# ============================================================
# LOAD COMPANIES
# ============================================================

def load_companies():

    if not os.path.exists(
        COMPANIES_FILE
    ):

        raise FileNotFoundError(
            f"Companies file not found: "
            f"{COMPANIES_FILE}"
        )

    try:

        with open(
            COMPANIES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Invalid companies.json: "
            f"{error}"
        )

    companies = data.get(
        "companies",
        []
    )

    if not isinstance(
        companies,
        list
    ):

        raise ValueError(
            "'companies' must be a list."
        )

    return companies


# ============================================================
# SCRAPE ONE COMPANY
# ============================================================

def scrape_company(company):

    name = company.get(
        "name",
        "Unknown Company"
    )

    ats = company.get(
        "ats",
        ""
    ).lower().strip()

    enabled = company.get(
        "enabled",
        True
    )


    # --------------------------------------------------------
    # DISABLED COMPANY
    # --------------------------------------------------------

    if not enabled:

        print(
            f"[SKIP] {name} is disabled."
        )

        return []


    print(
        f"[SCRAPING] {name} | ATS: {ats}"
    )


    try:

        # ====================================================
        # GREENHOUSE
        # ====================================================

        if ats == "greenhouse":

            board_token = company.get(
                "board_token"
            )

            if not board_token:

                print(
                    f"[CONFIG ERROR] {name}: "
                    f"board_token missing."
                )

                return []

            return fetch_greenhouse_jobs(
                name,
                board_token
            )


        # ====================================================
        # WORKDAY
        # ====================================================

        elif ats == "workday":

            base_url = company.get(
                "base_url"
            )

            tenant = company.get(
                "tenant"
            )

            site_name = company.get(
                "site_name"
            )

            if (
                not base_url
                or not tenant
                or not site_name
            ):

                print(
                    f"[CONFIG ERROR] {name}: "
                    f"base_url/tenant/"
                    f"site_name missing."
                )

                return []

            return fetch_workday_jobs(
                name,
                base_url,
                tenant,
                site_name
            )


        # ====================================================
        # LEVER
        # ====================================================

        elif ats == "lever":

            company_slug = company.get(
                "company_slug"
            )

            if not company_slug:

                print(
                    f"[CONFIG ERROR] {name}: "
                    f"company_slug missing."
                )

                return []

            return fetch_lever_jobs(
                name,
                company_slug
            )


        # ====================================================
        # ASHBY
        # ====================================================

        elif ats == "ashby":

            board_name = company.get(
                "board_name"
            )

            if not board_name:

                print(
                    f"[CONFIG ERROR] {name}: "
                    f"board_name missing."
                )

                return []

            return fetch_ashby_jobs(
                name,
                board_name
            )


        # ====================================================
        # SMARTRECRUITERS
        # ====================================================

        elif ats == "smartrecruiters":

            company_identifier = company.get(
                "company_identifier"
            )

            if not company_identifier:

                print(
                    f"[CONFIG ERROR] {name}: "
                    f"company_identifier missing."
                )

                return []

            return fetch_smartrecruiters_jobs(
                name,
                company_identifier
            )


        # ====================================================
        # UNSUPPORTED ATS
        # ====================================================

        else:

            print(
                f"[UNSUPPORTED ATS] "
                f"{name}: {ats}"
            )

            return []


    except Exception as error:

        print(
            f"[SCRAPER FAILED] "
            f"{name}: {error}"
        )

        return []


# ============================================================
# EARLY FILTER
# ============================================================

def filter_lightweight_jobs(jobs):
    """
    Run the already-tested basic filter BEFORE jobs
    are returned to main.py.

    Current basic filter is responsible for:
    - India location
    - Last 48 hours
    - Relevant role
    - Senior role rejection

    Full JD is NOT downloaded here.
    """

    filtered_jobs = []

    rejected_count = 0


    for job in jobs:

        try:

            passed, _ = basic_job_filter(
                job
            )

        except Exception as error:

            company = job.get(
                "company",
                "Unknown Company"
            )

            title = job.get(
                "title",
                "Unknown Role"
            )

            print(
                f"[FILTER ERROR] "
                f"{company} | {title}: "
                f"{error}"
            )

            rejected_count += 1

            continue


        if passed:

            filtered_jobs.append(
                job
            )

        else:

            rejected_count += 1


    return (
        filtered_jobs,
        rejected_count
    )


# ============================================================
# SCRAPE ALL COMPANIES
# ============================================================

def scrape_all_companies():

    companies = load_companies()

    all_filtered_jobs = []

    total_raw_jobs = 0

    total_rejected = 0


    print(
        f"\nCompanies loaded: "
        f"{len(companies)}\n"
    )


    for company in companies:

        # ----------------------------------------------------
        # FETCH RAW LIGHTWEIGHT JOBS
        # ----------------------------------------------------

        jobs = scrape_company(
            company
        )


        raw_count = len(
            jobs
        )

        total_raw_jobs += (
            raw_count
        )


        print(
            f"[FOUND] "
            f"{company.get('name', 'Unknown')}: "
            f"{raw_count} total jobs"
        )


        # ----------------------------------------------------
        # EARLY FILTER
        # ----------------------------------------------------

        filtered_jobs, rejected_count = (
            filter_lightweight_jobs(
                jobs
            )
        )


        kept_count = len(
            filtered_jobs
        )


        total_rejected += (
            rejected_count
        )


        all_filtered_jobs.extend(
            filtered_jobs
        )


        print(
            f"[ELIGIBLE] "
            f"{company.get('name', 'Unknown')}: "
            f"{kept_count} fresh India jobs"
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        "\n"
        "=========================================="
    )

    print(
        "        ROUTER FILTER SUMMARY"
    )

    print(
        "=========================================="
    )

    print(
        f"Raw jobs fetched       : "
        f"{total_raw_jobs}"
    )

    print(
        f"Rejected early         : "
        f"{total_rejected}"
    )

    print(
        f"Passed to main.py      : "
        f"{len(all_filtered_jobs)}"
    )

    print(
        "=========================================="
    )


    return all_filtered_jobs


# ============================================================
# FETCH FULL JOB DETAILS
# ============================================================

def fetch_job_details(job):
    """
    Fetch the full JD only after the lightweight job
    has passed the early filter.
    """

    source = job.get(
        "source",
        ""
    ).lower().strip()

    company = job.get(
        "company",
        "Unknown Company"
    )

    title = job.get(
        "title",
        "Unknown Role"
    )


    try:

        # ====================================================
        # GREENHOUSE
        # ====================================================

        if source == "greenhouse":

            return fetch_greenhouse_job_details(
                job
            )


        # ====================================================
        # WORKDAY
        # ====================================================

        elif source == "workday":

            return fetch_workday_job_details(
                job
            )


        # ====================================================
        # LEVER
        # ====================================================

        elif source == "lever":

            return fetch_lever_job_details(
                job
            )


        # ====================================================
        # ASHBY
        # ====================================================

        elif source == "ashby":

            return fetch_ashby_job_details(
                job
            )


        # ====================================================
        # SMARTRECRUITERS
        # ====================================================

        elif source == "smartrecruiters":

            return fetch_smartrecruiters_job_details(
                job
            )


        # ====================================================
        # UNKNOWN SOURCE
        # ====================================================

        else:

            print(
                f"[DETAIL ERROR] "
                f"{company} | {title}: "
                f"Unsupported source "
                f"'{source}'"
            )

            return job


    except Exception as error:

        print(
            f"[DETAIL FAILED] "
            f"{company} | {title}: "
            f"{error}"
        )

        return job


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    try:

        jobs = scrape_all_companies()


        print(
            "\nROUTER TEST COMPLETE"
        )

        print(
            f"Fresh India jobs returned: "
            f"{len(jobs)}"
        )

        print(
            "Full descriptions were NOT fetched."
        )


        # ----------------------------------------------------
        # SHOW JOBS THAT SURVIVED
        # ----------------------------------------------------

        if jobs:

            print(
                "\nJOBS PASSED TO MAIN:"
            )

            for index, job in enumerate(
                jobs,
                start=1
            ):

                print(
                    f"{index}. "
                    f"{job.get('company', '')} | "
                    f"{job.get('title', '')} | "
                    f"{job.get('location', '')}"
                )

        else:

            print(
                "\nNo matching fresh India jobs "
                "found in this run."
            )


    except Exception as error:

        print(
            "\nROUTER ERROR:"
        )

        print(
            error
        )
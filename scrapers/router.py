import os
import re
import json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

from config.settings import MAX_JOB_AGE_HOURS
from config.filters import keyword_in_text


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

COMPANIES_FILE = os.path.join(
    BASE_DIR,
    "companies",
    "companies.json"
)


# ============================================================
# PERFORMANCE
# ============================================================

MAX_WORKERS = 20


# ============================================================
# IMPORT ALL ATS SCRAPERS
# ============================================================

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


# ============================================================
# TARGET ROLES
# ============================================================

RELEVANT_ROLE_KEYWORDS = [

    "data analyst",
    "data analytics",
    "data analyst intern",
    "data analyst internship",

    "junior data analyst",
    "associate data analyst",

    "business analyst",
    "business analytics",
    "business analyst intern",

    "analytics analyst",
    "analytics associate",
    "analytics intern",

    "product analyst",
    "product analytics",
    "product analyst intern",

    "reporting analyst",
    "reporting analytics",

    "bi analyst",
    "business intelligence analyst",
    "business intelligence",

    "data scientist",
    "data science intern",
    "junior data scientist",

    "data engineer",
    "data engineering intern",
    "junior data engineer",

    "machine learning analyst",
    "machine learning intern",

    "marketing analyst",
    "marketing analytics",

    "operations analyst",
    "operations analytics",

    "research analyst",
    "research analytics",

    # Internships / Trainee
    "data analyst intern",
    "data analyst internship",
    "data analytics intern",
    "data analytics internship",
    "data science intern",
    "data science internship",
    "business analyst intern",
    "business analyst internship",
    "analytics intern",
    "analytics internship",
    "bi intern",
    "bi internship",
    "data engineering intern",
    "data engineering internship",
    "data intern",
    "data internship",
    "research intern",
    "research internship",
    "ml intern",
    "ml internship",
    "machine learning intern",
    "machine learning internship",

]


# ============================================================
# STRICT SENIORITY REJECTION
# ============================================================

SENIOR_KEYWORDS = [

    "senior",
    "sr.",
    "sr ",
    "lead",
    "principal",
    "director",
    "head of",
    "manager",
    "vice president",
    "vp ",
    "chief",
    "staff",
    "specialist",

    "data analyst ii",
    "data analyst iii",
    "data analyst iv",

    "business analyst ii",
    "business analyst iii",
    "business analyst iv",

    "data scientist ii",
    "data scientist iii",
    "data scientist iv",

    "data engineer ii",
    "data engineer iii",
    "data engineer iv",

    "analytics analyst ii",
    "analytics analyst iii",

    "level 2",
    "level 3",
    "level 4",

    "level ii",
    "level iii",
    "level iv",

]


# ============================================================
# CLEARLY UNRELATED ROLES
# ============================================================

UNRELATED_ROLE_KEYWORDS = [

    # Finance
    "financial analyst",
    "investment analyst",
    "investment banking",
    "project finance analyst",
    "accounting analyst",
    "tax analyst",

    # HR
    "human resources",
    "hr business partner",
    "hrbp",
    "recruiter",
    "recruitment",
    "talent acquisition",

    # Legal
    "legal counsel",
    "lawyer",
    "attorney",
    "paralegal",

    # Sales
    "sales representative",
    "sales executive",
    "account executive",
    "business development manager",

    # Development
    "java developer",
    "software developer",
    "software engineer",
    "frontend developer",
    "front end developer",
    "backend developer",
    "back end developer",
    "full stack developer",
    "fullstack developer",
    "mobile developer",
    "android developer",
    "ios developer",

    # Infrastructure
    "network engineer",
    "system administrator",
    "systems administrator",
    "storage administrator",
    "cloud engineer",
    "support technician",
    "service desk",

]


# ============================================================
# INDIA LOCATIONS
# ============================================================

INDIA_LOCATION_KEYWORDS = [

    "india",

    "bangalore",
    "bengaluru",

    "hyderabad",

    "pune",

    "mumbai",
    "navi mumbai",

    "chennai",

    "delhi",
    "new delhi",

    "gurgaon",
    "gurugram",

    "noida",
    "greater noida",

    "kolkata",

    "ahmedabad",

    "coimbatore",

    "kochi",
    "cochin",

    "trivandrum",
    "thiruvananthapuram",

    "mysore",
    "mysuru",

    "jaipur",

    "chandigarh",

    "indore",

    "bhubaneswar",

    "surat",

    "vadodara",

    "nagpur",

    "lucknow",

    "karnataka",
    "maharashtra",
    "telangana",
    "tamil nadu",
    "kerala",
    "gujarat",
    "rajasthan",
    "haryana",
    "uttar pradesh",
    "west bengal",
    "madhya pradesh",
    "odisha",
    "punjab",

    "manyatha",
    "embassy business park",

]


# ============================================================
# NORMALIZE
# ============================================================

def normalize(value):

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).lower().strip()
    )


# ============================================================
# TITLE FILTER
# ============================================================

def is_relevant_title(title):

    title = normalize(title)

    if not title:
        return False

    # Reject clearly unrelated roles first
    for keyword in UNRELATED_ROLE_KEYWORDS:

        if keyword_in_text(keyword, title):
            return False

    # Reject senior/management roles
    for keyword in SENIOR_KEYWORDS:

        if keyword_in_text(keyword, title):
            return False

    # Accept target roles
    for keyword in RELEVANT_ROLE_KEYWORDS:

        if keyword in title:
            return True

    return False


# ============================================================
# REMOTE / WFH KEYWORDS
# ============================================================

REMOTE_KEYWORDS = [
    "remote",
    "work from home",
    "wfh",
    "work from anywhere",
    "fully remote",
    "telecommute",
    "telecommuting",
    "virtual",
    "home based",
    "home-based",
    "distributed",
]


# ============================================================
# REMOTE / WFH CHECK
# ============================================================

def is_remote_or_wfh(location):

    location = normalize(location)

    if not location:
        return False

    return any(
        keyword in location
        for keyword in REMOTE_KEYWORDS
    )


# ============================================================
# INDIA LOCATION
# ============================================================

def is_india_location(location):

    location = normalize(location)

    if not location:
        return False

    if (
        "remote" in location
        and "india" in location
    ):
        return True

    for keyword in INDIA_LOCATION_KEYWORDS:

        if keyword in location:
            return True

    return False


# ============================================================
# SMART LOCATION CHECK
#
# RULES:
# - India: Accept all modes (onsite/hybrid/remote)
# - Foreign: Accept ONLY if remote / work-from-home
# ============================================================

def is_acceptable_location(location):

    # India jobs: accept all modes
    if is_india_location(location):
        return True

    # Foreign jobs: accept only if remote/WFH
    if is_remote_or_wfh(location):
        return True

    return False


# ============================================================
# POSTING DATE
# ============================================================

def get_posting_date(job):

    source = normalize(
        job.get("source", "")
    )

    if source == "workday":

        return (
            job.get("posted_on")
            or job.get("posted_date")
        )

    if source == "greenhouse":

        return (
            job.get("posted_date")
            or job.get("first_published")
            or job.get("updated_at")
            or job.get("posted_on")
        )

    if source == "lever":

        return (
            job.get("created_at")
            or job.get("posted_date")
        )

    if source == "ashby":

        return (
            job.get("published_at")
            or job.get("posted_date")
        )

    if source == "smartrecruiters":

        return (
            job.get("released_date")
            or job.get("posted_date")
        )

    return (
        job.get("posted_date")
        or job.get("posted_on")
        or job.get("published_at")
        or job.get("released_date")
        or job.get("created_at")
        or job.get("updated_at")
    )


# ============================================================
# DATE PARSER
# ============================================================

def parse_date(value):

    if value is None:
        return None

    if isinstance(value, (int, float)):

        timestamp = float(value)

        if timestamp > 10_000_000_000:
            timestamp /= 1000

        try:
            return datetime.fromtimestamp(
                timestamp,
                timezone.utc
            )
        except Exception:
            return None

    value = str(value).strip()

    if not value:
        return None

    text = normalize(value)

    if text in (
        "today",
        "posted today"
    ):

        return datetime.now(
            timezone.utc
        )

    if text in (
        "yesterday",
        "posted yesterday"
    ):

        return (
            datetime.now(timezone.utc)
            - timedelta(days=1)
        )

    match = re.search(
        r"(\d+)\s+hours?\s+ago",
        text
    )

    if match:

        hours = int(
            match.group(1)
        )

        return (
            datetime.now(timezone.utc)
            - timedelta(hours=hours)
        )

    match = re.search(
        r"(\d+)\s+days?\s+ago",
        text
    )

    if match:

        days = int(
            match.group(1)
        )

        return (
            datetime.now(timezone.utc)
            - timedelta(days=days)
        )

    # Numeric timestamp
    if re.fullmatch(
        r"\d+(?:\.\d+)?",
        value
    ):

        try:

            timestamp = float(value)

            if timestamp > 10_000_000_000:
                timestamp /= 1000

            return datetime.fromtimestamp(
                timestamp,
                timezone.utc
            )

        except Exception:
            return None

    # ISO format
    iso_value = value

    if iso_value.endswith("Z"):

        iso_value = (
            iso_value[:-1]
            + "+00:00"
        )

    try:

        parsed = datetime.fromisoformat(
            iso_value
        )

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(
            timezone.utc
        )

    except ValueError:
        pass

    formats = [

        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",

        "%m/%d/%Y",
        "%d/%m/%Y",

    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(
                value,
                fmt
            )

            return parsed.replace(
                tzinfo=timezone.utc
            )

        except ValueError:
            continue

    return None


# ============================================================
# RECENT JOB CHECK
# ============================================================

def is_recent_job(job):

    raw_date = get_posting_date(job)

    # If date is completely missing, allow it through so we don't miss fresh postings
    if raw_date is None or str(raw_date).strip() == "":
        return True

    posted_at = parse_date(
        raw_date
    )

    # If date is present but unparseable, block it if it has old-age keywords
    if posted_at is None:
        text = str(raw_date).lower()
        if any(k in text for k in ["30+", "30 days", "15 days", "10 days", "month", "weeks", "older"]):
            return False
        return True

    now = datetime.now(
        timezone.utc
    )

    age_hours = (
        now - posted_at
    ).total_seconds() / 3600

    # Reject future-dated jobs
    if age_hours < -6:
        return False

    return (
        age_hours <= MAX_JOB_AGE_HOURS
    )


# ============================================================
# LIGHTWEIGHT FILTER
# ============================================================

def lightweight_filter(job):

    title = job.get(
        "title",
        ""
    )

    location = job.get(
        "location",
        ""
    )

    if not title:
        return False

    if not is_acceptable_location(
        location
    ):
        return False

    if not is_recent_job(
        job
    ):
        return False

    if not is_relevant_title(
        title
    ):
        return False

    return True


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

    with open(
        COMPANIES_FILE,
        "r",
        encoding="utf-8-sig"
    ) as file:

        data = json.load(file)

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
# ATS SCRAPER
# ============================================================

def scrape_company(company):

    name = company.get(
        "name",
        "Unknown Company"
    )

    ats = normalize(
        company.get(
            "ats",
            ""
        )
    )

    if not company.get(
        "enabled",
        True
    ):

        return {
            "company": name,
            "ats": ats,
            "jobs": [],
            "error": None,
        }

    try:

        # -------------------------------
        # GREENHOUSE
        # -------------------------------

        if ats == "greenhouse":

            token = company.get(
                "board_token"
            )

            if not token:

                return {
                    "company": name,
                    "ats": ats,
                    "jobs": [],
                    "error": "Missing board_token",
                }

            jobs = fetch_greenhouse_jobs(
                name,
                token
            )


        # -------------------------------
        # WORKDAY
        # -------------------------------

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

            if not all([
                base_url,
                tenant,
                site_name
            ]):

                return {
                    "company": name,
                    "ats": ats,
                    "jobs": [],
                    "error": "Missing Workday configuration",
                }

            jobs = fetch_workday_jobs(
                name,
                base_url,
                tenant,
                site_name
            )


        # -------------------------------
        # LEVER
        # -------------------------------

        elif ats == "lever":

            slug = company.get(
                "company_slug"
            )

            if not slug:

                return {
                    "company": name,
                    "ats": ats,
                    "jobs": [],
                    "error": "Missing company_slug",
                }

            jobs = fetch_lever_jobs(
                name,
                slug
            )


        # -------------------------------
        # ASHBY
        # -------------------------------

        elif ats == "ashby":

            board = company.get(
                "board_name"
            )

            if not board:

                return {
                    "company": name,
                    "ats": ats,
                    "jobs": [],
                    "error": "Missing board_name",
                }

            jobs = fetch_ashby_jobs(
                name,
                board
            )


        # -------------------------------
        # SMARTRECRUITERS
        # -------------------------------

        elif ats == "smartrecruiters":

            identifier = company.get(
                "company_identifier"
            )

            if not identifier:

                return {
                    "company": name,
                    "ats": ats,
                    "jobs": [],
                    "error": "Missing company_identifier",
                }

            jobs = fetch_smartrecruiters_jobs(
                name,
                identifier
            )


        # -------------------------------
        # UNSUPPORTED
        # -------------------------------

        else:

            return {
                "company": name,
                "ats": ats,
                "jobs": [],
                "error": f"Unsupported ATS: {ats}",
            }

        if not isinstance(
            jobs,
            list
        ):

            jobs = list(jobs or [])

        return {
            "company": name,
            "ats": ats,
            "jobs": jobs,
            "error": None,
        }

    except Exception as error:

        return {
            "company": name,
            "ats": ats,
            "jobs": [],
            "error": str(error),
        }


# ============================================================
# PARALLEL SCRAPING
# ============================================================

def scrape_all_companies():

    companies = load_companies()

    enabled_companies = [
        company
        for company in companies
        if company.get(
            "enabled",
            True
        )
    ]

    print()
    print("=" * 60)
    print(
        f"COMPANIES LOADED : {len(companies)}"
    )
    print(
        f"COMPANIES ENABLED: {len(enabled_companies)}"
    )
    print(
        f"MAX WORKERS     : {MAX_WORKERS}"
    )
    print("=" * 60)

    # ========================================================
    # ATS SUMMARY BEFORE SCRAPING
    # ========================================================

    ats_counts = Counter(
        normalize(
            company.get(
                "ats",
                "unknown"
            )
        )
        for company in enabled_companies
    )

    print()
    print("ATS DISTRIBUTION")
    print("-" * 60)

    for ats, count in sorted(
        ats_counts.items()
    ):

        print(
            f"{ats:20} : {count}"
        )

    print("-" * 60)

    # ========================================================
    # RUN ALL ATS TYPES CONCURRENTLY
    # ========================================================

    all_jobs = []

    results = []

    completed = 0

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                scrape_company,
                company
            ): company
            for company in enabled_companies
        }

        for future in as_completed(
            futures
        ):

            company = futures[
                future
            ]

            name = company.get(
                "name",
                "Unknown"
            )

            try:

                result = future.result()

            except Exception as error:

                result = {
                    "company": name,
                    "ats": normalize(
                        company.get(
                            "ats",
                            ""
                        )
                    ),
                    "jobs": [],
                    "error": str(error),
                }

            results.append(
                result
            )

            completed += 1

            jobs = result.get(
                "jobs",
                []
            )

            ats = result.get(
                "ats",
                ""
            )

            if result.get("error"):

                print(
                    f"[FAILED {completed}/{len(enabled_companies)}] "
                    f"{name} | {ats} | "
                    f"{result['error']}"
                )

            else:

                print(
                    f"[DONE {completed}/{len(enabled_companies)}] "
                    f"{name} | {ats} | "
                    f"{len(jobs)} jobs"
                )

            all_jobs.extend(
                jobs
            )

    # ========================================================
    # RAW ATS SUMMARY
    # ========================================================

    raw_by_ats = Counter()

    for result in results:

        raw_by_ats[
            result.get(
                "ats",
                "unknown"
            )
        ] += len(
            result.get(
                "jobs",
                []
            )
        )

    print()
    print("=" * 60)
    print("RAW JOBS BY ATS")
    print("-" * 60)

    for ats, count in sorted(
        raw_by_ats.items()
    ):

        print(
            f"{ats:20} : {count}"
        )

    print("=" * 60)

    # ========================================================
    # LIGHTWEIGHT FILTER
    # ========================================================

    filtered_jobs = []

    rejected = 0

    for job in all_jobs:

        try:

            if lightweight_filter(
                job
            ):

                filtered_jobs.append(
                    job
                )

            else:

                rejected += 1

        except Exception:

            rejected += 1

    # ========================================================
    # DEDUPLICATION
    # ========================================================

    unique_jobs = []

    seen = set()

    for job in filtered_jobs:

        url = str(
            job.get(
                "url",
                ""
            )
            or job.get(
                "job_url",
                ""
            )
        ).strip()

        key = (
            normalize(
                job.get(
                    "company",
                    ""
                )
            ),
            normalize(
                job.get(
                    "title",
                    ""
                )
            ),
            normalize(
                job.get(
                    "location",
                    ""
                )
            ),
            url,
        )

        if key in seen:
            continue

        seen.add(key)

        unique_jobs.append(
            job
        )

    duplicates = (
        len(filtered_jobs)
        - len(unique_jobs)
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    final_by_ats = Counter(
        normalize(
            job.get(
                "source",
                "unknown"
            )
        )
        for job in unique_jobs
    )

    print()
    print("=" * 60)
    print("FINAL ROUTER SUMMARY")
    print("=" * 60)

    print(
        f"Companies loaded       : {len(companies)}"
    )

    print(
        f"Companies enabled      : {len(enabled_companies)}"
    )

    print(
        f"Raw jobs fetched       : {len(all_jobs)}"
    )

    print(
        f"Rejected early         : {rejected}"
    )

    print(
        f"Passed basic filter    : {len(filtered_jobs)}"
    )

    print(
        f"Duplicates removed     : {duplicates}"
    )

    print(
        f"Passed to main.py      : {len(unique_jobs)}"
    )

    print()
    print("FINAL JOBS BY ATS")
    print("-" * 60)

    for ats in [
        "greenhouse",
        "workday",
        "lever",
        "ashby",
        "smartrecruiters",
    ]:

        print(
            f"{ats:20} : "
            f"{final_by_ats.get(ats, 0)}"
        )

    print("=" * 60)

    return unique_jobs


# ============================================================
# FETCH FULL JOB DETAILS
# ============================================================

def fetch_job_details(job):

    source = normalize(
        job.get(
            "source",
            ""
        )
    )

    try:

        if source == "greenhouse":

            return fetch_greenhouse_job_details(
                job
            )

        if source == "workday":

            return fetch_workday_job_details(
                job
            )

        if source == "lever":

            return fetch_lever_job_details(
                job
            )

        if source == "ashby":

            return fetch_ashby_job_details(
                job
            )

        if source == "smartrecruiters":

            return fetch_smartrecruiters_job_details(
                job
            )

        return job

    except Exception as error:

        print(
            f"[DETAIL FAILED] "
            f"{job.get('company', '')} | "
            f"{job.get('title', '')} | "
            f"{error}"
        )

        return job


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    jobs = scrape_all_companies()

    print()
    print("=" * 60)
    print("ROUTER TEST COMPLETE")
    print(
        f"Fresh India jobs returned: {len(jobs)}"
    )
    print("=" * 60)

    for index, job in enumerate(
        jobs[:20],
        start=1
    ):

        print(
            f"{index:02d}. "
            f"{job.get('company', '')} | "
            f"{job.get('title', '')} | "
            f"{job.get('location', '')} | "
            f"{job.get('source', '')}"
        )
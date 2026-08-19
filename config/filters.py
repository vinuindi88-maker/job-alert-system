# ============================================================
# JOB ALERT SYSTEM - FINAL STRICT FRESHER FILTER
#
# PURPOSE:
# - India jobs only
# - Posted within configured freshness window (see settings.py)
# - Data / Analytics target roles only
# - Reject obvious unrelated roles
# - Reject senior / lead / management / higher-level roles
#
# IMPORTANT:
# Experience (0-2 years) is checked later from FULL JD.
# ============================================================

import re
from datetime import datetime, timezone, timedelta

from config.settings import MAX_JOB_AGE_HOURS


# ============================================================
# TARGET ROLES
# ============================================================

RELEVANT_ROLE_KEYWORDS = [

    # ---------------- DATA ANALYTICS ----------------
    "data analyst",
    "data analytics",
    "data associate",
    "analytics analyst",
    "analytics associate",

    # ---------------- BUSINESS ANALYTICS ----------------
    "business analyst",
    "business analytics",

    # ---------------- BUSINESS INTELLIGENCE ----------------
    "business intelligence",
    "bi analyst",
    "bi developer",
    "power bi",

    # ---------------- REPORTING / MIS ----------------
    "reporting analyst",
    "reporting associate",
    "mis analyst",
    "mis executive",
    "mis reporting",

    # ---------------- INSIGHTS ----------------
    "insights analyst",
    "insight analyst",
    "insights associate",

    # ---------------- DATA ENGINEERING ----------------
    "data engineer",
    "data engineering",

    # ---------------- DATA SCIENCE ----------------
    "data scientist",
    "data science",

    # ---------------- MACHINE LEARNING / AI ----------------
    "machine learning engineer",
    "ml engineer",
    "ai analyst",

    # ---------------- SQL / DATABASE ----------------
    "sql analyst",
    "database analyst",

    # ---------------- PRODUCT ANALYTICS ----------------
    "product analyst",

    # ---------------- MARKETING / GROWTH ANALYTICS ----------------
    "marketing analyst",
    "growth analyst",

    # ---------------- FRAUD ANALYTICS ----------------
    "fraud analyst",

    # ---------------- SUPPLY CHAIN ANALYTICS ----------------
    "supply chain analyst",
    "logistics analyst",
    "inventory analyst",
    "procurement analyst",

    # ---------------- OPERATIONS ANALYTICS ----------------
    "operations analyst",
    "operations analytics",

    # ---------------- PERFORMANCE / DECISION ----------------
    "performance analyst",
    "decision support",

    # ---------------- INTERNSHIPS / TRAINEE ----------------
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
# SENIOR / NON-FRESHER TITLE KEYWORDS
# ============================================================

SENIOR_KEYWORDS = [

    # ---------------- SENIOR ----------------
    "senior",
    "sr.",
    "sr ",

    # ---------------- LEAD ----------------
    "lead",
    "team lead",
    "tech lead",
    "technical lead",

    # ---------------- MANAGEMENT ----------------
    "manager",
    "management",
    "managing",
    "director",
    "associate director",
    "managing director",

    # ---------------- HIGH-LEVEL IC ----------------
    "principal",
    "architect",
    "expert",
    "staff",
    "specialist",

    # ---------------- LEADERSHIP ----------------
    "head of",
    "global head",

    # ---------------- EXECUTIVE ----------------
    "vice president",
    "president",
    "executive director",
    "chief",

    # ---------------- BANKING SENIORITY ----------------
    "assistant vice president",
    "associate vice president",

    # ---------------- EXPLICIT HIGHER LEVELS ----------------
    "analyst ii",
    "analyst iii",
    "analyst iv",

    "analyst 2",
    "analyst 3",
    "analyst 4",

    "engineer ii",
    "engineer iii",
    "engineer iv",

    "engineer 2",
    "engineer 3",
    "engineer 4",

    "scientist ii",
    "scientist iii",
    "scientist iv",

    "scientist 2",
    "scientist 3",
    "scientist 4",

    # ---------------- GENERIC LEVELS ----------------
    "level 2",
    "level 3",
    "level 4",

    "level ii",
    "level iii",
    "level iv",
]


# ============================================================
# SENIOR REGEX PATTERNS
#
# These catch short titles such as:
# VP - Data Analytics
# AVP, Business Analyst
# SVP Analytics
# MD - Analytics
# ============================================================

SENIOR_PATTERNS = [

    r"\bvp\b",
    r"\bavp\b",
    r"\bsvp\b",
    r"\bmd\b",

    r"\bvice[\s-]+president\b",
    r"\bassistant[\s-]+vice[\s-]+president\b",
    r"\bassociate[\s-]+vice[\s-]+president\b",

    r"\bmanaging[\s-]+director\b",
]


# ============================================================
# CLEARLY UNRELATED ROLES
# ============================================================

UNRELATED_ROLE_KEYWORDS = [

    # ---------------- FINANCE ----------------
    "project finance analyst",
    "finance analyst",
    "financial analyst",
    "investment analyst",
    "investment banking",
    "accounting analyst",
    "tax analyst",

    # ---------------- RISK ----------------
    "risk analyst",
    "climate risk",
    "market risk",
    "credit risk",

    # ---------------- HR ----------------
    "human resources",
    "hr business partner",
    "hrbp",
    "recruiter",
    "recruitment",
    "talent acquisition",

    # ---------------- LEGAL ----------------
    "legal counsel",
    "lawyer",
    "attorney",
    "paralegal",

    # ---------------- SALES ----------------
    "sales representative",
    "sales executive",
    "account executive",
    "business development manager",

    # ---------------- CREATIVE ----------------
    "copywriter",
    "graphic designer",
    "creative strategist",
    "content writer",
    "content creator",

    # ---------------- MEDICAL ----------------
    "doctor",
    "nurse",
    "physician",
    "pharmacist",

    # ---------------- PHYSICAL / FIELD ----------------
    "driver",
    "warehouse worker",
    "security guard",
    "field technician",

    # ---------------- SOFTWARE DEVELOPMENT ----------------
    "java developer",
    "java software engineer",
    "frontend developer",
    "front end developer",
    "backend developer",
    "back end developer",
    "full stack developer",
    "fullstack developer",
    "mobile developer",
    "android developer",
    "ios developer",

    # ---------------- IT INFRASTRUCTURE ----------------
    "network engineer",
    "system administrator",
    "systems administrator",
    "storage administrator",
    "cloud engineer",
    "support engineer",
    "support technician",
    "service desk",
]


# ============================================================
# INDIA LOCATIONS
# ============================================================

INDIA_LOCATION_KEYWORDS = [

    "india",

    # Cities
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

    # States
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

    # Common office locations
    "manyatha",
    "embassy business park",
]


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(value):

    if value is None:
        return ""

    value = str(value).lower().strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


def keyword_in_text(keyword, text):

    keyword = keyword.strip()

    if not keyword or not text:
        return False

    if re.search(r"\s", keyword) or "-" in keyword:
        return keyword in text

    pattern = (
        r"(?<!\w)"
        + re.escape(keyword)
        + r"(?!\w)"
    )

    return bool(
        re.search(
            pattern,
            text
        )
    )


# ============================================================
# TARGET ROLE CHECK
# ============================================================

def is_relevant_role(title):

    title = normalize_text(title)

    if not title:
        return False

    return any(
        keyword in title
        for keyword in RELEVANT_ROLE_KEYWORDS
    )


# ============================================================
# SENIOR ROLE CHECK
# ============================================================

def is_senior_role(title):

    title = normalize_text(title)

    if not title:
        return False

    # Keyword check
    if any(
        keyword_in_text(keyword, title)
        for keyword in SENIOR_KEYWORDS
    ):
        return True

    # Regex check
    if any(
        re.search(pattern, title)
        for pattern in SENIOR_PATTERNS
    ):
        return True

    return False


# ============================================================
# UNRELATED ROLE CHECK
# ============================================================

def is_clearly_unrelated(title):

    title = normalize_text(title)

    if not title:
        return True

    return any(
        keyword in title
        for keyword in UNRELATED_ROLE_KEYWORDS
    )


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

    location = normalize_text(location)

    if not location:
        return False

    return any(
        keyword in location
        for keyword in REMOTE_KEYWORDS
    )


# ============================================================
# INDIA LOCATION CHECK
# ============================================================

def is_india_location(location):

    location = normalize_text(location)

    if not location:
        return False

    return any(
        keyword in location
        for keyword in INDIA_LOCATION_KEYWORDS
    )


# ============================================================
# INTERN TITLE DETECTION
# ============================================================

INTERN_TITLE_KEYWORDS = [
    "intern",
    "internship",
    "trainee",
    "apprentice",
    "apprenticeship",
]


def is_intern_title(title):

    title = normalize_text(title)

    if not title:
        return False

    return any(
        keyword_in_text(keyword, title)
        for keyword in INTERN_TITLE_KEYWORDS
    )


# ============================================================
# BANGALORE LOCATION CHECK
# ============================================================

BANGALORE_KEYWORDS = [
    "bangalore",
    "bengaluru",
]


def is_bangalore_location(location):

    location = normalize_text(location)

    if not location:
        return False

    return any(
        keyword in location
        for keyword in BANGALORE_KEYWORDS
    )


# ============================================================
# SMART LOCATION CHECK
#
# RULES:
# - India jobs: Accept all modes (onsite/hybrid/remote)
# - Foreign jobs: Accept ONLY if remote / work-from-home
# - Intern jobs: Deferred (accept now, check paid/unpaid later)
# - Missing location: Reject
# ============================================================

def check_location(location, title=""):

    location_text = normalize_text(location)

    if not location_text:

        return (
            False,
            "Location missing"
        )

    # Example:
    # 2 Locations
    # 3 Locations
    #
    # Cannot confirm India or remote.

    if re.fullmatch(
        r"\d+\s+locations?",
        location_text
    ):

        return (
            False,
            "Location cannot be confirmed"
        )

    # INTERN: Defer location check to after JD fetch
    # (paid/unpaid determines which locations are OK)

    if is_intern_title(title):

        return (
            True,
            "Intern role (location check deferred to JD)"
        )

    # INDIA: Accept all modes (onsite / hybrid / remote)

    if is_india_location(location):

        return (
            True,
            "India location (all modes accepted)"
        )

    # FOREIGN: Accept only if remote / WFH

    if is_remote_or_wfh(location):

        return (
            True,
            "Foreign remote/WFH (accepted)"
        )

    return (
        False,
        "Foreign non-remote location (rejected)"
    )


# ============================================================
# GET ATS POSTING DATE
# ============================================================

def get_job_posting_date(job):

    source = normalize_text(
        job.get("source", "")
    )

    if source == "workday":

        return job.get(
            "posted_on"
        )

    if source == "greenhouse":

        return (
            job.get("posted_date")
            or job.get("first_published")
            or job.get("updated_at")
        )

    if source == "lever":

        return job.get(
            "created_at"
        )

    if source == "ashby":

        return job.get(
            "published_at"
        )

    if source == "smartrecruiters":

        return job.get(
            "released_date"
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
# WORKDAY RELATIVE DATE
# ============================================================

def check_workday_relative_date(value):

    if not value:
        return None

    text = normalize_text(value)

    # TODAY

    if text in (
        "posted today",
        "today"
    ):

        return (
            True,
            "Workday: Posted Today"
        )

    # YESTERDAY

    if text in (
        "posted yesterday",
        "yesterday"
    ):

        return (
            True,
            "Workday: Posted Yesterday"
        )

    # X HOURS AGO

    match = re.search(
        r"(?:posted\s+)?(\d+)\s+hours?\s+ago",
        text
    )

    if match:

        hours = int(
            match.group(1)
        )

        if hours <= MAX_JOB_AGE_HOURS:

            return (
                True,
                f"Workday: Posted {hours} hours ago"
            )

        return (
            False,
            f"Workday job is {hours} hours old"
        )

    # X DAYS AGO

    match = re.search(
        r"(?:posted\s+)?(\d+)\s+days?\s+ago",
        text
    )

    if match:

        days = int(
            match.group(1)
        )

        max_days = MAX_JOB_AGE_HOURS / 24

        if days <= max_days:

            return (
                True,
                f"Workday: Posted {days} day(s) ago"
            )

        return (
            False,
            f"Workday job is {days} days old"
        )

    return None


# ============================================================
# PARSE NORMAL ATS DATE
# ============================================================

def parse_job_date(value):

    if value is None:
        return None

    # --------------------------------------------------------
    # UNIX TIMESTAMP
    # --------------------------------------------------------

    if isinstance(
        value,
        (int, float)
    ):

        timestamp = float(value)

        if timestamp > 10_000_000_000:

            timestamp /= 1000

        try:

            return datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc
            )

        except (
            ValueError,
            OSError,
            OverflowError
        ):

            return None

    value = str(value).strip()

    if not value:
        return None

    # --------------------------------------------------------
    # NUMERIC TIMESTAMP STRING
    # --------------------------------------------------------

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
                tz=timezone.utc
            )

        except (
            ValueError,
            OSError,
            OverflowError
        ):

            return None

    # --------------------------------------------------------
    # ISO FORMAT
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # FALLBACK FORMATS
    # --------------------------------------------------------

    formats = [

        "%Y-%m-%d",

        "%Y-%m-%d %H:%M:%S",

        "%Y-%m-%dT%H:%M:%S",

        "%Y-%m-%dT%H:%M:%S.%f",

        "%m/%d/%Y",

        "%d/%m/%Y",
    ]

    for date_format in formats:

        try:

            parsed = datetime.strptime(
                value,
                date_format
            )

            return parsed.replace(
                tzinfo=timezone.utc
            )

        except ValueError:

            continue

    return None


# ============================================================
# STRICT FRESHNESS CHECK
# ============================================================

def check_job_age(job):

    source = normalize_text(
        job.get("source", "")
    )

    raw_date = get_job_posting_date(
        job
    )

    # If date is completely missing, allow it through
    if raw_date is None or str(raw_date).strip() == "":

        return (
            True,
            "Posting date unavailable (allowed)"
        )

    # WORKDAY RELATIVE DATE

    source = normalize_text(
        job.get("source", "")
    )

    if source == "workday":

        relative_result = (
            check_workday_relative_date(
                raw_date
            )
        )

        if relative_result is not None:

            return relative_result

    # NORMAL DATE

    posted_at = parse_job_date(
        raw_date
    )

    if posted_at is None:

        text = str(raw_date).lower()
        if any(k in text for k in ["30+", "30 days", "15 days", "10 days", "month", "weeks", "older"]):
            return (
                False,
                f"Rejected: Job posting is too old: {raw_date}"
            )

        return (
            True,
            f"Unparseable posting date (allowed): {raw_date}"
        )

    now = datetime.now(
        timezone.utc
    )

    age = (
        now - posted_at
    )

    # FUTURE DATE PROTECTION

    if age < timedelta(
        hours=-6
    ):

        return (
            False,
            "Posting date unexpectedly in future"
        )

    age_hours = max(
        0,
        age.total_seconds() / 3600
    )

    # FRESHNESS WINDOW

    if age_hours > MAX_JOB_AGE_HOURS:

        return (
            False,
            f"Job is {age_hours:.1f} hours old"
        )

    return (
        True,
        f"Posted {age_hours:.1f} hours ago"
    )


# ============================================================
# MAIN BASIC FILTER
# ============================================================

def basic_job_filter(job):

    title = normalize_text(
        job.get(
            "title",
            ""
        )
    )

    location = job.get(
        "location",
        ""
    )

    # --------------------------------------------------------
    # 1. TITLE REQUIRED
    # --------------------------------------------------------

    if not title:

        return (
            False,
            "Rejected: Missing job title"
        )

    # --------------------------------------------------------
    # DATE - FRESHNESS WINDOW
    # --------------------------------------------------------

    (
        age_passed,
        age_reason
    ) = check_job_age(
        job
    )

    if not age_passed:

        return (
            False,
            f"Rejected: {age_reason}"
        )

    # --------------------------------------------------------
    # 3. SENIOR ROLE - STRICT REJECTION
    # --------------------------------------------------------

    if is_senior_role(
        title
    ):

        return (
            False,
            "Rejected: Senior/non-entry-level title"
        )

    # --------------------------------------------------------
    # 4. CLEARLY UNRELATED ROLE
    # --------------------------------------------------------

    if is_clearly_unrelated(
        title
    ):

        return (
            False,
            "Rejected: Unrelated role"
        )

    # --------------------------------------------------------
    # 5. TARGET ROLE
    # --------------------------------------------------------

    if not is_relevant_role(
        title
    ):

        return (
            False,
            "Rejected: Not a target Data/Analytics role"
        )

    # --------------------------------------------------------
    # 6. LOCATION CHECK
    # --------------------------------------------------------

    (
        location_passed,
        location_reason
    ) = check_location(
        location,
        title
    )

    if not location_passed:

        return (
            False,
            f"Rejected: {location_reason}"
        )

    # --------------------------------------------------------
    # PASS
    # --------------------------------------------------------

    return (
        True,
        (
            "Passed basic filter | "
            f"{location_reason} | "
            f"{age_reason}"
        )
    )


# ============================================================
# SELF TEST
# ============================================================

if __name__ == "__main__":

    now = datetime.now(
        timezone.utc
    )

    test_jobs = [

        # SHOULD PASS

        {
            "source": "workday",
            "title": "Data Analyst",
            "location": "Bangalore, India",
            "posted_on": "Posted Today"
        },

        {
            "source": "workday",
            "title": "Business Analyst",
            "location": "Hyderabad, India",
            "posted_on": "Posted Yesterday"
        },

        {
            "source": "lever",
            "title": "Junior Data Engineer",
            "location": "Bengaluru, India",
            "created_at": int(
                (
                    now - timedelta(hours=12)
                ).timestamp() * 1000
            )
        },

        {
            "source": "ashby",
            "title": "Business Intelligence Analyst",
            "location": "Bangalore, India",
            "published_at": (
                now - timedelta(hours=20)
            ).isoformat()
        },

        # SHOULD REJECT - SENIOR

        {
            "source": "workday",
            "title": "Senior Data Analyst",
            "location": "Bangalore, India",
            "posted_on": "Posted Today"
        },

        {
            "source": "workday",
            "title": "Lead Data Engineer",
            "location": "Pune, India",
            "posted_on": "Posted Today"
        },

        {
            "source": "workday",
            "title": "Data Engineer 3",
            "location": "Bangalore, India",
            "posted_on": "Posted Today"
        },

        {
            "source": "workday",
            "title": "Data Scientist - Specialist",
            "location": "Pune, India",
            "posted_on": "Posted Today"
        },

        {
            "source": "workday",
            "title": "Operations Analyst",
            "location": "Jaipur, India",
            "posted_on": "Posted Today"
        },

        {
            "source": "workday",
            "title": "VP Data Analytics",
            "location": "Mumbai, India",
            "posted_on": "Posted Today"
        },

        {
            "source": "workday",
            "title": "Data Analytics & Management, MD",
            "location": "Bangalore, India",
            "posted_on": "Posted Today"
        },

        # SHOULD REJECT - IRRELEVANT

        {
            "source": "workday",
            "title": "Project Finance Analyst",
            "location": "Mumbai, India",
            "posted_on": "Posted Today"
        },

        {
            "source": "workday",
            "title": "Climate Risk Analyst",
            "location": "Mumbai, India",
            "posted_on": "Posted Today"
        },

        # SHOULD REJECT - OLD

        {
            "source": "workday",
            "title": "Data Analyst",
            "location": "Pune, India",
            "posted_on": "Posted 2 Days Ago"
        },

        # SHOULD REJECT - FOREIGN

        {
            "source": "greenhouse",
            "title": "Data Analyst",
            "location": "Tokyo, Japan",
            "updated_at": (
                now - timedelta(hours=5)
            ).isoformat()
        },
    ]

    print(
        "\nFINAL STRICT FRESHER FILTER TEST\n"
    )

    for job in test_jobs:

        passed, reason = basic_job_filter(
            job
        )

        result = (
            "PASS"
            if passed
            else "REJECT"
        )

        print(
            f"{result:6} | "
            f"{job['title']} | "
            f"{reason}"
        )
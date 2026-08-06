# ============================================================
# JOB ALERT SYSTEM - STRICT FRESH JOB FILTER
#
# RULES:
# 1. Target Data / Analytics roles only
# 2. India locations only
# 3. Senior roles rejected
# 4. Jobs must be within LAST 48 HOURS
# 5. Missing / invalid dates are rejected
# ============================================================

import re
from datetime import datetime, timezone, timedelta


# ============================================================
# SETTINGS
# ============================================================

MAX_JOB_AGE_HOURS = 48


# ============================================================
# TARGET ROLES
# ============================================================

RELEVANT_ROLE_KEYWORDS = [

    # Data Analyst
    "data analyst",
    "data analytics",
    "data associate",

    # Analytics
    "analytics analyst",
    "analytics associate",

    # Business Intelligence
    "business intelligence",
    "bi analyst",
    "bi developer",
    "power bi",

    # Business Analyst
    "business analyst",
    "business analytics",

    # Reporting / MIS
    "reporting analyst",
    "reporting associate",
    "mis analyst",
    "mis executive",
    "mis reporting",

    # Insights
    "insights analyst",
    "insight analyst",
    "insights associate",

    # Data Engineering
    "data engineer",
    "data engineering",

    # Data Science / ML
    "data scientist",
    "data science",
    "machine learning engineer",
    "ml engineer",
    "ai analyst",

    # SQL / Database
    "sql analyst",
    "database analyst",

    # Operations Analytics
    "operations analyst",
    "data operations",
    "analytics operations",

    # Product / Marketing
    "product analyst",
    "marketing analyst",
    "growth analyst",

    # Finance / Risk
    "financial analyst",
    "finance analyst",
    "risk analyst",
    "fraud analyst",
    "credit analyst",

    # Supply Chain
    "supply chain analyst",
    "logistics analyst",
    "inventory analyst",
    "procurement analyst",

    # Other Analyst Roles
    "performance analyst",
    "strategy analyst",
    "research analyst",
    "decision support",
]


# ============================================================
# SENIOR ROLE KEYWORDS
# ============================================================

SENIOR_KEYWORDS = [

    "senior",
    "sr.",
    "sr ",

    "lead ",
    "team lead",
    "tech lead",

    "manager",
    "managing",

    "director",
    "associate director",

    "principal",

    "staff ",

    "head of",
    "global head",

    "vice president",
    "vp ",

    "chief ",

    "architect",

    "president",
]


# ============================================================
# CLEARLY UNRELATED ROLES
# ============================================================

UNRELATED_ROLE_KEYWORDS = [

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

    # Creative
    "copywriter",
    "graphic designer",
    "creative strategist",
    "content writer",
    "content creator",

    # Medical
    "doctor",
    "nurse",
    "physician",
    "pharmacist",

    # Physical / Field
    "driver",
    "warehouse worker",
    "security guard",
    "technician",

    # Software Development
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

    # IT Infrastructure
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

    # Common office strings
    "manyatha",
    "embassy business park",
]


# ============================================================
# TEXT NORMALIZER
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


# ============================================================
# ROLE CHECK
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
# SENIOR CHECK
# ============================================================

def is_senior_role(title):

    title = normalize_text(title)

    if not title:
        return False

    return any(
        keyword in title
        for keyword in SENIOR_KEYWORDS
    )


# ============================================================
# UNRELATED CHECK
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
# STRICT INDIA LOCATION CHECK
# ============================================================

def check_location(location):

    location = normalize_text(location)

    if not location:

        return (
            False,
            "Location missing"
        )


    # Example:
    # "2 Locations"
    # "3 Locations"
    #
    # India cannot be confirmed.

    if re.fullmatch(
        r"\d+\s+locations?",
        location
    ):

        return (
            False,
            "India location cannot be confirmed"
        )


    if any(
        keyword in location
        for keyword in INDIA_LOCATION_KEYWORDS
    ):

        return (
            True,
            "India location"
        )


    return (
        False,
        "Non-India or unverified location"
    )


# ============================================================
# GET DATE FIELD FROM ATS
# ============================================================

def get_job_posting_date(job):

    source = normalize_text(
        job.get(
            "source",
            ""
        )
    )


    if source == "workday":

        return job.get(
            "posted_on"
        )


    if source == "greenhouse":

        return job.get(
            "updated_at"
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


    # Generic fallback

    return (
        job.get("posted_date")
        or job.get("posted_on")
        or job.get("published_at")
        or job.get("released_date")
        or job.get("created_at")
        or job.get("updated_at")
    )


# ============================================================
# WORKDAY RELATIVE DATE CHECK
# ============================================================

def check_workday_relative_date(value):

    if not value:
        return None


    text = normalize_text(value)


    # --------------------------------------------------------
    # POSTED TODAY
    # --------------------------------------------------------

    if text in (
        "posted today",
        "today"
    ):

        return (
            True,
            "Workday: Posted Today"
        )


    # --------------------------------------------------------
    # POSTED YESTERDAY
    # --------------------------------------------------------

    if text in (
        "posted yesterday",
        "yesterday"
    ):

        return (
            True,
            "Workday: Posted Yesterday"
        )


    # --------------------------------------------------------
    # POSTED X DAYS AGO
    # --------------------------------------------------------

    match = re.search(
        r"(?:posted\s+)?(\d+)\s+days?\s+ago",
        text
    )


    if match:

        days = int(
            match.group(1)
        )


        # Strict 48-hour policy:
        #
        # 0 days = PASS
        # 1 day  = PASS
        #
        # "2 Days Ago" could already be >48 hours,
        # therefore reject.

        if days <= 1:

            return (
                True,
                f"Workday: Posted {days} day(s) ago"
            )


        return (
            False,
            f"Workday job is {days} days old"
        )


    # --------------------------------------------------------
    # POSTED X HOURS AGO
    # --------------------------------------------------------

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


        # Milliseconds

        if timestamp > 10_000_000_000:

            timestamp = (
                timestamp / 1000
            )


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

                timestamp = (
                    timestamp / 1000
                )


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
# STRICT 48-HOUR CHECK
# ============================================================

def check_job_age(job):

    source = normalize_text(
        job.get(
            "source",
            ""
        )
    )


    raw_date = get_job_posting_date(
        job
    )


    # --------------------------------------------------------
    # DATE MUST EXIST
    # --------------------------------------------------------

    if raw_date is None:

        return (
            False,
            "Posting date missing"
        )


    if str(raw_date).strip() == "":

        return (
            False,
            "Posting date missing"
        )


    # --------------------------------------------------------
    # WORKDAY RELATIVE DATE
    # --------------------------------------------------------

    if source == "workday":

        relative_result = (
            check_workday_relative_date(
                raw_date
            )
        )


        if relative_result is not None:

            return relative_result


    # --------------------------------------------------------
    # NORMAL TIMESTAMP / ISO DATE
    # --------------------------------------------------------

    posted_at = parse_job_date(
        raw_date
    )


    if posted_at is None:

        return (
            False,
            f"Invalid/unparseable posting date: {raw_date}"
        )


    now = datetime.now(
        timezone.utc
    )


    age = (
        now - posted_at
    )


    # --------------------------------------------------------
    # FUTURE DATE PROTECTION
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # STRICT MAXIMUM 48 HOURS
    # --------------------------------------------------------

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


    # ========================================================
    # 1. TITLE REQUIRED
    # ========================================================

    if not title:

        return (
            False,
            "Rejected: Missing job title"
        )


    # ========================================================
    # 2. STRICT 48-HOUR CHECK
    # ========================================================

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


    # ========================================================
    # 3. SENIOR ROLE CHECK
    # ========================================================

    if is_senior_role(
        title
    ):

        return (
            False,
            "Rejected: Senior/Lead/Manager level role"
        )


    # ========================================================
    # 4. TARGET ROLE CHECK
    # ========================================================

    if not is_relevant_role(
        title
    ):

        return (
            False,
            "Rejected: Not a target data/analytics role"
        )


    # ========================================================
    # 5. UNRELATED ROLE CHECK
    # ========================================================

    if is_clearly_unrelated(
        title
    ):

        return (
            False,
            "Rejected: Clearly unrelated job role"
        )


    # ========================================================
    # 6. INDIA LOCATION CHECK
    # ========================================================

    (
        location_passed,
        location_reason
    ) = check_location(
        location
    )


    if not location_passed:

        return (
            False,
            f"Rejected: {location_reason}"
        )


    # ========================================================
    # PASS
    # ========================================================

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

        # ----------------------------------------------------
        # WORKDAY TODAY
        # ----------------------------------------------------

        {
            "source":
                "workday",

            "title":
                "Data Analyst",

            "location":
                "Bangalore, India",

            "posted_on":
                "Posted Today"
        },


        # ----------------------------------------------------
        # WORKDAY YESTERDAY
        # ----------------------------------------------------

        {
            "source":
                "workday",

            "title":
                "Data Analyst",

            "location":
                "Hyderabad, India",

            "posted_on":
                "Posted Yesterday"
        },


        # ----------------------------------------------------
        # WORKDAY 2 DAYS AGO - STRICT REJECT
        # ----------------------------------------------------

        {
            "source":
                "workday",

            "title":
                "Data Analyst",

            "location":
                "Pune, India",

            "posted_on":
                "Posted 2 Days Ago"
        },


        # ----------------------------------------------------
        # LEVER 12 HOURS
        # ----------------------------------------------------

        {
            "source":
                "lever",

            "title":
                "Data Analyst",

            "location":
                "Bangalore, India",

            "created_at":
                int(
                    (
                        now
                        - timedelta(hours=12)
                    ).timestamp()
                    * 1000
                )
        },


        # ----------------------------------------------------
        # ASHBY 30 HOURS
        # ----------------------------------------------------

        {
            "source":
                "ashby",

            "title":
                "Business Intelligence Analyst",

            "location":
                "Bangalore, India",

            "published_at":
                (
                    now
                    - timedelta(hours=30)
                ).isoformat()
        },


        # ----------------------------------------------------
        # SMARTRECRUITERS 60 HOURS - REJECT
        # ----------------------------------------------------

        {
            "source":
                "smartrecruiters",

            "title":
                "Data Analyst",

            "location":
                "Bangalore, India",

            "released_date":
                (
                    now
                    - timedelta(hours=60)
                ).isoformat()
        },


        # ----------------------------------------------------
        # FOREIGN JOB - REJECT
        # ----------------------------------------------------

        {
            "source":
                "greenhouse",

            "title":
                "Data Analyst",

            "location":
                "Tokyo, Japan",

            "updated_at":
                (
                    now
                    - timedelta(hours=5)
                ).isoformat()
        },


        # ----------------------------------------------------
        # SENIOR JOB - REJECT
        # ----------------------------------------------------

        {
            "source":
                "workday",

            "title":
                "Senior Data Analyst",

            "location":
                "Bangalore, India",

            "posted_on":
                "Posted Today"
        },
    ]


    print(
        "\nSTRICT FRESH-JOB FILTER TEST\n"
    )


    for job in test_jobs:

        passed, reason = (
            basic_job_filter(
                job
            )
        )


        result = (
            "PASS"
            if passed
            else "REJECT"
        )


        print(
            f"{result:6} | "
            f"{job['source']:16} | "
            f"{job['title']} | "
            f"{job['location']} | "
            f"{reason}"
        )
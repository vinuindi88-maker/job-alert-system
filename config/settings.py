# ==========================================
# JOB ALERT SYSTEM - GLOBAL SETTINGS
# ==========================================

# Minimum resume-to-job match required
MIN_MATCH_SCORE = 80

# Experience range
MIN_EXPERIENCE = 0
MAX_EXPERIENCE = 2

# Target job roles
TARGET_ROLES = [
    "Data Analyst",
    "Junior Data Analyst",
    "Associate Data Analyst",
    "Business Data Analyst",
    "BI Analyst",
    "Business Intelligence Analyst",
    "Reporting Analyst",
    "Junior Business Analyst",
    "Business Analyst",
    "Data Engineer",
    "Junior Data Engineer",
    "Associate Data Engineer",
    "Data Scientist",
    "Junior Data Scientist",
    "Associate Data Scientist",
]

# Roles we do NOT want
EXCLUDED_TITLE_KEYWORDS = [
    "Senior",
    "Sr.",
    "Lead",
    "Manager",
    "Principal",
    "Director",
    "Head",
    "Architect",
    "Staff",
]

# Allowed experience wording
ENTRY_LEVEL_KEYWORDS = [
    "fresher",
    "freshers",
    "entry level",
    "entry-level",
    "graduate",
    "new graduate",
    "0-1 years",
    "0-2 years",
]

# Location settings
# Start with India. Later we can add worldwide/visa-sponsored jobs.
ALLOWED_COUNTRIES = [
    "India",
]

PREFERRED_LOCATIONS = [
    "Bangalore",
    "Bengaluru",
    "Pune",
    "Mumbai",
    "Hyderabad",
    "Chennai",
    "Delhi",
    "Gurugram",
    "Gurgaon",
    "Noida",
    "Remote",
]

# Employment types
ALLOWED_EMPLOYMENT_TYPES = [
    "Full-time",
    "Full time",
    "Permanent",
]

# Job freshness
MAX_JOB_AGE_HOURS = 48

# Email only new jobs
SEND_DUPLICATE_ALERTS = False
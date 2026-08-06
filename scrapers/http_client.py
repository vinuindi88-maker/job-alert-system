# ============================================================
# JOB ALERT SYSTEM - COMMON HTTP CLIENT
# Retry + Backoff + Rate Limit Protection
# ============================================================

import random
import time
import requests


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_TIMEOUT = 30

MAX_RETRIES = 5

RETRY_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.headers.update(
    DEFAULT_HEADERS
)


# ============================================================
# BACKOFF
# ============================================================

def _wait_before_retry(attempt, response=None):
    """
    Exponential backoff with small random jitter.

    Example:
    ~1 sec
    ~2 sec
    ~4 sec
    ~8 sec
    ~16 sec
    """

    # Respect Retry-After when server provides it.

    if response is not None:

        retry_after = response.headers.get(
            "Retry-After"
        )

        if retry_after:

            try:

                wait_time = float(
                    retry_after
                )

                print(
                    f"[HTTP] Server requested "
                    f"{wait_time:.1f}s wait"
                )

                time.sleep(
                    wait_time
                )

                return

            except ValueError:
                pass


    wait_time = (
        2 ** attempt
    ) + random.uniform(
        0.2,
        0.8
    )

    print(
        f"[HTTP] Retrying in "
        f"{wait_time:.1f}s..."
    )

    time.sleep(
        wait_time
    )


# ============================================================
# REQUEST
# ============================================================

def request(
    method,
    url,
    *,
    timeout=DEFAULT_TIMEOUT,
    max_retries=MAX_RETRIES,
    polite_delay=0.10,
    **kwargs
):
    """
    Send an HTTP request with retry protection.

    Retries temporary errors:
    429
    500
    502
    503
    504

    Other HTTP errors are raised immediately.
    """

    last_error = None

    for attempt in range(
        max_retries + 1
    ):

        try:

            # Small delay prevents hammering ATS APIs.

            if polite_delay > 0:

                time.sleep(
                    polite_delay
                )


            response = session.request(
                method=method,
                url=url,
                timeout=timeout,
                **kwargs
            )


            # --------------------------------------------
            # SUCCESS
            # --------------------------------------------

            if response.status_code < 400:

                return response


            # --------------------------------------------
            # RETRYABLE HTTP ERROR
            # --------------------------------------------

            if (
                response.status_code
                in RETRY_STATUS_CODES
            ):

                print(
                    f"[HTTP] "
                    f"{response.status_code} "
                    f"from {url}"
                )


                if attempt >= max_retries:

                    response.raise_for_status()


                _wait_before_retry(
                    attempt,
                    response
                )

                continue


            # --------------------------------------------
            # NON-RETRYABLE HTTP ERROR
            # --------------------------------------------

            response.raise_for_status()


        except (
            requests.Timeout,
            requests.ConnectionError
        ) as error:

            last_error = error

            print(
                f"[HTTP] Temporary network error: "
                f"{error}"
            )


            if attempt >= max_retries:

                raise


            _wait_before_retry(
                attempt
            )


        except requests.RequestException:

            raise


    if last_error:

        raise last_error


    raise RuntimeError(
        "HTTP request failed after retries."
    )


# ============================================================
# GET
# ============================================================

def get(
    url,
    **kwargs
):

    return request(
        "GET",
        url,
        **kwargs
    )


# ============================================================
# POST
# ============================================================

def post(
    url,
    **kwargs
):

    return request(
        "POST",
        url,
        **kwargs
    )


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\nCOMMON HTTP CLIENT READY\n"
    )

    print(
        "Retry + backoff + "
        "rate-limit protection enabled."
    )
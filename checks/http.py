"""checks/http.py - is the service actually well? Extension tier.

The TCP check tells you a process is listening. This one asks it how it is.

YOU WRITE THIS. The signature and contract are fixed, because healthcheck.py
already calls it.
"""

from __future__ import annotations
from . import DEGRADED, DOWN, OK, CheckResult

# Added imports
import requests
import time

CHECK_NAME = "http"

def check_http(name: str, url: str, timeout: float) -> CheckResult:
    """GET the health endpoint at url, and classify what came back.

    Use requests.get(url, timeout=timeout). The timeout is not optional:
    requests has NO default timeout and will wait forever without one. Node 8803
    exists to prove it.

    Four outcomes, and each is a different finding:

      HTTP 200 and the body says "status": "ok"   ->  OK
      any other status code, or a 200 whose body
        says something other than ok              ->  DEGRADED
      the request timed out                       ->  DOWN
      the connection failed (refused, DNS)        ->  DOWN

    Why is a 500 DEGRADED and not DOWN? Because you reached it and it answered.
    Something is listening, and it is telling you it is unwell. That needs a
    different person to do a different thing from a host that is not there.

    Put the useful part of the answer in `detail`. Node 8802 explains itself in
    its response body - "HTTP 500: database connection pool exhausted" is far
    more use to an engineer than "HTTP 500".

    When the check passes, put the parsed JSON body in extra={"payload": body}.
    The disk check reads the disk figures from there, so you only make one
    request per target, not two.

    Never raises. Catch the requests exceptions you expect, specifically. The
    requests exceptions are related to each other in the same way the socket
    ones are, so the order of your except blocks matters again.
    """
    # TODO

    # Get server response and time it
    start = time.perf_counter()
    result = requests.get(url, timeout=timeout)
    end = time.perf_counter()

    # Calculate latency
    latencyMs = end - start * 1000

    # Isolate response code
    statusCode = result.status_code
    statusString = f"HTTP: {statusCode}"

    # Full body of the response
    body = result.json()

    if statusCode == 200:
        detail = statusString+": Connected and healthy"
        return CheckResult(
            target = name,
            check = CHECK_NAME,
            state = OK,
            detail = detail,
            latency_ms = latencyMs,
            extra= {"Full Response": body}
        )

    if statusCode // 100 == 2:
        detail = statusString + ": Connected but unhealthy"
        return CheckResult(
            target = name,
            check = CHECK_NAME,
            state = DEGRADED,
            detail = detail,
            latency_ms = latencyMs,
            extra= {"Full Response": body}
        )

    if statusCode // 100 == 3:
        return CheckResult(
            target = name,
            check = CHECK_NAME,
            state = DEGRADED,
            detail = statusString,
            latency_ms = latencyMs,
            extra= {"Full Response": body}
        )

    if statusCode // 100 == 4:
        return CheckResult(
            target = name,
            check = CHECK_NAME,
            state = DEGRADED,
            detail = statusString,
            latency_ms = latencyMs,
            extra= {"Full Response": body}
        )

    if statusCode // 100 == 2:
        return CheckResult(
            target = name,
            check = CHECK_NAME,
            state = DEGRADED,
            detail = statusString,
            latency_ms = latencyMs,
            extra= {"Full Response": body}
        )

    if statusCode // 100 == 5:
        return CheckResult(
            target = name,
            check = CHECK_NAME,
            state = DEGRADED,
            detail = statusString,
            latency_ms = latency,
            extra= {"Full Response": body}
        )

    raise NotImplementedError("check_http() in checks/http.py is not written yet")

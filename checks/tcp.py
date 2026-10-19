"""checks/tcp.py - is anything listening on that port? Core tier.

The cheapest check there is, and the first thing an engineer runs at 3am.

YOU WRITE THIS. The function signature and its contract are fixed, because
healthcheck.py already calls it. Fill in the body.
"""

from __future__ import annotations

import socket
import time

from . import DOWN, OK, CheckResult

CHECK_NAME = "tcp"


def check_tcp(name: str, host: str, port: int, timeout: float) -> CheckResult:
    """Open a TCP connection to host:port, close it again, and report.

    Returns a CheckResult with state OK if the connection opened, DOWN if not.

    Never raises. One unreachable host must not stop you checking the rest of
    the fleet, so every failure becomes a DOWN result rather than an exception.

    The tool to use is socket.create_connection((host, port), timeout=timeout),
    inside a `with` block so the socket is always closed.

    Tell these failure modes apart in `detail`. They mean different things to
    whoever reads your output:

      - the host name does not resolve        (try fleet-node-05.invalid)
      - connection refused - nothing listening (try 127.0.0.1 port 8804)
      - timed out - no answer at all

    Each one raises a different exception. Find out which by trying them in a
    Python shell before you write the except blocks, and think about the order
    you catch them in: they are related, and catching the general one first
    hides the specific ones.

    Measuring latency_ms is optional but cheap: time.perf_counter() before and
    after.

    Notice what this check cannot tell you. Run it against node 8802 when it
    works. Then read fleet/node_broken.py.
    """
    # TODO
    #raise NotImplementedError("check_tcp() in checks/tcp.py is not written yet")

    start = time.perf_counter()

    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass

        state = OK
        detail = "Connection successful"

    except socket.gaierror:
        state = DOWN
        detail = "Hostname could not be resolved"

    except ConnectionRefusedError:
        state = DOWN
        detail = "Connection refused"

    except TimeoutError:
        state = DOWN
        detail = "Connection timed out"

    except OSError as exc:
        state = DOWN
        detail = str(exc)

    latency_ms = (time.perf_counter() - start) * 1000

    return CheckResult(
        target=name,
        check=CHECK_NAME,
        state=state,
        detail=detail,
        latency_ms=latency_ms,
    )

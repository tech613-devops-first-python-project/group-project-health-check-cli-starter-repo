"""report.py - turn a list of CheckResults into something people and programs can read.

Two audiences, two formats. The console table is for the person running the
tool right now. The JSON report is for whatever reads it next: another script,
a ticket, or the same tool tomorrow comparing today against yesterday.

Neither replaces the log file. The log says what happened and when. The report
says what was true at the end.

YOU WRITE THIS. The signatures are fixed, because healthcheck.py and alerts.py
already call them.
"""

from __future__ import annotations

from pathlib import Path

from checks import DEGRADED, DOWN, OK, CheckResult


def worst_state(results: list[CheckResult]) -> str:
    """The overall verdict for the whole run. DOWN beats DEGRADED beats OK.

    This one function decides your tool's exit code, so it is worth a test.
    Core tier.
    """
    # TODO
    raise NotImplementedError("worst_state() in report.py is not written yet")


def render_table(results: list[CheckResult]) -> str:
    """Return a plain-text table of every check, one row per result. Core tier.

    Something like:

        TARGET         CHECK  STATE     DETAIL
        fleet-node-01  tcp    OK        connected to 127.0.0.1:8801
        fleet-node-04  tcp    DOWN      connection refused by 127.0.0.1:8804

    Return the string rather than printing it, so it is easy to test.

    Keep the columns lined up with f-string widths, such as f"{name:<15}".
    Avoid colour codes: they turn into junk characters in some Windows
    terminals and in any file the output is saved to.
    """
    # Define headers
    headers = ("TARGET", "CHECK", "STATE", "DETAIL")

    # Extract the list input and take only significant data
    rows = [
        (r.target, r.check, r.state, r.detail)
        for r in results
    ]

    # Find the widest value in each column, including the header. This was LLM generated.
    widths = [
        max(len(str(value)) for value in column)
        for column in zip(headers, *rows)
    ] if rows else [len(header) for header in headers]

    # Build the header and data rows.
    lines = [
        f"{headers[0]:<{widths[0]}}  "
        f"{headers[1]:<{widths[1]}}  "
        f"{headers[2]:<{widths[2]}}  "
        f"{headers[3]}"
    ]

    for row in rows:
        lines.append(
            f"{row[0]:<{widths[0]}}  "
            f"{row[1]:<{widths[1]}}  "
            f"{row[2]:<{widths[2]}}  "
            f"{row[3]}"
        )

    return "\n".join(lines)


def summarise(results: list[CheckResult]) -> dict:
    """Count results by state: {"OK": 7, "DEGRADED": 2, "DOWN": 3}. Core tier."""
    summary = {"OK": 0, "DEGRADED": 0, "DOWN": 0}
    for item in results:
        if item.state == OK:
            summary["OK"] += 1
        if item.state == DEGRADED:
            summary["DEGRADED"] += 1
        if item.state == DOWN:
            summary["DOWN"] += 1
    return summary


def write_json_report(results: list[CheckResult], path: Path) -> Path:
    """Write a structured JSON report to path, and return the path. Extension tier.

    Include at least: when the report was generated, the overall state, the
    summary counts, and every result (CheckResult.as_dict() does the work).

    Use pathlib to create the parent directory if it does not exist, and write
    the file with a context manager or Path.write_text.

    Make the timestamp timezone-aware, in UTC. A local time with no zone in an
    incident report is a real hazard: two people in different places read the
    same file and disagree about when it happened.
    """
    # TODO
    raise NotImplementedError("write_json_report() in report.py is not written yet")

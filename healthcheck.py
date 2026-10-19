"""healthcheck.py - check the health of a fleet of servers, and say so with an exit code.

YOUR TEAM WRITES THIS TOOL. This file is the entry point, and some of it is done
for you: the command-line arguments, the logging setup and the overall shape of
a run. The checks themselves live in the checks/ package, one module per check,
so that several of you can work at once on separate branches.

Run it, with the fake fleet running in another terminal:

    python healthcheck.py
    python healthcheck.py --config other.yaml
    python healthcheck.py --json-report reports/report.json
    python healthcheck.py --help

The exit code is a contract. Do not invent new codes:

    0  every target healthy
    1  something degraded (reachable, but failing a check), or the config is bad
    2  something down (unreachable, refused, timed out, or does not resolve)

Your closing demo is one line:

    python healthcheck.py && echo "DEPLOY"

The second command runs only if the first exits 0. That is a pipeline gate,
four weeks before you meet Jenkins.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import alerts
import report
from checks import DEGRADED, DOWN, OK, CheckResult
from checks.disk import check_local_disk, check_reported_disk
from checks.http import check_http
from checks.ping import check_ping
from checks.tcp import check_tcp
from config import ConfigError, load_config

EXIT_OK = 0
EXIT_DEGRADED = 1
EXIT_DOWN = 2

log = logging.getLogger("healthcheck")


# --------------------------------------------------------------------------
# Your team writes these two functions.
# --------------------------------------------------------------------------


def check_target(target: dict, timeout: float, threshold: int,
                 with_ping: bool = False) -> list[CheckResult]:
    """Run every check that applies to one target. Return a list of results.

    Build it up a tier at a time:

      Core       the TCP check only: check_tcp(name, host, port, timeout).
      Extension  if the target has a health_url, the HTTP check as well. If the
                 HTTP check's payload has disk figures, the disk check too.
      Stretch    if with_ping is True, the ping check.

    Two decisions for your team to make and to be able to explain in the demo:

      - If the TCP check says DOWN, is there any point running the HTTP check?
        What would the report look like if you did?
      - A target that never claimed to report its disk - the GitHub API, say -
        has no disk figures. Is that target degraded, or is that your tool
        inventing a problem?
    """
    # TODO
    raise NotImplementedError("check_target() in healthcheck.py is not written yet")



def overall_exit_code(results: list[CheckResult]) -> int:
    """Turn the worst result into an exit code from the contract above.

    report.worst_state() gives you the worst state. Map it to EXIT_OK,
    EXIT_DEGRADED or EXIT_DOWN.
    """
    # TODO
    worst = report.worst_state(results)
    if worst == DOWN:
        return EXIT_DOWN
    elif worst == DEGRADED:
        return EXIT_DEGRADED
    else:
        return EXIT_OK


# --------------------------------------------------------------------------
# Done for you. Read it - you will change parts of it as you go.
# --------------------------------------------------------------------------


def configure_logging(log_file: Path, verbose: bool) -> None:
    """Log to the console and to a file, at different levels.

    The console gets what the person watching needs right now. The file gets
    everything, including DEBUG, because the question a log file answers is
    usually asked tomorrow, by someone who was not there.

    The test to set yourself: could a teammate who was not there work out what
    happened from healthcheck.log alone?
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
    root.addHandler(console)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(name)s %(message)s")
    )
    root.addHandler(file_handler)


def build_parser() -> argparse.ArgumentParser:
    """Command-line arguments.

    argparse gives you --help for free, which is the difference between a
    script only you can run and a tool your team can run.
    """
    parser = argparse.ArgumentParser(
        description="Check the health of a fleet of servers.",
        epilog="Exit codes: 0 all healthy, 1 degraded or bad config, 2 something down.",
    )
    parser.add_argument("--config", type=Path, default=Path("targets.yaml"),
                        help="path to the fleet config (default: targets.yaml)")
    parser.add_argument("--timeout", type=float,
                        help="override the timeout in seconds for every check")
    parser.add_argument("--json-report", type=Path, metavar="PATH",
                        help="also write a structured JSON report to PATH")
    parser.add_argument("--log-file", type=Path, default=Path("healthcheck.log"),
                        help="where to write the log (default: healthcheck.log)")
    parser.add_argument("--ping", action="store_true",
                        help="also run a ping check (may be blocked on your network)")
    parser.add_argument("--local-disk", action="store_true",
                        help="also check the disk of the machine running this tool")
    parser.add_argument("--alert", action="store_true",
                        help=f"post an alert if anything is wrong, to ${alerts.ENV_VAR}")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="show debug output on the console")
    return parser


def run(args: argparse.Namespace) -> int:
    """One complete run of the tool. Returns the exit code."""
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        # Every problem at once, so the user fixes them all in one pass.
        log.error("%s is not usable. %d problem(s) found:",
                  args.config, len(exc.problems))
        for problem in exc.problems:
            log.error("  - %s", problem)
        log.error("nothing was checked and no network call was made")
        return EXIT_DEGRADED

    timeout = args.timeout if args.timeout is not None else config.timeout_seconds
    log.info("loaded %d target(s) from %s", len(config.targets), args.config)
    for target in config.targets:
        log.info("  %s (%s)", target.get("name"), target.get("host"))

    results: list[CheckResult] = []
    for target in config.targets:
        results.extend(
            check_target(target, timeout, config.disk_threshold_percent,
                         with_ping=args.ping)
        )

    if args.local_disk:
        results.append(check_local_disk(config.disk_threshold_percent))

    # The table goes to stdout and the logs to stderr. flush=True keeps them in
    # the right order when both appear in the same terminal.
    print(report.render_table(results), flush=True)

    counts = report.summarise(results)
    log.info("%d ok, %d degraded, %d down",
             counts.get(OK, 0), counts.get(DEGRADED, 0), counts.get(DOWN, 0))

    if args.json_report:
        written = report.write_json_report(results, args.json_report)
        log.info("wrote %s", written)

    if args.alert:
        alerts.send_alert(results)

    return overall_exit_code(results)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.log_file, args.verbose)

    try:
        return run(args)
    except NotImplementedError as exc:
        # Every unwritten function says which one it is. This turns "a wall of
        # traceback" into "here is the next thing to write". Once your tool is
        # complete, this never fires. Leave it in anyway.
        log.error("not finished yet: %s", exc)
        return EXIT_DEGRADED


if __name__ == "__main__":
    sys.exit(main())

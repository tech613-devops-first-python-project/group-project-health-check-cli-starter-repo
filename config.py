"""config.py - load targets.yaml and refuse to go on if it is wrong. Core tier.

This is the first thing your tool does, and the most important. A tool that
starts checking a fleet with a broken config produces confident nonsense.

YOU WRITE load_config(). ConfigError and Config are given, because
healthcheck.py already depends on their shape.
"""

from __future__ import annotations

from pathlib import Path

# Used if targets.yaml has no defaults block yet. Your team decides whether
# these numbers are right - they are a starting point, not an answer.
DEFAULT_TIMEOUT_SECONDS = 2.0
DEFAULT_DISK_THRESHOLD_PERCENT = 85

import yaml

class ConfigError(Exception):
    """Raised when the config cannot be used. Carries EVERY problem found."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


class Config:
    """A validated config. If you are holding one, it is safe to use."""

    def __init__(self, targets: list[dict], timeout_seconds: float,
                 disk_threshold_percent: int):
        self.targets = targets
        self.timeout_seconds = timeout_seconds
        self.disk_threshold_percent = disk_threshold_percent

    def __repr__(self) -> str:
        return (f"Config(targets={len(self.targets)}, "
                f"timeout_seconds={self.timeout_seconds}, "
                f"disk_threshold_percent={self.disk_threshold_percent})")


def load_config(path: Path) -> Config:
    """Read targets.yaml, validate it, and return a Config.

    Raises ConfigError listing EVERY problem found, not only the first one.
    Someone with three mistakes in the file should learn about all three in one
    run, not fix one, re-run, and find the next.

    The pattern that makes that possible: start with an empty list called
    problems, append to it every time you find something wrong, and raise
    ConfigError(problems) once at the very end if the list is not empty.

    Work up through these levels:

      1. The file exists, and it is valid YAML. A stray tab should give a clear
         message, not a traceback. Use yaml.safe_load, never yaml.load.
      2. There is a `targets` list and it is not empty.
      3. Every target has a name and a host. Once your team adds port, every
         target needs that too.
      4. The values make sense. A port is a whole number from 1 to 65535 - and
         watch out for port: "8801" in quotes, which YAML reads as text. A
         health_url starts with http. A timeout is a positive number. A disk
         threshold is a whole number from 1 to 100.

    All of this happens before a single network call. A run that fails here has
    contacted nothing and changed nothing, which is why it can stop cleanly.
    """
    
    # Store every problem we find.
    problems = []

    # Stop early if the file does not exist.
    if not path.is_file():
        raise ConfigError([f"Config file does not exist: {path}"])

    # Read the YAML file and handle invalid YAML.
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except (yaml.YAMLError, UnicodeError) as exc:
        raise ConfigError([f"Invalid YAML: {exc}"]) from exc
    except OSError as exc:
        raise ConfigError([f"Cannot read config file: {exc}"]) from exc

    # The top level must be a dictionary.
    if not isinstance(data, dict):
        raise ConfigError(["Config must contain a YAML mapping."])

    # Read the defaults, or use the supplied default values.
    defaults = data.get("defaults", {})
    if not isinstance(defaults, dict):
        problems.append("'defaults' must be a mapping.")
        defaults = {}

    timeout = defaults.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    threshold = defaults.get(
        "disk_threshold_percent",
        DEFAULT_DISK_THRESHOLD_PERCENT,
    )

    # Check the timeout.
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or timeout <= 0
    ):
        problems.append("timeout_seconds must be a positive number.")

    # Check the disk threshold.
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, int)
        or not 1 <= threshold <= 100
    ):
        problems.append(
            "disk_threshold_percent must be a whole number from 1 to 100."
        )

    # Check that targets is a non-empty list.
    targets = data.get("targets")

    if not isinstance(targets, list) or not targets:
        problems.append("'targets' must be a non-empty list.")
        targets = []

    # Validate every target instead of stopping at the first problem.
    for index, target in enumerate(targets, start=1):
        label = f"Target {index}"

        if not isinstance(target, dict):
            problems.append(f"{label} must be a mapping.")
            continue

        # Check the required name.
        if not isinstance(target.get("name"), str) or not target["name"].strip():
            problems.append(f"{label} needs a non-empty name.")

        # Check the required host.
        if not isinstance(target.get("host"), str) or not target["host"].strip():
            problems.append(f"{label} needs a non-empty host.")

        # Check the port. Quoted strings such as "8801" are rejected.
        port = target.get("port")
        if (
            isinstance(port, bool)
            or not isinstance(port, int)
            or not 1 <= port <= 65535
        ):
            problems.append(
                f"{label} port must be a whole number from 1 to 65535."
            )

        # Validate health_url only when it is supplied.
        url = target.get("health_url")
        if url is not None and (
            not isinstance(url, str)
            or not url.startswith(("http://", "https://"))
        ):
            problems.append(f"{label} health_url must start with http.")

    # If anything was wrong, report all collected problems together.
    if problems:
        raise ConfigError(problems)

    # Return a validated configuration.
    return Config(
        targets=targets,
        timeout_seconds=float(timeout),
        disk_threshold_percent=threshold,
    )




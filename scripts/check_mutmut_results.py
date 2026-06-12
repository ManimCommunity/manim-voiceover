from __future__ import annotations

import subprocess
import sys

FAILING_STATUSES = {"survived", "timeout", "no tests", "suspicious", "not checked"}


def collect_failures(output: str) -> list[tuple[str, str]]:
    failures = []
    for line in output.splitlines():
        if ":" not in line:
            continue
        name, status = line.rsplit(":", 1)
        status = status.strip()
        if status in FAILING_STATUSES:
            failures.append((name.strip(), status))
    return failures


def print_failures(failures: list[tuple[str, str]]) -> None:
    print("Mutation testing left failing mutants:")
    counts: dict[str, int] = {}
    for _, status in failures:
        counts[status] = counts.get(status, 0) + 1
    for status in sorted(counts):
        print(f"- {status}: {counts[status]}")
    print()
    for name, status in failures[:100]:
        print(f"{name}: {status}")
    if len(failures) > 100:
        print(f"... {len(failures) - 100} more")


def main() -> int:
    completed = subprocess.run(
        ["mutmut", "results"],
        capture_output=True,
        check=False,
        text=True,
    )
    output = completed.stdout + completed.stderr
    failures = collect_failures(output)

    if failures:
        print_failures(failures)
        return 1

    if completed.returncode != 0:
        sys.stderr.write(output)
        return completed.returncode

    print("Mutation testing passed: no surviving, timed-out, suspicious, or untested mutants.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

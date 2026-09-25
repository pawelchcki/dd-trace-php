#!/usr/bin/env python3
"""Measure full-matrix rebuilds after one C edit and one Rust edit.

The workflow must build the target set once before running this script. Each
temporary one-line edit changes a compiled value, remains in place for three
samples, and is restored before the next source is edited. Results attach to the
BuildBuddy workflow through BUILDBUDDY_ARTIFACTS_DIRECTORY.
"""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    "//bazel/products/tracer:ddtrace_fat_all",
    "//bazel/php:product_matrix",
    "//:rust_datadog_php_shared_amd64_glibc",
    "//:rust_datadog_php_shared_amd64_musl",
    "//:rust_datadog_php_shared_arm64_glibc",
    "//:rust_datadog_php_shared_arm64_musl",
    "//:dd_library_php_tracer_tarballs",
]
FLAGS = [
    "--config=remote-hermetic-amd64",
    "--remote_executor=grpcs://remote.buildbuddy.io",
    "--remote_cache=grpcs://remote.buildbuddy.io",
    "--remote_instance_name=",
    "--remote_exec_header=x-buildbuddy-platform.Pool=linux-amd64-kvm",
    "--remote_exec_header=x-buildbuddy-platform.use-self-hosted-executors=true",
    "--remote_local_fallback=false",
    "--remote_download_outputs=toplevel",
    "--jobs=25",
]
COMMAND = ["bazel", "build", *TARGETS, *FLAGS]
EDIT_CASES = [
    ("c", Path("components/log/log.c"), b"char buf[0x100];", b"char buf[0x101];"),
    (
        "rust", Path("components-rs/log.rs"),
        b"; This message is only displayed once. Specify DD_TRACE_ONCE_LOGS=0 to show all messages.",
        b"; This message is displayed once. Specify DD_TRACE_ONCE_LOGS=0 to show all messages.",
    ),
]
INVOCATION_URL = re.compile(r"https://[^\s]+/invocation/[0-9a-f-]{36}")
ANALYSIS = re.compile(r"Analyzed .*\((\d+) packages loaded, (\d+) targets configured")


def artifact_path():
    root = Path(os.environ.get("BUILDBUDDY_ARTIFACTS_DIRECTORY", "/tmp"))
    root.mkdir(parents=True, exist_ok=True)
    return root / "full-matrix-incremental-samples.json"


def save(path, results):
    path.write_text(json.dumps({"targets": TARGETS, "samples": results}, indent=2) + "\n")


def run_sample(name, results, report):
    print(f"=== {name}: starting full-matrix build ===", flush=True)
    started = time.monotonic()
    process = subprocess.Popen(
        COMMAND, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, errors="replace", bufsize=1,
    )
    record = {"name": name}
    recent_errors = []
    assert process.stdout is not None
    for raw in process.stdout:
        line = raw.rstrip("\n")
        if any(secret in line.lower() for secret in
               ("api-key", "client-identity", "authorization:")):
            continue
        match = ANALYSIS.search(line)
        if match:
            record["packages_loaded"] = int(match.group(1))
            record["targets_configured"] = int(match.group(2))
        match = INVOCATION_URL.search(line)
        if match:
            record["invocation_url"] = match.group(0)
        if " processes:" in line or " process:" in line:
            record["processes"] = line.strip()
        if line.startswith(("ERROR:", "WARNING:", "FAIL:")):
            recent_errors.append(line)
            recent_errors = recent_errors[-15:]
        if (line.startswith(("ERROR:", "WARNING:")) or
                "Analyzed " in line or "Elapsed time:" in line or
                " processes:" in line or " process:" in line or
                "Build completed" in line or "Streaming build results to:" in line):
            print(line[:500], flush=True)
    record["exit_code"] = process.wait()
    record["elapsed_seconds"] = round(time.monotonic() - started, 3)
    if recent_errors:
        record["recent_errors"] = recent_errors
    results.append(record)
    save(report, results)
    print("=== " + name + ": " + json.dumps(record, sort_keys=True) + " ===", flush=True)
    if record["exit_code"]:
        raise RuntimeError(f"{name} failed with exit code {record['exit_code']}")


def verify_clean(path):
    status = subprocess.run(["git", "diff", "--quiet", "--", str(path)], cwd=ROOT)
    if status.returncode:
        raise RuntimeError(f"Refusing to overwrite modified source: {path}")


def edited_samples(kind, path, before, after, results, report):
    verify_clean(path)
    source = ROOT / path
    original = source.read_bytes()
    if original.count(before) != 1:
        raise RuntimeError(f"Expected one edit location in {path}")
    edited = original.replace(before, after, 1)
    source.write_bytes(edited)
    try:
        for sample in range(1, 4):
            run_sample(f"{kind}-edit-{sample}", results, report)
    finally:
        if source.read_bytes() != edited:
            raise RuntimeError(f"Source changed during measurement: {path}")
        source.write_bytes(original)
    verify_clean(path)
    run_sample(f"{kind}-restore", results, report)


def main():
    os.chdir(ROOT)
    report = artifact_path()
    results = []
    save(report, results)
    print("Full-matrix sample report: " + str(report), flush=True)
    try:
        for kind, path, before, after in EDIT_CASES:
            edited_samples(kind, path, before, after, results, report)
    except Exception as error:
        print(f"Measurement failed: {error}", file=sys.stderr, flush=True)
        raise
    for _, path, _, _ in EDIT_CASES:
        verify_clean(path)


if __name__ == "__main__":
    main()

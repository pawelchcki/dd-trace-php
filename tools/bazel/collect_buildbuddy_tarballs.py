#!/usr/bin/env python3
"""Check the four tracer archives and publish them as BuildBuddy artifacts."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tarfile


ROOT = Path(__file__).resolve().parents[2]
PLATFORMS = (
    ("x86_64", "linux-gnu", 62, 3),
    ("x86_64", "linux-musl", 62, 2),
    ("aarch64", "linux-gnu", 183, 3),
    ("aarch64", "linux-musl", 183, 2),
)


def inspect_archive(path, version, machine, variants_per_api):
    names = set()
    variants = {}
    source_files = 0
    with tarfile.open(path, mode="r|gz") as archive:
        for member in archive:
            raw = member.name
            parts = PurePosixPath(raw).parts
            if raw.startswith("/") or ".." in parts or not parts or parts[0] != "dd-library-php":
                raise ValueError(f"Unsafe archive path: {raw}")
            name = "/".join(parts)
            if name in names:
                raise ValueError(f"Duplicate archive member: {name}")
            names.add(name)
            if member.issym() or member.islnk():
                raise ValueError(f"Archive contains a link: {name}")
            if not member.isfile():
                continue
            if name == "dd-library-php/VERSION":
                actual_version = archive.extractfile(member).read().decode().strip()
                if actual_version != version:
                    raise ValueError(f"Archive version {actual_version!r} differs from {version!r}")
            elif name.startswith("dd-library-php/trace/src/"):
                source_files += 1
            elif name.startswith("dd-library-php/trace/ext/"):
                relative = parts[3:]
                if len(relative) != 2 or not relative[0].isdigit() or not relative[1].startswith("ddtrace") or not relative[1].endswith(".so"):
                    raise ValueError(f"Unexpected extension path: {name}")
                header = archive.extractfile(member).read(20)
                if len(header) != 20 or header[:4] != b"\x7fELF" or header[4] != 2 or int.from_bytes(header[18:20], "little") != machine:
                    raise ValueError(f"Wrong ELF architecture: {name}")
                variants.setdefault(relative[0], set()).add(relative[1])
    if "dd-library-php/VERSION" not in names or source_files < 100:
        raise ValueError("Archive is missing VERSION or the tracer PHP source tree")
    expected_files = {"ddtrace.so", "ddtrace-zts.so"}
    if variants_per_api == 3:
        expected_files.add("ddtrace-debug.so")
    if len(variants) != 11 or any(files != expected_files for files in variants.values()):
        raise ValueError(f"Expected 11 PHP APIs with {variants_per_api} extension variants each; got {variants}")
    return {"php_apis": len(variants), "extensions": sum(map(len, variants.values())), "source_files": source_files}


def main():
    version = (ROOT / "VERSION").read_text().strip()
    if not re.fullmatch(r"[A-Za-z0-9._+-]+", version):
        raise ValueError("Unsafe VERSION for artifact filename")
    artifact_dir = Path(os.environ["BUILDBUDDY_ARTIFACTS_DIRECTORY"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for arch, libc, machine, variants_per_api in PLATFORMS:
        name = f"dd-library-php-tracer-{arch}-{libc}.tar.gz"
        source = ROOT / "bazel-bin" / name
        shape = inspect_archive(source, version, machine, variants_per_api)
        destination = artifact_dir / f"dd-library-php-tracer-{version}-{arch}-{libc}.tar.gz"
        digest = hashlib.sha256()
        with source.open("rb") as from_file, destination.open("wb") as to_file:
            while chunk := from_file.read(1024 * 1024):
                digest.update(chunk)
                to_file.write(chunk)
        record = {"file": destination.name, "sha256": digest.hexdigest(), "bytes": destination.stat().st_size, **shape}
        manifest.append(record)
        print(json.dumps(record, sort_keys=True), flush=True)
    (artifact_dir / "tarballs.json").write_text(json.dumps({"version": version, "tarballs": manifest}, indent=2) + "\n")


if __name__ == "__main__":
    main()

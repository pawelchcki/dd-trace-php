"""Installable tracer-only Linux archives from the canonical release rows."""

load("//bazel/php:product_matrix.bzl", "product_matrix_rows")
load(":bundle.bzl", "deterministic_ssi_bundle", "ssi_payload")

_ARCH_NAMES = {"amd64": "x86_64", "arm64": "aarch64"}
_LIBC_NAMES = {"glibc": "linux-gnu", "musl": "linux-musl"}
_PROFILE_NAMES = {
    "nts": "ddtrace.so",
    "zts": "ddtrace-zts.so",
    "debug": "ddtrace-debug.so",
}

def tracer_installable_packages():
    """Emits four installer-compatible archives containing the release tracer."""
    sources = native.glob(["src/**"], exclude_directories = 1)
    if not sources:
        fail("tracer installable package has no PHP source files")
    common = {}
    for source in sources:
        common[source] = "trace/" + source

    contents = {}
    validations = {}
    required = {}
    counts = {}
    for arch in _ARCH_NAMES:
        for libc in _LIBC_NAMES:
            key = "%s_%s" % (arch, libc)
            contents[key] = dict(common)
            validations[key] = []
            required[key] = ["VERSION", "trace/src"]
            counts[key] = 0

    for row in product_matrix_rows():
        release = row.sdk_family == "release" or (row.sdk_family == "alpine" and not row.shared_build)
        if not release or not row.product_labels["tracer"]:
            continue
        if row.abi_profile not in _PROFILE_NAMES:
            fail("unsupported release tracer profile: %s" % row.name)
        key = "%s_%s" % (row.target_arch, row.target_libc)
        product = row.product_labels["tracer"][0]
        destination = "trace/ext/%s/%s" % (row.php_api, _PROFILE_NAMES[row.abi_profile])
        if destination in required[key]:
            fail("duplicate installable tracer destination: %s" % destination)
        contents[key][product + "_binary"] = destination
        validations[key].append(product + "_check")
        required[key].append(destination)
        counts[key] += 1

    archives = []
    for arch in _ARCH_NAMES:
        for libc in _LIBC_NAMES:
            key = "%s_%s" % (arch, libc)
            expected = 33 if libc == "glibc" else 22
            if counts[key] != expected:
                fail("expected %d release tracer products for %s; got %d" % (expected, key, counts[key]))
            name = "dd-library-php-tracer-%s-%s" % (_ARCH_NAMES[arch], _LIBC_NAMES[libc])
            payload = "_" + name + "_payload"
            ssi_payload(
                name = payload,
                srcs = contents[key],
                required_paths = required[key],
                validation = validations[key],
                version = "//:VERSION",
                version_destination = "VERSION",
                preserve_version = True,
            )
            deterministic_ssi_bundle(
                name = name,
                payload = ":" + payload,
                prefix = "dd-library-php",
            )
            archives.append(":" + name)
    native.filegroup(
        name = "dd_library_php_tracer_tarballs",
        srcs = archives,
    )

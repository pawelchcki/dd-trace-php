# BuildBuddy demo measurements

Measured on 2026-09-24 and 2026-09-25. Each Bazel step duration is reported by
BuildBuddy's child invocation. The workflow duration includes runner scheduling,
checkout, snapshot handling, and cleanup. The release runs cover one product
and do not predict the time to build the complete PHP release matrix.

| Workflow | First Bazel step | Replay | Whole workflow | Evidence |
| --- | ---: | ---: | ---: | --- |
| Warm runner, initial push | 7.584s | 0.245s | 41.565s | [Invocation](https://pawel.buildbuddy.io/invocation/3b51cf18-e490-4bd3-9522-5915972e033e) |
| Warm runner, same commit rerun | 0.258s | 0.120s | 51.673s | [Invocation](https://pawel.buildbuddy.io/invocation/4a7483a0-d0a9-4822-acbf-35994e207280) |
| Warm runner, later push | 0.194s | 0.094s | 5.618s | [Invocation](https://pawel.buildbuddy.io/invocation/3c15e158-5085-4a9c-9abf-0ba4ba61ba73) |
| Forced RBE probe on `linux-amd64-kvm` | 7.675s | 0.169s | 41.709s | [Invocation](https://pawel.buildbuddy.io/invocation/7d151469-4aee-4043-ac16-3900da13ec48) |
| Warm runner, next push | 0.268s | 0.146s | 5.591s | [Invocation](https://pawel.buildbuddy.io/invocation/16cc52a3-4536-401c-8fd4-2dc72ad5d899) |
| RBE probe, next push | 0.192s | 0.093s | 4.655s | [Invocation](https://pawel.buildbuddy.io/invocation/8bb28415-f264-4ca9-9206-dfd899e3471a) |
| PHP 8.5 release tracer, forced first build | 925.861s | 3.291s | 963.845s | [Invocation](https://pawel.buildbuddy.io/invocation/90cf47af-e676-4f36-96a5-fb8fcd7bb0d1) |
| PHP 8.5 release tracer, remote cache warm but runner cold | 296.952s | 2.806s | 332.263s | [Invocation](https://pawel.buildbuddy.io/invocation/a73c88a4-aa87-4146-a119-eaca96211a64) |
| PHP 8.5 release tracer, explicit branch snapshot policy | 240.013s | 2.366s | 271.295s | [Invocation](https://pawel.buildbuddy.io/invocation/178b1c1a-288b-43b2-9c58-89edd673a666) |
| PHP 8.5 release tracer, same-commit API rerun | 220.100s | 1.878s | 250.981s | [Invocation](https://pawel.buildbuddy.io/invocation/1e1f667d-0b6f-46e3-9d57-b11e37288ce5) |
| PHP 8.5 release tracer, newest snapshot read policy | 261.742s | 2.660s | 296.632s | [Invocation](https://pawel.buildbuddy.io/invocation/300a8b2f-0c0a-4f82-bd9a-fea2d984cffb) |
| PHP 8.5 release tracer, newest policy same-commit rerun | 256.627s | 2.998s | 290.931s | [Invocation](https://pawel.buildbuddy.io/invocation/509e0ef8-97fa-4fa9-a0b1-0d5665e34da7) |
| PHP 8.5 release tracer, warm snapshot on next push | 1.341s | 0.757s | 9.214s | [Invocation](https://pawel.buildbuddy.io/invocation/b2356d2a-c3d1-42f6-9f21-385ca085a2e1) |

The forced RBE probe disables action cache reads in its first step and specifies
the custom executor pool. A direct client run of the same target reported one
remote process in 14.180s: [invocation](https://pawel.buildbuddy.io/invocation/c6280902-3e87-4a39-b299-4d4de017bfb9).

The 51.673s same-commit rerun demonstrates the difference between a hot Bazel
server and whole-workflow latency. Its Bazel work totaled 0.378s. The later
5.618s workflow shows that whole-run latency can also reach seconds when a warm
runner is available promptly.

The PHP release variant analyzed 492 packages and 58,169 configured targets,
then executed 1,089 remote processes in its first build. The immediate replay
loaded zero packages and configured zero targets. The first build intentionally
bypassed action cache reads; later runs allow cache reads.

The next workflow started from a fresh checkout and reported 1,089 remote
cache hits, but still spent 296.952s in its first Bazel step. That separates
remote action caching from keeping the Bazel client and repository downloads
warm across workflow invocations. An explicit `first-non-default-ref` branch
snapshot policy also started cold. BuildBuddy's execution metadata says that
run saved both local and remote snapshots, but the same-commit rerun still
started with `git init`, analyzed all 58,169 targets, and took 220.100s for
the first Bazel step. Explicitly requesting the newest snapshot on reads did
not change the result: the first run saved a remote VM snapshot, and the
same-commit rerun used the same snapshot key but started with `git init` and
re-analyzed all 58,169 targets. Both runs reported 1,089 remote cache hits.
The execution metadata for the API rerun has no `lastExecutedTask`, so it did
not resume a VM snapshot. The following push did resume from that API run's
snapshot: its execution metadata names the preceding invocation, the checkout
synced an existing repository, and Bazel loaded and configured zero targets.
This made the full workflow 9.214s. Snapshot reuse can therefore make this
release variant finish in seconds, but the earlier cold reruns show it is not
yet reliable for every invocation. The reason those reruns missed is unknown.

## Full release tracer matrix and installable archives

Measured on 2026-09-26 on fork branch `bazel-buildbuddy-matrix-demo` using the
`linux-amd64-kvm` executor pool. The target set was
`//bazel/products/tracer:ddtrace_fat_all`, `//bazel/php:product_matrix`, the
four `rust_datadog_php_shared_*` targets, and (in the second run)
`//:dd_library_php_tracer_tarballs`. Bazel builds the archives from the release
tracer variants for all four architecture/libc combinations. The archive
collector verifies their layout, version, PHP API coverage, extension names,
and ELF architecture before uploading them.

| Run | First Bazel build | Immediate replay | Whole workflow | Evidence |
| --- | ---: | ---: | ---: | --- |
| Cold baseline, before archive target (`c38a3c06`) | 54m40.193s | 6.456s | 55m19.732s | [Workflow](https://pawel.buildbuddy.io/invocation/a6bc0452-296f-4010-9b98-76213056d6ef) |
| Archives and source edit samples (`54328104`) | 8m04.982s | 8.525s | 26m42.638s | [Workflow and artifacts](https://pawel.buildbuddy.io/invocation/ecb6a7a5-e3f2-4926-b2dc-e60ff17595eb) |

The second run had a warm remote action cache: Bazel reported 23,847 remote
cache hits and eight remote executions in its first build. Its runner still
started a fresh checkout and configured 159,300 targets; the configured
snapshot policy did not resume the previous VM for that invocation. The two
whole-workflow durations therefore include different initial cache states and
the second includes the edit samples. They should not be used as a direct
before/after comparison of archive cost.

The sample script made one C edit to `components/log/log.c` and one Rust edit
to `components-rs/log.rs`. Each row built the complete target set, including
the archive target. The second and third build for each edit used the same
edited source; the restore rows returned the source to its original content.
All eight builds passed and Bazel loaded/configured zero targets in each.

| Sample | First edited build | Second build | Third build | Restore build |
| --- | ---: | ---: | ---: | ---: |
| C | [6m33.355s](https://pawel.buildbuddy.io/invocation/3170cd37-a8ea-459c-b47e-ca80fc8938ac) | [3.371s](https://pawel.buildbuddy.io/invocation/d695e8a7-8b8a-4f28-9bd7-ff960f39c6b3) | [3.209s](https://pawel.buildbuddy.io/invocation/555b7639-478b-431c-a8aa-a903c2ca8f6f) | [2m07.561s](https://pawel.buildbuddy.io/invocation/6a54773e-bc13-46c9-9b96-f41037408209) |
| Rust | [6m30.243s](https://pawel.buildbuddy.io/invocation/43311d7d-dddb-4c93-a895-daa1f726f3d9) | [3.011s](https://pawel.buildbuddy.io/invocation/b5a8f958-0e8e-4b59-a4d8-145fe623cb66) | [2.791s](https://pawel.buildbuddy.io/invocation/5a934983-193f-4aa7-af3d-ec168943b3f0) | [2m21.034s](https://pawel.buildbuddy.io/invocation/eeb144e7-98a0-4abf-9252-864b950803a2) |

The first C edit executed 1,018 remote actions; the first Rust edit executed
622. The restore builds retrieved those affected actions from the remote cache
but still took more than two minutes to materialize and validate the full
target set. The immediate no-change replay was 8.525s, and repeated builds
with the same source edit were 2.791–3.371s.

The successful workflow uploaded these versioned tracer archives and a JSON
manifest as artifacts. Sizes and hashes come from the collector's validation
output. Each glibc archive has 33 PHP extensions; each musl archive has 22.
Each archive has 168 PHP source files and covers 11 PHP APIs.

| Archive | Bytes | SHA-256 |
| --- | ---: | --- |
| `dd-library-php-tracer-1.25.1-x86_64-linux-gnu.tar.gz` | 237,900,877 | `fe55c549d169e4d44cbbf6040bba5b2d0bc732928f9f7efdcbe81f2808ee90fc` |
| `dd-library-php-tracer-1.25.1-x86_64-linux-musl.tar.gz` | 159,170,419 | `6840403e4d02c2a49ea34e7f188a687edc46ec7d80ddf9c699fdac951ac0db10` |
| `dd-library-php-tracer-1.25.1-aarch64-linux-gnu.tar.gz` | 222,113,710 | `414ab093e77b5420da22bb92e2566b9ac93b11fcad99b9d903cd29d7da7f359a` |
| `dd-library-php-tracer-1.25.1-aarch64-linux-musl.tar.gz` | 148,389,435 | `14503869b4fde7a0ddae2c02b6398ef2da05dc1f6b62fce5f940e04da5ac5ce3` |

These archives provide the tracer portion of the installer layout. Profiler
and AppSec payloads are not included, and this run validated archive contents
without executing `datadog-setup.php` against a PHP installation.

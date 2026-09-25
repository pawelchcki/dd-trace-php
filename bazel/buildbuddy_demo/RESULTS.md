# BuildBuddy demo measurements

Measured on 2026-09-24. Each Bazel step duration is reported by BuildBuddy's
child invocation. The workflow duration includes runner scheduling, checkout,
snapshot handling, and cleanup. These probes are small; they do not predict the
time to build the complete PHP release matrix.

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
The execution metadata for the rerun has no `lastExecutedTask`, while the
small demo's warm runs do. This points to a snapshot restore or eligibility
problem for this larger runner, not an action-cache miss. The cause is not yet
known.

# BuildBuddy demo

This small Bazel target exercises BuildBuddy without fetching the PHP release
toolchains. The root `buildbuddy.yaml` also builds the real bootstrap manifest
twice on a BuildBuddy workflow runner. The second command reuses the same Bazel
server for a hot replay. Both commands use the remote action cache and run
cache misses on the workflow runner.

A second workflow action forces this target onto the `linux-amd64-kvm` RBE
executor pool, then measures a hot replay. Its first step bypasses the action
cache so a passing workflow verifies that an executor really ran the action.

A third action builds and checks one actual PHP 8.5 glibc release tracer on the
same RBE pool. This is a representative release product; the complete release
matrix contains many more variants. It requests a branch VM snapshot and the
newest available snapshot on later runs, so the runner can attempt to preserve
the Bazel analysis cache and repository downloads across workflows.

Measured runs and invocation links are in [RESULTS.md](RESULTS.md).

After `bb login`, a local client can test the action cache with:

```sh
bb build //bazel/buildbuddy_demo:hello \
  --remote_executor=grpcs://remote.buildbuddy.io \
  --remote_cache=grpcs://remote.buildbuddy.io \
  --spawn_strategy=local
bb clean
bb build //bazel/buildbuddy_demo:hello \
  --remote_executor=grpcs://remote.buildbuddy.io \
  --remote_cache=grpcs://remote.buildbuddy.io \
  --spawn_strategy=local
```

The clean rebuild should report a remote cache hit. To execute the action on
BuildBuddy, use `--spawn_strategy=remote --remote_local_fallback=false` instead
of `--spawn_strategy=local`, and add these flags to select the custom pool:

```sh
--remote_exec_header=x-buildbuddy-platform.Pool=linux-amd64-kvm
--remote_exec_header=x-buildbuddy-platform.use-self-hosted-executors=true
```

The workflow also requires a workflows runner and the fork to be linked in
BuildBuddy Workflows.
Run `bb clean` first and add `--remote_accept_cached=false` when checking that
an action actually reached an executor; an up-to-date or cached target does not
prove that remote execution is available.

The target is only a connectivity and warm state probe. It does not represent
the cost of the PHP release build.

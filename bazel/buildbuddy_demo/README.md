# BuildBuddy demo

This small Bazel target exercises BuildBuddy without fetching the PHP release
toolchains. The root `buildbuddy.yaml` runs it twice on a BuildBuddy workflow
runner: the first build bypasses the remote action cache to verify execution,
and the second reuses the same Bazel server for a hot replay.

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
of `--spawn_strategy=local`. This requires an available Linux amd64 executor in
the BuildBuddy organization. The workflow also requires a workflows runner and
the fork to be linked in BuildBuddy Workflows.
Run `bb clean` first and add `--remote_accept_cached=false` when checking that
an action actually reached an executor; an up-to-date or cached target does not
prove that remote execution is available.

The target is only a connectivity and warm state probe. It does not represent
the cost of the PHP release build.

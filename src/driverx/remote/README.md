# driverx.remote

## Purpose

Owns provider-neutral remote GPU utility code. The first concrete helper is a
RunPod SSH resolver that converts current pod metadata into the `GPU_SSH_HOST`
and `GPU_SSH_OPTS` shape used by the remote Alpamayo and SimLingo scripts.

## Public API

- `fetch_runpod_pods(api_key, api_url=...)`
- `extract_runpod_pods(payload)`
- `select_runpod_ssh_target(pods, ...)`
- `write_runpod_ssh_resolution(run_dir, target, pods)`

## Example

```bash
PYTHONPATH=src python3 -m driverx resolve-runpod-ssh \
  --env-file .env \
  --ssh-key ~/.ssh/id_ed25519_runpod \
  --run-id runpod-current
```

Then use the emitted `GPU_SSH_HOST` and `GPU_SSH_OPTS` with remote scripts.

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_runpod_remote
```

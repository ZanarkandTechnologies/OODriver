# driverx.remote

Remote GPU and provider-control helpers.

## Rules

- Never print API keys, Hugging Face tokens, private keys, or full `.env`
  contents.
- Treat cloud host coordinates as volatile; prefer resolver artifacts over
  hard-coded SSH ports.
- Keep network calls at CLI/script edges so local tests can use fixture payloads.
- Store heavy remote caches and model downloads on persistent workspace volumes,
  not small container root disks.

# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.9.x   | yes       |
| < 0.9   | no        |

## Reporting a vulnerability

Email `security@ton-gram-labs.dev` with:

- Affected file(s) and version.
- A minimal reproduction (script or command).
- Impact assessment — e.g. remote code execution via a malicious
  `config/sources.yaml`, secret leakage through logs, or SSRF via a
  user-supplied endpoint URL.

We acknowledge within 72 hours and aim to ship a patch within 14 days for
high-severity issues.

## Scope

In scope: the Python package under `src/ton_price_predictor/`, the CLI,
config loading, HTTP client wrappers, and the serialized model artifacts.

Out of scope: third-party data providers, the TON blockchain itself, and
any deployment outside this repository.

## Hardening notes

- Never commit `.env`, API keys, or exchange credentials. `.gitignore`
  blocks them, but double-check `git status` before pushing.
- Config files are parsed with `yaml.safe_load` only. Do not switch to
  `yaml.load`.
- Model artifacts are loaded with `joblib` **without** `pickle` fallbacks
  from untrusted sources. Treat any `.pkl` outside `artifacts/` as hostile.
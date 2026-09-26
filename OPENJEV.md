# OpenJEV support added to fuzzyif

This fork adds optional support for [OpenJEV](https://openjev.sh), a free community
gateway to the same Jev model built by [TypeSafe](https://typesafe.ai).

## What was added

| File | Change |
|---|---|
| `src/fuzzyif/config.py` | Added OpenJEV constants (`OPENJEV_ENV_VAR`, `OPENJEV_BASE_URL`, `OPENJEV_MODEL`, `PROVIDER_ENV_VAR`), `provider` field on `Settings`, and `resolve_provider()` which returns `(base_url, model, api_key)` based on the selection rule below. |
| `src/fuzzyif/client.py` | `JevClient.__init__` now calls `resolve_provider()` instead of hardcoding `settings.base_url`, `settings.model`, and `resolve_api_key()`. The resolved model is stored as `self.model` and used in every request body. |
| `README.md` | OpenJEV note after the intro; provider-selection documentation in the Install and Configuration sections. |

TypeSafe code, defaults, and key resolution are unchanged. No TypeSafe text was
removed or renamed.

## Provider selection rule

1. **Explicit choice wins** — `settings.provider` or the `JEV_PROVIDER` env var:
   `"openjev"` → OpenJEV, `"typesafe"` → TypeSafe.
2. **TypeSafe if its key is available** — if `TYPESAFE_API_KEY` is set or
   `~/.config/typesafe/api_key` exists, TypeSafe is used (unchanged default).
3. **OpenJEV fallback** — if only `OPENJEV_API_KEY` is set, OpenJEV is used.

Anyone with a TypeSafe key sees zero behaviour change.

## Configuration

```python
# Use TypeSafe (default — unchanged):
fuzzyif.configure(api_key="ts_...")           # or set TYPESAFE_API_KEY

# Use OpenJEV:
fuzzyif.configure(api_key="oj_...", provider="openjev")
# or: set OPENJEV_API_KEY and leave TYPESAFE_API_KEY unset
# or: export JEV_PROVIDER=openjev

# TypeSafe is still the default even if both keys are present,
# unless provider="openjev" or JEV_PROVIDER=openjev is set.
```

| Provider | Endpoint | Model | Key env var |
|---|---|---|---|
| TypeSafe (default) | `https://api.typesafe.ai/v1/systemone` | `jev-latest` | `TYPESAFE_API_KEY` |
| OpenJEV | `https://api.openjev.sh/v1/systemone` | `openjev` | `OPENJEV_API_KEY` |

OpenJEV returns HTTP 503 when overloaded (TypeSafe returns 529); both are retried
alongside 429 and other 5xx by the existing retry logic (`status >= 500`).

## Verification

A live request was made to the OpenJEV systemone endpoint with model `openjev`,
state `ping`, and one `noul` question — it returned HTTP 200 with a valid
`answers` block. A `grep` confirmed no hardcoded `api.typesafe.ai` default remains
outside of the TypeSafe-specific constants (which are intentional).

## Upstream

Original project: https://github.com/Tdual/fuzzyif by [@Tdual](https://github.com/Tdual).
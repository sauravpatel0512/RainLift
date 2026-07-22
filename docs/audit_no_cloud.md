# No-cloud audit (local stack)

Repo is intended to run **only** local Docker + public HTTP sources (TLC CDN, Open-Meteo). No cloud deployment wiring is included.

Checks (run from repo root):

```bash
rg -i "aws\\.amazon" .
rg -i "amazonaws|googleapis|azure\\.com|snowflake|databricks" .
```

Latest manual scan in this workspace: **no matches** for `aws.amazon` in tracked content; deployment-related cloud vendor strings are absent from Compose/CI beyond generic S3 API compatibility settings for MinIO.

Public dataset URLs (e.g. `cloudfront.net` TLC Parquet) are **not** AWS accounts or credentials — they are HTTPS downloads only.

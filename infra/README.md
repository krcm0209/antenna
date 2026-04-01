# Infrastructure

Pulumi (Python) project managing GCP resources for Antenna.

## Resources

- **APIs** — Cloud Run, Artifact Registry, IAM, Cloud Resource Manager, IAM Credentials, Cloud Storage
- **Artifact Registry** — Docker repository for container images
- **Cloud Storage** — Bucket for the FCC database (`fcc.db`)
- **Service Account** — `github-actions-deploy`, used by GitHub Actions workflows
- **IAM Bindings** — Cloud Run Admin, Artifact Registry Writer, Service Account User, Storage Object Admin
- **Workload Identity Federation** — OIDC provider for GitHub Actions (no static keys)

## Usage

```sh
cd infra
pulumi up
```

## Stack Outputs

| Output | Used as GitHub secret |
|--------|----------------------|
| `project_id` | `GCP_PROJECT_ID` |
| `wif_provider` | `GCP_WIF_PROVIDER` |
| `service_account_email` | `GCP_SERVICE_ACCOUNT` |
| `fcc_db_bucket` | `GCP_FCC_DB_BUCKET` |
| `artifact_repo_url` | — |

## Configuration

Set in `Pulumi.<stack>.yaml`:

| Key | Description |
|-----|-------------|
| `gcp:project` | GCP project ID |
| `antenna:github_repo` | GitHub repo (e.g. `krcm0209/antenna`) |
| `antenna:region` | GCP region (default: `us-east1`) |

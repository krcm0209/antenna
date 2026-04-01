"""Antenna GCP infrastructure for GitHub Actions CI/CD to Cloud Run."""

import pulumi
import pulumi_gcp as gcp

config = pulumi.Config()
gcp_config = pulumi.Config("gcp")
project = gcp_config.require("project")
region = config.get("region") or "us-east1"
github_repo = config.require("github_repo")

# --- Enable APIs ---

apis = {}
for api in [
    "run.googleapis.com",                   # deploy and manage the API service
    "artifactregistry.googleapis.com",      # store container images
    "iam.googleapis.com",                   # service accounts and role bindings
    "cloudresourcemanager.googleapis.com",  # project-level IAM policy management
    "iamcredentials.googleapis.com",        # WIF token exchange for GitHub Actions
    "storage.googleapis.com",               # GCS bucket for FCC database
]:
    short = api.split(".")[0]
    apis[short] = gcp.projects.Service(
        f"api-{short}",
        service=api,
        disable_on_destroy=False,
        disable_dependent_services=False,
    )


def depends_on_api(*names: str) -> pulumi.ResourceOptions:
    """Ensure the named GCP APIs are enabled before creating a resource."""
    return pulumi.ResourceOptions(depends_on=[apis[n] for n in names])


# --- Artifact Registry ---

repo = gcp.artifactregistry.Repository(
    "repo",
    repository_id="antenna",
    format="DOCKER",
    location=region,
    description="Antenna container images",
    cleanup_policy_dry_run=False,
    cleanup_policies=[
        {
            "id": "keep-latest",
            "action": "KEEP",
            "most_recent_versions": {"keep_count": 1},
        },
        {
            "id": "delete-old",
            "action": "DELETE",
            "condition": {"older_than": "604800s"},  # 7 days
        },
    ],
    opts=depends_on_api("artifactregistry"),
)

# --- Service Account for GitHub Actions ---

deploy_sa = gcp.serviceaccount.Account(
    "deploy-sa",
    account_id="github-actions-deploy",
    display_name="GitHub Actions Deploy",
    description="Used by GitHub Actions to deploy to Cloud Run",
    opts=depends_on_api("iam"),
)

deploy_roles = [
    "roles/run.admin",
    "roles/artifactregistry.writer",
    "roles/iam.serviceAccountUser",
]

for role in deploy_roles:
    short = role.split("/")[1]
    gcp.projects.IAMMember(
        f"deploy-sa-{short}",
        project=project,
        role=role,
        member=deploy_sa.member,
    )

# --- Workload Identity Federation ---

wif_pool = gcp.iam.WorkloadIdentityPool(
    "github-pool",
    workload_identity_pool_id="github",
    display_name="GitHub",
    description="GitHub Actions OIDC",
    opts=depends_on_api("iam", "iamcredentials"),
)

wif_provider = gcp.iam.WorkloadIdentityPoolProvider(
    "github-provider",
    workload_identity_pool_id=wif_pool.workload_identity_pool_id,
    workload_identity_pool_provider_id="github-provider",
    display_name="GitHub Actions",
    attribute_mapping={
        "google.subject": "assertion.sub",
        "attribute.repository": "assertion.repository",
    },
    attribute_condition=f'assertion.repository == "{github_repo}"',
    oidc={"issuer_uri": "https://token.actions.githubusercontent.com"},
)

def _wif_member(pool_name: str) -> str:
    return f"principalSet://iam.googleapis.com/{pool_name}/attribute.repository/{github_repo}"


gcp.serviceaccount.IAMMember(
    "wif-sa-binding",
    service_account_id=deploy_sa.name,
    role="roles/iam.workloadIdentityUser",
    member=wif_pool.name.apply(_wif_member),  # ty: ignore[missing-argument, invalid-argument-type]
)

# --- Cloud Storage (FCC database) ---

fcc_db_bucket = gcp.storage.Bucket(
    "fcc-db-bucket",
    name=f"{project}-fcc-data",
    location=region,
    uniform_bucket_level_access=True,
    force_destroy=True,
    opts=depends_on_api("storage"),
)

gcp.storage.BucketIAMMember(
    "deploy-sa-storage-access",
    bucket=fcc_db_bucket.name,
    role="roles/storage.objectAdmin",
    member=deploy_sa.member,
)

# --- Outputs (values needed as GitHub secrets) ---

pulumi.export("project_id", project)
pulumi.export("wif_provider", wif_provider.name)
pulumi.export("service_account_email", deploy_sa.email)
pulumi.export(
    "artifact_repo_url",
    pulumi.Output.concat(region, "-docker.pkg.dev/", project, "/antenna"),
)
pulumi.export("fcc_db_bucket", fcc_db_bucket.name)

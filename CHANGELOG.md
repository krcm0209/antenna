# Changelog

## [0.4.1](https://github.com/krcm0209/antenna/compare/v0.4.0...v0.4.1) (2026-04-01)


### Bug Fixes

* **dashboard:** use featureGroup for contour layer to support getBounds ([06f421d](https://github.com/krcm0209/antenna/commit/06f421da8ed096e53f108542c72acbdb7c074d58))

## [0.4.0](https://github.com/krcm0209/antenna/compare/v0.3.0...v0.4.0) (2026-04-01)


### Features

* add dashboard SPA and enable IAP on Cloud Run ([29184f7](https://github.com/krcm0209/antenna/commit/29184f7cb6bb8007cc3447f8a2d67cf78273cb39))

## [0.3.0](https://github.com/krcm0209/antenna/compare/v0.2.5...v0.3.0) (2026-04-01)


### Features

* switch production image to distroless cc-debian13 ([f4071d5](https://github.com/krcm0209/antenna/commit/f4071d55a4bd57d593a513d6fb440a8784be06d8))

## [0.2.5](https://github.com/krcm0209/antenna/compare/v0.2.4...v0.2.5) (2026-04-01)


### Bug Fixes

* run fastapi directly instead of via uv run in production image ([3d1e605](https://github.com/krcm0209/antenna/commit/3d1e6058ce041688c2ed6cb31d558eaf7153629e))

## [0.2.4](https://github.com/krcm0209/antenna/compare/v0.2.3...v0.2.4) (2026-04-01)


### Bug Fixes

* use --no-install-workspace for Docker build with uv workspaces ([a26c5f0](https://github.com/krcm0209/antenna/commit/a26c5f04f931912fa28a31c2f5a2c808bc4cd3cd))

## [0.2.3](https://github.com/krcm0209/antenna/compare/v0.2.2...v0.2.3) (2026-04-01)


### Bug Fixes

* use --no-sources in Dockerfile to skip workspace resolution ([e424e4d](https://github.com/krcm0209/antenna/commit/e424e4dccf56f8733b6008ff491152ff33f8620d))

## [0.2.2](https://github.com/krcm0209/antenna/compare/v0.2.1...v0.2.2) (2026-04-01)


### Bug Fixes

* copy README.md into Docker image for uv_build ([1eac2c6](https://github.com/krcm0209/antenna/commit/1eac2c6036a5883f4789142ea954928206e3db09))

## [0.2.1](https://github.com/krcm0209/antenna/compare/v0.2.0...v0.2.1) (2026-04-01)


### Bug Fixes

* split uv sync in Dockerfile to fix build without source tree ([a7c951d](https://github.com/krcm0209/antenna/commit/a7c951d10833b87e0e980e7a5fee4101246c3f13))

## [0.2.0](https://github.com/krcm0209/antenna/compare/v0.1.1...v0.2.0) (2026-04-01)


### Features

* add GCS-backed FCC database sync pipeline ([c3115ac](https://github.com/krcm0209/antenna/commit/c3115ac447cb249591f1bc297928dc59fa4a2c40))


### Bug Fixes

* **ci:** skip AM contour fetch in weekly sync workflow ([7aff7cc](https://github.com/krcm0209/antenna/commit/7aff7cc25bc4d9811a428838e12f4d864cf98cf4))

## [0.1.1](https://github.com/krcm0209/antenna/compare/v0.1.0...v0.1.1) (2026-03-31)


### Bug Fixes

* **ci:** trigger deploy workflow after release-please creates a release ([8c6ec5a](https://github.com/krcm0209/antenna/commit/8c6ec5a07cec7657e4af231ebc5051bd5b708554))

## 0.1.0 (2026-03-31)


### Features

* add GCP infrastructure and GitHub Actions CI/CD pipeline ([cd08bf2](https://github.com/krcm0209/antenna/commit/cd08bf23021d3fefa6119ebab52854c3717c48e3))


### Bug Fixes

* **ci:** use full semver tag for setup-uv action ([7bfbbb1](https://github.com/krcm0209/antenna/commit/7bfbbb157c9a6c79110ba8a314fafe8d4211fc57))

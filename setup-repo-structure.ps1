# setup-repo-structure.ps1
# Creates the initial folder structure for Nebula Insurance Data Contracts.
# Goal: start with Property & Casualty, while leaving room for Life, Health, and other insurance domains later.

$ErrorActionPreference = "Stop"

Write-Host "Creating Nebula Insurance Data Contracts folder structure..." -ForegroundColor Cyan

# Folders to create
$folders = @(
    # Core reference structure
    "references",
    "references/odcs",
    "references/odcs/pc",
    "references/odcs/pc/core",
    "references/odcs/pc/coverage",
    "references/odcs/pc/exposure",
    "references/odcs/pc/claims",
    "references/odcs/pc/financial",
    "references/odcs/pc/reference-data",

    # Future domain placeholders
    "references/odcs/life",
    "references/odcs/health",
    "references/odcs/annuity",
    "references/odcs/reinsurance",
    "references/odcs/shared",

    # Glossary and design guidance
    "references/glossary",
    "references/glossary/pc",
    "references/design-decisions",
    "references/design-decisions/pc",
    "references/patterns",
    "references/patterns/pc",

    # Target platform guidance
    "targets",
    "targets/fabric",
    "targets/databricks",
    "targets/snowflake",
    "targets/dbt",
    "targets/kafka",
    "targets/api",

    # Scripts and validation
    "scripts",
    "scripts/validation",
    "scripts/generation",

    # Docs
    "docs",
    "docs/examples",
    "docs/roadmap",

    # Private local-only workspace
    "_private-research",
    "_private-research/source-review",
    "_private-research/scratch",
    "_private-research/extraction"
)

foreach ($folder in $folders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
        Write-Host "Created: $folder"
    }
    else {
        Write-Host "Exists:  $folder" -ForegroundColor DarkGray
    }
}

# Add .gitkeep to empty folders except private research folders
foreach ($folder in $folders) {
    if ($folder -notlike "_private-research*") {
        $gitkeepPath = Join-Path $folder ".gitkeep"
        if (-not (Test-Path $gitkeepPath)) {
            New-Item -ItemType File -Path $gitkeepPath | Out-Null
        }
    }
}

# Root .gitignore
$gitignore = @"
# Operating system files
.DS_Store
Thumbs.db
desktop.ini

# Editor files
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# Python artifacts
__pycache__/
*.pyc
.venv/
venv/
.env

# Node artifacts
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build/output artifacts
dist/
build/
out/
tmp/
temp/

# Local/private research material
# Keep external source analysis, scratch mappings, downloaded standards,
# DDLs, OWLs, PDFs, generated extractions, and comparison work out of the repo.
_private-research/
_external-sources/
_source-review/
_research/
_scratch/

# Source/reference artifacts that should not be committed
*.erwin
*.xmi
*.ddl
*.owl

# Large/generated data
*.parquet
*.delta
*.csv
*.xlsx
*.db
*.sqlite
*.bak

# Secrets
*.pem
*.key
*.pfx
*.p12
.env.*
!.env.example
"@

Set-Content -Path ".gitignore" -Value $gitignore -Encoding UTF8
Write-Host "Created/updated: .gitignore" -ForegroundColor Green

# Private research local gitignore, in case folder exists locally
$privateGitignore = @"
# Everything under _private-research is local-only.
*
!.gitignore
"@

Set-Content -Path "_private-research/.gitignore" -Value $privateGitignore -Encoding UTF8
Write-Host "Created/updated: _private-research/.gitignore" -ForegroundColor Green

# Optional README files for important folders
$readmes = @{
    "references/odcs/README.md" = @"
# ODCS Contracts

Canonical insurance data contracts authored in ODCS v3 YAML.

The initial domain package is Property & Casualty under `pc/`.
Future domains may include Life, Health, Annuity, Reinsurance, and shared cross-domain contracts.
"@

    "references/odcs/pc/README.md" = @"
# Property & Casualty Contracts

Canonical Property & Casualty insurance data contracts.

Suggested first contract areas:

- Party and roles
- Policy and policy term
- Product and coverage
- Insurable object
- Exposure
- Claims
- Financial transactions
- Reference data
"@

    "references/glossary/README.md" = @"
# Glossary

Canonical business terms used by the insurance data contracts.

Definitions should be written in original language for this repository and should avoid copying external reference text verbatim.
"@

    "references/design-decisions/README.md" = @"
# Design Decisions

Records of canonical modeling choices.

Use this area to explain why entity boundaries, naming conventions, exposure modeling, financial modeling, role modeling, and lifecycle event modeling were chosen.
"@

    "references/patterns/README.md" = @"
# Patterns

Reusable modeling patterns for canonical insurance data contracts.

Examples:

- Party-role pattern
- Policy-coverage pattern
- Exposure pattern
- Financial transaction pattern
- Event/lifecycle pattern
"@

    "targets/README.md" = @"
# Targets

Platform-specific implementation guidance.

The core contracts are platform-neutral by default. Target folders may describe how to implement or generate artifacts for Fabric, Databricks, Snowflake, dbt, Kafka, APIs, or other platforms.
"@

    "scripts/README.md" = @"
# Scripts

Automation scripts for validating, generating, or inspecting contracts.

Scripts should support the canonical contracts without making the contracts platform-specific.
"@

    "docs/README.md" = @"
# Documentation

Project documentation, examples, roadmap notes, and usage guidance.
"@
}

foreach ($path in $readmes.Keys) {
    if (-not (Test-Path $path)) {
        Set-Content -Path $path -Value $readmes[$path] -Encoding UTF8
        Write-Host "Created: $path" -ForegroundColor Green
    }
    else {
        Write-Host "Exists:  $path" -ForegroundColor DarkGray
    }
}

# Optional starter contract placeholder files
$starterFiles = @{
    "references/odcs/pc/core/party.odcs.yaml" = @"
# Placeholder for Party canonical data contract.
"@

    "references/odcs/pc/core/policy.odcs.yaml" = @"
# Placeholder for Policy canonical data contract.
"@

    "references/odcs/pc/coverage/policy-coverage.odcs.yaml" = @"
# Placeholder for Policy Coverage canonical data contract.
"@

    "references/odcs/pc/exposure/exposure.odcs.yaml" = @"
# Placeholder for base Exposure canonical data contract.
"@

    "references/odcs/pc/exposure/vehicle-exposure.odcs.yaml" = @"
# Placeholder for Vehicle Exposure canonical data contract.
"@

    "references/odcs/pc/exposure/property-exposure.odcs.yaml" = @"
# Placeholder for Property Exposure canonical data contract.
"@

    "references/odcs/pc/exposure/workers-comp-exposure.odcs.yaml" = @"
# Placeholder for Workers Comp Exposure canonical data contract.
"@

    "references/odcs/pc/claims/claim.odcs.yaml" = @"
# Placeholder for Claim canonical data contract.
"@

    "references/odcs/pc/financial/financial-transaction.odcs.yaml" = @"
# Placeholder for Financial Transaction canonical data contract.
"@
}

foreach ($path in $starterFiles.Keys) {
    if (-not (Test-Path $path)) {
        Set-Content -Path $path -Value $starterFiles[$path] -Encoding UTF8
        Write-Host "Created: $path" -ForegroundColor Green
    }
    else {
        Write-Host "Exists:  $path" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "Done. Suggested next commands:" -ForegroundColor Cyan
Write-Host "  git status"
Write-Host "  git add ."
Write-Host "  git commit -m `"Initialize canonical insurance data contract structure`""
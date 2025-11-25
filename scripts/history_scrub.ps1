<#
Purpose: Assist with repository history scrub for secrets on Windows PowerShell 5.1.

Instructions:
1. Install git-filter-repo (recommended)
   pip install git-filter-repo

2. Mirror backup BEFORE scrubbing:
   git clone --mirror . ..\kings-theorem-mirror.git

3. Run scrubs (examples below modify history IRREVERSIBLY):

   # Remove keys/ directory and .env files from entire history
   git filter-repo --path keys/ --invert-paths
   git filter-repo --path-glob "**/.env" --invert-paths

   # Remove PEM/KEY files by extension
   git filter-repo --invert-paths --path-glob "**/*.pem" --path-glob "**/*.key"

4. Force-push protected branches (coordinate with team!)
   git push --force --all; git push --force --tags

5. Rotate credentials IMMEDIATELY after scrub.

Note: Coordinate with all collaborators to re-clone after history rewrite.
#>

Write-Host "History scrub helper loaded. Read the comments in this script for steps." -ForegroundColor Yellow

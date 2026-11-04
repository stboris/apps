#!/usr/bin/env bash
# Deploy the static site to cyon via rsync over SSH (https://apps.borisstiner.com).
# Same host as eracunpro.com; only the webroot differs.
set -euo pipefail

SSH_TARGET="jupubozi@s133.cyon.net"
REMOTE_ROOT="/home/jupubozi/public_html/apps.borisstiner.com"

cd "$(dirname "$0")"

# index.src.html (bilingual source) -> index.html (en) + de/index.html; both are committed for GitHub Pages.
python3 tools/bilingual.py index.src.html . https://apps.borisstiner.com/ en

rsync -avz --delete --exclude .git --exclude .nojekyll --exclude deploy.sh --exclude index.src.html --exclude tools \
    ./ "$SSH_TARGET:$REMOTE_ROOT/"

# The webroot must stay readable for the web server, whatever mode the local folder has
# (macOS rsync has no --chmod).
ssh "$SSH_TARGET" "chmod 755 $REMOTE_ROOT && find $REMOTE_ROOT -mindepth 1 -type d -exec chmod 755 {} + && find $REMOTE_ROOT -type f -exec chmod 644 {} +"

echo "Deployed to https://apps.borisstiner.com"

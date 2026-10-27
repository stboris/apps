#!/usr/bin/env bash
# Deploy the static site to cyon via rsync over SSH (https://apps.borisstiner.com).
# Same host as eracunpro.com; only the webroot differs.
set -euo pipefail

SSH_TARGET="jupubozi@s133.cyon.net"
REMOTE_ROOT="/home/jupubozi/public_html/apps.borisstiner.com"

cd "$(dirname "$0")"

rsync -avz --delete --exclude .git --exclude .nojekyll --exclude deploy.sh \
    ./ "$SSH_TARGET:$REMOTE_ROOT/"

# The webroot must stay readable for the web server, whatever mode the local folder has
# (macOS rsync has no --chmod).
ssh "$SSH_TARGET" "chmod 755 $REMOTE_ROOT && find $REMOTE_ROOT -mindepth 1 -type d -exec chmod 755 {} + && find $REMOTE_ROOT -type f -exec chmod 644 {} +"

echo "Deployed to https://apps.borisstiner.com"

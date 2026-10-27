#!/usr/bin/env bash
# Deploy the static site to cyon via rsync over SSH (https://apps.borisstiner.com).
# Same host as eracunpro.com; only the webroot differs.
set -euo pipefail

SSH_TARGET="jupubozi@s133.cyon.net"
REMOTE_ROOT="/home/jupubozi/public_html/apps.borisstiner.com"

cd "$(dirname "$0")"

rsync -avz --delete --exclude .git --exclude .nojekyll --exclude deploy.sh \
    ./ "$SSH_TARGET:$REMOTE_ROOT/"

echo "Deployed to https://apps.borisstiner.com"

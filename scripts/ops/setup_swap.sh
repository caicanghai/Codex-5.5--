#!/usr/bin/env bash
# Create a 2GB swapfile if the box has little RAM and no swap (2GB VPS safety).
set -euo pipefail

if [ "$(swapon --show | wc -l)" -gt 0 ]; then
  echo "Swap already present:"
  swapon --show
  exit 0
fi

SWAPFILE="/swapfile"
echo "No swap found — creating 2GB ${SWAPFILE} ..."
sudo fallocate -l 2G "$SWAPFILE" || sudo dd if=/dev/zero of="$SWAPFILE" bs=1M count=2048
sudo chmod 600 "$SWAPFILE"
sudo mkswap "$SWAPFILE"
sudo swapon "$SWAPFILE"
if ! grep -q "$SWAPFILE" /etc/fstab; then
  echo "$SWAPFILE none swap sw 0 0" | sudo tee -a /etc/fstab >/dev/null
fi
echo "Swap enabled:"
swapon --show

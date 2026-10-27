#!/usr/bin/env bash
# Run as root once after `wsl --import Ubuntu-24.04 D:\WSL\Ubuntu-24.04 ...`
#   wsl -d Ubuntu-24.04 -u root bash /mnt/d/paper/TAIMMA_2027/AnytimeSwarm_Journal/setup/01_create_user.sh
# Creates the Linux user, makes it the default login and keeps Windows PATH out of builds.
set -euo pipefail
USER_NAME=${1:-highp}

if ! id "$USER_NAME" >/dev/null 2>&1; then
  useradd -m -s /bin/bash -G sudo "$USER_NAME"
  passwd -d "$USER_NAME"            # no password yet; set one later with `passwd`
fi
# Unattended installs (PX4 ubuntu.sh calls sudo). Remove this file to require a password again.
echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-$USER_NAME
chmod 440 /etc/sudoers.d/90-$USER_NAME

cat > /etc/wsl.conf <<EOF
[user]
default=$USER_NAME

[interop]
appendWindowsPath=false

[boot]
systemd=false
EOF
echo "user $USER_NAME ready; run 'wsl --terminate Ubuntu-24.04' to apply wsl.conf"

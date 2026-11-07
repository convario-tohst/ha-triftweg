#!/bin/bash
# Sichert /config nach GitHub (aufgerufen von packages/git_backup.yaml)
cd /config || exit 1
export GIT_SSH_COMMAND="ssh -i /config/.ssh/id_ed25519 -o UserKnownHostsFile=/config/.ssh/known_hosts -o StrictHostKeyChecking=accept-new"
git add -A
git diff --cached --quiet && exit 0
git -c user.name="Home Assistant Triftweg" -c user.email="ha@triftweg.local" \
    commit -q -m "${1:-Auto-Backup} $(date '+%Y-%m-%d %H:%M')"
git push -q origin main

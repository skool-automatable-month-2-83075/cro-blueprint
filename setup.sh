#!/usr/bin/env bash
# Run once, right after cloning. Copies the starters into your working files.
#
# Why this exists: everything this creates is gitignored, so it is YOURS. When
# an update ships you run `git pull` and it lands cleanly, because your work and
# the repo's work never touch the same files.
set -e
[ -d website ]  || { cp -R website-starter website; echo "created website/ from the starter"; }
[ -d starters ] && [ -n "$(find starters -type f -print -quit)" ] || {
  echo "ERROR: starters/ is missing or empty. Your copy of the repo is incomplete."
  echo "Re-clone the repo, then run ./setup.sh again."
  exit 1
}
for f in $(cd starters && find . -type f | sed 's|^\./||'); do
  [ -f "$f" ] || { mkdir -p "$(dirname "$f")"; cp "starters/$f" "$f"; echo "created $f"; }
done
[ -f .env ] || { cp .env.example .env; echo "created .env"; }
echo
echo "Done. website/ and context/ are yours now - git will not touch them."
echo "Next: /audit <the link to your page>"

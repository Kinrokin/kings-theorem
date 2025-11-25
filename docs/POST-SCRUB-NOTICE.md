# Post-Rewrite Notice (History Scrub)

On 2025-11-24 we rewrote git history to remove sensitive files (e.g., `.env`, private keys, `*_priv.pem`, `*.key`, Docker model blobs).

What this means for collaborators:
- You must re-sync your local clone since commit hashes changed.

Safe re-clone (recommended):
```
git clone https://github.com/Kinrokin/kings-theorem.git
cd kings-theorem
git checkout kt/harden-api-v1
```

Hard reset (advanced, destructive):
```
git fetch --all --prune
git checkout kt/harden-api-v1
git reset --hard origin/kt/harden-api-v1
```

Branch protection & CI:
- Branch protection should be revalidated after the rewrite.
- CI is intact; nightly red-team remains scheduled.

Contact: see `SECURITY.md` for security contact and incident procedures.

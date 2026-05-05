# Releasing LaMetric Rotator

The release procedure mirrors the other PowerPilz-family integrations (Companion, Demo): work on `main`, fast-forward into `release` to publish.

## TL;DR

```bash
# 1. Work on main — code, test, commit
git checkout main
# ... normal dev ...

# 2. Bump the version in manifest.json
#    "version": "X.Y.Z"
# Commit the bump (subject: "release: bump version to X.Y.Z").

# 3. Push main
git push origin main

# 4. Fast-forward merge main to release — this triggers the release
git checkout release
git pull --ff-only           # guard: release shouldn't be ahead remotely
git merge main --ff-only
git push origin release
git checkout main
```

The **Release** GitHub Action then:

1. Reads the version from `custom_components/lametric_rotator/manifest.json`
2. Refuses to proceed if the tag `vX.Y.Z` already exists (bump first)
3. Zips the `custom_components/lametric_rotator/` subtree
4. Creates the GitHub Release `vX.Y.Z` with auto-generated notes and `lametric_rotator.zip` attached

HACS users pick the new release up automatically.

## Golden rules

1. **Never commit directly to `release`.** Always work on `main`, then fast-forward merge.
2. **Bump `manifest.json` in the same commit you finalize a release.** The Release workflow derives the tag from it.
3. **Always fast-forward `main → release` (`git merge main --ff-only`).** If a fast-forward isn't possible, `release` has diverged — investigate before continuing.

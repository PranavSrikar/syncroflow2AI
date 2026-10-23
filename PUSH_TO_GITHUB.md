# Publish the preserved project to GitHub

Prepared after the indefinite-pause handoff. No GitHub remote/authentication was available at preparation time. Do not interpret these instructions or a local checkpoint as a completed push.

## Source and history

Use an existing repository you own or create an empty **private** repository on GitHub, without adding a README/license/gitignore there. The project already has history. Choose the repository URL explicitly; do not guess an account or overwrite an unrelated project. Authentication happens through Git's browser credential flow or GitHub CLI; never paste an access token into chat or commit it.

From this project root, substitute the actual URL:

```powershell
git remote -v
# Only when origin does not already exist:
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin phase6b-ux-refinement
git push origin --all
git push origin --tags
git ls-remote --heads --tags origin
```

No force push is needed. If an existing remote has conflicting history, fetch and inspect before proceeding. In GitHub repository settings, choose **phase6b-ux-refinement** as the default branch: local `master` is an older Phase 4 checkpoint. Alternatively create a current main branch deliberately, preserving historical refs.

If Git is not on PATH in the current shell, replace `git` with `& 'C:/Program Files/Git/cmd/git.exe'`. Windows Git Credential Manager may open a browser at push time. If authentication is unavailable, complete it in an interactive local terminal and retry.

## Reproducibility assets

Source Git excludes venv/node_modules, credentials, caches and `.checkpoints`. Camera video/weights, raw research checkpoints and complete screenshots must be transferred separately. `ARTIFACT_MANIFEST.json` lists archive names, lengths and SHA-256 values. The current pause recovery pointer adds the final documentation source/history archives.

For a private GitHub repository, attach the verified archives to a release associated with the pause checkpoint. If GitHub CLI is installed/authenticated, an example is:

```powershell
gh auth status
gh release create project-pause-handoff --repo YOUR_ACCOUNT/YOUR_REPOSITORY --verify-tag --title 'Project pause handoff' --notes 'Read README.md and PROJECT_HANDOFF.md. Optional research/perception assets are separate; MAPPO remains unqualified.'
gh release upload project-pause-handoff --repo YOUR_ACCOUNT/YOUR_REPOSITORY .checkpoints/phase5-artifacts-20261023T031002271576Z.zip .checkpoints/phase6b-evidence.zip
```

Also upload the latest source ZIP, Git bundle and pause recovery manifest named in `.checkpoints/PAUSE_RECOVERY.json`. Use the exact generated paths, not a wildcard that might include unrelated files. Verify remote file sizes/hashes after downloading to a separate location. For a public repository, establish redistribution rights for third-party video/model assets before publishing them; use private archival storage if needed.

A successful code push alone does not prove these assets were uploaded. Check remote branch/tag commit IDs, release contents and hashes. Record the final repository URL and transfer status in the handoff once verified. Keep the separate local recovery copies until off-device restoration has been tested.

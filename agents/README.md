# Keeping agent guides in sync

Every FIDES repository needs the rules in its `AGENTS.md`, because agents read
that file first and do not reliably follow links. Copying the rules by hand
means every repository drifts. Instead, each repository holds a **managed
block** that a scheduled workflow keeps in step with a FIDES release, through
a pull request a person reviews.

- `fides-rules.md`: the shared rules, the only text inside the block.
- `sync_agents.py`: replaces the block in a guide with a release's rules.
- `../.github/workflows/sync-agents.yml`: the reusable workflow that runs the
  script and opens the pull request.

## Why a pull request, not a live link

- **Pinned.** A rule change reaches a repository only when someone merges it,
  so the rules never get ahead of that repository's checker.
- **Reviewed.** The change arrives as a diff with the release notes linked.
- **Safe.** Agents never fetch instructions from the network, so a
  compromised upstream cannot instruct every agent at once.

## Adopt it in a repository

1. Put the markers in `AGENTS.md` where the rules belong. Everything outside
   them stays yours: where code goes, the check command, the framework's
   mapping, and any stricter rules.

   ```markdown
   <!-- FIDES:BEGIN -->
   <!-- FIDES:END -->
   ```

2. Add `.github/workflows/fides-sync.yml`:

   ```yaml
   name: FIDES rules sync
   on:
     schedule:
       - cron: '23 13 * * 1'
     workflow_dispatch:
   jobs:
     sync:
       permissions:
         contents: write
         pull-requests: write
       uses: Subschema-LLC/FIDES-Software-Architecture/.github/workflows/sync-agents.yml@v0.4
       # with:
       #   base: development   # if pull requests target a branch other than the default
       #   version: v0.4       # to hold at a release instead of following the latest
   ```

3. In the repository's settings, under Actions, allow GitHub Actions to create
   pull requests.
4. Run the workflow once by hand to fill the block.

## Things to know

- A schedule only runs from the default branch, so the caller workflow must
  be merged there.
- Pull requests opened with the workflow's token do not start other
  workflows. Close and reopen the pull request, or push to it, to run CI.
- Pin the reusable workflow to a release tag, as above. Dependabot's
  `github-actions` updates then propose new tags like any other action.
- A repository's own rules outside the block win where they differ: its
  checker enforces them. When a release changes a rule, update the checker
  and those rules in the same pull request as the sync.

Run the script's tests with `python3 -m unittest discover agents`.

# Coding Agent Instructions

## What This Is

`ryl-action` is the GitHub Action for [ryl](https://github.com/owenlamont/ryl), a
fast YAML linter and formatter. It is a composite action: it downloads the ryl
release binary for the runner, verifies it against the release's `SHA256SUMS`, and
runs ryl with the `args` input. The repo holds only this one action, as GitHub
Marketplace requires.

## Project Structure

- **`action.yml`** - inputs, outputs and the single composite step.
- **`scripts/ryl-action.sh`** - install and run logic. It runs under macOS's
  bash 3.2, so avoid bash 4 builtins (`mapfile`, `${var,,}`, associative arrays).
- **`mirror.py`** - pins `action.yml`'s `version` default and the README's
  `ryl-action@vX.Y.Z` references to each new ryl release, then commits and tags
  `vX.Y.Z` to match. Run with `uv run --script mirror.py`.
- **`.github/workflows/mirror.yml`** - runs `mirror.py` every 4 hours, on manual
  dispatch, and on a `ryl_release` repository dispatch from ryl's release workflow.
- **`.github/workflows/ci.yml`** - runs the action from the checkout (`uses: ./`)
  on Linux, macOS and Windows against `tests/fixture.yaml`.

## Coding Standards

- Before a non-trivial behaviour change or a new input, propose a short plan and
  agree the approach with the maintainer first.
- Keep the action thin: behaviour belongs in ryl, not in this wrapper.
- Keep code succinct, and comment only the non-obvious *why*.
- Never `eval` the `args` input: a workflow may build it from untrusted text.
- Verify ryl behaviour with the ryl CLI rather than memory.

## Code Change Requirements

- `prek run --all-files` must pass. prek does not scan new files until they are
  `git add`ed.
- CI is the test suite: a behaviour change needs a step in `ci.yml` that would fail
  without it.
- Update the README for any user-facing change.

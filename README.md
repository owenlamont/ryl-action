# ryl-action

A GitHub Action for [ryl](https://github.com/owenlamont/ryl), the fast YAML
linter and formatter. It downloads the ryl release binary for the runner, checks
it against the release's `SHA256SUMS`, and runs it. Linux, macOS (Apple silicon)
and Windows runners are supported, on x64 and ARM64 where ryl publishes a binary.

## Usage

```yaml
- uses: actions/checkout@v7
- uses: owenlamont/ryl-action@v0.26.1
```

The default runs `ryl check .`. ryl enables no rules without a config, so commit
a `.ryl.toml`: copy a preset from the
[configuration presets](https://ryl-docs.pages.dev/config-presets/). Problems
appear as annotations on the pull request, since ryl switches to GitHub output
under Actions.

Each action tag matches a ryl release and installs that release by default.

## Inputs

| Input | Default | Description |
| --- | --- | --- |
| `version` | the tag's ryl release | ryl release to install, as `X.Y.Z` |
| `args` | `check .` | Arguments for ryl, split like a shell command line |
| `install-only` | `false` | Install ryl onto `PATH` without running it |

## Outputs

| Output | Description |
| --- | --- |
| `ryl-version` | Version of the installed ryl |
| `ryl-path` | Absolute path to the installed ryl executable |

## Examples

Quoted values in `args` stay whole, so an inline config works as on the command
line:

```yaml
- uses: owenlamont/ryl-action@v0.26.1
  with:
    args: >-
      check -d '{extends: default, rules: {line-length: disable, truthy: disable},
      ignore: [pnpm-lock.yaml]}' .
```

That yamllint-style YAML config is deprecated in ryl. The TOML equivalent is the
`default` preset in a `.ryl.toml`, with these changes:

```toml
exclude = "pnpm-lock.yaml"

[lint.rules]
line-length = "disable"
truthy = "disable"
```

Inline TOML can span lines inside the quotes:

```yaml
- uses: owenlamont/ryl-action@v0.26.1
  with:
    args: |
      check -d '
      exclude = "pnpm-lock.yaml"
      [lint.rules]
      key-duplicates = "enable"
      truthy = "enable"
      ' .
```

Check formatting as well as lint:

```yaml
- uses: owenlamont/ryl-action@v0.26.1
- uses: owenlamont/ryl-action@v0.26.1
  with:
    args: format --check .
```

Install ryl for later steps:

```yaml
- uses: owenlamont/ryl-action@v0.26.1
  with:
    install-only: true
- run: ryl check --strict config/
```

## License

MIT (see [LICENSE](LICENSE))

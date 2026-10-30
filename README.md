# ryl-action

A GitHub Action for [ryl](https://github.com/owenlamont/ryl), the fast YAML
linter and formatter. It downloads the ryl release binary for the runner, checks
it against the release's `SHA256SUMS`, and runs it. Linux, macOS (Apple silicon)
and Windows runners are supported, on x64 and ARM64 where ryl publishes a binary.
It runs in bash, which GitHub-hosted runners have (Windows through Git for
Windows), so a self-hosted Windows runner needs Git for Windows installed.

## Usage

```yaml
- uses: actions/checkout@v7
- uses: owenlamont/ryl-action@v0.27.0
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
| `args` | `check .` | Arguments for ryl, split on whitespace across lines |
| `config` | | Path to a config file, passed as `-c` |
| `config-data` | | Inline config, passed whole as `-d` |
| `install-only` | `false` | Install ryl onto `PATH` without running it |

## Outputs

| Output | Description |
| --- | --- |
| `ryl-version` | Version of the installed ryl |
| `ryl-path` | Absolute path to the installed ryl executable |

## Examples

`args` is split on whitespace without quote handling, so pass an inline config
through `config-data`, which reaches ryl whole:

```yaml
- uses: owenlamont/ryl-action@v0.27.0
  with:
    config-data: >-
      {extends: default, rules: {line-length: disable, truthy: disable},
      ignore: [pnpm-lock.yaml]}
```

That yamllint-style YAML config is deprecated in ryl. The TOML equivalent is the
`default` preset in a `.ryl.toml`, with these changes:

```toml
exclude = "pnpm-lock.yaml"

[lint.rules]
line-length = "disable"
truthy = "disable"
```

Inline TOML can span lines:

```yaml
- uses: owenlamont/ryl-action@v0.27.0
  with:
    config-data: |
      exclude = "pnpm-lock.yaml"
      [lint.rules]
      key-duplicates = "enable"
      truthy = "enable"
```

Check formatting as well as lint:

```yaml
- uses: owenlamont/ryl-action@v0.27.0
- uses: owenlamont/ryl-action@v0.27.0
  with:
    args: format --check .
```

Install ryl for later steps:

```yaml
- uses: owenlamont/ryl-action@v0.27.0
  with:
    install-only: true
- run: ryl check --strict config/
```

## License

MIT (see [LICENSE](LICENSE))

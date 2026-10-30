#!/usr/bin/env bash
# Portable to bash 3.2 (macOS's /bin/bash): no mapfile or ${var,,}.

set -euo pipefail

version="${GHA_RYL_VERSION#v}"
install_only="${GHA_RYL_INSTALL_ONLY}"

if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "::error::Invalid version: '${GHA_RYL_VERSION}' (expected X.Y.Z, e.g. 0.26.1)"
    exit 1
fi
if [ "$install_only" != "true" ] && [ "$install_only" != "false" ]; then
    echo "::error::Invalid install-only value: '$install_only' (must be 'true' or 'false')"
    exit 1
fi

ryl_args=()
if [ "$install_only" = "false" ]; then
    # Folds lines so a multi-line args block passes every line, not only the first.
    read -ra ryl_args <<<"$(printf '%s' "$GHA_RYL_ARGS" | tr '\r\n' '  ')"
    if [ ${#ryl_args[@]} -eq 0 ]; then
        echo "::error::args is empty; pass a ryl command such as 'check .', or set install-only"
        exit 1
    fi
    if [ -n "$GHA_RYL_CONFIG" ]; then
        ryl_args+=(-c "$GHA_RYL_CONFIG")
    fi
    if [ -n "$GHA_RYL_CONFIG_DATA" ]; then
        ryl_args+=(-d "$GHA_RYL_CONFIG_DATA")
    fi
fi

case "${RUNNER_OS:-}-${RUNNER_ARCH:-}" in
Linux-X64) asset="ryl-x86_64-unknown-linux-musl.tar.gz" ;;
Linux-ARM64) asset="ryl-aarch64-unknown-linux-musl.tar.gz" ;;
macOS-ARM64) asset="ryl-aarch64-apple-darwin.tar.gz" ;;
Windows-X64) asset="ryl-x86_64-pc-windows-msvc.zip" ;;
Windows-ARM64) asset="ryl-aarch64-pc-windows-msvc.zip" ;;
*)
    echo "::error::ryl publishes no binary for RUNNER_OS='${RUNNER_OS:-}' RUNNER_ARCH='${RUNNER_ARCH:-}'"
    exit 1
    ;;
esac
bin_name="ryl"
if [ "${RUNNER_OS}" = "Windows" ]; then
    bin_name="ryl.exe"
fi

base_url="https://github.com/owenlamont/ryl/releases/download/v${version}"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

download() {
    curl --fail --silent --show-error --location --retry 3 --output "$2" "$1"
}

echo "Downloading ryl ${version}: ${base_url}/${asset}"
download "${base_url}/${asset}" "${workdir}/${asset}"
download "${base_url}/SHA256SUMS" "${workdir}/SHA256SUMS"

# Matches the file name exactly: a substring match would let the -gnu and -musl
# archives of one arch stand in for each other.
expected="$(tr -d '\r' <"${workdir}/SHA256SUMS" | awk -v name="$asset" '$2 == name || $2 == "*" name { print $1 }')"
if [ -z "$expected" ]; then
    echo "::error::SHA256SUMS for ryl ${version} does not list ${asset}"
    exit 1
fi
if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "${workdir}/${asset}" | awk '{ print $1 }')"
else
    actual="$(shasum -a 256 "${workdir}/${asset}" | awk '{ print $1 }')"
fi
if [ "$expected" != "$actual" ]; then
    echo "::error::Checksum mismatch for ${asset}: expected ${expected}, got ${actual}"
    exit 1
fi
echo "Verified ${asset} against SHA256SUMS"

# RUNNER_TEMP is a native path on Windows (D:\a\_temp), which pwsh and cmd can
# resolve once it is on PATH; an MSYS path from mktemp would not be.
bin_dir="${RUNNER_TEMP}/ryl-bin"
mkdir -p "$bin_dir"
if [ "${asset##*.}" = "zip" ]; then
    # Git Bash's GNU tar cannot read zip; Windows' own bsdtar can.
    /c/Windows/System32/tar.exe -xf "${workdir}/${asset}" -C "$workdir"
else
    tar -xzf "${workdir}/${asset}" -C "$workdir"
fi
mv "${workdir}/${bin_name}" "${bin_dir}/${bin_name}"
chmod +x "${bin_dir}/${bin_name}"
ryl_path="${bin_dir}/${bin_name}"

# Takes effect from the next step on, which is why this step calls $ryl_path.
printf '%s\n' "$bin_dir" >>"$GITHUB_PATH"
installed_version="$("$ryl_path" --version)"
installed_version="${installed_version#ryl }"
{
    printf 'ryl-version=%s\n' "$installed_version"
    printf 'ryl-path=%s\n' "$ryl_path"
} >>"$GITHUB_OUTPUT"
echo "Installed ryl ${installed_version} at ${ryl_path}"

if [ "$install_only" = "true" ]; then
    exit 0
fi

echo "Running: ryl ${ryl_args[*]}"
"$ryl_path" "${ryl_args[@]}"

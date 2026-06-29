#!/usr/bin/env bash
# Time Assistant — runtime bootstrap
#
# Modes:
#   --find-system   Print the first python >= 3.10 found on PATH, or nothing (exit 0).
#   --print-url     Print the standalone-Python download URL for this OS/arch.
#                   Override detection via TA_OS / TA_ARCH env vars.
#   (default)       Resolve an interpreter (system first, then download if absent),
#                   write "export TIME_ASSISTANT_PYTHON=..." to $CLAUDE_ENV_FILE if set,
#                   and print the resolved path.
#
# Environment:
#   TA_OS          Override OS detection (darwin | linux | windows)
#   TA_ARCH        Override arch detection (x86_64 | arm64 | aarch64)
#   TA_DATA_DIR    Where to store the downloaded Python (default: ~/.local/share/TimeAssistant)
#   CLAUDE_ENV_FILE  Claude injects this; we append the export line to it when set.
set -eu

# ---------------------------------------------------------------------------
# Release constants — bump when upgrading the standalone-Python version.
# ---------------------------------------------------------------------------
TA_RELEASE="20260623"
TA_PY_VER="3.12.13"

# ---------------------------------------------------------------------------
# OS / arch detection (overridable for testing via TA_OS / TA_ARCH)
# ---------------------------------------------------------------------------
_detect_os() {
    if [ -n "${TA_OS:-}" ]; then
        echo "$TA_OS"
        return
    fi
    case "$(uname -s)" in
        Darwin)               echo "darwin" ;;
        Linux)                echo "linux" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *)                    uname -s | tr '[:upper:]' '[:lower:]' ;;
    esac
}

_detect_arch() {
    if [ -n "${TA_ARCH:-}" ]; then
        echo "$TA_ARCH"
        return
    fi
    uname -m
}

# ---------------------------------------------------------------------------
# Build the download URL for astral-sh/python-build-standalone
# ---------------------------------------------------------------------------
_build_url() {
    local os="$1" arch="$2"
    local base="https://github.com/astral-sh/python-build-standalone/releases/download/${TA_RELEASE}"
    local triple
    case "${os}:${arch}" in
        darwin:arm64|darwin:aarch64)
            triple="aarch64-apple-darwin" ;;
        darwin:x86_64)
            triple="x86_64-apple-darwin" ;;
        linux:x86_64)
            triple="x86_64-unknown-linux-gnu" ;;
        linux:aarch64|linux:arm64)
            triple="aarch64-unknown-linux-gnu" ;;
        windows:x86_64)
            triple="x86_64-pc-windows-msvc" ;;
        *)
            echo "bootstrap.sh: unsupported OS/arch combination: ${os}/${arch}" >&2
            exit 1 ;;
    esac
    echo "${base}/cpython-${TA_PY_VER}+${TA_RELEASE}-${triple}-install_only.tar.gz"
}

# ---------------------------------------------------------------------------
# Find first python >= 3.10 on PATH; prints path or nothing (exit 0 always)
# ---------------------------------------------------------------------------
_find_system() {
    for cand in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v "$cand" >/dev/null 2>&1; then
            if "$cand" -c 'import sys;exit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null; then
                command -v "$cand"
                return 0
            fi
        fi
    done
    # Not found — exit 0 with no output per spec.
    return 0
}

# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
TA_OS="$(_detect_os)"
TA_ARCH="$(_detect_arch)"

case "${1:-}" in

    --find-system)
        _find_system
        ;;

    --print-url)
        _build_url "$TA_OS" "$TA_ARCH"
        ;;

    "")
        # Default: resolve an interpreter.
        py_path="$(_find_system)"

        if [ -z "$py_path" ]; then
            # No suitable system Python — download a standalone build.
            # Per-OS data dir ($TA_OS already resolved above).
            case "$TA_OS" in
                windows) data_dir="${TA_DATA_DIR:-${APPDATA:-${HOME}/AppData/Roaming}/TimeAssistant}" ;;
                darwin)  data_dir="${TA_DATA_DIR:-${HOME}/Library/Application Support/TimeAssistant}" ;;
                *)       data_dir="${TA_DATA_DIR:-${HOME}/.local/share/TimeAssistant}" ;;
            esac

            # The install_only tarball extracts to a top-level "python/" directory.
            case "$TA_OS" in
                windows) interp="${data_dir}/python/python.exe" ;;
                *)       interp="${data_dir}/python/bin/python3" ;;
            esac

            if [ ! -x "$interp" ]; then
                url="$(_build_url "$TA_OS" "$TA_ARCH")"
                tgz="${data_dir}/cpython-standalone.tar.gz"
                mkdir -p "$data_dir"
                echo "bootstrap.sh: no system Python >= 3.10 found; downloading standalone build..." >&2
                echo "bootstrap.sh: source: ${url}" >&2
                curl -fsSL "$url" -o "$tgz"
                tar -xzf "$tgz" -C "$data_dir"
                rm -f "$tgz"
            fi

            py_path="$interp"
        fi

        # Append the export to CLAUDE_ENV_FILE so Claude sources it before each Bash call.
        if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
            echo "export TIME_ASSISTANT_PYTHON=\"${py_path}\"" >> "$CLAUDE_ENV_FILE"
        fi

        echo "$py_path"
        ;;

    *)
        echo "bootstrap.sh: unknown argument: $1" >&2
        exit 1 ;;
esac

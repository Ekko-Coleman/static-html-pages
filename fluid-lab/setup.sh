#!/usr/bin/env bash
# Fluid Lab one-shot setup: checks and installs what the project needs, then starts the /goal loop.
#
#   ./setup.sh                 set up, then start Claude Code interactively with /goal
#   ./setup.sh --no-launch     set up only (start later with: npm run goal)
#   ./setup.sh --headless      set up, then run /goal non-interactively (claude -p)
#   ./setup.sh --mode auto     Claude Code permission mode for the loop (default: acceptEdits)
#   ./setup.sh --yes           answer "yes" to install prompts (doesn't answer the reference-Mac question)
#
# Safe to re-run: every step checks before it acts.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
cd "$here"

orig_args=("$@")
launch=1
yes=0
run_args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-launch) launch=0 ;;
    --headless) run_args+=(--headless) ;;
    --mode) run_args+=(--mode "$2"); shift ;;
    --yes|-y) yes=1 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

bold() { printf '\n\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
die()  { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }
ask()  { # ask "question" default(y|n)
  local reply hint="[y/N]"; [[ "$2" == y ]] && hint="[Y/n]"
  if [[ $yes -eq 1 ]]; then return 0; fi
  if [[ ! -t 0 ]]; then [[ "$2" == y ]]; return; fi
  read -r -p "  $1 $hint " reply
  reply="${reply:-$2}"
  [[ "$reply" =~ ^[Yy] ]]
}

# ---------------------------------------------------------------------------
bold "1/8  Machine"
os="$(uname -s)"; arch="$(uname -m)"
if [[ "$os" == Darwin && "$arch" == arm64 ]]; then
  ok "macOS on Apple Silicon ($(sw_vers -productVersion))"
else
  warn "$os/$arch: this isn't an Apple Silicon Mac. You can build and unit-test here, but benchmark numbers only count on the reference Mac."
fi

# ---------------------------------------------------------------------------
bold "2/8  Project location"
command -v git >/dev/null 2>&1 || die "git is required. On macOS, run: xcode-select --install"
top="$(git -C "$here" rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -n "$top" && "$top" != "$here" ]]; then
  # Downloaded as part of a bigger repo. Experiment worktrees and the baseline tag need their own repo.
  dest="${FLUIDLAB_DIR:-$HOME/fluid-lab}"
  warn "This folder is inside another git repo ($top). Fluid Lab needs a repo of its own."
  if [[ -e "$dest" ]]; then die "$dest already exists. Set FLUIDLAB_DIR to a free path and re-run."; fi
  if ask "Copy the project to $dest and continue there?" y; then
    mkdir -p "$dest"
    (cd "$here" && tar --exclude=node_modules --exclude=dist -cf - .) | (cd "$dest" && tar -xf -)
    ok "Copied to $dest"
    exec "$dest/setup.sh" ${orig_args[@]+"${orig_args[@]}"}
  fi
  die "Copy the fluid-lab folder somewhere outside $top and run setup.sh there."
fi
ok "$here"

# ---------------------------------------------------------------------------
bold "3/8  Node.js (>= 22.12)"
node_ok() { command -v node >/dev/null 2>&1 && node -e 'const [a,b]=process.versions.node.split(".").map(Number);process.exit(a>22||(a===22&&b>=12)?0:1)'; }
if ! node_ok; then
  if command -v brew >/dev/null 2>&1 && ask "Node.js 22.12+ not found. Install it with Homebrew (brew install node)?" y; then
    brew install node
  else
    die "Install Node.js 22.12 or newer (https://nodejs.org, or: brew install node), then re-run."
  fi
fi
node_ok || die "Node.js is still older than 22.12 on PATH: $(command -v node)"
ok "node $(node -v) · npm $(npm -v)"

# ---------------------------------------------------------------------------
bold "4/8  Claude Code"
export PATH="$HOME/.local/bin:$PATH"
if ! command -v claude >/dev/null 2>&1; then
  if ask "Claude Code isn't installed. Install it with the official installer (curl -fsSL https://claude.ai/install.sh | bash)?" y; then
    curl -fsSL https://claude.ai/install.sh | bash
    hash -r
  fi
fi
command -v claude >/dev/null 2>&1 || die "Install Claude Code (https://code.claude.com/docs) and re-run."
ok "$(claude --version 2>/dev/null | head -1)"

# ---------------------------------------------------------------------------
bold "5/8  Dependencies"
if [[ -f package-lock.json ]]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi
ok "npm packages installed"
if [[ -n "${PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD:-}" ]]; then
  warn "PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD is set, so the Chromium download was skipped (the harness needs it on the reference Mac)"
else
  npx playwright install chromium
fi
ok "Playwright Chromium $(npx playwright --version 2>/dev/null | awk '{print $2}') installed (pinned by package.json)"

# ---------------------------------------------------------------------------
bold "6/8  Reference machine (SPEC Q1)"
node scripts/machine-info.mjs --out .fluidlab/machine.json >/dev/null
ok "This machine is recorded in .fluidlab/machine.json"
if [[ -f harness/reference-machine.json ]]; then
  ok "Reference machine already set: harness/reference-machine.json"
elif [[ "$os" == Darwin && -t 0 ]]; then
  # Mike's decision, so --yes doesn't answer it.
  read -r -p "  Is THIS Mac the reference machine for all published benchmark numbers? [y/N] " reply
  if [[ "$reply" =~ ^[Yy] ]]; then
    cp .fluidlab/machine.json harness/reference-machine.json
    sed -i.bak 's/^- \[ \] 👤 Reference Mac confirmed/- [x] 👤 Reference Mac confirmed/' docs/MILESTONES.md && rm -f docs/MILESTONES.md.bak
    ok "Saved harness/reference-machine.json and ticked the M0 item"
  else
    warn "Not set. The loop will raise Q1 under \"Blocked on Mike\" when it needs the answer."
  fi
else
  warn "Skipped. The reference machine must be a Mac; the loop will raise Q1 when it needs it."
fi

# ---------------------------------------------------------------------------
bold "7/8  Git"
if [[ ! -d .git ]]; then
  git init -q -b main
  ok "Initialized a new repo on branch main"
fi
if [[ -z "$(git config user.email || true)" ]]; then
  warn "git has no user.email. The loop commits every step, so set one for this repo."
  read -r -p "  Your name: " gname; read -r -p "  Your email: " gemail
  git config user.name "$gname"; git config user.email "$gemail"
fi
if ! git rev-parse -q --verify HEAD >/dev/null; then
  git add -A && git commit -q -m "chore: Fluid Lab scaffold"
  ok "Initial commit created"
elif [[ -n "$(git status --porcelain)" ]]; then
  git add -A && git commit -q -m "chore: setup.sh updates"
  ok "Committed setup changes"
else
  ok "Working tree clean"
fi

# ---------------------------------------------------------------------------
bold "8/8  Smoke test (npm run check)"
npm run check --silent
ok "typecheck, unit tests, guard tests and build all pass"

echo
node scripts/goal-status.mjs

if [[ $launch -eq 0 ]]; then
  bold "Setup done. Start the loop with: npm run goal"
  exit 0
fi
bold "Setup done. Starting the /goal loop…"
exec bash scripts/run-goal.sh ${run_args[@]+"${run_args[@]}"}

#!/usr/bin/env bash
set -euxo pipefail

# dirs from mounts
mkdir -p ~/.claude/ ~/.config/gh

# files from mounts
touch \
	~/.claude/.config.json \
	~/.gitconfig \
	~/.gitignore_global

#!/usr/bin/env bash
# Install reddit-find Claude Code skill
# Usage: curl -fsSL https://raw.githubusercontent.com/LeadGrowGTM/reddit-find/main/install-skill.sh | bash

set -e

SKILL_URL="https://raw.githubusercontent.com/LeadGrowGTM/reddit-find/main/skills/reddit-find/SKILL.md"
INSTALL_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills/reddit-find}"

echo "Installing reddit-find skill..."
mkdir -p "$INSTALL_DIR"
curl -fsSL "$SKILL_URL" -o "$INSTALL_DIR/SKILL.md"
echo "Skill installed: $INSTALL_DIR/SKILL.md"
echo ""
echo "Next steps:"
echo "  1. pip install reddit-find"
echo "  2. export SERPER_API_KEY=your_key   # serper.dev"
echo "  3. export ANTHROPIC_API_KEY=your_key"
echo "  4. reddit-find fetch \"your topic\" -o research.md"

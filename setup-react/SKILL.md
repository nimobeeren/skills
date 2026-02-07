---
name: setup-react
description: Set up a new React project from scratch
---

## Prerequisites

Check that these are installed before doing anything:

- Node.js >= 23 (for running TypeScript natively)
- pnpm

If any are missing, recommend installing them first.

## Usage

1. Run `node <path_to_this_skill>/scripts/setup.ts` which will:
  1. Set up a Git repo
  2. Set up shadcn with Vite following: https://ui.shadcn.com/docs/installation/vite
  3. Remove Vite boilerplate and replace with a minimal shadcn example
  4. Remove Vite README and replace with a minimal installation+usage example
  4. Install Prettier and set up precommit hook to format staged files
2. Test
3. Commit

Constraints:

- use kebab-case for all TypeScript files (including React components)

## Updating

If asked to update the skill:

1. Run `trash <path_to_this_skill>/scripts/setup.ts`
2. Write it again from scratch following the steps above
3. Test it in a temp directory

Hints:

- `tsconfig.json` can contain comments, which `JSON.parse` can't handle

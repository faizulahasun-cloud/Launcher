# AI Handoff Desk

A Telegram Mini App-friendly, mobile-first dashboard for preparing explicit message handoffs between ChatGPT, Claude, and Hermes.

## Current prototype

- Tabs for ChatGPT, Claude, Hermes, Workflow, and Settings.
- Add/paste messages into each workspace.
- Per-message **Copy**, **Share**, **Send to Claude**, and **Send to Hermes** actions.
- Handoff packets are queued locally and can be copied/shared again from Workflow.
- Browser-local message history with JSON export.
- Telegram Mini App viewport/header integration when opened inside Telegram.
- Responsive layout for phone and desktop.

## Important integration boundary

This branch is a **frontend prototype**, not yet an end-to-end AI bridge.

- It does not read the user's existing ChatGPT Chrome tab or private conversation.
- It does not log into or control the consumer ChatGPT or Claude websites.
- Handoff packets are prepared and copied; the user still pastes them into Claude or delivers them through a configured Hermes channel.
- Hermes execution requires a separately configured, authenticated bridge reachable from the dashboard.
- GitHub Pages is static hosting. Do not put provider API keys, Telegram bot tokens, or other secrets in browser JavaScript.

The app stores message content in this browser's local storage. Do not paste passwords, API keys, or sensitive information.

## Try it

Open `index.html` locally, or deploy this branch to a preview before merging. GitHub Pages deployment from `main` remains unchanged until this branch is merged.

## Next integration stages

1. Verify the UI in a browser and inside Telegram's Mini App.
2. Choose a secure backend/bridge and define authentication.
3. Connect Hermes through a narrowly scoped endpoint or Telegram bot integration.
4. Add delivery acknowledgements and task status only after real end-to-end tests.
5. Keep ChatGPT/Claude consumer sessions manual unless a supported, user-authorized integration is available.

# Bridge Bank Add-on Documentation

## Overview

Bridge Bank syncs EU bank transactions to [Actual Budget](https://actualbudget.org/) via [Enable Banking](https://enablebanking.com/) open banking APIs. It supports 2,500+ banks across 29 European countries.

## Configuration

### Add-on Options

| Option | Description |
|--------|-------------|
| `actual_url` | URL of your Actual Budget instance (e.g. `http://192.168.1.100:5006`) |
| `actual_password` | Your Actual Budget password |
| `actual_sync_id` | Sync ID from Actual Budget (Settings → Advanced → Sync ID) |
| `actual_account` | Account name in Actual Budget to sync to |
| `actual_verify_ssl` | Verify SSL certificates for Actual Budget (default: false) |
| `eb_redirect_url` | OAuth redirect URL (set this if using Nabu Casa) |
| `sync_time` | Time of day to sync (HH:MM format, default: 06:00) |
| `sync_frequency` | Hours between syncs: 6, 12, or 24 (default: 24) |
| `notify_email` | Email address for sync notifications |
| `smtp_user` | SMTP login username |
| `smtp_password` | SMTP login password (app-specific password) |
| `smtp_host` | SMTP server (auto-detected for Gmail, iCloud, Outlook, Yahoo) |
| `smtp_port` | SMTP port (default: 587) |
| `smtp_from` | Sender email address (if different from smtp_user) |
| `notify_on` | When to send notifications: `all` or `errors` |

### Enable Banking Setup

1. Sign up at [enablebanking.com](https://enablebanking.com)
2. Register a new API application
3. Set the redirect URL to your Bridge Bank callback URL
4. Download the `.pem` private key file
5. Upload it through the Bridge Bank web UI

### OAuth with Nabu Casa

If using Nabu Casa for remote access:

1. Install the Bridge Bank custom integration (from `ha_component/`)
2. Set Enable Banking redirect URL to: `https://<nabu-casa-url>/api/bridge_bank/callback`
3. Set `eb_redirect_url` in add-on config to the same URL

## Web UI

Access Bridge Bank through the Home Assistant sidebar (Bridge Bank icon) or via the add-on's "Open Web UI" button. The setup wizard guides you through:

1. **Enable Banking** — upload your `.pem` file and Application ID
2. **Actual Budget** — connect to your Actual Budget instance
3. **Notifications** — configure email alerts
4. **Bank** — search and connect your bank via OAuth
5. **Status** — monitor sync history and manage connections

## Session Renewal

Bank sessions expire roughly every 180 days. You'll get an email warning before expiry. Re-authorise from the Bank tab in the web UI.

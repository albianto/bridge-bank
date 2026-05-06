# Bridge Bank

**Your EU bank transactions, inside Actual Budget. Automatically.**

Bridge Bank connects to your EU bank via open banking and imports your transactions into a self-hosted [Actual Budget](https://actualbudget.org/) instance once a day. It runs on your own machine — your financial data never touches any third-party server.

---

## What you get

- **Flexible sync frequency** — sync every 6, 12, or 24 hours, at a time you choose
- **2,500+ European banks** — Revolut, N26, Monzo, Wise, Millennium BCP, Santander, ING, BNP Paribas, and more across 29 countries
- **Multiple bank accounts** — connect multiple bank accounts, each syncing to a different Actual Budget account
- **Read-only, always** — Bridge Bank can never move money or modify your account
- **Pending transaction tracking** — pending transactions are imported as uncleared and automatically confirmed when they settle
- **Duplicate detection** — Bridge Bank tracks every transaction ID so nothing gets imported twice
- **Email notifications** — an alert if something goes wrong, and a warning before your bank session expires
- **Your data, your machine** — bank data goes directly from Enable Banking to your machine, never our servers
- **Lightweight** — runs as a single Docker container
- **Runs anywhere** — supports x86, Raspberry Pi, and other ARM devices out of the box

---

## Requirements

- A [Home Assistant](https://www.home-assistant.io/) instance with Supervisor (HAOS or Supervised install), **or** Docker and Docker Compose for standalone mode
- A free [Enable Banking](https://enablebanking.com/) account
- A self-hosted [Actual Budget](https://actualbudget.org/) instance

---

## Installation

### Option A: Home Assistant Add-on (recommended)

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**
2. Click the three dots (⋮) in the top right, then **Repositories**
3. Add this repository URL: `https://github.com/albianto/bridge-bank`
4. Find **Bridge Bank** in the store and click **Install**
5. Go to the **Configuration** tab and fill in your Actual Budget details (URL, password, Sync ID, account name)
6. Start the add-on
7. Click **Open Web UI** (or find it in the sidebar as "Bridge Bank") to access the setup wizard

The add-on web UI is accessible directly from Home Assistant's sidebar via Ingress — no port forwarding needed.

#### Home Assistant Integration (optional sensors)

To get sync status sensors in Home Assistant:

1. Copy the `ha_component/bridge_bank/` folder to your Home Assistant `custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration → Bridge Bank**
4. Enter the Bridge Bank URL (use `http://localhost:3000` if running as an add-on)

This gives you three sensors:
- **Bridge Bank Status** — overall health (ok / degraded / unhealthy)
- **Bridge Bank Last Sync** — timestamp and status of the last sync
- **Bridge Bank Banks Connected** — number of connected bank accounts

#### OAuth with Nabu Casa

If you use Nabu Casa for remote access and need bank OAuth redirects to work externally:

1. In Enable Banking, set the redirect URL to: `https://<your-nabu-casa-url>/api/bridge_bank/callback`
2. In the Bridge Bank add-on configuration, set `eb_redirect_url` to the same URL
3. Install the Bridge Bank integration (above) — it will catch the OAuth callback and redirect it to the add-on

### Option B: Standalone Docker

### 1. Set up Enable Banking

Enable Banking is the regulated open banking provider that connects Bridge Bank to your bank.

1. Sign up at [enablebanking.com](https://enablebanking.com)
2. Go to **API applications** and click **Register new application**
3. Fill in the form:
   - **Application name:** Bridge Bank
   - **Allowed redirect URLs:** your Bridge Bank instance URL + `/callback` (e.g. `http://your-server:3002/callback`)
   - **Application description:** Connect Actual Budget with my bank
   - **Email for data protection matters:** your email address
   - **Privacy URL:** (your own or leave blank)
   - **Terms URL:** (your own or leave blank)
4. Click **Register** — a `.pem` file will be saved to your Downloads folder. The filename matches your Application ID (e.g. `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.pem`). Keep it safe — you'll need it in the setup wizard.
5. Click **Activate by linking accounts** on your application page
6. Select your country and bank from the dropdowns and click **Link**
7. Follow the steps to log in to your bank and approve read-only access — this activates your Enable Banking app

### 2. Install Bridge Bank (standalone Docker)

**On your server**, create the folder and download the compose file:
```bash
mkdir -p ~/bridge-bank/data && cd ~/bridge-bank
curl -O https://raw.githubusercontent.com/albianto/bridge-bank/main/docker-compose.yml
```

Start the container:
```bash
docker compose up -d
```

Open **http://your-server-address:3002** in your browser. The setup wizard will guide you through the rest.

---

## Setup wizard

The browser-based wizard walks you through four steps:

1. **Enable Banking** — enter your Application ID and upload your `.pem` file
2. **Actual Budget** — enter your Actual Budget URL, password, and Sync ID
3. **Notifications** — set your email and SMTP credentials
4. **Bank** — connect your bank via OAuth. You choose which Actual Budget account each bank syncs to.
5. **Status** — view sync history, manage bank connections, check for updates

You can connect multiple bank accounts. Each bank syncs to a different Actual Budget account (e.g. Revolut → "Revolut", N26 → "N26"). To add another bank, go to the **Bank** tab and search for another bank.

Once complete, Bridge Bank runs silently in the background and syncs your transactions every day at the time you chose.

---

## First sync and duplicates

On the first sync, Bridge Bank will import all transactions from the start date you set in the wizard. If you set a past date and already have those transactions in Actual Budget from another source, you may see duplicates — just delete the extras manually. This will only happen once. From the second sync onwards, Bridge Bank tracks every transaction ID and will never import the same transaction twice.

To avoid duplicates entirely, set the start date to today when going through the wizard.

---

## How it works
```
Your bank
   ↓  (read-only OAuth, Enable Banking)
Bridge Bank (running on your machine)
   ↓  (Actual Budget API)
Your Actual Budget instance
   ↓  (SMTP)
Your inbox  ← alert emails
```

On each sync run, Bridge Bank:

1. Fetches transactions since the last sync from Enable Banking
3. Filters out any transaction IDs already imported
4. Writes new transactions to Actual Budget
5. Updates any previously pending transactions that have since settled
6. Logs the result and sends an alert email if something went wrong

---

## Session renewal (every ~180 days)

Enable Banking requires you to re-authorise access roughly every 6 months. If you configured email notifications, you will receive a warning before expiry.

To re-authorise, go to the **Bank** tab in the Bridge Bank web UI and click **Re-authorise bank**.

---

## Updating

Click **Check for updates** on the Status page. Bridge Bank will pull the latest version and restart automatically.

Or run manually:
```bash
docker compose pull && docker compose up -d
```

---

## License deactivation

Each licence key supports up to 2 machine activations. To move Bridge Bank to a new machine, go to the **Status** page in the web UI and click **Deactivate license** before reinstalling.

---

## License

MIT + Commons Clause. Free to self-host for personal use. You may not sell, sublicense, or offer Bridge Bank as a competing service.

Built by [David Alves](https://david-alves.com).

---

## To generate Docker Image run

```bash
docker buildx build --platform linux/amd64 -t bridge-bank:latest -o type=oci,dest=bridge-bank-oci.tar .
scp /Users/Alberto/Downloads/bridge-bank-main/bridge-bank-oci.tar root@192.168.1.250:/var/lib/vz/template/cache/
```
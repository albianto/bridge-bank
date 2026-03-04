#!/usr/bin/env python3
import os, json, time, logging, datetime, decimal, requests, schedule
from actual import Actual
from actual.queries import get_or_create_account, reconcile_transaction, get_transactions

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ACTUAL_URL      = os.environ["ACTUAL_URL"]
ACTUAL_PASSWORD = os.environ["ACTUAL_PASSWORD"]
ACTUAL_SYNC_ID  = os.environ["ACTUAL_SYNC_ID"]
ACTUAL_ACCOUNT  = os.environ.get("ACTUAL_ACCOUNT", "Revolut")
EB_APP_ID       = os.environ["EB_APPLICATION_ID"]
SYNC_HOURS      = int(os.environ.get("SYNC_INTERVAL_HOURS", "6"))
STATE_FILE      = "/data/state.json"
EB_API          = "https://api.enablebanking.com"
NOTIFY_EMAIL    = os.environ.get("NOTIFY_EMAIL", "")
SMTP_HOST       = os.environ.get("SMTP_HOST", "")
SMTP_PORT       = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER       = os.environ.get("SMTP_USER", "")
SMTP_PASS       = os.environ.get("SMTP_PASS", "")


def send_email(subject, body):
    if not all([NOTIFY_EMAIL, SMTP_HOST, SMTP_USER, SMTP_PASS]):
        return
    import smtplib
    from email.mime.text import MIMEText
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = SMTP_USER
    msg["To"]      = NOTIFY_EMAIL
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, NOTIFY_EMAIL, msg.as_string())
        log.info("Email notification sent")
    except Exception as e:
        log.warning("Failed to send email: %s", e)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def make_headers():
    import jwt, uuid
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    key_data = open("/data/private.pem", "rb").read()
    key = load_pem_private_key(key_data, password=None)
    now = int(time.time())
    payload = {
        "iss": "enablebanking.com",
        "aud": "api.enablebanking.com",
        "iat": now,
        "exp": now + 3600,
        "jti": str(uuid.uuid4()),
        "sub": EB_APP_ID,
    }
    token = jwt.encode(payload, key, algorithm="RS256", headers={"kid": EB_APP_ID})
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_session(state):
    sid = state.get("eb_session_id")
    uid = state.get("eb_account_uid")
    exp = state.get("eb_session_expiry")
    if not sid or not uid:
        raise RuntimeError("No session found. Run dosetup.py first.")
    expiry = datetime.datetime.fromisoformat(exp)
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=datetime.timezone.utc)
    days_left = (expiry - datetime.datetime.now(datetime.timezone.utc)).days
    if days_left < 7:
        log.warning("Session expires in %d days. Re-run dosetup.py soon.", days_left)
        send_email(
            f"Revolut-Actual sync: session expires in {days_left} days",
            f"""Your Enable Banking session expires in {days_left} days.

To renew it, SSH into your server and run:

  python3 dosetup.py

Then follow the instructions -- open the URL in your browser, approve bank access,
and paste the redirect URL back in the terminal.

Finally restart the container:

  docker compose restart

Done. Next renewal will be in 180 days.
""",
        )
    return sid, uid


def fetch_transactions(account_uid, date_from):
    headers = make_headers()
    params = {
        "date_from": date_from.isoformat(),
        "date_to": datetime.date.today().isoformat(),
    }
    txns = []
    url = f"{EB_API}/accounts/{account_uid}/transactions"
    while url:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        txns.extend(data.get("transactions", []))
        ck = data.get("continuation_key")
        url = f"{EB_API}/accounts/{account_uid}/transactions" if ck else None
        params = {"continuation_key": ck} if ck else {}
    log.info("Fetched %d transactions from Enable Banking", len(txns))
    return txns


def parse_date(t):
    raw = t.get("transaction_date") or t.get("booking_date") or t.get("value_date")
    if not raw:
        raise ValueError("No date in transaction")
    return datetime.date.fromisoformat(raw[:10])


def parse_amount(t):
    amt = decimal.Decimal(str((t.get("transaction_amount") or {}).get("amount", "0")))
    indic = t.get("credit_debit_indicator") or t.get("credit_debit_indic", "")
    if indic.upper() == "DBIT":
        amt = -abs(amt)
    else:
        amt = abs(amt)
    return amt


def parse_payee(t):
    return (
        (t.get("creditor") or {}).get("name")
        or (t.get("debtor") or {}).get("name")
        or t.get("creditor_name")
        or t.get("debtor_name")
        or "Unknown"
    )


def parse_notes(t):
    ref = t.get("remittance_information_unstructured")
    return ref if ref else ""


def run_sync():
    log.info("Starting sync...")
    state = load_state()
    try:
        _, account_uid = get_session(state)
    except RuntimeError as e:
        log.error(str(e))
        return

    last = state.get("last_sync_date")
    if last:
        date_from = datetime.date.fromisoformat(last)
    else:
        date_from = datetime.date.today() - datetime.timedelta(days=30)
        log.info("First run: fetching last 30 days")

    try:
        raw = fetch_transactions(account_uid, date_from)
    except requests.HTTPError as e:
        log.error("Enable Banking API error: %s", e)
        return

    if not raw:
        log.info("No new transactions")
        state["last_sync_date"] = datetime.date.today().isoformat()
        save_state(state)
        return

    # pending_map: "date|amount" -> actual transaction id
    pending_map = state.get("pending_map", {})

    try:
        with Actual(
            base_url=ACTUAL_URL,
            password=ACTUAL_PASSWORD,
            file=ACTUAL_SYNC_ID,
            data_dir="/data/actual-cache",
        ) as actual:
            account = get_or_create_account(actual.session, ACTUAL_ACCOUNT)
            existing = list(get_transactions(actual.session, account=account))
            already_matched = existing[:]
            added = updated = skipped = 0

            for txn in raw:
                try:
                    status = txn.get("status", "BOOK")
                    date   = parse_date(txn)
                    amount = parse_amount(txn)
                    payee  = parse_payee(txn)
                    notes  = parse_notes(txn)
                    key    = f"{date}|{amount}"

                    log.debug("Txn: %s | %s | %s | %s", status, date, amount, payee)

                    if status == "PDNG":
                        # Import as uncleared if not already tracked
                        if key not in pending_map:
                            t = reconcile_transaction(
                                actual.session, date, account, payee, notes,
                                None, amount, cleared=False, already_matched=already_matched,
                            )
                            already_matched.append(t)
                            if t.changed():
                                pending_map[key] = str(t.id)
                                added += 1
                                log.info("Pending imported: %s | %s | %s", date, amount, payee)
                            else:
                                skipped += 1
                        else:
                            skipped += 1

                    else:  # BOOK = confirmed
                        if key in pending_map:
                            # Match the pending transaction and mark it cleared
                            txn_id = pending_map[key]
                            existing_txn = next(
                                (t for t in existing if str(t.id) == txn_id), None
                            )
                            if existing_txn:
                                existing_txn.cleared = True
                                if payee and payee != "Unknown":
                                    existing_txn.payee_name = payee
                                del pending_map[key]
                                updated += 1
                                log.info("Pending confirmed: %s | %s | %s", date, amount, payee)
                            else:
                                # Was deleted manually in Actual -- import fresh
                                del pending_map[key]
                                t = reconcile_transaction(
                                    actual.session, date, account, payee, notes,
                                    None, amount, cleared=True, already_matched=already_matched,
                                )
                                already_matched.append(t)
                                if t.changed():
                                    added += 1
                        else:
                            # Normal confirmed transaction
                            t = reconcile_transaction(
                                actual.session, date, account, payee, notes,
                                None, amount, cleared=True, already_matched=already_matched,
                            )
                            already_matched.append(t)
                            if t.changed():
                                added += 1
                            else:
                                skipped += 1

                except Exception as e:
                    log.warning("Skipping transaction: %s | %s", e, txn)

            actual.commit()
            log.info("Done: %d added, %d confirmed, %d skipped", added, updated, skipped)

    except Exception as e:
        log.error("Actual Budget error: %s", e)
        return

    state["last_sync_date"] = datetime.date.today().isoformat()
    state["pending_map"] = pending_map
    save_state(state)


if __name__ == "__main__":
    log.info("Starting scheduler (every %dh)", SYNC_HOURS)
    run_sync()
    schedule.every(SYNC_HOURS).hours.do(run_sync)
    while True:
        schedule.run_pending()
        time.sleep(60)

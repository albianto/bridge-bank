import os
import json

CONFIG_FILE = "/data/config.json"
HA_OPTIONS_FILE = "/data/options.json"

# Defaults — all overridable by HA add-on options, config.json, or environment variables
ACTUAL_URL           = ""
ACTUAL_PASSWORD      = ""
ACTUAL_SYNC_ID       = ""
ACTUAL_ACCOUNT       = ""
ACTUAL_VERIFY_SSL    = "false"
EB_APPLICATION_ID    = ""
EB_BANK_NAME         = ""
EB_BANK_COUNTRY      = ""
EB_PSU_TYPE          = "personal"
EB_REDIRECT_URL      = ""
SYNC_TIME            = "06:00"
SYNC_FREQUENCY       = "24"
START_SYNC_DATE      = ""
ACCOUNT_HOLDER_NAME  = ""
NOTIFY_EMAIL         = ""
SMTP_USER            = ""
SMTP_PASSWORD        = ""
SMTP_HOST            = ""
SMTP_PORT            = "587"
SMTP_FROM            = ""
NOTIFY_ON            = "all"
NOTIFY_ENABLED       = "false"
BRIDGE_BANK_URL      = "https://localhost:3000"

def _load():
    """Load config from HA add-on options, then config.json, then environment variables."""
    # 1. Load HA add-on options (/data/options.json) if available
    ha_options = {}
    if os.path.exists(HA_OPTIONS_FILE):
        try:
            with open(HA_OPTIONS_FILE) as f:
                ha_options = json.load(f)
        except Exception:
            pass

    # 2. Load config.json (wizard-persisted settings)
    data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
        except Exception:
            pass

    g = globals()
    for key in list(g.keys()):
        if key.startswith("_") or not key.isupper():
            continue
        # Priority: config.json > HA options > env vars > defaults
        if key in data and data[key]:
            g[key] = str(data[key])
        elif key.lower() in ha_options and ha_options[key.lower()]:
            g[key] = str(ha_options[key.lower()])
        else:
            env_val = os.environ.get(key)
            if env_val is not None:
                g[key] = env_val

def set(key: str, value: str):
    """Persist a config value to config.json and update the in-memory global."""
    data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
        except Exception:
            pass
    data[key] = value
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    globals()[key] = value

def is_configured() -> bool:
    """Returns True if all required fields are set."""
    return bool(ACTUAL_URL and ACTUAL_PASSWORD and
                ACTUAL_SYNC_ID and ACTUAL_ACCOUNT)

def is_connected() -> bool:
    """Returns True if at least one bank account is connected."""
    from . import db
    return db.get_bank_account_count() > 0

# Load on import
_load()

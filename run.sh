#!/usr/bin/env bash
# ==============================================================================
# Bridge Bank - Home Assistant Add-on entry script
# ==============================================================================

# shellcheck source=/usr/lib/bashio/bashio.sh
source /usr/lib/bashio/bashio.sh

bashio::log.info "Starting Bridge Bank add-on..."

# Export add-on options as environment variables so app/config.py can read them
export ACTUAL_URL="$(bashio::config 'actual_url')"
export ACTUAL_PASSWORD="$(bashio::config 'actual_password')"
export ACTUAL_SYNC_ID="$(bashio::config 'actual_sync_id')"
export ACTUAL_ACCOUNT="$(bashio::config 'actual_account')"
export ACTUAL_VERIFY_SSL="$(bashio::config 'actual_verify_ssl')"
export EB_REDIRECT_URL="$(bashio::config 'eb_redirect_url')"
export SYNC_TIME="$(bashio::config 'sync_time')"
export SYNC_FREQUENCY="$(bashio::config 'sync_frequency')"
export NOTIFY_EMAIL="$(bashio::config 'notify_email')"
export SMTP_USER="$(bashio::config 'smtp_user')"
export SMTP_PASSWORD="$(bashio::config 'smtp_password')"
export SMTP_HOST="$(bashio::config 'smtp_host')"
export SMTP_PORT="$(bashio::config 'smtp_port')"
export SMTP_FROM="$(bashio::config 'smtp_from')"
export NOTIFY_ON="$(bashio::config 'notify_on')"

# Ingress support: resolve ingress base path from env or Supervisor metadata
if [ -z "${INGRESS_ENTRY:-}" ]; then
	_ingress_entry="$(bashio::addon.ingress_entry 2>/dev/null || true)"
	export INGRESS_ENTRY="${_ingress_entry%/}"
else
	export INGRESS_ENTRY="${INGRESS_ENTRY%/}"
fi

# Data directory (HA add-ons use /data for persistent storage)
export DATA_DIR="/data"

bashio::log.info "Ingress entry: ${INGRESS_ENTRY}"
bashio::log.info "Data directory: ${DATA_DIR}"

# Install/update the Bridge Bank integration into custom_components
INTEGRATION_SRC="/app/ha_component/bridge_bank"
# homeassistant_config:rw mounts HA config at /config in this environment
HA_CONFIG="/config"
INTEGRATION_DST="$HA_CONFIG/custom_components/bridge_bank"

if [ -d "$INTEGRATION_SRC" ]; then
  mkdir -p "$HA_CONFIG/custom_components"
  rm -rf "$INTEGRATION_DST"
  cp -r "$INTEGRATION_SRC" "$INTEGRATION_DST"
  bashio::log.info "Integration installed to $INTEGRATION_DST"
else
  bashio::log.warning "Integration source not found at $INTEGRATION_SRC"
fi

# Notify HA to auto-discover the Bridge Bank integration
bashio::log.info "Triggering integration discovery..."
curl -sSf -X POST \
  -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"addon":"self","service":"bridge_bank","config":{"bridge_bank_url":"http://local-bridge-bank:3000"}}' \
  "http://supervisor/discovery" > /dev/null 2>&1 || true

cd /app
exec python -u main.py

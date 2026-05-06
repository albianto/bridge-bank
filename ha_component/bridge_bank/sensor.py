"""Sensors for Bridge Bank integration."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, BridgeBankCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Bridge Bank sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            BridgeBankStatusSensor(coordinator, entry),
            BridgeBankLastSyncSensor(coordinator, entry),
            BridgeBankBanksConnectedSensor(coordinator, entry),
        ]
    )


class BridgeBankStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing overall Bridge Bank health status."""

    _attr_icon = "mdi:bank-check"

    def __init__(self, coordinator: BridgeBankCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_name = "Bridge Bank Status"

    @property
    def native_value(self) -> str:
        """Return the health status."""
        data = self.coordinator.data or {}
        return data.get("status", "unknown")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional health attributes."""
        data = self.coordinator.data or {}
        attrs = {}
        if "hours_since_last_sync" in data:
            attrs["hours_since_last_sync"] = data["hours_since_last_sync"]
        if "sync_overdue" in data:
            attrs["sync_overdue"] = data["sync_overdue"]
        if "scheduler_jobs" in data:
            attrs["scheduler_jobs"] = data["scheduler_jobs"]
        if "sessions_expiring_soon" in data:
            attrs["sessions_expiring_soon"] = data["sessions_expiring_soon"]
        return attrs


class BridgeBankLastSyncSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the last sync timestamp and status."""

    _attr_icon = "mdi:sync"

    def __init__(self, coordinator: BridgeBankCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_sync"
        self._attr_name = "Bridge Bank Last Sync"

    @property
    def native_value(self) -> str | None:
        """Return the last sync timestamp."""
        data = self.coordinator.data or {}
        last = data.get("last_sync")
        if last:
            return last.get("ran_at")
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return last sync details."""
        data = self.coordinator.data or {}
        last = data.get("last_sync")
        if last:
            return {
                "status": last.get("status", "unknown"),
                "message": last.get("message", ""),
            }
        return {}


class BridgeBankBanksConnectedSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the number of connected bank accounts."""

    _attr_icon = "mdi:bank"

    def __init__(self, coordinator: BridgeBankCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_banks_connected"
        self._attr_name = "Bridge Bank Banks Connected"

    @property
    def native_value(self) -> int:
        """Return the number of connected banks."""
        data = self.coordinator.data or {}
        return data.get("banks_connected", 0)

"""Binary sensor entities for the Bang & Olufsen integration."""
from __future__ import annotations

from mozart_api.models import BatteryState, WebsocketNotificationTag

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONNECTION_STATUS,
    DOMAIN,
    HASS_BINARY_SENSORS,
    BangOlufsenVariables,
    WebSocketNotification,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Binary Sensor entities from config entry."""
    entities = []
    configuration = hass.data[DOMAIN][config_entry.unique_id]

    # Add Binary Sensor entities
    for binary_sensor in configuration[HASS_BINARY_SENSORS]:
        entities.append(binary_sensor)

    async_add_entities(new_entities=entities, update_before_add=True)


class BangOlufsenBinarySensor(BangOlufsenVariables, BinarySensorEntity):
    """Base Binary Sensor class."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Init the Binary Sensor."""
        super().__init__(entry)

        self._attr_available = True
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self._unique_id)})

    async def async_added_to_hass(self) -> None:
        """Turn on the dispatchers."""
        self._dispatchers = [
            async_dispatcher_connect(
                self.hass,
                f"{self._unique_id}_{CONNECTION_STATUS}",
                self._update_connection_state,
            )
        ]

    async def async_will_remove_from_hass(self) -> None:
        """Turn off the dispatchers."""
        for dispatcher in self._dispatchers:
            dispatcher()

    async def _update_connection_state(self, connection_state: bool) -> None:
        """Update entity connection state."""
        self._attr_available = connection_state

        self.async_write_ha_state()


class BangOlufsenBinarySensorBatteryCharging(BangOlufsenBinarySensor):
    """Battery charging Binary Sensor."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Init the battery charging Binary Sensor."""
        super().__init__(entry)

        self._attr_name = f"{self._name} Battery charging"
        self._attr_unique_id = f"{self._unique_id}-battery-charging"
        self._attr_icon = "mdi:battery-charging"
        self._attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    async def async_added_to_hass(self) -> None:
        """Turn on the dispatchers."""

        self._dispatchers = [
            async_dispatcher_connect(
                self.hass,
                f"{self._unique_id}_{WebSocketNotification.BATTERY}",
                self._update_battery_charging,
            ),
            async_dispatcher_connect(
                self.hass,
                f"{self._unique_id}_{CONNECTION_STATUS}",
                self._update_connection_state,
            ),
        ]

    async def _update_battery_charging(self, data: BatteryState) -> None:
        """Update binary sensor."""
        self._battery = data
        self._attr_is_on = self._battery.is_charging

        self.async_write_ha_state()


class BangOlufsenBinarySensorProximity(BangOlufsenBinarySensor):
    """Proximity Binary Sensor."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Init the proximity Binary Sensor."""
        super().__init__(entry)

        self._attr_name = f"{self._name} proximity"
        self._attr_unique_id = f"{self._unique_id}-proximity"
        self._attr_icon = "mdi:account-question"
        self._attr_device_class = "proximity"
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Turn on the dispatchers."""
        self._dispatchers = [
            async_dispatcher_connect(
                self.hass,
                f"{self._unique_id}_{WebSocketNotification.PROXIMITY}",
                self._update_proximity,
            ),
            async_dispatcher_connect(
                self.hass,
                f"{self._unique_id}_{CONNECTION_STATUS}",
                self._update_connection_state,
            ),
        ]

    async def _update_proximity(self, data: WebsocketNotificationTag) -> None:
        """Update binary sensor."""
        self._notification = data

        if self._notification.value == "proximityPresenceDetected":
            self._attr_is_on = True
        elif self._notification.value == "proximityPresenceNotDetected":
            self._attr_is_on = False

        self.async_write_ha_state()
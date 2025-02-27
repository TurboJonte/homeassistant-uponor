from homeassistant import config_entries
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import logging

from UponorJnap import UponorJnap

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME
)

from .const import (
    DOMAIN,
    SIGNAL_UPONOR_STATE_UPDATE,
    DEVICE_MANUFACTURER
)

_LOGGER = logging.getLogger(__name__)


class DomainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    def __init__(self):
        self._api_response = {}
        self._entry_data = {}

    @property
    def schema(self):
        return vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_NAME, default=DEVICE_MANUFACTURER): str,
            }
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            try:
                client = UponorJnap(user_input[CONF_HOST])
                self._api_response = await self.hass.async_add_executor_job(client.get_data)
            except Exception as e:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self.schema,
                    errors={"base": "invalid_host", "debug": repr(e)}
                )

            self._entry_data = user_input
            return self.async_show_form(
                step_id="rooms",
                data_schema=self.get_rooms_schema()
            )

        return self.async_show_form(step_id="user", data_schema=self.schema)

    async def async_step_rooms(self, user_input=None):
        """Handle 2nd step."""
        data = {**self._entry_data, **user_input}

        return self.async_create_entry(
            title="Uponor",
            data=data
        )

    def get_rooms_schema(self):
        rooms_schema = {}
        for t in self.get_active_thermostats():
            rooms_schema[vol.Optional(t.lower(), default=self.get_room_name(t))] = str
        return vol.Schema(rooms_schema)

    def get_active_thermostats(self):
        active = []
        for c in range(1, 5):
            var = 'sys_controller_' + str(c) + '_presence'
            if var in self._api_response and self._api_response[var] != "1":
                continue
            for i in range(1, 21):
                var = 'C' + str(c) + '_thermostat_' + str(i) + '_presence'
                if var in self._api_response and self._api_response[var] == "1":
                    active.append('C' + str(c) + '_T' + str(i))
        return active

    def get_room_name(self, thermostat):
        var = 'cust_' + thermostat + '_name'
        if var in self._api_response:
            return self._api_response[var]
        return thermostat

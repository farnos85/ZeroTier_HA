"""Platform for ZeroTier connection"""
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.components.binary_sensor import PLATFORM_SCHEMA
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from datetime import timedelta
from datetime import datetime
import logging
import requests as r
import json

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ZeroTier"

CONF_NETWORK = "network"
CONF_TOKEN = "token"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NETWORK): cv.string,
    vol.Required(CONF_TOKEN): cv.string
})

scan_interval = timedelta(minutes=1)

url = "https://my.zerotier.com/api/v1"

def get_members(config):
    network = config.get(CONF_NETWORK)
    header = {"Authorization": f"Bearer {config.get(CONF_TOKEN)}"}
    _url = f"{url}/network/{network}/member"
    try:
        resp = r.get(_url, headers = header)
    except:
        _LOGGER.error("Errore di connessione")
        return None
    else:
        if resp.status_code == 200:
            members = resp.json()
            return members
        else:
            _LOGGER.error(f"Errore di connessione: {resp.text}")
            return None

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    members = get_members(config)
    entities = []
    for member in members:
        zt = ZeroTier(hass, config, member["id"].split("-")[1])
        _LOGGER.info(f'Creato sensore {member["name"]}')
        entities.append(zt)
        async_track_time_interval(hass, zt._update, scan_interval)
    add_entities(entities)
    

class ZeroTier(Entity):
    """Representation of a Sensor."""

    def __init__(self, hass, config, member):
        """Initialize the sensor."""
        self.network = config.get(CONF_NETWORK)
        self.header = {"Authorization": f"Bearer {config.get(CONF_TOKEN)}"}
        self.member = member
        self.member_data = None
        self._attributes = None
        self._update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return f'ZT-{self.member_data["name"]}'
    
    @property
    def state(self):
        if self.member_data["online"]:
            #_LOGGER.info(f'Dispositivo {self.member_data["name"]} online')
            return "on"
        else:
            #_LOGGER.info(f'Dispositivo {self.member_data["name"]} offline')
            return "off"
    
    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self.member_data["online"]

    @property
    def device_class(self):
        return "connectivity"

    @property
    def unique_id(self):
        return self.member

    @property
    def icon(self):
        if self.member_data["online"]:
            return "mdi:lan-connect"
        else:
            return "mdi:lan-disconnect"
    
    def _update(self, now = None):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        _url = f"{url}/network/{self.network}/member/{self.member}"
        try:
            resp = r.get(_url, headers = self.header)
        except:
            _LOGGER.error("Errore di connessione")
        else:
            self.member_data = resp.json()
            _time = str(datetime.fromtimestamp(int((self.member_data["lastOnline"])/1000)))
            try:
                local_ip = self.member_data["config"]["ipAssignments"][0]
            except:
                _LOGGER.info(f'Local IP {self.member_data["name"]} non recuperato')
                local_ip = None
            attributes = {  "last_conn": _time,
                            "local_ip": local_ip,
                            "remote_ip": self.member_data["physicalAddress"]
                            }
            self._attributes = attributes
    
    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return self._attributes
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.components.binary_sensor import (
                                                    PLATFORM_SCHEMA,
                                                    DEVICE_CLASS_CONNECTIVITY,
                                                    SCAN_INTERVAL
                                                    )
from homeassistant.const import (
                                    CONF_API_TOKEN,
                                    STATE_ON,
                                    STATE_OFF,
                                    CONF_SCAN_INTERVAL
                                    )
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from datetime import datetime
import logging
import requests as r
import json

_LOGGER = logging.getLogger(__name__)

CONF_NETWORK = "network"

scan_interval = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NETWORK): cv.string,
    vol.Required(CONF_API_TOKEN): cv.string
    })

url = "https://my.zerotier.com/api/v1"

def get_members(config):
    network = config.get(CONF_NETWORK)
    header = {"Authorization": f"Bearer {config.get(CONF_API_TOKEN)}"}
    _url = f"{url}/network/{network}/member"
    try:
        resp = r.get(_url, headers = header)
    except:
        _LOGGER.error("Members list download - Connection error")
        return None
    else:
        if resp.status_code == 200:
            members = resp.json()
            return members
        else:
            _LOGGER.error(f"Members list download - Response: {resp.text}")
            return None

def setup_platform(hass, config, add_entities, discovery_info=None):
    members = get_members(config)
    entities = []
    for member in members:
        zt = ZeroTier(config, member["id"].split("-")[1])
        _LOGGER.info(f'Sensor {member["name"]} created')
        entities.append(zt)
        async_track_time_interval(hass, zt._update, scan_interval)
    add_entities(entities, True)
    

class ZeroTier(Entity):
    def __init__(self, config, member):
        self.network = config.get(CONF_NETWORK)
        self.header = {"Authorization": f"Bearer {config.get(CONF_API_TOKEN)}"}
        self.member = member
        self.member_data = None
        self._attributes = None
        self._update()

    @property
    def name(self):
        return f'ZT-{self.member_data["name"]}'
    
    @property
    def state(self):
        if self.member_data["online"]:
            return STATE_ON
        else:
            return STATE_OFF
    
    @property
    def is_on(self):
        return self.member_data["online"]

    @property
    def device_class(self):
        return DEVICE_CLASS_CONNECTIVITY

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
        _url = f"{url}/network/{self.network}/member/{self.member}"
        try:
            resp = r.get(_url, headers = self.header)
        except:
            _LOGGER.error("Fetching data: Connection error")
        else:
            if resp.status_code == 200:
                self.member_data = resp.json()
                _time = str(datetime.fromtimestamp(int((self.member_data["lastOnline"])/1000)))
                try:
                    local_ip = self.member_data["config"]["ipAssignments"][0]
                except:
                    _LOGGER.info(f'Local IP {self.member_data["name"]} unavailable')
                    local_ip = None
                attributes = {  "last_conn": _time,
                                "local_ip": local_ip,
                                "remote_ip": self.member_data["physicalAddress"]
                                }
            else:
                _LOGGER.error(f"Fetching data - Response: {resp.text}")
            self._attributes = attributes
    
    @property
    def extra_state_attributes(self):
        return self._attributes

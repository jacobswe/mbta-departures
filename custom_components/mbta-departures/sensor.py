from datetime import datetime, timezone, timedelta
import logging
import json
import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_PREDICTIONS = "predictions"
CONF_STATION = "station"
CONF_LINE = "line"
CONF_LIMIT = "limit"
CONF_DIRECTION = 'direction'
CONF_API_KEY = 'api_key'
CONF_LABEL = 'label'

metadata = {}

SCAN_INTERVAL = timedelta(seconds=5)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_PREDICTIONS): [
            {
                vol.Required(CONF_STATION): cv.string,
                vol.Required(CONF_LINE): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_LABEL): cv.string,
                vol.Optional(CONF_NAME): cv.string,
                vol.Optional(CONF_DIRECTION, default=0): cv.positive_int,
                vol.Optional(CONF_LIMIT, default=5): cv.positive_int
            }
        ]
    }
)


# noinspection PyUnusedLocal,SpellCheckingInspection
def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the MBTA sensor"""
    gen_metadata()

    sensors = []
    for next_train in config.get(CONF_PREDICTIONS):
        station = next_train.get(CONF_STATION)
        line = next_train.get(CONF_LINE)
        limit = next_train.get(CONF_LIMIT)
        name = next_train.get(CONF_NAME)
        direction = next_train.get(CONF_DIRECTION)
        api_key = next_train.get(CONF_API_KEY)
        label = next_train.get(CONF_LABEL)

        sensors.append(MBTADeparture(station, line, direction, limit, api_key, label, name))
    add_entities(sensors, True)

def gen_metadata():
    global metadata
    res = requests.get("https://api-v3.mbta.com/routes?include=stop")
    res.raise_for_status()
    res_json = res.json()
    for route in res_json['data']:
        metadata[route['id']] = {
            'color': route['attributes']['color']
        }


class MBTADeparture(Entity):
    """Implementation of an MBTA departure sensor"""

    def __init__(self, station, line, direction, limit, api_key, label, name):
        """Initialize the sensor"""
        self._station = station
        self._line = line
        self._limit = limit
        self._direction = direction
        self._label = label
        self._name = name if name else f"mbta_{self._station}_{self._line}".replace(' ', '_')
        self._arrivals = []
        self._alerts = []
        self._api_key = api_key

        self._station_params = station_params = {
            'pred_params': {
                "filter[route]": self._line,
                "filter[stop]": self._station,
                "filter[direction_id]": self._direction,
                "api_key": self._api_key},
            'alert_params': {
                "filter[route]": self._line,
                "filter[stop]": self._station,
                "api_key": self._api_key}
        }

    @property
    def name(self):
        """Return the name of the sensor"""
        return self._name

    @property
    def state(self):
        """Return the next arrival time"""
        if len(self._arrivals) == 0:
            logging.debug("No valid predictions, returning empty list")
            return "No Trains Departing Soon"
        else:
            return self._arrivals[0]

    @property
    def device_state_attributes(self):
        """Return the state attributes """
        logging.debug("returing attributes")
        return {
            "station": self._station,
            "upcoming_departures": self._arrivals[1:self._limit],
            "label": self._label.replace('_', ' '),
            "line": self._line,
            "alerts": self._alerts,
            "direction": self._direction,
            "color": metadata[self._line]['color']
        }

    def get_alerts_string_list(self):
        response = requests.get("https://api-v3.mbta.com/alerts", params=self._station_params['alert_params'])
        response_json = json.loads(response.text)

        alert_list = []
        for alert in response_json["data"]:
            alert_list.append(alert["attributes"]["header"])
        return alert_list

    def get_predictions_json(self):
        response = requests.get("https://api-v3.mbta.com/predictions", params=self._station_params['pred_params'])
        if response and response.status_code == 200:
            response_json = json.loads(response.text)
            return response_json
        else:
            return {}

    def update(self):
        """Get the latest data and update the state."""
        try:
            response_json = self.get_predictions_json()
            alert_list = self.get_alerts_string_list()

            arrivals = []
            current_time = datetime.now()
            for prediction in response_json["data"][:self._limit]:
                arrival_time = datetime.strptime(prediction["attributes"]["arrival_time"][:-6],
                                                          '%Y-%m-%dT%H:%M:%S')
                seconds_till_arrival = (arrival_time - current_time).total_seconds()
                if seconds_till_arrival > 0:
                    arrivals.append(arrival_time.strftime("%H:%M") + " Arrival in " + str(
                        int(seconds_till_arrival // 60)) + "m" + str(round(seconds_till_arrival % 60)) + "s")

            alerts = []
            for alert in alert_list:
                alerts.append(alert)

            self._arrivals = arrivals
            self._alerts = alerts

        except Exception as e:
            logging.exception(f"Encountered Exception: {e}")

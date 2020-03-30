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
stopnames = {}

SCAN_INTERVAL = timedelta(seconds=8)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_PREDICTIONS): [
            {
                vol.Required(CONF_STATION): cv.string,
                vol.Required(CONF_LINE): cv.string,
                vol.Optional(CONF_LABEL): cv.string,
                vol.Optional(CONF_NAME): cv.string,
                vol.Optional(CONF_DIRECTION, default=0): cv.positive_int,
                vol.Optional(CONF_LIMIT, default=5): cv.positive_int
            }
        ],
        vol.Required(CONF_API_KEY): cv.string
    }
)


# noinspection PyUnusedLocal,SpellCheckingInspection
def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the MBTA sensor"""
    gen_metadata()

    sensors = []
    api_key = config.get(CONF_API_KEY)
    for next_train in config.get(CONF_PREDICTIONS):
        station = next_train.get(CONF_STATION)
        line = next_train.get(CONF_LINE)
        limit = next_train.get(CONF_LIMIT)
        name = next_train.get(CONF_NAME)
        direction = next_train.get(CONF_DIRECTION)
        label = next_train.get(CONF_LABEL)

        sensors.append(MBTADeparture(station, line, direction, limit, api_key, label, name))
    add_entities(sensors, True)

def gen_metadata():
    global metadata
    res = requests.get("https://api-v3.mbta.com/routes")
    res.raise_for_status()
    res_json = res.json()
    for route in res_json['data']:
        metadata[route['id']] = {
            'color': route['attributes']['color'],
            'destinations': route['attributes']['direction_destinations'],
            'directions': route['attributes']['direction_names'],
            'long_name': route['attributes']['long_name']
        }

    global stopnames
    res = requests.get("https://api-v3.mbta.com/stops")
    res.raise_for_status()
    res_json = res.json()
    for stop in res_json['data']:
        stopnames[stop['id']] = stop['attributes']['name']



class MBTADeparture(Entity):
    """Implementation of an MBTA departure sensor"""

    def __init__(self, station, line, direction, limit, api_key, label, name):
        """Initialize the sensor"""
        self._station = station
        self._line = line
        self._limit = limit
        self._direction = direction

        self._label = label if label else f"""
                     {metadata[self._line]['long_name']} to
                     {metadata[self._line]['destinations'][self._direction]}"""
        self._name = name.replace(' ', '_').lower() if name else f"mbta_{self._station}_{self._direction}"

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
            "station": stopnames[self._station],
            "upcoming_departures": self._arrivals[:self._limit],
            "label": self._label.replace('_', ' '),
            "line": metadata[self._line]['long_name'],
            "direction": metadata[self._line]['destinations'][self._direction],
            "color": metadata[self._line]['color'],
            "alerts": self._alerts if len(self._alerts)>0 else ['No Alerts']
        }

    def get_alerts_string_list(self):
        response = requests.get("https://api-v3.mbta.com/alerts", params=self._station_params['alert_params'])
        response_json = json.loads(response.text)

        if response and response.status_code == 200:
            alert_list = []
            for alert in response_json["data"]:
                alert_list.append(alert["attributes"]["header"])
            return alert_list
        else:
            return []

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
            preds_json = self.get_predictions_json()
            alert_list = self.get_alerts_string_list()

            current_time = datetime.now()

            preds = []

            for prediction in preds_json["data"]:
                arrival_time = datetime.strptime(prediction["attributes"]["arrival_time"][:-6],
                                                 '%Y-%m-%dT%H:%M:%S')
                departure_time = datetime.strptime(prediction["attributes"]["departure_time"][:-6],
                                                   '%Y-%m-%dT%H:%M:%S')
                seconds_till_departure = (departure_time - current_time).total_seconds()
                seconds_till_arrival = (arrival_time - current_time).total_seconds()
                if seconds_till_departure > 0:
                    preds.append({'Arrival':arrival_time.strftime("%H:%M:%S"),
                                  'Departure':departure_time.strftime('%H:%M:%S'),
                                  'Until': str(int(seconds_till_departure // 60)) +
                                           "m" + str(round(seconds_till_departure % 60)) +
                                           "s",
                                  'Is Boarding': seconds_till_arrival<0})

            alerts = []
            for alert in alert_list:
                alerts.append(alert)

            self._arrivals = list({a['Until']:a for a in preds}.values())
            self._alerts = alerts

            return preds

        except Exception as e:
            logging.exception(f"Encountered Exception: {e}")

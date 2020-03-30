# mbta-departures
A Home Assistant custom component and lovelace card to fetch and display the next departures of MBTA trains, busses, and rail lines.

## Installation
Within the custom_components folder, there is a folder named mbta_departures. This must be placed in the custom_components folder of your Home Assistant integration. This will allow you to create sensors that report back the upcoming departures for the stations you configure.

## Configuration
To enable this sensor, add the following example lines to your `configuration.yaml` file:

```yaml
sensor:
  - platform: mbta-departures
    api_key: API_KEY
    predictions:
      - station: place-haecl
        line: Green-C
      - station: place-armnl
        line: Green-E
        label: A Custom Label
        direction: 1
        name: id_in_homeassistant
        api_key: ebeea428c6a44b41b067e4b452efb44f
```

### Configuration Variables
#### api_key
> (string) (Required) the API key given to you by the [mbta api site](https://api-v3.mbta.com/)
#### prediction
> (list) (Required) list of sensors to be created
  #### station
  > (string) (Required) the MBTA name of your station. See [mbta stops](https://mbta.com/stops). See also [stops.csv](https://github.com/jacobswe/mbta-departures/blob/master/reference/stops.csv) for the full list of available stops.
  #### line
  > (string) (Required) the `route_id` of the line you are using (e.g. `Green-C`). See [routes.csv](https://github.com/jacobswe/mbta-departures/blob/master/reference/routes.csv) for the full list of available lines.
  #### label
  > (string) (Required) A label to display in place of the LINE to TERIMINAL STATION.
  #### name
  > (string) (Optional) the name of the sensor (default: "mbta_STATION_LINE_DIRECTION")
  #### limit
  > (int) (Optional) the maximum number of predictions to send back (default: `5`)
  #### direction
  > (int) (Optional) the direction of the train `0` or `1` (default: `0`)

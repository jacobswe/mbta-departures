# mbta-departures
A Home Assistant custom component and lovelace card to fetch and display the next departures of MBTA trains, busses, and rail lines.

## Installation
Within the custom_components folder, there is a folder named mbta_departures. This must be placed in the custom_components folder of your Home Assistant integration. This will allow you to create sensors that report back the upcoming departures for the stations you configure.

## Configuration
To enable this sensor, add the following example lines to your `configuration.yaml` file:

```yaml
sensor:
  - platform: mbta-departures
    predictions:
      - station: place-haecl
        line: Green-C
        name: Haymarket_C_West
        direction: 0
        friendly_name: "Haymarket C to Clevland Circle"
        api_key: ebeea428c6a44b41b067e4b452efb44f
      - station: place-armnl
        line: Green-C
        name: Arlington_C_East
        direction: 1
        friendly_name: "Arlington C to North Station"
        api_key: ebeea428c6a44b41b067e4b452efb44f
```

### Configuration Variables
#### station
> (string) (Required) the MBTA name of your station. See [mbta stops](https://mbta.com/stops) for a full list of available station names. Click into the station you would like to configure, then navigate to the URL. For example [this](https://www.mbta.com/stops/place-asmnl) would be input as `place-asmnl`.
#### line
> (string) (Required) the `route_id` of the line you are using (e.g. `Green-C`). See [routes.csv](https://github.com/jacobswe/mbta-departures/blob/master/Stations/routes.csv) for the full list of available lines.
#### friendly_name
> (string) (Required) the name to display.
#### name
> (string) (Optional) the name of the sensor (default: "mbta_STATION_LINE")
#### limit
> (int) (Optional) the maximum number of predictions to send back (default: `5`)
#### direction
> (int) (Optional) the direction of the train `0` or `1` (default: `0`)
#### api_key
> (string) (Required) the API key given to you by the [mbta api site](https://api-v3.mbta.com/).

## Inspirations and Thanks
I wanted a lightweight and robust departure board for the MBTA. The amazing work of [mbta_predictions](https://github.com/dhanani94/mbta_predictions) was a great starting place, and in tandem with a little help from friends in understanding and accessing the API, this component was able to come to be. Thanks to all!

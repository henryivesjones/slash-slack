from urllib.parse import quote

import requests

from slash_slack import Flag, SlashSlack

slash = SlashSlack(
    dev=True, description="An example slack bot using the framework SlashSlack"
)
app = slash.get_fast_api()

_NL = "\n"


def convert_c_to_f(celsius: float):
    return (celsius * (1.8)) + 32.0


def _generate_day_forecast(
    date: str,
    temp_min: float,
    temp_max: float,
    real_feel_min: float,
    real_feel_max: float,
    sunrise: str,
    sunset: str,
    rain: float,
    shower: float,
    snowfall: float,
    precipitation_probability: float,
    celsius: bool,
):
    sunrise_time = sunrise.split("T")[-1]
    sunset_time = sunset.split("T")[-1]
    temp_unit = "C" if celsius else "F"
    length_unit = "cm" if celsius else '"'
    if not celsius:
        temp_min = convert_c_to_f(temp_min)
        temp_max = convert_c_to_f(temp_max)
        real_feel_min = convert_c_to_f(real_feel_min)
        real_feel_max = convert_c_to_f(real_feel_max)
        rain = rain * 0.0393701
        shower = shower * 0.0393701
        snowfall = snowfall * 10 * 0.0393701
    else:
        rain = rain / 10.0
        shower = shower / 10.0
    return f"""
> *{date}*
> :sunrise: {sunrise_time} :city_sunset: {sunset_time}
> Temp/Real-feel :arrow_up_small: {round(temp_max)}/{round(real_feel_max)}{temp_unit} :arrow_down_small: {round(temp_min)}/{round(real_feel_min)}{temp_unit}
> Precipitation: {round(precipitation_probability )}% | :rain_cloud: {round(rain + shower, 2)}{length_unit} :snow_cloud: {round(snowfall, 1)}{length_unit}
    """.strip()


@slash.command(
    "forecast",
    summary="Weather forecast.",
    help="Provides the forecast for the given location. Defaults to temperatures in F.",
)
def forecast(location: str, celsius=Flag(help="Use Celsius for temperatures.")):
    raw_location_data = requests.get(f"https://geocode.xyz/{quote(location)}?json=1")
    if not raw_location_data.ok:
        return "There was an issue with `geocode.xyz`. Please try again."
    location_data = raw_location_data.json()
    if "error" in location_data:
        return "There was a problem identifying the provided location."
    refined_location = f'{location_data["standard"]["city"]} | {location_data["standard"]["countryname"]}'
    latitude = location_data["latt"]
    longitude = location_data["longt"]

    raw_weather_data = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "auto",
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "sunrise",
                "sunset",
                "rain_sum",
                "showers_sum",
                "snowfall_sum",
                "precipitation_probability_mean",
            ],
        },
    )
    if not raw_weather_data.ok:
        return "There was an issue with `open-meteo.com`. Please try again."
    weather_data = raw_weather_data.json()
    daily = weather_data["daily"]
    forecast_blocks = []
    for index, date in enumerate(daily["time"]):
        forecast_blocks.append(
            _generate_day_forecast(
                date,
                daily["temperature_2m_min"][index],
                daily["temperature_2m_max"][index],
                daily["apparent_temperature_min"][index],
                daily["apparent_temperature_max"][index],
                daily["sunrise"][index],
                daily["sunset"][index],
                daily["rain_sum"][index],
                daily["showers_sum"][index],
                daily["snowfall_sum"][index],
                daily["precipitation_probability_mean"][index],
                celsius,
            )
        )
    _TEMPLATE = f"""
*7 day forecast for {refined_location}*
{(_NL * 2).join(forecast_blocks)}
    """.strip()

    return _TEMPLATE

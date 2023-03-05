import os
from typing import List

from slash_slack import Enum, Flag, Float, SlashSlack, String, UnknownLengthList

slash = SlashSlack(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    description="An example Slack slash command server.",
)
app = slash.get_fast_api()


@slash.command(
    "echo",
    summary="Echoes the input.",
    help="Echoes the input, modifying the content if specified.",
)
def echo(
    content: str = String(help="The content to be echoed."),
    upper=Flag(help="The response should be made UPPER CASE"),
    lower=Flag(help="The response should be made lower case"),
):
    if upper:
        return content.upper()
    if lower:
        return content.lower()
    return content


@slash.command(
    "agg",
    summary="Aggregates given values.",
    help="Aggregates the given values according to the specified aggregate function.",
)
def agg(
    fn: str = Enum(
        values={"avg", "sum", "count"}, help="The aggregate function to be used."
    ),
    nums: List[float] = UnknownLengthList(
        arg_type=Float(), help="The numbers to be aggregated."
    ),
    r: bool = Flag(help="Round the response to the nearest whole number."),
):
    if fn == "avg":
        v = sum(nums) / len(nums)
    elif fn == "sum":
        v = sum(nums)
    else:
        v = len(nums)

    if r:
        return round(v)
    return v


from urllib.parse import quote

import requests


def get_location(location: str):
    raw_location_data = requests.get(f"https://geocode.xyz/{quote(location)}?json=1")
    if not raw_location_data.ok:
        return (
            None,
            None,
            None,
            "There was an issue with `geocode.xyz`. Please try again.",
        )
    location_data = raw_location_data.json()
    if "error" in location_data:
        return (
            None,
            None,
            None,
            "There was a problem identifying the provided location.",
        )
    refined_location = f'{location_data["standard"]["city"]} | {location_data["standard"]["countryname"]}'
    latitude = location_data["latt"]
    longitude = location_data["longt"]
    return latitude, longitude, refined_location, None


def get_forecast(latitude: float, longitude: float):
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
        return None, "There was an issue with `open-meteo.com`. Please try again."
    weather_data = raw_weather_data.json()
    daily = weather_data["daily"]
    return daily, None


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
):
    sunrise_time = sunrise.split("T")[-1]
    sunset_time = sunset.split("T")[-1]
    return f"""
> *{date}*
> :sunrise: {sunrise_time} :city_sunset: {sunset_time}
> Temp/Real-feel :arrow_up_small: {round(temp_max)}/{round(real_feel_max)}C :arrow_down_small: {round(temp_min)}/{round(real_feel_min)}C
> Precipitation: {round(precipitation_probability )}% | :rain_cloud: {round(rain + shower, 2)}mm :snow_cloud: {round(snowfall, 1)}cm
    """.strip()


@slash.command("forecast")
def forecast(location: str):
    latitude, longitude, location_description, err = get_location(location)
    if err is not None or latitude is None or longitude is None:
        return err
    daily, err = get_forecast(latitude, longitude)
    if err is not None or daily is None:
        return err

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
            )
        )

    joined_blocks = "\n\n".join(forecast_blocks)
    return f"""
*7 day forecast for {location_description}*
{joined_blocks}
    """.strip()

# How to create a Slack slash command bot using python.
In this article I will go over how to make a python Slack slash command bot, connect it to your slack workspace, and deploy it using Heroku.

I will split this article up into two sections: building/testing the bot locally using the `slash-slack` framework and deploying/integrating the bot with your slack workspace.

# slash-slack framework
When a Slack slash-command is executed Slack sends a `POST` request to the configured endpoint with the content, channel, user, etc... as the payload.
`slash-slack` is a python framework for building a web-server that listens for, parses, routes, and responds to  Slack slash command requests. In addition it will generate help dialogs based on your code.
In order to expedite development `slash-slack` comes bundled with a `mock-slack` tool which can be used to mock Slack slash command payloads for your app.

# Echo Command
Lets get started with the `slash-slack` framework... Start by creating a new project directory. In that directory create a `main.py` file.

Next install the `slash-slack` package using `pip install slash-slack`.

There are two lines of code that MUST be in every `slash-slack` based app. The first is the `SlashSlack` object which we have to instantiate, the second is the underlying `FastAPI` object which we must expose so that it can be imported by the ASGI server (EX: `uvicorn`).

For our development purposes we are going to set `dev=True` for the `SlashSlack` object to disable signature verification.
```python
from slash_slack import SlashSlack

slash = SlashSlack(dev=True)
app = slash.get_fast_api()
```
Now lets make our first slash command. To get comfortable we will implement an `echo` command, which will respond with whatever was passed in. We will add `--upper` and `--lower` flags to indicate that we should respond with the input upper/lower cased.

In order to tell `slash-slack` what inputs we expect from the user we simple define parameters for the decorated function. In this case we have one `string` parameter, and two `flag` parameters. When there is only one non-flag parameter and that parameter is a `string`, `slash-slack` knows that it should pass the entire input to the function instead of parsing out each word in the input to each function parameter.
```python
from slash_slack import SlashSlack, Flag

slash = SlashSlack(dev=True)
app = slash.get_fast_api()

@slash.command("echo")
def echo(content: str, upper = Flag(), lower = Flag()):
    if upper:
        return content.upper()
    if lower:
        return content.lower()
    return content
```
Now that we have a command setup, we can test it out by running the `slash-slack` server locally, and utilizing the `mock-slack` tool.

To run the server locally we will utilize `uvicorn`. Install using `pip install uvicorn`.

From the terminal we can start the server and serve it on port `9002`:
```bash
uvicorn main:app --port 9002 --reload
```
If the server is running you should see:
```bash
INFO:     Uvicorn running on http://127.0.0.1:9002 (Press CTRL+C to quit)
INFO:     Started reloader process [45640] using StatReload
INFO:     Started server process [45642]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```
Now that the server is running, we can send mock requests to it using `mock-slack`.

In a different terminal, run the command `mock-slack`. You will be prompted by `MSG: ` to send a mock message to the server we just started. When using `mock-slack` you don't need to include the `/slash_command` portion of the request.

To test our echo command enter `echo hello world --upper` and then hit return. On the `uvicorn` server you should see the `POST` request. `mock-slack` will open your web browser with the response loaded into the [Slack Block Kit builder](https://app.slack.com/block-kit-builder/#%7B%22blocks%22:%5B%7B%22type%22:%22section%22,%22text%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22HELLO%20WORLD%22%7D%7D%5D%7D). AFAIK this is the only way to view how slack block kit will be rendered.

![Slack Block Kit Builder](https://github.com/henryivesjones/slash-slack/blob/main/how_to/images/hello_world_echo_upper.png?raw=true)

# Agg command
To get better acquainted with the `slash-slack` input parsing we will implement a command with a more complicated input structure.

This command will take the form: `agg {function} num1, num2, etc...`. To do this we will have to use `Enum` and `UnknownLengthList` input arg types. `Enum` parses the value and confirms that it is part of a pre-defined list of possible values. `UnknownLengthList` parses the rest of the input and returns a list of the predefined type, this allows an arbitrary amount of elements to be passed/parsed by the command.

```python
from typing import List
from slash_slack import SlashSlack, Enum, UnknownLengthList, Flag

slash = SlashSlack(dev=True)
app = slash.get_fast_api()

@slash.command("agg")
def agg(
    fn: str = Enum(values={"avg", "sum", "count"}),
    nums: List[float] = UnknownLengthList(arg_type=Float()),
    r: bool = Flag()
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
```
Now we can test out this command using `mock-slack`. Run `agg sum 1 2 3 4`, you should see:
![Slack Block Kit Builder](https://github.com/henryivesjones/slash-slack/blob/main/how_to/images/agg_sum_1_2_3_4.png?raw=true)
# Help dialog
Now that we have built two commands, we can look at the built in help dialog. Then we will enhance the help dialog by adding in metadata to the commands and arguments.

To view the global app help dialog run the command `help` or `--help`:
![Slack Block Kit Builder](https://github.com/henryivesjones/slash-slack/blob/main/how_to/images/global_help_bare.png?raw=true)

To view the help for a specific command run the command `echo --help` or `agg --help`:
![Slack Block Kit Builder](https://github.com/henryivesjones/slash-slack/blob/main/how_to/images/echo_help_bare.png?raw=true)
![Slack Block Kit Builder](https://github.com/henryivesjones/slash-slack/blob/main/how_to/images/agg_help_bare.png?raw=true)

Theses help dialogs already give us a lot information, however we can augment this by adding metadata to the command decorator and arguments:

```python
from typing import List
from slash_slack import SlashSlack, Enum, UnknownLengthList, Flag, String

slash = SlashSlack(dev=True, description="An example Slack slash command server.")
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

```
Now request the different help dialogs and see how this metadata is added.

![Slack Block Kit Builder](https://github.com/henryivesjones/slash-slack/blob/main/how_to/images/global_help.png?raw=true)

![Slack Block Kit Builder](https://github.com/henryivesjones/slash-slack/blob/main/how_to/images/echo_help.png?raw=true)

![Slack Block Kit Builder](https://github.com/henryivesjones/slash-slack/blob/main/how_to/images/agg_help.png?raw=true)

# Weather forecast
Now that we have a better handle on creating slash commands, lets take it up a notch and make a command that has to reach out the internet to get data.

We will build a forecast command which will take in a text input such as `boston mass` and will return the 7 day forecast.

To do this we will utilize the free and open API `open-meteo.com`. This api takes in latitude and longitude, so we will first need to convert the location given by the user into latitude and longitude.

To do this we will use the free and open API `geocode.xyz` which can take in our string `boston mass` and return the latitude and longitude.

To get started lets first understand how the [`geocode.xyz` API](https://geocode.xyz/api) works. Let's use `curl` and `jq` to view the api response. (If you get a throttling response, wait and try again.)
```bash
curl 'https://geocode.xyz/boston%20mass?json=1' | jq
```
```json
{
  "standard": {
    "addresst": {},
    "statename": {},
    "city": "Boston",
    "prov": "US",
    "countryname": "United States of America",
    "postal": {},
    "confidence": "0.266666666666667"
  },
  "longt": "-71.08913",
  "alt": {},
  "elevation": {},
  "latt": "42.32050"
}
```
All of the information we need (latitude and longitude) is right there in the response. Now lets see how the [`open-meteo.com` API](https://open-meteo.com/en/docs) works.
```bash
curl 'https://api.open-meteo.com/v1/forecast?latitude=42.32050&longitude=-71.08913&timezone=auto&daily=temperature_2m_max&daily=precipitation_probability_mean' | jq
```
```json
{
  "latitude": 42.31353,
  "longitude": -71.08243,
  "generationtime_ms": 3.103017807006836,
  "utc_offset_seconds": -18000,
  "timezone": "America/New_York",
  "timezone_abbreviation": "EST",
  "elevation": 31,
  "daily_units": {
    "time": "iso8601",
    "temperature_2m_max": "°C",
    "precipitation_probability_mean": "%"
  },
  "daily": {
    "time": [
      "2023-03-05",
      "2023-03-06",
      "2023-03-07",
      "2023-03-08",
      "2023-03-09",
      "2023-03-10",
      "2023-03-11"
    ],
    "temperature_2m_max": [
      5.4,
      5,
      2.2,
      6.4,
      6.5,
      8.3,
      4.7
    ],
    "precipitation_probability_mean": [
      2,
      0,
      6,
      3,
      13,
      2,
      48
    ]
  }
}
```
Now that we can see the responses from these two API's we can utilize them within the `slash-slack` framework.

First let's set up the command and command function:
```python
@slash.command("forecast")
def forecast(location: str):
    pass
```

Now, lets define a function that will use the `geocode.xyz` API to return the latitude, longitude, and name of the given place.
```python
from urllib.parse import quote
import requests

def get_location(location: str):
    raw_location_data = requests.get(f"https://geocode.xyz/{quote(location)}?json=1")
    if not raw_location_data.ok:
        return None, None, None, "There was an issue with `geocode.xyz`. Please try again."
    location_data = raw_location_data.json()
    if "error" in location_data:
        return None, None, None, "There was a problem identifying the provided location."
    refined_location = f'{location_data["standard"]["city"]} | {location_data["standard"]["countryname"]}'
    latitude = location_data["latt"]
    longitude = location_data["longt"]
    return latitude, longitude, refined_location, None
```

Next, lets define a function that will use the `open-meteo.com` API to get the forecast for a given latitude and longitude.
```python
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
```

Now that we can get the forecast data we can define a function that will render the forecast for a given day.

```python
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
```

Now we can string all of this together into the command function.

```python
@slash.command("forecast")
def forecast(location: str):
    latitude, longitude, location_description, err = get_location(location)
    if err is not None:
        return err
    daily, err = get_forecast(latitude, longitude)
    if err is not None:
        return err

    forecast_blocks = []
    for index, date in enumerate(daily['time']):
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
```
With everything put together you should be able to use the command using `mock-slack`. EX: `forecast boston mass`:
![Boston Mass Forecast](https://github.com/henryivesjones/slash-slack/blob/main/how_to/images/forecast_boston_mass.png?raw=true)

Now with the bot complete we can move onto deployment. To enable signature verification we will set up the app to retrieve the `SLACK_SIGNING_SECRET` variable from the environment and pass it into the `SlashSlack` object.
```python
slash = SlashSlack(signing_secret=os.environ['SLACK_SIGNING_SECRET'], description="An example Slack slash command server.")
```

# Deployment
There are going to be five steps to deploy and integrate this app.

1. Create deployment container.
2. Create Slack App.
3. Create Heroku App.
4. Create slash command integration within Slack App.
5. Distribute the Slack app in your workspace.

## Create deployment container.
If you are familiar with Docker, then this will be straightforward. We will need to create some extra files alongside our `main.py` file:

### requirements.txt
```
slash-slack==0.1.4
requests==2.28.2
uvicorn==0.20.0
```
### Dockerfile
```
FROM python:3.9.16-slim-bullseye

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY startup.sh startup.sh
COPY main.py main.py

CMD ["./startup.sh"]
```

### startup.sh
You will need to make this file executable: `chmod +x startup.sh`
```
#!/bin/bash
uvicorn main:app --port $PORT --host 0.0.0.0
```

To verify that everything is working as intended run
```bash
docker build . -t slash-slack:latest
docker run --env PORT=9002 slash-slack:latest
```
You should see:
```
INFO:     Started server process [7]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9002 (Press CTRL+C to quit)
```

Now that we have the container build and running, we can create the Slack App.
## Create Slack App
1. Navigate to [the slack apps page](https://api.slack.com/apps/) and click on `Create New App`.
2. Select the `From Scratch` option.
3. Enter in an app name and select the workspace that you want to develop your app in.

You should now be on the app `Basic Information` page:
![Slack Basic Information](https://github.com/henryivesjones/slash-slack/blob/main/how_to/images/basic_app_info.png?raw=true)

Reveal and copy the `Signing Secret` located in the `App Credentials` section.

## Create Heroku App
In a new tab navigate to the [Heroku New App page](https://dashboard.heroku.com/new-app). Create an account if you don't already have one. Enter in an app name and press `Create App`.

Before we upload and deploy our container to this Heroku app, we need to set the `SLACK_SIGNING_SECRET` environment variable.

Navigate to the app settings page and press `Reveal config vars`. Add a config var with the key `SLACK_SIGNING_SECRET` and value the signing secret you copied from the Slack `App Credentials` section.

Now we are ready to upload and deploy our container to our Heroku app. To do this we will utilize the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).

```
heroku login
heroku container:login
heroku container:push web -a heroku-app-name
heroku container:release web -a heroku-app-name
```
We can confirm that our `slash-slack` server is running by viewing the container logs:
```
heroku logs --tail -a heroku-app-name
```
```
2023-03-05T21:17:13.636623+00:00 heroku[web.1]: Starting process with command `./startup.sh`
2023-03-05T21:17:16.055350+00:00 app[web.1]: INFO:     Started server process [4]
2023-03-05T21:17:16.055507+00:00 app[web.1]: INFO:     Waiting for application startup.
2023-03-05T21:17:16.056016+00:00 app[web.1]: INFO:     Application startup complete.
2023-03-05T21:17:16.056843+00:00 app[web.1]: INFO:     Uvicorn running on http://0.0.0.0:23636 (Press CTRL+C to quit)
2023-03-05T21:17:16.118923+00:00 heroku[web.1]: State changed from starting to up
```

Now that our app is running, we can get the address where it is running from the heroku CLI:
```
heroku domains -a heroku-app-name
```
## Create the slash command
Go back to the Slack `Basic Information` page and click on `Slash Commands`. On the slash commands page click `Create New Command`. This is where you will define the command and the Request URL.

For the command use `/slash-slack`.

For the Request URL put: `https://heroku-app-name.herokuapp.com/slash_slack`

For the usage hint I recommend putting `help` so that users know what to run in order to get detailed help.

Lastly hit `Save`.

The last thing we need to do is install that app in your workspace.

## Distribute the Slack App.
From the Slack App page, navigate to the `Install App` section located on the sidebar.

Press the `Install to Workspace` button. On the next page press allow.

**Congratulations** your first Slack slash command can now be used. Invoke it from any channel or DM `/slash-slack forecast boston mass`

# Complete app
```python
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
```

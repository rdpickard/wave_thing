"""
A RESTful gateway for the NOAA National Data Buoy Center API. The gateway transforms tabular data from
the NOAA API into JSON or XML encoded objects.
"""

import requests
import arrow
import flask
import flask_restful
from src.json2xml import Json2xml

import json
import xml.etree.ElementTree as ET

__author__ = "Robert Daniel Pickard"
__copyright__ = "None"
__credits__ = ["Robert Daniel Pickard"]
__license__ = "MIT License"
__version__ = ".1"
__maintainer__ = "Robert Daniel Pickard"
__email__ = "codez@chalkfarm.org"
__status__ = "Caveat Emptor"

application = flask.Flask(__name__)
api = flask_restful.Api(application)

noaa_buoy_url = "http://www.ndbc.noaa.gov/data/realtime2/{buoyid}.{data_type}"
noaa_stations_url = "https://www.ndbc.noaa.gov/activestations.xml"


def not_implemented(timestamp, line_data):
    """
    For data sets that haven't been implemented yet in wave thing, return a 501 message to the 
    client.
    
    :param timestamp: There to keep consistancy with whatever_response_to_data_points functions but ignored
    :param line_data: There to keep consistancy with whatever_response_to_data_points functions but ignored

    :return: Nothing. The Flask framework handles getting the 501 to the HTTP client
    """
    flask.abort(501)


def timestamp_from_noaa_format_and_normalize_for_missing_data(line_data):
    """
    All NOAA buoy response lines start with a 5 elements for the timestamp and encode missing values
    as 'MM'. This function extracts the timestamp and maps 'MM' to None to be more RESTful
    
    :param line_data: A single line of a response from the NOAA API
    :return: The timestamp of the line as an arrow object and a mapped set of values that replaces
    missing data 'MM' notation with None
    """
    # Change the date parts into a time stamp
    timestamp = arrow.get("{year}-{month}-{day} {hour}:{min}".format(year=line_data[0],
                                                                     month=line_data[1],
                                                                     day=line_data[2],
                                                                     hour=line_data[3],
                                                                     min=line_data[4]))

    # Convert the strings that should be numbers into floats. If a value is missing the
    # NOAA API returns "MM" as a value. Change these to 'crap' which will later be convered
    # in None values.
    # The intermediate 'crap' step is needed because None evaluates to False in python so
    # that will throw off the mapping function
    line_data[5:] = list(map(
        lambda v: v == "MM" and "crap" or v.replace(".", "").replace("-", "").replace("+", "").isnumeric() and float(
            v) or v, line_data[5:]))

    # Convert "crap" place holders in None values
    i = 0
    for line_element in line_data.copy():
        if line_element == "crap":
            line_data[i] = None
        i += 1

    return timestamp, line_data


def spectral_data_remap_samples(samples):
    """
    The NOAA API has 5 different spectral data sets that have different meaning but are encoded
    in a similar way. This function parses the data lines for each of the spectral data set
    
    :param samples: An array of samples
    :return: A array of sample pair arrays
    """

    # need to re-map the data_spec values again because there is some mark up
    # where the wave direction in the denisity+direction pairs are inside of a parentheses
    # '0.000', '(0.033)', '0.000', '(0.038)', '0.000', '(0.043)' ...
    # This makes all values into floats

    samples = list(map(lambda v: float(str(v).replace("(", "").replace(")", "")), samples))
    return list(zip(*[samples[i::2] for i in range(2)]))


def data_spec_response_to_data_points(timestamp, line_data):
    data_point = {"utc_timestamp": str(timestamp),
                  "seperation_frequency": line_data[5],
                  "sample_pairs": spectral_data_remap_samples(line_data[6:])}

    return data_point


def spec_response_to_data_points(timestamp, line_data):
    return {"utc_timestamp": str(timestamp),
            "significant_wave_height": line_data[5],
            "swell_height": line_data[6],
            "swell_period": line_data[7],
            "wind_wave_height": line_data[8],
            "wind_wave_period": line_data[9],
            "swell_direction": line_data[10],
            "wind_wave_direction": line_data[11],
            "wind_steepness": line_data[12],
            "average_wave_period": line_data[13],
            "dominant_wave_agerage_direction": line_data[14]
            }


def cwind_response_to_data_points(timestamp, line_data):
    return {"utc_timestamp": str(timestamp),
            "ten_minute_average_wind_direction": line_data[5],
            "ten_minute_average_wind_speed": line_data[6],
            "ten_minute_average_wind_gust_direction": line_data[7],
            "wind_gust_hourly_peak": line_data[8],
            "wind_gust_hourly_peak_time": line_data[9]
            }


def drift_response_to_data_points(timestamp, line_data):
    return {"utc_timestamp": str(timestamp),
            "heat": line_data[5],
            "ice": line_data[6],
            "wind_speed_ten_meter_delta": line_data[7],
            "wind_speed_twenty_meter_delta": line_data[8]
            }


def txt_response_to_data_points(timestamp, line_data):
    data_point = {"utc_timestamp": str(timestamp),
                  "wind_direction": line_data[5],
                  "wind_speed": line_data[6],
                  "wind_speed_gust": line_data[7],
                  "signifigant_wave_height": line_data[8],
                  "dominant_wave_period": line_data[9],
                  "average_wave_period": line_data[10],
                  "dominant_wave_direction": line_data[11],
                  "sea_level_pressure": line_data[12],
                  "air_temperature": line_data[13],
                  "surface_sea_temperature": line_data[14],
                  "dew_point_temperature": line_data[15],
                  "visibility": line_data[16],
                  "pressure_tendency": line_data[17],
                  "tide": line_data[18]}

    return data_point


# This is mapping from each of the data set types that NOAA supports to a decoding function that
# knows what each element signifies by it's position in a line of response from the NOAA API
noaa_data_sets = {"txt": txt_response_to_data_points,
                  "drift": drift_response_to_data_points,
                  "cwind": cwind_response_to_data_points,
                  "spec": spec_response_to_data_points,
                  "data_spec": data_spec_response_to_data_points,
                  "swdir": data_spec_response_to_data_points,
                  "swdir2": data_spec_response_to_data_points,
                  "swr1": data_spec_response_to_data_points,
                  "swr2": data_spec_response_to_data_points,
                  "adcp": not_implemented,
                  "ocean": not_implemented,
                  "tide": not_implemented}


def get_latest_stations_details_from_noaa():
    """
    Get the latest XML document of buoy descriptive information from NOAA.

    :return: XML as an ETree object or None if there was an error making the request
    """
    application.logger.debug("requesting station details")
    stations_request = requests.get(noaa_stations_url)

    if stations_request.status_code != 200:
        application.logger.warn("request for station details at url [{}] returned non-OK status code [{}]".format(
            noaa_stations_url, stations_request.status_code))
        return None

    try:
        d = ET.fromstring(stations_request.text)
        return d
    except Exception as e:
        application.logger.error("Could not parse station details XML /{}/".format(e))


def station_detail_by_id(station_id):
    """
    Filter the NOAA buoy details document for just the information of a specific buoy by the ID of that buoy.
    :param station_id: The buoy to filter on
    :return: An array of dictionaries, key being the detail name. Array will be empty if buoy ID is not in the the
    NOAA document.
    """
    stations_details = get_latest_stations_details_from_noaa()
    if stations_details is not None:
        station_elements = stations_details.findall('.//station[@id="{}"]'.format(station_id))
        return list(map(lambda s: s.attrib, station_elements))


class BuoyTalkResource(flask_restful.Resource):
    def get(self, buoy_id, buoy_data_type):

        # figure out the desired response format, json or XML
        response_mime = flask.request.accept_mimetypes.best_match(['application/json', 'application/xml'])

        if buoy_data_type not in noaa_data_sets:
            response = {"message": "Unsupported NOAA data set {buoy_data_type}".format(buoy_data_type=buoy_data_type)}
            if response_mime == 'application/xml':
                response_data = Json2xml(response).json2xml()
            else:
                response_data = json.dumps(response)
            return flask.Response(response_data, status=400, content_type=response_mime)

        buoy_request_url = noaa_buoy_url.format(buoyid=buoy_id, data_type=buoy_data_type)
        buoy_request = requests.get(buoy_request_url)

        if buoy_request.status_code == 404:
            # Pass through a 404 response from NOAA to the wave_thing client. This is how NOAA indicates
            # that a buoy does not have a data set
            return flask.Response("", status=404)
        elif buoy_request.status_code != 200:
            # The request to NOAA failed. Since this script didn't itself fail return a 502: bad gateway message
            response = {
                "message": "NOAA URL {noaa_url} returned response code {request_status_code}. Expecting 200".format(
                    noaa_url=buoy_request_url,
                    request_status_code=buoy_request.status_code),
                "upstream code": buoy_request.status_code
            }
            if response_mime == 'application/xml':
                response_data = Json2xml(response).json2xml()
            else:
                response_data = json.dumps(response)
            return flask.Response(response_data, status=502, content_type=response_mime)
        else:
            # request was good.
            buoy_response = {"buoy_id": buoy_id,
                             "data_type": buoy_data_type,
                             "data_points": [],
                             "request_timestamp_utc": str(arrow.now('utc')),
                             "details": None}

            details = station_detail_by_id(buoy_id)
            if len(details) > 1:
                application.logger.info("NOAA buoy details had more than one result for id [{}]. "
                                        "Taking first, ignoring the remainder".format(buoy_id))
            if len(details) >= 1:
                buoy_response["details"] = details[0]
            else:
                application.logger.info("NOAA had not details for buoy with id [{}]".format(buoy_id))

            # Ignore the comment lines that start with hash
            data_lines = filter(lambda line: not line.startswith("#"), buoy_request.text.splitlines())

            # Loop over the remaining lines and pass the content to the appropriate decoding function as
            # that is mapped to the data type string. IE data type 'txt' -> txt_response_to_data_points
            for data_line in data_lines:
                buoy_response["data_points"].append(
                    noaa_data_sets[buoy_data_type](
                        *timestamp_from_noaa_format_and_normalize_for_missing_data(data_line.split()))
                )

            if response_mime == 'application/xml':
                response_data = Json2xml(buoy_response).json2xml()
            else:
                response_data = json.dumps(buoy_response)
            return flask.Response(response_data, status=200, content_type=response_mime)


@application.route('/')
def index():
    """
    Renders the 'index' page
    :return: 
    """
    return flask.render_template('index.jinja2', my_server=flask.request.url_root)


@application.route('/docs/wave_thing_api.swagger.yaml')
def api_docs():
    """
    Renders the swagger documentation of the API as a download
    :return: 
    """
    return flask.send_from_directory("docs", "wave_thing_api.swagger.yaml")


api.add_resource(BuoyTalkResource, '/api/buoytalk/<buoy_id>/<buoy_data_type>')

if __name__ == '__main__':
    application.run(debug=True)

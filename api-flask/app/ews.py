"""Collect and parse Cambodia EWS-1294."""
from datetime import datetime, timedelta, timezone

from dateutil.parser import parse as dtparser

from flask import request

import requests

from werkzeug.exceptions import BadRequest, NotFound


BASE_API = 'https://api.ews1294.com/v1/'
DATA_COLLECTION_START_DATE_STR = '2021-05-01'


def parse_ews_params():
    """Transform params used for ews request."""
    only_dates = True if request.args.get('onlyDates') else False
    location_id = request.args.get('locationId', None)
    today = datetime.now().replace(tzinfo=timezone.utc)
    begin_datetime_str = request.args.get('beginDateTime')

    if begin_datetime_str is not None:
        begin_datetime = dtparser(begin_datetime_str)
    else:
        # yesterday
        begin_datetime = today
    begin_datetime = begin_datetime.replace(tzinfo=timezone.utc)

    end_datetime_str = request.args.get('endDateTime')
    if end_datetime_str is not None:
        end_datetime = dtparser(end_datetime_str)
    else:
        # today
        end_datetime = today
    end_datetime = end_datetime.replace(tzinfo=timezone.utc)

    # strptime function includes hours, minutes, and seconds as 00 by default.
    # This check is done in case the begin and end datetime values are the same.
    if end_datetime == begin_datetime:
        end_datetime = end_datetime + timedelta(days=1)

    if begin_datetime > end_datetime:
        raise BadRequest('beginDateTime value must be lower than endDateTime')

    if begin_datetime > today:
        raise BadRequest('beginDateTime value must be less or equal to today')

    return only_dates, location_id, begin_datetime, end_datetime


def get_ews_responses(
        only_dates: bool,
        location_id: int or str or None,
        begin: datetime,
        end: datetime
):
    """Get datapoints for sensor locations."""
    if only_dates:
        the_beginning = datetime.strptime(DATA_COLLECTION_START_DATE_STR, '%Y-%m-%d')
        today = datetime.now()
        days = [the_beginning + timedelta(days=d) for d in range((today - the_beginning).days+1)]
        return list(map(lambda d: {'date': d.strftime('%Y-%m-%d')}, days))

    start_date = begin.date()
    end_date = end.date()

    locations_url = '{0}locations?type=river&start={1}&end={2}'.format(
        BASE_API,
        start_date, end_date
    )

    resp = requests.get(locations_url)
    resp.raise_for_status()
    features = resp.json().get('features')

    def format_details(location):
        """Massage received location details into PRISM format."""
        ACTIVE = 'active'
        OPERATIONAL = 'operational'

        coordinates = location['geometry']['coordinates']
        properties = location['properties']
        trigger_levels = properties['trigger_levels']
        is_active = properties['status'].lower() == ACTIVE
        is_operational = properties['status1'].lower() == OPERATIONAL

        return {
            'lon': coordinates[0],
            'lat': coordinates[1],
            'id': properties['id'],
            'external_id': properties['external_id'],
            'name': properties['name'],
            'is_available': is_active and is_operational,
            'water_height': properties['water_height'],
            'watch_level': trigger_levels['watch_level'],
            'warning': trigger_levels['warning'],
            'severe_warning': trigger_levels['severe_warning'],
        }

    locations = list(map(format_details, features))

    if location_id:
        filtered_locations = [_ for _ in locations if int(_['id']) == int(location_id)]

        if not filtered_locations:
            raise NotFound('locationId not found')

        location_url = '{0}datapoints?location={1}&start={2}&end={3}'.format(
            BASE_API,
            location_id,
            start_date, end_date
        )

        resp = requests.get(location_url)
        resp.raise_for_status()
        return {
            'values': [_['value'] for _ in resp.json()],
            **filtered_locations[0]
        }
    else:
        return locations
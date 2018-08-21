import database
import datetime
from flask import Flask, render_template
from flask_restful import Resource, Api, reqparse
from pytimeparse.timeparse import timeparse
import iso8601

_DEFAULT_FROM = '-1h'
_DEFAULT_TO = '0m'

_app = Flask(__name__)
_api = Api(_app)

def _parse_time(time_str):
    '''
    The time can be given as a timeparse time delta, or given iso8601 timestring, or given as epoch in second.

    Timeparse time delta is e.g. -1m, -2h30m, etc.
    iso8601 format example: 2018-08-19T01:06:28-07:00

    :param time_str: value to parse.
    :return: epoch in second.
    '''
    dt = timeparse(time_str)
    if dt is None:
        try:
            return iso8601.parse_date(time_str)
        except iso8601.ParseError as e:
            return int(time_str)
    return int(datetime.datetime.now().timestamp()) + int(dt)

class List(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('from', type=str)
        parser.add_argument('to', type=str)
        parser.add_argument('user_id', type=str)

        args = parser.parse_args()
        t_from, t_to = _parse_time(args['from']), _parse_time(args['to'])
        return database.read_transactions(
            database.COLUMN_FAMILY_ID_LIST,
            args['user_id'],
            t_from,
            t_to)

class Hour(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('from', type=str)
        parser.add_argument('to', type=str)
        parser.add_argument('user_id', type=str)

        args = parser.parse_args()
        t_from, t_to = _parse_time(args['from']), _parse_time(args['to'])
        return database.read_transactions(
            database.COLUMN_FAMILY_ID_BY_HOUR,
            args['user_id'],
            t_from,
            t_to)

class Sum(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('from', type=str)
        parser.add_argument('to', type=str)
        parser.add_argument('user_id', type=str)

        args = parser.parse_args()
        t_from, t_to = _parse_time(args['from']), _parse_time(args['to'])
        return database.sum_transactions(
            database.COLUMN_FAMILY_ID_BY_HOUR,
            args['user_id'],
            t_from,
            t_to)

@_app.route('/ui')
@_app.route('/')
def render():
    return render_template('index.html')


_api.add_resource(List, '/list')
_api.add_resource(Hour, '/hour')
_api.add_resource(Sum, '/sum')

if __name__ == '__main__':
    database.init()
    _app.run(debug=True)



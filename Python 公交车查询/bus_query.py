#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import random
from datetime import datetime
import os


class BusQuery:
    def __init__(self, data_file='data/bus_data.json'):
        self.data_file = data_file
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'lines': []}

    def search_stations(self, keyword):
        stations = set()
        for line in self.data['lines']:
            for station in line['stations']:
                if keyword in station:
                    stations.add(station)
        return sorted(list(stations))

    def get_lines_by_station(self, station_name):
        lines = []
        for line in self.data['lines']:
            if station_name in line['stations']:
                lines.append(line)
        return lines

    def get_line_detail(self, line_name):
        for line in self.data['lines']:
            if line['name'] == line_name:
                return line
        return None

    def get_all_lines(self):
        return self.data['lines']

    def get_real_time_arrival(self, station_name, line_name):
        line = self.get_line_detail(line_name)
        if not line or station_name not in line['stations']:
            return None

        station_index = line['stations'].index(station_name)
        buses = []

        for i in range(3):
            distance = random.randint(1, station_index + 2)
            if distance <= station_index:
                bus_station_index = station_index - distance
                eta = random.randint(1, distance * 2)
                buses.append({
                    'bus_number': '{}-{:02d}'.format(line_name, i+1),
                    'current_station': line['stations'][bus_station_index],
                    'eta_minutes': eta,
                    'stations_away': distance
                })

        return {
            'station': station_name,
            'line': line_name,
            'buses': buses,
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def get_lines_passing_station(self, station_name):
        result = []
        for line in self.data['lines']:
            if station_name in line['stations']:
                real_time = self.get_real_time_arrival(station_name, line['name'])
                result.append({
                    'line': line,
                    'real_time': real_time
                })
        return result
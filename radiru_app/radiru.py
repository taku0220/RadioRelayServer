import urllib.request, urllib.error, urllib.parse
import os
import subprocess
import signal
import itertools
from collections import OrderedDict

import xml.etree.ElementTree as ET

import logging

class Radiru():

    CHANNEL_FULL_URL = "https://www.nhk.or.jp/radio/config/config_web.xml"
    stations = None
    inst_ctr = 0

    def __init__(self, playlist={}, force_get_stations=False, logger=None):
        Radiru.inst_ctr += 1
        default_logger = logging.getLogger(__name__)
        default_logger.addHandler(logging.NullHandler)
        self.logger = logger or default_logger
        self.logger.debug('Radiru constructor: {}'.format(Radiru.inst_ctr))

        if force_get_stations:
            self.logger.info('getting stations')
            self.get_stations()
            if playlist:
                self.gen_playlist(
                    playlist['url'],
                    playlist['file']
                )

    def play(self, station):
        self.logger.info('playing {}'.format(station))
        if station in self.stations:
            m3u8 = Radiru.stations[station][3]
            self.logger.info('{} URL {}'.format(station, m3u8))
            if not m3u8:
                self.logger.error('m3u8_url fail')
            else:
                cmd = (
                    "ffmpeg -y -i '{}' "
                    "-acodec copy -f adts -loglevel error /dev/stdout"
                ).format(m3u8)
                proc = subprocess.Popen(
                    cmd, shell=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, preexec_fn=os.setsid
                )
                self.logger.debug('started subprocess: group id {}'
                    .format(os.getpgid(proc.pid)))

                try:
                    while True:
                        out = proc.stdout.read(512)
                        if proc.poll() is not None:
                            self.logger.error(
                                'subprocess died: {}'.format(station)
                            )
                            break
                        if out:
                            yield out
                finally:
                    self.logger.info('stop playing {}'.format(station))
                    if not proc.poll():
                        pgid = os.getpgid(proc.pid)
                        self.logger.debug('killing process group {}'.format(pgid))
                        os.killpg(pgid, signal.SIGTERM)
                        proc.wait()
        else:
            self.logger.error('{} not in available stations'.format(station))

    def get_stations(self):
        headers = {"User-Agent": "curl/7.56.1"}
        req = urllib.request.Request(Radiru.CHANNEL_FULL_URL, None, headers)
        res = urllib.request.urlopen(req)
        xml_string = res.read()
        root = ET.fromstring(xml_string)
        areas = []
        for e in root.findall('.//area'):
            areas.append(e.text)
        self.logger.debug('areas : {}'.format(areas))
        channels = ['r1hls', 'r2hls', 'fmhls']
        channel_name_jp = {'r1hls': '第１', 'r2hls': '第２', 'fmhls': 'FM'}
        stations = OrderedDict()

        for area, channel in itertools.product(areas, channels):
            data = []
            for stream_url in root.findall('.//data'):
                if stream_url.find('area').text == area:
                    data = stream_url
            station_id = '{}-{}'.format(channel, area)
            channel_name = channel_name_jp.get(channel,'')
            channel_url = data.find(channel).text

            stations[station_id] = (
                area, channel, channel_name, channel_url
                )
        Radiru.stations = stations
        self.logger.debug('Radiru.stations: {}'.format(Radiru.stations))

    def gen_playlist(self, url_template, outfile):
        self.logger.info('writing playlist: {}'.format(outfile))
        with open(outfile, 'w') as f:
            f.write('#EXTM3U\n')
            f.write('\n')
            url = url_template
            for (
                    station_id, 
                    (area, channel, channel_name, channel_url)
                ) in Radiru.stations.items():
                station_str = '{} / NHKラジオ{}'.format(area.capitalize(), channel_name)
                f.write('#EXTINF:-1,{}\n'.format(station_str))
                f.write(url.format(station_id)+'\n')

    def __del__(self):
        Radiru.inst_ctr -= 1
        self.logger.debug('Radiru destructor: {}'.format(Radiru.inst_ctr))


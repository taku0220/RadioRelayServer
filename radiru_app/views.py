from django.views import View
from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
from . import radiru
from settings import config
import logging

def index(request):
    return HttpResponse("Hello, world. You're at the radiru_app index.")

class Tune(View):
    def get(self, request, station_id):
        logger = logging.getLogger('radio.debug')
        logger.debug(request)
        playlist = {
            'url': config.RADIRU_PLAYLIST_URL, 
            'file': config.RADIRU_PLAYLIST_FILE
        }
        rdk = radiru.Radiru(playlist, logger=logger)
        response = StreamingHttpResponse(
            rdk.play(station_id), content_type="audio/aac"
        )
        response['Cache-Control'] = 'no-cache, no-store'
        logger.debug('get returning response')
        return response


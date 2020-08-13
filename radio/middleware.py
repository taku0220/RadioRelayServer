from radiko_app import radiko
from radiru_app import radiru
try:
    from settings import account
except:
    pass
from settings import config
import logging

class SampleMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        #print('(1) init')
        
        ### Radiko ###
        playlist = {
            'url': config.RADIKO_PLAYLIST_URL, 
            'file': config.RADIKO_PLAYLIST_FILE
        }
        try:
            act = {'mail':account.RADIKO_MAIL, 'pass':account.RADIKO_PASS}
        except:
            act = {}
        radiko.Radiko(act, playlist, logger=logging.getLogger('radio.debug'))

        ### Radiru ###
        playlist = {
            'url': config.RADIRU_PLAYLIST_URL, 
            'file': config.RADIRU_PLAYLIST_FILE
        }
        radiru.Radiru(playlist, force_get_stations=True, logger=logging.getLogger('radio.debug'))

    def __call__(self, request):
        #print('(2): before get_response')

        response = self.get_response(request)

        #print('(3): after get_response')

        return response



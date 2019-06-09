# -*-: coding utf-8 -*-
""" Philips Hue skill for Snips. """

import requests
import json
import sys


class HueSetup:
    @staticmethod
    def validate_config(bridge_ip, api_key):
        config_changed = False
        if bridge_ip is None:
            bridge_ip = HueSetup._get_bridge_ip()
            api_key = None
        if api_key is None or not HueSetup._is_connected(bridge_ip, api_key):
            api_key = HueSetup._connect_user(bridge_ip)
            config_changed = True
        return bridge_ip, api_key, config_changed

    @staticmethod
    def _get_bridge_ip():
        bridge_ip_json_key = "internalipaddress"
        response = requests.get('http://www.meethue.com/api/nupnp').json()
        if type(response) is list:
            if len(response) == 1:
                return response[0][bridge_ip_json_key]
            else:
                return response[0][bridge_ip_json_key]
        else:
            return response[bridge_ip_json_key]

    @staticmethod
    def _is_connected(bridge_ip, api_key):
        response = requests.get(HueSetup._create_url(bridge_ip, api_key)).json()
        if 'lights' in response:
            print('Connected to the Hub')
            return True
        elif 'error' in response[0]:
            if response[0]['error']['type'] == 1:
                return False
        else:
            print('Strange error. No lights connected to hue bridge but no error either.')
            print("Http response:\n{}".format(str(response)))
            return False

    @staticmethod
    def _connect_user(bridge_ip):
        created = False
        print('[!] Please, press the button on the Hue bridge')
        while not created:
            payload = json.dumps({'devicetype': 'snipshue'})
            response = requests.post("http://" + bridge_ip + "/api", data=payload).json()
            if 'error' in response[0]:
                if response[0]['error']['type'] != 101:
                    print('Unhandled error creating configuration on the Hue')
                    sys.exit(response)
            else:
                api_key = response[0]['success']['username']
                created = True
        print('User connected')
        return api_key

    @staticmethod
    def _create_url(bridge_ip, username):
        return 'http://{}/api/{}'.format(bridge_ip, username)

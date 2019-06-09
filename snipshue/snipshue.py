# -*-: coding utf-8 -*-
""" Philips Hue skill for Snips. """

import requests
import json
import time
from snipshue.hue_setup import HueSetup


class SnipsHue:
    """ Philips Hue skill for Snips. """

    def __init__(self, bridge_ip, api_key, locale=None):
        """ Initialisation.

        :param bridge_ip: Philips Hue hostname
        :param api_key: Philips Hue username
        :param light_ids: Philips Hue light ids
        """
        self.api_key = api_key
        self.bridge_ip = bridge_ip

        #TODO: Same url used in hue_setup
        url = 'http://{}/api/{}'.format(bridge_ip, api_key)
        self.groups_endpoint = url + "/groups"
        self.scenes_endpoint = url + "/scenes"
        #self.lights_endpoint = url + "/lights"
        #self.config_endpoint = url + "/config"

        self.groups = requests.get(self.groups_endpoint).json()
        self.scenes = requests.get(self.scenes_endpoint).json()

    def _get_room_name(self, room_id):
        return self.groups[room_id]['name']

    def _get_secne_name(self, scene_id):
        return self.scenes[scene_id]['name']

    def get_rooms(self):
        return {v['name']:k for k,v in self.groups.items()}

    def get_scenes_for_room(self, room_id):
        return {v['name']: k for k, v in self.scenes.items() if 'group' in v and v['group'] == room_id}

    # section -> action handlers
    def light_on(self, room_id):
        print("[HUE] turning on lights preserving last state in room {}".format(self._get_room_name(room_id)))
        self._put_group_state({"on": True}, room_id)

    def light_off(self, room_id):
        print("[HUE] turning off lights in room {}".format(self._get_room_name(room_id)))
        self._put_group_state({"on": False}, room_id)

    def set_scene(self, scene_id, room_id):
        print("[HUE] setting scene {} in room {}".format(self._get_secne_name(scene_id), self._get_room_name(room_id)))
        self._put_group_state({"scene": scene_id}, room_id)

    def light_brightness(self, percent, room_id):
        print("[HUE] set brightness to {} percent in room {}".format(percent, self._get_room_name(room_id)))
        brightness = int(round(percent * 254 / 100))
        self._put_group_state({"on": True, "bri": brightness}, room_id)

    def shift_brightness(self, room_id, percent, up):
        """
        :type up: bool Shift up if true o/wise shift down.
        """
        print("[HUE] shift {} by {} percent in room {}".format("up" if up else "down", percent,
                                                               self._get_room_name(room_id)))
        cur_brightness = self._get_group_brightness(room_id)
        delta = int(round(percent * 254 / 100))
        if not up:
            delta = delta * (-1)
        new_bri = cur_brightness + delta
        if new_bri > 254:
            new_bri = 254
        if new_bri < 0:
            new_bri = 0
        self._put_group_state({"on": True, "bri": new_bri}, room_id)

    # section -> send command to device
    def _put_group_state(self, payload, group_id):
        print("[HUE] Setting for group " + str(group_id) + ": " + str(payload))

        try:
            url = "{}/{}/action".format(self.groups_endpoint, group_id)
            res = requests.put(url, data=json.dumps(payload), headers=None)
            print(res.text)
        except Exception as e:
            print(e)
            print("[HUE] Request timeout. Is the Hue Bridge reachable?")
            pass

    # section -> get different info
    def _get_group_status(self, group_id):
        try:
            url = "{}/{}/".format(self.groups_endpoint, group_id)
            group_status = requests.get(url).json()
            return group_status
        except Exception as e:
            print(e)
            print("[HUE] Request timeout. Is the Hue Bridge reachable?")
            pass

    def _get_group_brightness(self, group_id):
        status = self._get_group_status(group_id)
        if status["action"].get("bri"):
            return status["action"]["bri"]
        else:
            return None

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hermes_python.hermes import Hermes
from snipshue.snipshue import SnipsHue, HueSetup
from snipshelpers.config_parser import SnipsConfigParser
from snipshelpers.config_parser import BRIDGE_IP_KEY
from snipshelpers.config_parser import API_KEY_KEY
from fuzzywuzzy import process
import traceback

MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

TURN_ON_INTENT = 'turnOn'
TURN_OFF_INTENT = 'turnOff'
SET_BRIGHTNESS_INTENT = 'setBrightness'
SET_SCENE_INTENT = 'setScene'
SHIFT_UP_INTENT = 'shiftUp'
SHIFT_DOWN_INTENT = 'shiftDown'
ALL_INTENTS = [TURN_ON_INTENT, TURN_OFF_INTENT,
               SET_BRIGHTNESS_INTENT, SET_SCENE_INTENT,
               SHIFT_UP_INTENT, SHIFT_DOWN_INTENT]


class Skill_Hue:
    def __init__(self):
        config_dict = SnipsConfigParser.read_configuration_file()
        bridge_ip = config_dict.get(BRIDGE_IP_KEY, None)
        api_key = config_dict.get(API_KEY_KEY, None)
        (bridge_ip, api_key, config_changed) = HueSetup.validate_config(bridge_ip, api_key)
        if config_changed:
            SnipsConfigParser.write_configuration_file(bridge_ip, api_key)
        self.snipshue = SnipsHue(bridge_ip, api_key)

        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intents(self.callback).start()

    # section -> extraction of slot value
    def _select_best_match(self, val, choices, min_match_percent):
        res = process.extractOne(val, choices)
        if res[1] > min_match_percent:
            return res[0]
        else:
            return None

    def extract_house_room(self, intent_message):
        available_house_rooms = self.snipshue.get_rooms()
        if intent_message.slots.house_room:
            best_match = self._select_best_match(intent_message.slots.house_room.first().value,
                                                 available_house_rooms.keys(), 90)
            if best_match:
                return best_match, available_house_rooms[best_match]
            else:
                return None, None

    def extract_percentage(self, intent_message, default_percentage):
        percentage = default_percentage
        if intent_message.slots.percent:
            percentage = intent_message.slots.percent.first().value
        if percentage < 0:
            percentage = 0
        if percentage > 100:
            percentage = 100
        return percentage

    def extract_scene(self, intent_message, house_room_id):
        available_scenes = self.snipshue.get_scenes_for_room(house_room_id)
        if intent_message.slots.scene:
            best_match = self._select_best_match(intent_message.slots.scene.first().value,
                                                 available_scenes.keys(), 90)
            if best_match:
                return best_match, available_scenes[best_match]
            else:
                return None, None

    # section -> handlers of intents

    def callback(self, hermes, intent_message):
        intent_name = intent_message.intent.intent_name
        if ':' in intent_name:
            intent_name = intent_name.split(":")[1]
        if intent_name not in ALL_INTENTS:
            return
        try:
            print("[HUE] Received {}".format(intent_message.intent.intent_name))
            # all the intents have to have a house_room slot, extract here
            room_name, room_id = self.extract_house_room(intent_message)
            if room_id:
                if intent_name == TURN_ON_INTENT:
                    self.turn_on(hermes, intent_message, room_id)
                if intent_name == TURN_OFF_INTENT:
                    self.turn_off(hermes, intent_message, room_id)
                if intent_name == SET_BRIGHTNESS_INTENT:
                    self.set_brightness(hermes, intent_message, room_id)
                if intent_name == SET_SCENE_INTENT:
                    self.set_scene(hermes, intent_message, room_id)
                if intent_name == SHIFT_UP_INTENT:
                    self.shift_up(hermes, intent_message, room_id)
                if intent_name == SHIFT_DOWN_INTENT:
                    self.shift_down(hermes, intent_message, room_id)
            else:
                self.terminate_feedback(hermes, intent_message, "Sorry no fitting room was detected.")
        except:
            traceback.print_exc()
            self.terminate_feedback(hermes, intent_message, "Unknown exception detected. Please consult log files.")

    def turn_on(self, hermes, intent_message, room_id):
        self.snipshue.light_on(room_id)
        self.terminate_feedback(hermes, intent_message)

    def turn_off(self, hermes, intent_message, room_id):
        self.snipshue.light_off(room_id)
        self.terminate_feedback(hermes, intent_message)

    def set_brightness(self, hermes, intent_message, room_id):
        percent = self.extract_percentage(intent_message, None)
        self.snipshue.light_brightness(percent, room_id)
        self.terminate_feedback(hermes, intent_message)

    def set_scene(self, hermes, intent_message, room_id):
        scene_name, scene_id = self.extract_scene(intent_message, room_id)
        if scene_id:
            self.snipshue.set_scene(scene_id, room_id)
            self.terminate_feedback(hermes, intent_message)
        else:
            self.terminate_feedback(hermes, intent_message, "Sorry, no matching seen found.")

    def shift_up(self, hermes, intent_message, room_id):
        percent = self.extract_percentage(intent_message, 20)
        self.snipshue.shift_brightness(room_id, percent, True)
        self.terminate_feedback(hermes, intent_message)

    def shift_down(self, hermes, intent_message, room_id):
        percent = self.extract_percentage(intent_message, 20)
        self.snipshue.shift_brightness(room_id, percent, False)
        self.terminate_feedback(hermes, intent_message)

    # section -> feedback reply // future function
    def terminate_feedback(self, hermes, intent_message, message=""):
        hermes.publish_end_session(intent_message.session_id, message)


if __name__ == "__main__":
    Skill_Hue()

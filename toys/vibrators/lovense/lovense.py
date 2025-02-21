import requests
from common.util import *
from toys.vibrators.vibrator import Vibrator
import settings
import random
import math

class LovenseInterface(Vibrator):
    def __init__(self):
        self.COMMAND_URL = "http://{}/command".format(settings.LOVENSE_HOST)
        super().__init__("Lovense")

    def shutdown(self):
        pass
    
    def _command(self, command, duration):
        info("Sending vibrate command")
        params = {
            'command':"Function",
            'action': command,
            'timeSec': duration,
            'apiVer':1
        }
        return requests.post(self.COMMAND_URL, verify=False, json=params)

    def _send_pattern(self, duration, pattern, strength):
        pattern = pattern.split(";")
        interval = (350 + (1000 - strength * 10))
        scale_intensity = False
        if len(pattern) > 1:
            for x in pattern[1:]:
                if x == "scale_intensity":
                    scale_intensity = True
                if "interval" in x:
                    interval = int(x.split("=")[1])
        pattern = random.choice(self.patterns[pattern[0]])
        pattern = ";".join([str(self.scale_strength(x, strength, scale_intensity)) for x in pattern])
        info("Sending pattern command: {} at interval {} (scale_intensity={})".format(str(pattern), interval, scale_intensity))
        # interval should be 100 minimum, ms inbetwen steps
        if settings.LOVENSE_USE_NEW_API:
            rule = "V:1;F:v,r,p,t,s,f;S:{}#".format(interval)
        else:
            rule = "V:1;F:vrp;S:{}#".format(interval)
        params = {
            'command': "Pattern",
            'rule': rule,
            'strength': pattern,
            'timeSec': duration,
            'apiVer': 1
        }
        return requests.post(self.COMMAND_URL, verify=False, json=params)
    
    def connect(self):
        return

    def check_in(self):
        return

    def scale_strength(self, strength, original_strength, scale_intensity):
        ret = math.ceil(strength * (float(settings.LOVENSE_STRENGTH_SCALE) / 100))
        if scale_intensity:
            ret *= math.ceil(original_strength/5)
        if ret >= 20:
            ret = 20
        return ret
    
    def vibrate(self, duration, strength, pattern=""):
        if pattern == "":
            strength = self.scale_strength(strength, 0, False)
            strength = math.ceil(int(strength)/5) # Lovense supports 0-20 scale for vibrations
            r = self._command("Vibrate:"+str(strength), duration)
        else:
            r = self._send_pattern(duration, pattern, strength)
        if r.json()['code'] == 200:
            success("  " + str(r.json()))
        elif r.json()['code'] == 404:
            fail("  Request failed. Try Toggling the 'Use New API' setting: " + str(r.json()))
        elif r.json()['code'] == 402:
            fail("  Remote server refused request. Make sure that you're logged in, control is permitted, or (if using a phone) that you're in game mode: " + str(r.json()))
        else:
            fail("  " + str(r.json()))
    def stop(self):
        r = self._command("Stop", 0)
        if r.json()['code'] == 200:
            success("  " + str(r.json()))
        else:
            fail("  " + str(r.json()))

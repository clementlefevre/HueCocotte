#!/usr/bin/env python
import schedule

__author__ = 'ThinkPad'

import logging
import smtplib
import time


from config import EMAIL_PASSWORD, EMAIL_ADDRESS, IP_BRIDGE, EMAIL_SUBJECT, USERNAME, OPTIMAL_XY

from phue import Bridge, PhueRequestTimeout

START_PATTERN = {'_brightness': 254, '_colortemp': 369, '_hue': 14922,
                 '_saturation': 144}

MATCHING_THRESHOLD = 20



logging.basicConfig(filename='hue.log', filemode='w', level=logging.WARNING, format='%(asctime)s %(message)s')

logger = logging.getLogger('logger_hue')




class HueCocotte():
    def main(self):
        self.createConfig()



    def createConfig(self):
        created = False
        logger.warning('***********************Press the button on the Hue bridge*************************')
        while not created:
            b = Bridge(IP_BRIDGE)
            b.connect()
            # Get the bridge state (This returns the full dictionary that you can explore)
            b.get_api()
            if len(b.lights)>0:
                created=True
                HueCocotte().send_mail(EMAIL_SUBJECT, "Philips HUE connected")
                logger.warning("Bridge connected !")
                self.polling()




    def set_all_light(self):

        global FAILURES_COUNT

        b = Bridge(IP_BRIDGE)

        try:
            b.connect()
            lights = b.lights

            for light in lights:

                xy_delta = self.get_xy_delta(light)
                threshold = self.is_start_pattern(light)

                if xy_delta > 10 and threshold < MATCHING_THRESHOLD:
                    logger.warning("The light in the {0} has been switched !".format(light.name))
                    self.send_mail(EMAIL_SUBJECT, "The light in the {0} has been switched !".format(light.name))
                    light.brightness = 207
                    light.colortemp = 459
                    light.colortemp_k = 2179
                    light.saturation = 209
                    light.saturation = 100
                    light.xy = OPTIMAL_XY

        except PhueRequestTimeout:
            logger.warning("PhueRequestTimeout - Could not connect with Bridge !!!")
            self.send_mail(EMAIL_SUBJECT, "No connection with bridge [{0}]".format(IP_BRIDGE)
                           )
            self.createConfig()

    def polling(self):
        global FAILURES_COUNT
        FAILURES_COUNT = 0
        schedule.every(5).seconds.do(self.set_all_light)


        while 1 and FAILURES_COUNT == 0:
            schedule.run_pending()
            time.sleep(1)

    def send_mail(self, title, value):
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        message = 'Subject: %s\n\n%s' % (title, value)
        server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, message)
        server.quit()

    def get_xy_delta(self, light):
        xy_delta = [light.xy[0] - OPTIMAL_XY[0], light.xy[1] - OPTIMAL_XY[1]]
        return (abs(xy_delta[0]) + abs(xy_delta[1])) * 1000

    def is_start_pattern(self, light):
        light_dict = light.__dict__
        matching = 0
        for key in START_PATTERN:
            if light_dict[key] is not None:
                matching += self.pattern_threshold(key, light_dict[key])

        if matching > MATCHING_THRESHOLD:
            return True
        else:
            return False

    def pattern_threshold(self, parameter, value):
        delta_threshold = abs(START_PATTERN[parameter] * 100 - value * 100) / START_PATTERN[parameter]
        return delta_threshold



if __name__ == '__main__':
    HueCocotte().main()




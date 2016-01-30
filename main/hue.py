import logging
import smtplib
import time
import sys

import schedule as schedule

from config import EMAIL_PASSWORD, EMAIL_ADDRESS, IP_BRIDGE

__author__ = 'ThinkPad'

from beautifulhue.api import Bridge
from phue import Bridge as phueBridge, PhueRequestTimeout

START_BRIGHTNESS = 254
START_COLORTEMP = 369
START_SATURATION = 144
START_XY = [0.4595, 0.4105]

EMAIL_SUBJECT = "Philips HUE"
username = 'clementsan'
bridge = Bridge(device={'ip': IP_BRIDGE}, user={'name': username})

logging.basicConfig(filename='hue.log', filemode='w', level=logging.WARNING, format='%(asctime)s %(message)s')

logger = logging.getLogger('logger_hue')


def exception_handler(type, value, tb):
    logger.exception("Uncaught exception: {0}".format(str(value)))
    HueCocotte().send_mail(EMAIL_SUBJECT, "Error by Philips HUE : {0}".format(value))


# Install exception handler
sys.excepthook = exception_handler


class HueCocotte():
    def main(self):
        self.createConfig()
        response = self.getSystemData()

        if 'lights' in response:
            print 'Connected to the Hub'
            print response['lights']
        elif 'error' in response[0]:
            error = response[0]['error']
            if error['type'] == 1:
                self.createConfig()

    def createConfig(self):

        # resource = {'user': {'name': username}}
        # bridge.config.delete(resource)

        created = False
        print '***********************Press the button on the Hue bridge*************************'
        while not created:
            resource = {'user': {'devicetype': 'beautifulhuetest', 'name': username}}
            response = bridge.config.create(resource)['resource']
            if 'error' in response[0]:
                if response[0]['error']['type'] != 101:
                    print 'Unhandled error creating configuration on the Hue'
                    sys.exit(response)
            else:
                created = True

                print "Bridge connected with username : {0}".format(response[0]['success']['username'])
                self.polling()

    def getSystemData(self):
        resource = {'which': 'system'}
        return bridge.config.get(resource)['resource']

    def set_all_light(self):

        global FAILURES_COUNT

        b = phueBridge(IP_BRIDGE)

        try:
            b.connect()
            lights = b.lights

            for light in lights:
                if light.brightness == START_BRIGHTNESS and light.colortemp == START_COLORTEMP and light.saturation == START_SATURATION and light.xy == START_XY:
                    self.send_mail(EMAIL_SUBJECT, "The light in the {0} has been switched !".format(light.name))
                    light.brightness = 207
                    light.colortemp = 459
                    light.colortemp_k = 2179
                    light.saturation = 209
                    light.saturation = 100
                    light.xy = [0.509, 0.4149]

        except PhueRequestTimeout:
            logger.warning("Could not connect with Bridge !!!")
            self.send_mail(EMAIL_SUBJECT, "Pas de signal avec {0}".format(IP_BRIDGE)
                           )
            FAILURES_COUNT += 1

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


if __name__ == '__main__':
    HueCocotte().main()

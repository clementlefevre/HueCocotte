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

OPTIMAL_XY = [0.509, 0.4149]

EMAIL_SUBJECT = "Philips HUE"
username = 'clementsan'
bridge = Bridge(device={'ip': IP_BRIDGE}, user={'name': username})

logging.basicConfig(filename='hue.log', filemode='w', level=logging.WARNING, format='%(asctime)s %(message)s')

logger = logging.getLogger('logger_hue')


def exception_handler(type, value, tb):
    logger.exception("Uncaught exception: {0}".format(str(value)))
    logger.warning("Exception occured")
    logger.warning(value)

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
                    logger.exception(
                        "sys.exit(response) activated : Unhandled error creating configuration on the Hue : ")
                    logger.exception("Resource : {0}".format(resource))
                    logger.exception("Response from Bridge : {0}".format(response))
                    HueCocotte().send_mail(EMAIL_SUBJECT, "Error by Philips HUE : {0}".format(
                        "sys.exit(response) activated : Unhandled error creating configuration on the Hue : Resource : {0} "
                        "Response from Bridge : {1}".format(resource, response)))
                    sys.exit(response)
            else:
                created = True

                print "Bridge connected with username : {0}".format(response[0]['success']['username'])
                self.polling()

    def getSystemData(self):
        resource = {'which': 'system'}
        try:

            return bridge.config.get(resource)['resource']
        except Exception:
            logger.warning("Could get bridge resource")

    def set_all_light(self):

        global FAILURES_COUNT

        b = phueBridge(IP_BRIDGE)

        try:
            b.connect()
            lights = b.lights

            for light in lights:
                print("Light : {0} - xy : {1} ".format(light.name, light.xy))
                delta = self.get_xy_delta(light)
                print(delta)
                if delta > 10:
                    print ("The light in the {0} has been switched !".format(light.name))
                    logger.warning("The light in the {0} has been switched !".format(light.name))
                    self.send_mail(EMAIL_SUBJECT, "The light in the {0} has been switched !".format(light.name))
                    light.brightness = 207
                    light.colortemp = 459
                    light.colortemp_k = 2179
                    light.saturation = 209
                    light.saturation = 100
                    light.xy = OPTIMAL_XY

        except PhueRequestTimeout:
            logger.warning(" PhueRequestTimeout - Could not connect with Bridge !!!")
            self.send_mail(EMAIL_SUBJECT, "No connection with bridge [{0}]".format(IP_BRIDGE)
                           )
            FAILURES_COUNT += 1

    def polling(self):
        global FAILURES_COUNT
        FAILURES_COUNT = 0
        schedule.every(5).seconds.do(self.set_all_light)
        logger.warning("Failure count : {0}".format(FAILURES_COUNT))

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
        xy_delta = [light.xy[0] - OPTIMAL_XY[0], light.xy[1] - OPTIMAL_XY+[1]]
        return (abs(xy_delta[0]) + abs(xy_delta[1])) * 1000


if __name__ == '__main__':
    HueCocotte().main()

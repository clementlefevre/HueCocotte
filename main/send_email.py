import smtplib

__author__ = 'ThinkPad'

EMAIL_ADDRESS = "clement.san2000@gmail.com"
EMAIL_PASSWORD = "ninaditkindoupetitkindou2000"


def send_mail(value):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    msg = value
    server.sendmail(EMAIL_ADDRESS, "clement.san@gmail.com", msg)
    server.quit()


send_mail("je t encule")

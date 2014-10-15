import json
import re
import urllib2
import datetime
from PIL import Image, ImageDraw, ImageFont

import webapp2


PLUGIN_INFO = {
    "name": "Barcoo product information"
}

# cache for 2 days
EXPIRATION_IN_SECONDS = 2 * 24 * 60 * 60
rating_font = ImageFont.truetype("Roboto-Bold.ttf", 13)
rating_footer_font = ImageFont.truetype("Roboto-Bold.ttf", 9)


class GMT(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=10)

    def tzname(self, dt):
        return "GMT"

    def dst(self, dt):
        return datetime.timedelta(0)


def get_expiration_stamp(seconds):
    gmt = GMT()
    delta = datetime.timedelta(seconds=seconds)
    expiration = datetime.datetime.now()
    expiration = expiration.replace(tzinfo=gmt)
    expiration = expiration + delta
    return expiration.strftime("%a, %d %b %Y %H:%M:%S %Z")


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.set_default_headers()

        barcode = self.request.params.get("q", None)
        if barcode:
            url = "http://www.barcoo.com/" + barcode
            open_details = self.request.params.get("d", None)
            if open_details:
                self.redirect(str(url))
            else:
                request = urllib2.Request(url, None, {'Referrer': 'http://shoppistant.com'})
                response = urllib2.urlopen(request)
                m = re.search("<span class=\"ratingCount\">(.*) aus", response.read())
                if m:
                    self.send_rating_image(m.group(1))
                else:
                    self.response.write("Not found")
                    self.response.status = 404
        else:
            self.response.content_type = "application/json"
            self.response.write(json.dumps(PLUGIN_INFO))

    def set_default_headers(self):
        # allow CORS
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        self.response.headers["Expires"] = get_expiration_stamp(EXPIRATION_IN_SECONDS)
        self.response.headers["Content-Type"] = "application/json"
        self.response.headers["Cache-Control"] = "public, max-age=%d" % EXPIRATION_IN_SECONDS

    def send_rating_image(self, rating):
        img = Image.open("rating_background.png")
        draw = ImageDraw.Draw(img)
        w, _ = draw.textsize(rating)
        draw.text((25 - w / 2, 4), rating, (255, 255, 255), font=rating_font)
        draw.text((17, 20), "of 5", (255, 255, 255), font=rating_footer_font)
        self.response.content_type = "image/png"
        img.save(self.response, "PNG")


app = webapp2.WSGIApplication([
                                  ('/', MainHandler)
                              ], debug=True)

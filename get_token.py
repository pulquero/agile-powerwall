import sys
import teslapy
import json

default_email = ""

email = sys.argv[1] if len(sys.argv) == 2 else default_email

with teslapy.Tesla(email) as tesla:
    pws = tesla.battery_list()

with open("cache.json") as f:
    data = json.load(f)

print(data[email]["sso"]["refresh_token"])

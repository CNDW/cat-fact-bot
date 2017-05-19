from time import sleep
from slackclient import SlackClient
import os
from datetime import datetime
from fogofacts import *
from random import choice
from pytz import timezone
import atexit
from tinys3 import Connection

NAME = 'fogo_facts'

def get_icon_emoji():
    return choice([
        ':fogo:',
        ':travisman:',
        ':party_dino:',
        ':partyparrot:',
        ':aaww_yea_part:',
        ':awwyeah:',
        ':blues_clues_parrot:',
        ':busterspin:',
        ':captainamerica:',
        ':gangnamstyle:',
        ':jalepeno:'
    ])

posted = False

#channels = {} #Mapping from channel_id to user_id

usage = """
Welcome to Fogo Facts!
To subscribe to your daily fogo fact, tag me and say "subscribe".
To unsubscribe from this service, tag me and say "unsubscribe".
To get a fact right now, tag me and say "fact"!

Anything else and I'll show you this message to help you out!

If you have any facts you want to add, comments, complaints, or bug reports, message Jack Reichelt.
"""


@atexit.register
def save_subs():
    print('Writing subscribers.')
    cf.write_subscribers()
    conn.upload('subscribers.txt', open('subscribers.txt', 'rb'), 'better-fogo-facts')
#     sys.exit(0)
#
# signal.signal(signal.SIGTERM, sigterm_handler)

TOKEN = os.environ.get('TOKEN', None)  # found at https://api.slack.com/web#authentifogoion
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY', None)
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY', None)

conn = Connection(S3_ACCESS_KEY, S3_SECRET_KEY, endpoint='s3-ap-southeast-2.amazonaws.com')

saved_subs = conn.get('subscribers.txt', 'better-fogo-facts')

f = open('subscribers.txt', 'wb')
f.write(saved_subs.content)
f.close()

cf = CatFacts()

sc = SlackClient(TOKEN)
if sc.rtm_connect() is True:
  print('Connected.')

  sc.api_call("im.list")

  while True:
    response = sc.rtm_read()
    for part in response:
      if 'ims' in part:
        channels = part['ims']
        if part['type'] == 'message':
            if '<@U1MKHKV8U>' in part['text']:
              if 'unsubscribe' in part['text'].lower():
                cf.remove_subscriber(part['channel'].strip())
                save_subs()
                sc.api_call("chat.postMessage", channel=part['channel'], text="We're sorry to see you go.", username=NAME, icon_emoji=':crying_fogo_face:')
            elif 'subscribe' in part['text'].lower():
                cf.add_subscriber(part['channel'].strip())
                save_subs()
                sc.api_call("chat.postMessage", channel=part['channel'], text="Thanks for subscribing to fogo facts! Here's your complimentary first fogo fact!", username=NAME, icon_emoji=':iseewhatyoudidthere:')
                sc.api_call("chat.postMessage", channel=part['channel'], text=cf.get_fact(part['channel'].strip()), username=NAME, icon_emoji=':iseewhatyoudidthere:')
            elif 'fact' in part['text'].lower():
                sc.api_call("chat.postMessage", channel=part['channel'], text=cf.get_fact(part['channel'].strip()), username=NAME, icon_emoji=get_icon_emoji())
                save_subs()
            elif 'list' in part['text'].lower() and part['user'] == 'U0PDQ1P2R':
                sc.api_call("chat.postMessage", channel=part['channel'], text=cf.list_subscribers(), username=NAME, icon_emoji=get_icon_emoji())
            else:
                sc.api_call("chat.postMessage", channel=part['channel'], text=usage, username=NAME, icon_emoji=get_icon_emoji())

    if 0 <= datetime.now(timezone('Australia/Sydney')).time().hour < 1 and posted is True: #midnight to 1am
        print('It\'s a new day.')
        posted = False
    if 15 <= datetime.now(timezone('Australia/Sydney')).time().hour < 17 and posted is False: #3pm to 5pm
        print('It\'s fogo fact time!')
        posted = True
    for channel in cf.get_subscribers():
        print('Sending a fact to {}.'.format(channel))
        sc.api_call("chat.postMessage", channel=channel, text=cf.get_fact(channel), username=NAME, icon_emoji=get_icon_emoji())
        save_subs()

        sleep(1)
    else:
      print('Connection Failed, invalid token?')

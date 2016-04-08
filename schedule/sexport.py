#!/usr/bin/env python

# miniLAC16 schedule exporter
# ===========================
# Copyright (C) 2016 riot <riot@c-base.org>
#
# GPLv3
from datetime import timedelta, datetime
from pprint import pprint
import argparse
import requests
import json
import sys
import pytz
import calendar

__author__ = 'riot'

DEBUG = False
OFFLINE = False

baseurl = "http://minilac.linuxaudio.org/api.php?action=parse&page=%s&prop" \
          "=wikitext&format=json"

conference = {
    'conference': {
        'acronym': 'miniLAC16',
        'title': 'Mini Linux Audio Conference 2016',
        'basedate': '2016-04-08',
        'timezone': 'Europe/Berlin',
        'license': 'CC-BY-SA-4.0',
        'language': 'en'
    },
    'events': {}
}

rooms = [
    'Mainhall',
    'Weltenbaulab',
    'Seminar room',
    'Upper-deck',
    'Soundlab'
]

webdatacache = {}


def strip_tags(markup):
    markup = markup.lstrip().rstrip()
    markup = markup.replace("'''", "")

    if "[[" not in markup:
        return markup

    wobble = markup
    ham = ""

    while '[[' in wobble:
        wibble, wobble = wobble.split("[[", maxsplit=1)
        ham += wibble

        spam, wobble = wobble.split("]]", maxsplit=1)

        if spam.startswith('User'):
            if DEBUG:
                print("Found a user: ", spam)
            ham += str(spam.split("|")[1])
        if spam in rooms:
            if DEBUG:
                print("Room encountered")
            ham += spam
        elif spam.startswith('Image'):
            if DEBUG:
                print("Found an image: ", spam)

    ham += wobble

    return ham


def get_events(eventtype="Lecture"):
    if eventtype not in webdatacache:
        if DEBUG:
            print("Object not in cache!")
        if not OFFLINE:
            webdata = requests.get(baseurl % eventtype)
        else:
            print("Cannot get object! Offline!")
            sys.exit(-1)

        if DEBUG:
            pprint(webdata.json(), indent=1)

        wikidata = "".join(list(webdata.json()['parse']['wikitext']['*']))
        webdatacache[eventtype] = wikidata
    else:
        wikidata = webdatacache[eventtype]

    rawevents = []
    events = []

    for no, part in enumerate(wikidata.split("{{Template:" + eventtype)):
        if not no == 0:
            if DEBUG:
                print("#" * 5)
            part = part.split("}}")[0]

            if DEBUG:
                print(part)
            rawevents.append(part)

    for rawevent in rawevents:
        rawevent = rawevent.split("\n")
        if DEBUG:
            print(rawevent)
        event = {
            'title': '',
            'type': eventtype,
            'id': 1,
            'room': '',

            # only valid when basedate is given, use full datetime in
            # 'start' otherwise
            'day': 0,

            # can be a whole ISO datetime, otherwise, 'basedate' is used as
            # a base
            'start': '',
            'duration': '01:00',  # alternative: 'end'

            'people': '',  # can be an array. alias: 'persons'

            'type': eventtype,  # optional. default: lecture
            'license': 'CC-BY-SA',  # optional


            'description': '',  # optional
        }

        for no, line in enumerate(rawevent):
            if DEBUG:
                print(line)
            split = line[1:].split(
                "=")  # Cut off pipe, then split into k,v pair
            if len(split) > 2:
                if DEBUG:
                    print(
                        "Oh, my, a raw event line with more than key and "
                        "value!")
            if DEBUG:
                pprint(split)

            if split[0] == 'description':
                description = " ".join(rawevent[no:]).split("|description=")[1]
                description = description.lstrip().rstrip()
                description = strip_tags(description)
                event['description'] = description
                break
            if split[0] in event.keys():
                if split[0] in ('id', 'day'):
                    try:
                        if split[0] == 'id':
                            split[1] = int(split[1]) + 1
                        else:
                            split[1] = int(split[1])
                    except TypeError:
                        if DEBUG:
                            print("Malformed ID or day in event! "
                                  "Appending string for inspection.")
                    event[split[0]] = split[1]
                else:
                    event[split[0]] = strip_tags(split[1])

        if DEBUG:
            pprint(event)
        events.append(event)

        # pprint(rawevents)

    return events


def get_infobeamer_events():
    lectures = get_events('Lecture')
    workshops = get_events('Workshop')
    hacksessions = get_events('Hacking')

    all_events = lectures + workshops + hacksessions

    infobeamer_events = []

    for event in all_events:
        hours = event['start'].split(":")
        duration = event['duration'].split(":")

        # TODO: Fetch static parts from conference metadata above
        start = datetime(2016, 4, 9 + int(event['day']), hour=int(hours[0]),
                         minute=int(hours[1]), tzinfo=pytz.utc) #pytz.timezone(
                #"Europe/Berlin"))
        #print(start)
        #print(hours)


        #print(start)
        unixtime = int(calendar.timegm(start.timetuple()))
        # TODO: Mean hack, we should do that better:
        unixtime -= (120*60)
        #print("This is the timestamp:", unixtime)
        duration = (int(duration[0]) * 60 + int(duration[1]))
        stop = unixtime + int(duration) * 60
        if DEBUG:
            print(event['room'], start, stop, event['title'])

        new = {
            'title': event['title'],
            'event_id': event['id'],
            'place': event['room'],
            'unix_end': stop,
            'unix': unixtime,
            'duration': duration,
            'speakers': event['people'].split(", "),
            'lines': event['description'][:200].split("."),
            'lang': 'en',
            'start': event['start']
        }
        if len(new['lines']) == 100:
            new['lines'] += " - for more information, check the wiki."

        infobeamer_events.append(new)

    sortedlist = sorted(infobeamer_events, key=lambda k: k['unix'])

    return sortedlist


def get_voc_events():
    lectures = get_events('Lecture')
    workshops = get_events('Workshop')
    hacksessions = get_events('Hacking')

    all_events = lectures + workshops + hacksessions

    return all_events


def generate_schedule(scheduletype):
    if DEBUG:
        print("Generating for %s" % scheduletype)
    if scheduletype == 'voc':
        events = get_voc_events()
        conference['events'] = events
        return conference
    elif scheduletype == 'infobeamer':
        events = get_infobeamer_events()
        return events


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputfile",
                        help="Specify output filename",
                        default="schedule.json")
    parser.add_argument("--cachefile",
                        help="Read from given cache file",
                        default="schedule.cache.json")
    parser.add_argument("--debug",
                        help="Printout debug info to STDOUT(!)",
                        action="store_true")
    parser.add_argument("--writecache",
                        help="Store retrieved data to a file",
                        action="store_true")
    parser.add_argument("--readcache",
                        help="Read cache from file",
                        action="store_true")
    parser.add_argument("--offline",
                        help="Read cache and stay offline, do not write cache",
                        action="store_true")
    parser.add_argument("--scheduletype",
                        default='voc',
                        help="Either 'voc' or 'infobeamer' - infobeamer "
                             "generates minilac-room-next-node compatible "
                             "json, voc generates for c3voc's tracker.")

    args = parser.parse_args()

    if args.debug:
        DEBUG = True

    if args.offline:
        OFFLINE = True

    if args.readcache or args.offline:
        with open(args.cachefile, "r") as f:
            webdatacache = json.load(f)

    with open(args.outputfile, "w") as f:
        json.dump(generate_schedule(args.scheduletype), f, indent=4,
                  sort_keys=True)

    if args.writecache and not args.offline:
        with open(args.cachefile, "w") as f:
            json.dump(webdatacache, f)

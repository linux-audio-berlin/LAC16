#!/usr/bin/env python

# miniLAC16 schedule exporter
# ===========================
# Copyright (C) 2016 riot <riot@c-base.org>
#
# GPLv3

__author__ = 'riot'

import sys
from pprint import pprint
import argparse
import requests
import json

DEBUG = False

baseurl = "http://minilac.linuxaudio.org/api.php?action=parse&page=%s&prop=wikitext&format=json"

conference = {
    'conference': {
        'acronym': 'miniLAC16',
        'title': 'Mini Linux Audio Conference 2016',
        'basedate': '2016-04-08',
        'timezone': 'Europe/Berlin',
        'license': 'CC-BY-SA',
        'language': 'en'
    },
    'events': {}
}

rooms = [
    'Mainhall',
    'Weltenbaulab',
    'Seminar_room',
    'Upper_Deck',
    'Soundlab'
]

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
    webdata = requests.get(baseurl % eventtype)

    if DEBUG:
        pprint(webdata.json(), indent=1)

    wikidata = "".join(list(webdata.json()['parse']['wikitext']['*']))
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
            'id': 0,
            'room': '',
            'day': 0,  # only valid when basedate is given, use full datetime in 'start' otherwise
            'start': '',  # can be a whole ISO datetime, otherwise, 'basedate' is used as a base
            'duration': '01:00',  # alternative: 'end'

            'people': '',  # can be an array. alias: 'persons'

            'type': eventtype,  # optional. default: lecture
            'license': 'CC-BY-SA',  # optional


            'description': '',  # optional
        }

        for no, line in enumerate(rawevent):
            if DEBUG:
                print(line)
            split = line[1:].split("=")  # Cut off pipe, then split into k,v pair
            if len(split) > 2:
                if DEBUG:
                    print("Oh, my, a raw event line with more than key and value!")
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
                        split[1] = int(split[1])
                    except TypeError:
                        if DEBUG:
                            print("Malformed ID or day in event! Appending string for inspection.")
                    event[split[0]] = split[1]
                else:
                    event[split[0]] = strip_tags(split[1])

        if DEBUG:
            pprint(event)
        events.append(event)

        # pprint(rawevents)

    return events

def generate_schedule():
    lectures = get_events('Lecture')
    workshops = get_events('Workshop')
    hacksessions = get_events('Hacking')

    all_events = lectures + workshops + hacksessions
    conference['events'] = all_events
    return conference


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputfile", help="Specify output filename", type=str, default="schedule.json")
    parser.add_argument("--debug", help="Printout debug info to STDOUT(!)", action="store_true")

    args = parser.parse_args()

    if args.debug:
        DEBUG = True

    with open(args.outputfile, "w") as f:
        json.dump(generate_schedule(), f, indent=4)

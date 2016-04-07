#!/usr/bin/env python

# miniLAC16 schedule exporter
# ===========================
# Copyright (C) 2016 riot <riot@c-base.org>
#
# GPLv3

__author__ = 'riot'

from os import environ
from pprint import pprint
import argparse
import requests
import json

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
    if "[[" not in markup:
        return markup
    wobble = markup
    ham = ""
    while '[[' in wobble:
        wibble, wobble = wobble.split("[[", maxsplit=1)
        ham += wibble

        spam, wobble = wobble.split("]]", maxsplit=1)

        if spam.startswith('User'):
            print("Found a user: ", spam)
            ham += str(spam.split("|")[1])
        if spam in rooms:
            print("Room encountered")
            ham += spam
        elif spam.startswith('Image'):
            print("Found an image: ", spam)

    ham += wobble

    return ham


def get_events(eventtype="Lecture"):
    webdata = requests.get(baseurl % eventtype)

    # pprint(webdata.json(), indent=1)

    wikidata = "".join(list(webdata.json()['parse']['wikitext']['*']))
    rawevents = []
    events = []

    for no, part in enumerate(wikidata.split("{{Template:" + eventtype)):
        if not no == 0:
            print("#" * 5)
            part = part.split("}}")[0]

            print(part)
            rawevents.append(part)

    for rawevent in rawevents:
        rawevent = rawevent.split("\n")
        print(rawevent)
        event = {
            'title': '',
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
            print(line)
            split = line[1:].split("=")  # Cut off pipe, then split into k,v pair
            if len(split) > 2:
                print("Oh, my, a raw event line with more than key and value!")
            pprint(split)

            if split[0] == 'description':
                description = " ".join(rawevent[no:]).split("|description=")[1]
                description = description.lstrip().rstrip()
                description = strip_tags(description)
                event['description'] = description
                break
            if split[0] in event.keys():
                event[split[0]] = strip_tags(split[1])

        pprint(event)
        events.append(event)

        # pprint(rawevents)

    return events

def generate_schedule(events):
    conference['events'] = events
    return conference


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputfile", help="Specify output filename", type=str, default="schedule.json")

    args = parser.parse_args()

    events = get_events()

    with open(args.outputfile, "w") as f:
        json.dump(generate_schedule(events), f, indent=4)

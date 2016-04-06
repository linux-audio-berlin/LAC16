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

def stripImages(description):
    wobble = description
    ham = ""
    while '[[' in wobble:
        wibble, wobble = wobble.split("[[", maxsplit=1)
        ham += wibble

        spam, wobble = wobble.split("]]", maxsplit=1)

        if spam.startswith('User'):
            print("Found a user: ", spam)
            ham += str(spam.split("|")[1])
        elif spam.startswith('Image'):
            print("Found an image: ", spam)
    print(ham)

    return ham


def getEvents(eventtype="Lecture"):
    webdata = requests.get(baseurl % eventtype)

    # pprint(webdata.json(), indent=1)

    wikidata = "".join(list(webdata.json()['parse']['wikitext']['*']))
    rawevents = []

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
            'subtitle': '',
            'room': '',
            'track': '',  # optional
            'day': 0,  # only valid when basedate is given, use full datetime in 'start' otherwise
            'start': '',  # can be a whole ISO datetime, otherwise, 'basedate' is used as a base
            'duration': '01:00',  # alternative: 'end'

            'people': '',  # can be an array. alias: 'persons'

            'type': eventtype,  # optional. default: lecture
            'optout': False,  # optional. default: false
            'license': 'CC-BY-SA',  # optional
            'language': '',  # optional, if given in 'conference' section

            'abstract': '',  # optional
            'description': '',  # optional
            'links': [  # optional
                {
                    'href': '',
                    'text': 'Null'
                }
            ]
        }

        for no, line in enumerate(rawevent):
            print(line)
            split = line[1:].split("=")  # Cut off pipe, then split into k,v pair
            if len(split) > 2:
                print("Oh, my, a raw event line with more than key and value!")
            pprint(split)

            if split[0] == 'description':
                description = "".join(rawevent[no:]).split("|description=")[1]
                description = description.lstrip().rstrip()
                description = stripImages(description)
                event['description'] = description
                break
            if split[0] in event.keys():
                event[split[0]] = split[1]

        pprint(event)

        # pprint(rawevents)


def generate_schedule(args):
    def processday(day):
        stuff = day.split("Schedule")[1]
        stuff = stuff.split("}}")[0]
        print("-" * 23)
        pprint(stuff)

    inputlines = ""
    with open(args.inputfile) as f:
        for line in f:
            inputlines += line

    parts = inputlines.split("Timetable")
    parts.remove(parts[0])
    print(len(parts))
    for day in parts:
        print("#" * 23)
        processday(day)

    grab = False
    date = None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputfile", help="Specify input filename", type=str, default="input.wiki")

    args = parser.parse_args()

    getEvents()
    # generate_schedule(args)

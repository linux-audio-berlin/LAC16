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

def generate_schedule(args):
    def processday(day):
        stuff = day.split("Schedule")[1]
        stuff = stuff.split("}}")[0]
        print("-"*23)
        pprint(stuff)

    inputlines = ""
    with open(args.inputfile) as f:
        for line in f:
            inputlines += line

    parts = inputlines.split("Timetable")
    parts.remove(parts[0])
    print(len(parts))
    for day in parts:
        print("#"*23)
        processday(day)

    grab = False
    date = None



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputfile", help="Specify input filename", type=str, default="input.wiki")

    args = parser.parse_args()

    generate_schedule(args)

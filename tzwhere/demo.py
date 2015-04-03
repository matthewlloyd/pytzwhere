#!/usr/bin/python

import datetime
import argparse
from tzwhere import tzwhere


def main():
    parser = argparse.ArgumentParser(description="Convert lat/lng to timezones.")
    parser.add_argument('--json_file', default='tz_world_compact.json',
                    help='path to the json input file')
    parser.add_argument('--pickle_file', default='tz_world.pickle',
                    help='path to the pickle input file')
    parser.add_argument('--read_pickle', action='store_true',
                    help='read pickle data instead of json')
    parser.add_argument('--write_pickle', action='store_true',
                    help='whether to output a pickle file')
    args = parser.parse_args()

    if args.read_pickle:
        filename = args.pickle_file
    else:
        filename = args.json_file

    start = datetime.datetime.now()
    w = tzwhere(filename, args.read_pickle, args.write_pickle)
    end = datetime.datetime.now()
    print 'Initialized in: ',
    print end-start
    print w.tzNameAt(float(35.295953), float(-89.662186)) #Arlington, TN
    print w.tzNameAt(float(33.58), float(-85.85)) #Memphis, TN
    print w.tzNameAt(float(61.17), float(-150.02)) #Anchorage, AK
    print w.tzNameAt(float(44.12), float(-123.22)) #Eugene, OR
    print w.tzNameAt(float(42.652647), float(-73.756371)) #Albany, NY


if __name__ == "__main__":
    main()

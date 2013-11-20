#!/usr/bin/env python3
"""
honstats console statistics program for Heroes of Newerth

This file is part of honstats.

honstats is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

honstats is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with honstats.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import os
import argparse
import configparser

import text
import html
from provider import HttpDataProvider


def printoutput(output):
    print(output, end='')


def playercommand(args):
    printoutput(args.outputobj.playerinfo(args.id, args.statstype))


def matchescommand(args):
    printoutput(args.outputobj.matchesinfo(args.id, args.statstype, args.limit))


def matchcommand(args):
    printoutput(args.outputobj.matchinfo(args.id))


def playerheroesscommand(args):
    printoutput(args.outputobj.playerheroesinfo(
        args.id, args.statstype, args.sort_by, args.order, args.limit))


def lastmatchescommand(args):
    printoutput(args.outputobj.lastmatchesinfo(
        args.id, args.statstype, args.hero, args.limit, args.count))


def heroescommand(args):
    printoutput(args.outputobj.heroesinfo(args.limit))


def main():
    parser = argparse.ArgumentParser(description='honstats fetches and displays Heroes of Newerth statistics')
    parser.add_argument('-q', '--quiet', action='store_true', help='Limit exception output to one liners')
    parser.add_argument('--host', default='api.heroesofnewerth.com', help='statistic host provider')
    parser.add_argument('-l', '--limit', type=int, help='Limit output to the given number')
    parser.add_argument('-t', '--token', help="hon statistics token")
    parser.add_argument('-s', '--statstype', choices=['ranked', 'public', 'casual'],
                        default='ranked', help='Statstype to show')
    parser.add_argument('--config', default='/etc/honstats', help='path to configuration file')
    parser.add_argument('-o', '--outputmode', choices=['text', 'html'], default='text', help='set output mode')

    subparsers = parser.add_subparsers(help='honstats commands')
    playercmd = subparsers.add_parser('player', help='Show player stats')
    playercmd.set_defaults(func=playercommand)
    playercmd.add_argument('id', nargs='+', help='Player nickname or hon id')

    matchescmd = subparsers.add_parser('matches', help='Show matches of a player(s)')
    matchescmd.set_defaults(func=matchescommand)
    matchescmd.add_argument('id', nargs='+', help='Player nickname or hon id')

    matchcmd = subparsers.add_parser('match', help='Show stats for match(es)')
    matchcmd.set_defaults(func=matchcommand)
    matchcmd.add_argument('matchid', nargs='+', help='HoN match id')

    playerheroescmd = subparsers.add_parser('player-heroes', help='Show stats for heroes played')
    playerheroescmd.set_defaults(func=playerheroesscommand)
    playerheroescmd.add_argument('id', nargs='+', help='Player nickname or hon id')
    playerheroescmd.add_argument('-b', "--sort-by", choices=['use', 'kdr', 'k', 'd', 'a',
                                 'kpg', 'dpg', 'apg', 'gpm', 'wpg', 'wins', 'losses', 'wlr'],
                                 default='use', help='Sort by specified stat')
    playerheroescmd.add_argument('-o', "--order", choices=['asc', 'desc'], default='desc', help='sort order')

    lastmatchescmd = subparsers.add_parser('lastmatches', help='lastmatches for a player')
    lastmatchescmd.set_defaults(func=lastmatchescommand)
    lastmatchescmd.add_argument('id', nargs='+', help='Player nickname or hon id')
    lastmatchescmd.add_argument('-c', '--count', default=3, type=int, help='How many games')
    lastmatchescmd.add_argument('--hero', type=str, help='Filter to games with a certian hero')

    heroescmd = subparsers.add_parser('heroes', help='Show hero statistics')
    heroescmd.set_defaults(func=heroescommand)

    args = parser.parse_args()

    try:
        configpath = args.config
        if not os.path.exists(configpath):
            configpath = os.path.expanduser('~/.config/honstats/config')
        if os.path.exists(configpath):
            cp = configparser.ConfigParser({'directory': os.path.expanduser('~/.honstats')})
            cp.read(configpath)
        else:
            cp = {}

        if not args.token and not 'auth' in cp:
            sys.exit('Token not specified and no config file found.')
        else:
            args.token = cp.get('auth', 'token')

        host = "http://{host}".format(host=cp.get('auth', 'host', fallback=args.host))

        if 'func' in args:
            args.dataprovider = HttpDataProvider(host, token=args.token, cachedir=cp.get('cache', 'directory'))

            # set output class
            if args.outputmode == 'html':
                args.outputobj = html.Html(args.dataprovider)
            else:
                args.outputobj = text.Text(args.dataprovider)

            args.func(args)
        else:
            parser.print_help()
    except Exception as e:
        if args.quiet:
            sys.stderr.write(str(e) + '\n')
        else:
            raise e

if __name__ == "__main__":
    main()

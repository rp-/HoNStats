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

from data import Player, Match, Hero
from provider import HttpDataProvider


def playercommand(args):
    print(Player.header())

    for id_ in args.id:
        #print(url)
        data = args.dataprovider.fetchplayer(id_, args.statstype)
        nickname = args.dataprovider.id2nick(int(data['account_id']))
        player = Player(nickname, data)
        #print(json.dumps(data))
        print(player.str())


def matchescommand(args):
    for id_ in args.id:
        matchids = args.dataprovider.matches(id_, args.statstype)

        limit = args.limit if args.limit else len(matchids)
        print(args.dataprovider.id2nick(id_))
        print(Match.headermatches())
        for i in range(limit):
            matches = args.dataprovider.fetchmatchdata([matchids[i]])
            match = Match.creatematch(matches[matchids[i]])
#        matches = args.dataprovider.fetchmatchdata(matchids[:limit])
#        for matchid in matchids[:limit]:
#            match = Match(matches[matchid])
            print(match.matchesstr(args.dataprovider.nick2id(id_), args.dataprovider))
        #print(json.dumps(history))


def matchcommand(args):
    matches = args.dataprovider.fetchmatchdata(args.matchid)
    for mid in args.matchid:
        match = Match.creatematch(matches[mid])
        print(match.matchstr(args.dataprovider))


def playerherosscommand(args):
    for id_ in args.id:
        data = args.dataprovider.fetchplayer(id_, args.statstype)
        nickname = args.dataprovider.id2nick(int(data['account_id']))
        player = Player(nickname, data)
        stats = player.playerheros(args.dataprovider, args.statstype, args.sort_by, args.order)

        limit = args.limit if args.limit else len(stats)
        print(args.dataprovider.id2nick(id_))
        print(Player.PlayerHeroHeader)
        for i in range(limit):
            stat = stats[i]
            stat['hero'] = args.dataprovider.heroid2name(stat['heroid'])[:10]
            print(Player.PlayerHeroFormat.format(**stat))


def lastmatchescommand(args):
    for id_ in args.id:
        id_hero = (id_, args.hero) if args.hero else None
        matchids = args.dataprovider.matches(id_, args.statstype)
        limit = args.limit if (args.limit or args.count) < args.count else args.count
        matches = args.dataprovider.fetchmatchdata(matchids, limit=limit, id_hero=id_hero)
        print(args.dataprovider.id2nick(id_))
        for mid in sorted(matches.keys(), reverse=True):
            match = Match.creatematch(matches[mid])
            print(match.matchstr(args.dataprovider))

def heroescommand(args):
    heroesdata = args.dataprovider.heroes()
    heroids = list(heroesdata.keys())
    heroids.sort(key=int)
    limit = args.limit if args.limit else len(heroids)
    for heroidindex in range(limit):
        hero = Hero(heroesdata[heroids[heroidindex]])
        print(hero.herostr())

def main():
    parser = argparse.ArgumentParser(description='honstats fetches and displays Heroes of Newerth statistics')
    parser.add_argument('-q', '--quiet', action='store_true', help='Limit exception output to one liners')
    parser.add_argument('--host', default='api.heroesofnewerth.com', help='statistic host provider')
    parser.add_argument('-l', '--limit', type=int, help='Limit output to the given number')
    parser.add_argument('-t', '--token', help="hon statistics token")
    parser.add_argument('-s', '--statstype', choices=['ranked', 'public', 'casual'],
                        default='ranked', help='Statstype to show')

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

    playerheroscmd = subparsers.add_parser('player-heros', help='Show stats for heros played')
    playerheroscmd.set_defaults(func=playerherosscommand)
    playerheroscmd.add_argument('id', nargs='+', help='Player nickname or hon id')
    playerheroscmd.add_argument('-b', "--sort-by", choices=['use', 'kdr', 'k', 'd', 'a',
                                                            'kpg', 'dpg', 'apg', 'gpm', 'wpg', 'wins', 'losses'],
                                default='use', help='Sort by specified stat')
    playerheroscmd.add_argument('-o', "--order", choices=['asc', 'desc'], default='desc', help='sort order')

    lastmatchescmd = subparsers.add_parser('lastmatches', help='lastmatches for a player')
    lastmatchescmd.set_defaults(func=lastmatchescommand)
    lastmatchescmd.add_argument('id', nargs='+', help='Player nickname or hon id')
    lastmatchescmd.add_argument('-c', '--count', default=3, type=int, help='How many games')
    lastmatchescmd.add_argument('--hero', type=str, help='Filter to games with a certian hero')

    heroescmd = subparsers.add_parser('heroes', help='Show hero statistics')
    heroescmd.set_defaults(func=heroescommand)

    args = parser.parse_args()

    try:
        configpath = '/etc/honstats'
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
            args.dataprovider = HttpDataProvider(host, token=args.token,  cachedir=cp.get('cache', 'directory'))
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

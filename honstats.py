#!/usr/bin/env python3
import sys
import os
import argparse
import configparser

from data import Player, Match
from provider import DataProvider, HttpDataProvider

"""honstats console statistics program for Heroes of Newerth
"""
def playercommand(args):
    print(Player.header())

    for id in args.id:
        #print(url)
        data = args.dataprovider.fetch('player_statistics/' + args.statstype + DataProvider.nickoraccountid(id))
        player = Player(id, data)
        #print(json.dumps(data))
        print(player.str(args.statstype))

def matchescommand(args):
    for id in args.id:
        data = args.dataprovider.fetchmatches(id, args.statstype)
        history = ""
        if len(data) > 0:
            history = data[0]['history']
        hist = history.split(',')
        limit = args.limit if args.limit else len(hist)
        matchids = [ int(x.split('|')[0]) for  x in hist ]
        matchids = sorted(matchids, reverse=True)

        print(args.dataprovider.id2nick(id))
        print(Match.headermatches())
        for i in range(limit):
            match = Match(args.dataprovider.fetchmatchdata(matchids[i]))
            print(match.matchesstr(args.dataprovider.nick2id(id), args.dataprovider))
        #print(json.dumps(history))

def matchcommand(args):
    print(args)

def main():
    parser = argparse.ArgumentParser(description='honstats fetches and displays Heroes of Newerth statistics')
    #parser.add_argument('--host', default='http://api.heroesofnewerth.com/', help='statistic host provider')
    parser.add_argument('--host', default='http://localhost:1234/', help='statistic host provider')
    parser.add_argument('-t', '--token', help="hon statistics token")
    parser.add_argument('-s', '--statstype', choices=['ranked', 'public', 'casual'], default='ranked', help='Statstype to show')

    subparsers = parser.add_subparsers(help='honstats commands')
    playercmd = subparsers.add_parser('player', help='Show player stats')
    playercmd.set_defaults(func=playercommand)
    playercmd.add_argument('id', nargs='+', help='Player nickname or hon id')

    matchescmd = subparsers.add_parser('matches', help='Show matches of a player(s)')
    matchescmd.set_defaults(func=matchescommand)
    matchescmd.add_argument('-l', '--limit', type=int, help='Limit output to the given number')
    matchescmd.add_argument('id', nargs='+', help='Player nickname or hon id')

    matchescmd = subparsers.add_parser('match', help='Show stats for match(es)')
    matchescmd.set_defaults(func=matchcommand)
    matchescmd.add_argument('matchid', nargs='+', help='HoN match id')

    args = parser.parse_args()

    configpath = '/etc/honstats'
    if not os.path.exists(configpath):
        configpath = os.path.expanduser('~/.config/honstats/config')
    if os.path.exists(configpath):
        cp = configparser.ConfigParser()
        cp.read(configpath)
    else:
        cp = {}

    if not args.token and not 'auth' in cp:
        sys.exit('Token not specified and no config file found.')
    else:
        args.token = cp.get('auth', 'token')

    if 'func' in args:
        args.dataprovider = HttpDataProvider(args.host, token=args.token,  cachedir=cp.get('cache', 'directory'))
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

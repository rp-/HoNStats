#!/usr/bin/env python3
import sys
import os
import argparse
import urllib.request
import json
import configparser

"""honstats console statistics program for Heroes of Newerth
"""
dp = None

class DataProvider(object): pass

class HttpDataProvider(DataProvider):
    def __init__(self, url = 'http://api.heroesofnewerth.com/', token=None):
        self.url = url
        self.token = token

    def fetch(self, path):
        resp = urllib.request.urlopen(self.url + path + "/?token=" + self.token)
        return json.loads(resp.read().decode('utf-8'))

class FSDataProvider(DataProvider):
    def __init__(self, url = './sampledata'):
        self.url = os.path.abspath(url)

    def fetch(self, path):
        with open(os.path.join(self.url, path)) as fd:
            return json.load(fd)

def nickoraccountid(id):
    try:
        int(id)
        return '/accountid/' + id
    except ValueError:
        return '/nickname/' + id

def playercommand(args):
    headerformat = "{nick:<10s} {mmr:<5s} {k:<6s} {d:<6s} {a:<6s} {wg:<3s} {cd:<5s} {kdr:<5s} {gp:<4s} {wp:<2s}"
    playerformat = "{nick:<10s} {rank:<5d} {k:<6d}/{d:<6d}/{a:<6d} {wg:3.1f} {cd:4.1f} {kdr:5.2f}  {pg:<4d} {wp:2.0f}"

    print(headerformat.format(nick="Nick",
                              mmr="MMR",
                              k="K",
                              d="D",
                              a="A",
                              wg="W/G",
                              cd="CD",
                              kdr="KDR",
                              gp="GP",
                              wp="W%"))

    statsmapping = { 'ranked': 'rnk', 'public': 'acc', 'casual': 'cs'}
    prefix = statsmapping[args.statstype]
    for id in args.id:
        #print(url)
        data = dp.fetch('player_statistics/' + args.statstype + nickoraccountid(id))
        #print(json.dumps(data))
        print(playerformat.format(nick=id,
                                  rank=int(float(data[prefix + '_amm_team_rating'])),
                                  k=int(data[prefix + '_herokills']),
                                  d=int(data[prefix + '_deaths']),
                                  a=int(data[prefix + '_heroassists']),
                                  wg=int(data[prefix + '_wards'])/int(data[prefix + '_games_played']),
                                  cd=int(data[prefix + '_denies'])/int(data[prefix + '_games_played']),
                                  kdr=int(data[prefix + '_herokills'])/int(data[prefix + '_deaths']),
                                  pg=int(data[prefix + '_games_played']),
                                  wp=int(data[prefix + '_wins'])/int(data[prefix + '_games_played'])*100))

def matchescommand(args):
    for id in args.id:
        path = 'match_history/' + args.statstype + nickoraccountid(id)
        data = dp.fetch(path)
        print(json.dumps(data))

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
    matchescmd.add_argument('id', nargs='+', help='Player nickname or hon id')

    matchescmd = subparsers.add_parser('match', help='Show stats for match(es)')
    matchescmd.set_defaults(func=matchcommand)
    matchescmd.add_argument('matchid', nargs='+', help='HoN match id')

    args = parser.parse_args()

    if not args.token:
        # read token from config file
        configpath = '/etc/honstats'
        if not os.path.exists(configpath):
            configpath = os.path.expanduser('~/.config/honstats/config')
            if not os.path.exists(configpath):
                sys.exit('Token not specified and now config file found.')
        cp = configparser.ConfigParser()
        cp.read(configpath)
        args.token = cp.get('auth', 'token')

    if 'func' in args:
        global dp
        dp = FSDataProvider() #development url
        #dp = HttpDataProvider(args.host, token=args.token)
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

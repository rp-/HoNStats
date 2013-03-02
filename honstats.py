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

class Stats(object):
    DefaultStatsType = 'ranked'

class Player(object):
    StatsMapping = { 'ranked': 'rnk', 'public': 'acc', 'casual': 'cs'}
    HeaderFormat = "{nick:<10s} {mmr:<5s} {k:<6s} {d:<6s} {a:<6s} {wg:<3s} {cd:<5s} {kdr:<5s} {gp:<4s} {wp:<2s}"
    PlayerFormat = "{nick:<10s} {rank:<5d} {k:<6d}/{d:<6d}/{a:<6d} {wg:3.1f} {cd:4.1f} {kdr:5.2f}  {pg:<4d} {wp:2.0f}"

    def __init__(self, nickname, data):
        self.nickname = nickname
        self.data = data

    def rating(self, type = Stats.DefaultStatsType):
        if 'public' != type:
            return int(float(self.data[self.StatsMapping[type] + '_amm_team_rating']))
        return int(float(self.data['acc_pub_skill']))

    def kills(self, type = Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type] + '_herokills'])

    def deaths(self, type = Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type] + '_deaths'])

    def assists(self,  type = Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type] + '_heroassists'])

    def gamesplayed(self, type = Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type] + '_games_played'])

    def wards(self, type = Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type] + '_wards'])

    def denies(self, type = Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type] + '_denies'])

    def wins(self, type = Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type] + '_wins'])

    @staticmethod
    def header(type=Stats.DefaultStatsType):
        return Player.HeaderFormat.format(nick="Nick",
                              mmr="MMR",
                              k="K",
                              d="D",
                              a="A",
                              wg="W/G",
                              cd="CD",
                              kdr="KDR",
                              gp="GP",
                              wp="W%")

    @staticmethod
    def nickoraccountid(id):
        try:
            int(id)
            return '/accountid/' + id
        except ValueError:
            return '/nickname/' + id

    def str(self, type=Stats.DefaultStatsType):
        return Player.PlayerFormat.format(nick=self.nickname,
                          rank=self.rating(type),
                          k=self.kills(type),
                          d=self.deaths(type),
                          a=self.assists(type),
                          wg=self.wards(type)/self.gamesplayed(type),
                          cd=self.denies(type)/self.gamesplayed(type),
                          kdr=self.kills(type)/self.deaths(type),
                          pg=self.gamesplayed(type),
                          wp=self.wins(type)/self.gamesplayed(type)*100)

def playercommand(args):
    print(Player.header())

    for id in args.id:
        #print(url)
        data = dp.fetch('player_statistics/' + args.statstype + Player.nickoraccountid(id))
        player = Player(id, data)
        #print(json.dumps(data))
        print(player.str(args.statstype))

def matchescommand(args):
    for id in args.id:
        path = 'match_history/' + args.statstype + Player.nickoraccountid(id)
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
        #dp = FSDataProvider() #development url
        dp = HttpDataProvider(args.host, token=args.token)
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

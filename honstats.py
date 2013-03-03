#!/usr/bin/env python3
import sys
import os
import argparse
import urllib.request
from urllib.error import HTTPError
import json
import configparser
import gzip
import time

"""honstats console statistics program for Heroes of Newerth
"""
dp = None

class DataProvider(object):
    MatchCacheDir = 'match'
    PlayerCacheDir = 'player'

class HttpDataProvider(DataProvider):
    def __init__(self, url = 'http://api.heroesofnewerth.com/', token=None, cachedir=None):
        self.url = url
        self.token = token
        self.cachedir = os.path.abspath(os.path.expanduser(cachedir))
        if self.cachedir:
            os.makedirs(os.path.join(self.cachedir, DataProvider.MatchCacheDir), exist_ok=True)
            os.makedirs(os.path.join(self.cachedir, DataProvider.PlayerCacheDir), exist_ok=True)

    def fetch(self, path):
        url = self.url + path + "/?token=" + self.token
        #print(url)
        try:
            resp = urllib.request.urlopen(url)
        except HTTPError as e:
            if e.code == 429: #too much requests
                time.sleep(0.1) # this might be a bit harsh, but fetch until we get what we want
                return self.fetch(path)
            raise e
        return json.loads(resp.read().decode('utf-8'))

    def fetchmatches(self, id, statstype):
        playerdir = os.path.join(self.cachedir,  DataProvider.PlayerCacheDir)
        #TODO: make sure id is the accountid
        #TODO: only cache for a certain time 10mins?
        playermatches = os.path.join(playerdir, "{id}_matches.{statstype}".format(id=id, statstype=statstype))
        if os.path.exists(playermatches):
            with gzip.open(playermatches, 'rt') as f:
                data = json.load(f)
        else:
            path = 'match_history/' + statstype + Player.nickoraccountid(id)
            data = dp.fetch(path)
            with gzip.open(playermatches,'wt+') as f:
                f.write(json.dumps(data))
        return data

    def fetchmatch(self, matchid):
        """Fetches match data by id and caches it onto disk
           First checks if the match stats are already cached
        """
        matchdir = os.path.join(self.cachedir,  DataProvider.MatchCacheDir)
        matchpath = os.path.join(matchdir, matchid[0:4])
        os.makedirs(matchpath, exist_ok=True)
        matchpath = os.path.join(matchpath, matchid)
        if os.path.exists(matchpath):
            with gzip.open(matchpath, 'rt') as f:
                data = json.load(f)
        else:
            data = self.fetch('match/summ/matchid/{id}'.format(id=matchid))
            matchstats = self.fetch('match/all/matchid/{id}'.format(id=matchid))
            data.append(matchstats[0][0]) # settings
            data.append(matchstats[1]) # items
            data.append(matchstats[2]) # player stats
            with gzip.open(matchpath, 'wt+') as f:
                f.write(json.dumps(data))
        return Match(data)

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

class Match(object):
    def __init__(self, data):
        self.data = data

    def str(self):
        return self.data[0]['match_id']

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
        data = dp.fetchmatches(id, args.statstype)
        history = ""
        if len(data) > 0:
            history = data[0]['history']
        hist = history.split(',')
        limit = args.limit if args.limit else len(hist)
        for i in range(limit):
            matchid, _, date = hist[i].split('|')
            match = dp.fetchmatch(matchid)
            print(match.str())
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
        global dp
        #dp = FSDataProvider() #development url
        dp = HttpDataProvider(args.host, token=args.token,  cachedir=cp.get('cache', 'directory'))
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

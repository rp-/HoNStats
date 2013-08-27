"""
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
import json
from datetime import timedelta

from datetimeutil import Local, parsedate


class Stats(object):
    DefaultStatsType = 'ranked'
    CacheTime = 60 * 5


class Player(object):
    StatsMapping = {'ranked': 'rnk', 'public': 'acc', 'casual': 'cs'}
    HeaderFormat = "{nick:<10s} {mmr:<5s} {k:<6s} {d:<6s} {a:<6s} {wg:<3s} {cd:<5s} {kdr:<5s} {gp:<4s} {wp:<2s}"
    PlayerFormat = "{nick:<10s} {rank:<5d} {k:<6d}/{d:<6d}/{a:<6d} {wg:3.1f} {cd:4.1f} {kdr:5.2f}  {pg:<4d} {wp:2.0f}"

    PlayerHeroHeaderFormat = "{hero:<10s} {use:<3s} {perc:<2s} {k:3s} " \
        "{d:<3s} {a:<3s} {kdr:<5s} {w:<2s} {l:<2s} {kpg:<5s} " \
        "{dpg:<5s} {apg:<5s} {gpm:<3s} {wpg:<3s}"
    PlayerHeroHeader = PlayerHeroHeaderFormat.format(hero='Hero', use='Use',
                                                          perc=' %', k='  K', d='  D',
                                                          a='  A', kdr='KDR', w='W',
                                                          l='L', kpg='KPG', dpg='DPG',
                                                          apg='APG', gpm='GPM',
                                                          wpg='WPG')

    PlayerHeroFormat = "{hero:<10s} {use:3d} {perc:2d} {k:3d} " \
        "{d:3d} {a:3d} {kdr:<5.2f} {wins:<2d} {losses:<2d} {kpg:<5.2f} " \
        "{dpg:<5.2f} {apg:<5.2f} {gpm:<3d} {wpg:<3.1f}"

    def __init__(self, nickname, data):
        self.nickname = nickname
        self.data = data

    def id(self):
        return int(self.data['account_id'])

    def nickname(self):
        return self.nickname

    def rating(self, type_=Stats.DefaultStatsType):
        if 'public' != type_:
            return int(float(self.data[self.StatsMapping[type_] + '_amm_team_rating']))
        return int(float(self.data['acc_pub_skill']))

    def kills(self, type_=Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type_] + '_herokills'])

    def deaths(self, type_=Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type_] + '_deaths'])

    def assists(self,  type_=Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type_] + '_heroassists'])

    def gamesplayed(self, type_=Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type_] + '_games_played'])

    def wards(self, type_=Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type_] + '_wards'])

    def denies(self, type_=Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type_] + '_denies'])

    def wins(self, type_=Stats.DefaultStatsType):
        return int(self.data[Player.StatsMapping[type_] + '_wins'])

    def playerheroes(self, dp, type_=Stats.DefaultStatsType, sortby='use', order='asc'):
        matches = dp.matches(self.id(), type_)
        playerhero = {}
        matchdata = dp.fetchmatchdata(matches)
        for matchid in matchdata:
            match = Match.creatematch(matchdata[matchid])
            heroid = int(match.playerstat(self.id(), 'hero_id'))
            if not heroid in playerhero:
                playerhero[heroid] = {'heroid': heroid,
                                      'use': 0,
                                      'k': 0,
                                      'd': 0,
                                      'a': 0,
                                      'wins': 0,
                                      'losses': 0,
                                      'gpm': 0,
                                      'wards': 0,
                                      'gold': 0,
                                      'playedtime': 0}
            playerhero[heroid]['use'] += 1
            playerhero[heroid]['k'] += int(match.playerstat(self.id(), 'herokills'))
            playerhero[heroid]['d'] += int(match.playerstat(self.id(), 'deaths'))
            playerhero[heroid]['a'] += int(match.playerstat(self.id(), 'heroassists'))
            playerhero[heroid]['wins'] += int(match.playerstat(self.id(), 'wins'))
            playerhero[heroid]['losses'] += int(match.playerstat(self.id(), 'losses'))
            playerhero[heroid]['gold'] += int(match.playerstat(self.id(), 'gold'))
            playerhero[heroid]['wards'] += int(match.playerstat(self.id(), 'wards'))
            playerhero[heroid]['playedtime'] += match.gameduration().total_seconds()

        # finalize stats so we can sort all values easily after
        for heroid in playerhero:
            stats = playerhero[heroid]
            stats['perc'] = int(stats['use'] / len(matchdata) * 100)
            stats['kdr'] = stats['k'] / stats['d'] if stats['d'] > 0 else stats['k']
            stats['kpg'] = stats['k'] / stats['use']
            stats['dpg'] = stats['d'] / stats['use']
            stats['apg'] = stats['a'] / stats['use']
            stats['wpg'] = stats['wards'] / stats['use']
            stats['gpm'] = int(stats['gold'] / (stats['playedtime'] / 60))
        sortedstats = sorted(playerhero.values(), key=lambda x: x[sortby], reverse=order == 'desc')
        return sortedstats

    @staticmethod
    def header():
        return Player.HeaderFormat.format(
            nick="Nick",
            mmr="MMR",
            k="K",
            d="D",
            a="A",
            wg="W/G",
            cd="CD",
            kdr="KDR",
            gp="GP",
            wp="W%")

    def str(self, type_=Stats.DefaultStatsType):
        return Player.PlayerFormat.format(
            nick=self.nickname,
            rank=self.rating(type_),
            k=self.kills(type_),
            d=self.deaths(type_),
            a=self.assists(type_),
            wg=self.wards(type_) / self.gamesplayed(type_),
            cd=self.denies(type_) / self.gamesplayed(type_),
            kdr=self.kills(type_) / self.deaths(type_),
            pg=self.gamesplayed(type_),
            wp=self.wins(type_) / self.gamesplayed(type_) * 100)

class EmptyMatch():
    def gametype(self):
        return ""

    def players(self, team=None):
        return {}

    def playermatchstats(self, id_):
        return None

    def playerstat(self, id_, stat):
        return 0

    def mid(self):
        return 0

    def gameduration(self):
        return timedelta(seconds=0)

    def gamedatestr(self):
        date = datetime.now()
        return date.astimezone(Local).isoformat(' ')[:16]

    def matchesstr(self, id_, dp):
        return "Unable to fetch"

    def matchstr(self, dp):
        return "Unable to fetch"

    def __repr__(self):
        return "EmptyMatch()"


class Match(EmptyMatch):
    MatchesHeader = "{mid:10s} {gt:2s} {gd:4s} {date:16s} {k:>2s} " \
        "{d:>2s} {a:>2s} {hero:5s} {wl:3s} {wa:2s} {ck:>3s} {cd:2s} {gpm:3s}"
    MatchesFormat = "{mid:<10d} {gt:2s} {gd:4s} {date:15s} {k:2d} " \
        "{d:2d} {a:2d} {hero:5s}  {wl:1s}  {wa:2d} {ck:3d} {cd:2d} {gpm:3d}"

    def __init__(self, data):
        self.data = data

    @staticmethod
    def creatematch(data):
        if data:
            return Match(data)
        return EmptyMatch()

    @staticmethod
    def headermatches():
        return Match.MatchesHeader.format(mid="MID",
                                          gt="GT",
                                          gd="GD",
                                          date="Date",
                                          k="K",
                                          d="D",
                                          a="A",
                                          hero="Hero",
                                          wl="W/L",
                                          wa="Wa",
                                          ck="CK",
                                          cd="CD",
                                          gpm="GPM")

    def gametype(self):
        if not self.data:
            return "NA"

        options = self.data[1]
        if int(options['ap']) > 0:
            return "AP"
        if int(options['ar']) > 0:
            return "AR"
        return "SD"

    def players(self, team=None):
        if team:
            iteam = 1 if team == "legion" else 2
            return {int(data['account_id']): data for data in self.data[3] if int(data['team']) == iteam}
        return {int(data['account_id']): data for data in self.data[3]}

    def playermatchstats(self, id_):
        playerstats = self.data[3]
        for stats in playerstats:
            if int(id_) == int(stats['account_id']):
                return stats
        return None

    def playerstat(self, id_, stat):
        stats = self.playermatchstats(id_)
        return int(stats[stat])

    def mid(self):
        return int(self.data[0]['match_id'])

    def gameduration(self):
        return timedelta(seconds=int(self.data[0]['time_played']))

    def gamedatestr(self):
        date = parsedate(self.data[0]['mdt'])
        return date.astimezone(Local).isoformat(' ')[:16]

    def matchesstr(self, id_, dp):
        matchsum = self.data[0]
        return Match.MatchesFormat.format(
            mid=int(matchsum['match_id']),
            gt=self.gametype(),
            gd=str(self.gameduration())[:4],
            date=self.gamedatestr(),
            k=self.playerstat(id_, 'herokills'),
            d=self.playerstat(id_, 'deaths'),
            a=self.playerstat(id_, 'heroassists'),
            hero=dp.heroid2name(self.playerstat(id_, 'hero_id'))[:5],
            wl="W" if int(self.playerstat(id_, 'wins')) > 0 else "L",
            wa=self.playerstat(id_, 'wards'),
            ck=self.playerstat(id_, 'teamcreepkills') + self.playerstat(id_, 'neutralcreepkills'),
            cd=self.playerstat(id_, 'denies'),
            gpm=int(self.playerstat(id_, 'gold') / (self.gameduration().total_seconds() / 60)))

    def matchstr(self, dp):
        legionplayers = self.players(team="legion")
        hellbourneplayers = self.players(team='hellbourne')

        outstr = "Match {mid} -- {date} - GD: {gd}\n".format(
            mid=self.mid(), date=self.gamedatestr(), gd=self.gameduration())
        legion = "Legion(W)" if int(legionplayers[next(iter(legionplayers))]['wins']) > 0 else "Legion(L)"
        hellbourne = "Hellbourne(L)"
        if int(hellbourneplayers[next(iter(hellbourneplayers))]['wins']) > 0:
            hellbourne = "Hellbourne(W)"
        header = "{legion:14s} {hero:5s} {level:>2s} {kills:>2s} {deaths:>2s} {assists:>2s} "
        header += "{ck:>3s} {cd:>2s} {wards:>2s} {gpm:>3s} {gl2d:>4s}  "
        header += "{hell:14s} {hero:5s} {level:>2s} {kills:>2s} {deaths:>2s} {assists:>2s} "
        header += "{ck:>3s} {cd:>2s} {wards:>2s} {gpm:>3s} {gl2d:>4s}\n"
        outstr += header.format(legion=legion, hero="Hero", level="LV", kills="K", deaths="D",
                                assists="A", hell=hellbourne, ck="CK", cd="CD", wards="W", gpm="GPM", gl2d="GL2D")

        playerformat = "{nick:14s} {hero:5s} {lvl:2d} {k:2d} {d:2d} {a:2d} {ck:3d} {cd:2d} {wa:2d} {gpm:3d} {gl2d:4d}"
        legionstr = []
        for id_ in legionplayers.keys():
            legionstr.append(playerformat.format(
                nick=dp.id2nick(id_),
                hero=dp.heroid2name(self.playerstat(id_, 'hero_id'))[:5],
                lvl=self.playerstat(id_, 'level'),
                k=self.playerstat(id_, 'herokills'),
                d=self.playerstat(id_, 'deaths'),
                a=self.playerstat(id_, 'heroassists'),
                ck=self.playerstat(id_, 'teamcreepkills') + self.playerstat(id_, 'neutralcreepkills'),
                cd=self.playerstat(id_, 'denies'),
                wa=self.playerstat(id_, 'wards'),
                gpm=int(self.playerstat(id_, 'gold') / (self.gameduration().total_seconds() / 60)),
                gl2d=self.playerstat(id_, 'goldlost2death')
            ))

        hellstr = []
        for id_ in hellbourneplayers.keys():
            hellstr.append(playerformat.format(
                nick=dp.id2nick(id_),
                hero=dp.heroid2name(self.playerstat(id_, 'hero_id'))[:5],
                lvl=self.playerstat(id_, 'level'),
                k=self.playerstat(id_, 'herokills'),
                d=self.playerstat(id_, 'deaths'),
                a=self.playerstat(id_, 'heroassists'),
                ck=self.playerstat(id_, 'teamcreepkills') + self.playerstat(id_, 'neutralcreepkills'),
                cd=self.playerstat(id_, 'denies'),
                wa=self.playerstat(id_, 'wards'),
                gpm=int(self.playerstat(id_, 'gold') / (self.gameduration().total_seconds() / 60)),
                gl2d=self.playerstat(id_, 'goldlost2death')
            ))

        size = max(len(hellstr), len(legionstr))
        for i in range(0, size):
            if i < len(legionstr):
                outstr += legionstr[i] + "  " + hellstr[i] + '\n'
            else:
                outstr += " " * 34 + hellstr[i]

        return outstr

    def __repr__(self):
        return json.dumps(self.data, indent=2)

class Hero():
    heroformat = "{heroid:>3s} {name:15s}"
    def __init__(self, data):
        self.data = data

    def herostr(self):
        return Hero.heroformat.format(
                heroid=self.data['hero_id'],
                name=self.data['disp_name'].strip())

    def __repr__(self):
        return json.dumps(self.data, indent=2)

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
__author__ = 'rp'

import datetime

from data import Player, Match, Hero


class Text():

    def __init__(self, dp):
        self.dp = dp

    def playerinfo(self, ids, statstype):
        output = Player.header() + '\n'

        for id_ in ids:
            #print(url)
            data = self.dp.fetchplayer(id_, statstype)
            nickname = self.dp.id2nick(int(data['account_id']))
            player = Player(nickname, data)
            #print(json.dumps(data))
            output += player.str() + '\n'
        return output

    @classmethod
    def initavgdata(cls):
        avgdata = {'mid': 0,
                   'gt': "--",
                   'gd': datetime.timedelta(),
                   'date': '',
                   'k': 0,
                   'd': 0,
                   'a': 0,
                   'kdr': 0,
                   'hero': '',
                   'wl': '-',
                   'wa': 0,
                   'ck': 0,
                   'cd': 0,
                   'gpm': 0}
        return avgdata

    @classmethod
    def fillavgdata(cls, avgdata, matchdata):
        avgdata['gd'] += matchdata['gd']
        avgdata['k'] += matchdata['k']
        avgdata['d'] += matchdata['d']
        avgdata['a'] += matchdata['a']
        avgdata['wa'] += matchdata['wa']
        avgdata['ck'] += matchdata['ck']
        avgdata['cd'] += matchdata['cd']
        avgdata['gpm'] += matchdata['gpm']
        return avgdata

    @classmethod
    def finalizeavgdata(cls, avgdata, limit):
        avgdata['gd'] = str(avgdata['gd'] / limit)[:4]
        avgdata['k'] = int(avgdata['k'] / limit)
        avgdata['d'] = int(avgdata['d'] / limit)
        avgdata['a'] = int(avgdata['a'] / limit)
        avgdata['kdr'] = avgdata['k'] / avgdata['d']
        avgdata['wa'] = int(avgdata['wa'] / limit)
        avgdata['ck'] = int(avgdata['ck'] / limit)
        avgdata['cd'] = int(avgdata['cd'] / limit)
        avgdata['gpm'] = int(avgdata['gpm'] / limit)
        return avgdata

    def matchesinfo(self, ids, statstype, limit):
        output = ''
        for id_ in ids:
            matchids = self.dp.matches(id_, statstype)
            avgdata = Text.initavgdata()
            limit = min(limit, len(matchids)) if limit else len(matchids)
            output += self.dp.id2nick(id_) + '\n'
            output += Match.headermatches() + '\n'
            for i in range(limit):
                matches = self.dp.fetchmatchdata([matchids[i]])
                match = Match.creatematch(matchids[i], matches[matchids[i]])

                # count average
                if isinstance(match, Match):
                    matchdata = match.matchesdata(self.dp.nick2id(id_), self.dp)
                    avgdata = Text.fillavgdata(avgdata, matchdata)
                output += match.matchesstr(self.dp.nick2id(id_), self.dp) + '\n'
            avgdata = Text.finalizeavgdata(avgdata, limit)
            output += "average   " + Match.MatchesFormat.format(**avgdata)[10:] + '\n'
            #print(json.dumps(history))
        return output

    def matchinfo(self, ids):
        matches = self.dp.fetchmatchdata(ids)
        output = ''
        for mid in ids:
            match = Match.creatematch(mid, matches[mid])
            output += match.matchstr(self.dp) + '\n'
        return output

    def playerheroesinfo(self, ids, statstype, sort_by, order, arglimit):
        output = ''
        for id_ in ids:
            data = self.dp.fetchplayer(id_, statstype)
            nickname = self.dp.id2nick(int(data['account_id']))
            player = Player(nickname, data)
            stats = player.playerheroes(self.dp, statstype, sort_by, order)

            limit = arglimit if arglimit else len(stats)
            output += self.dp.id2nick(id_) + '\n'
            output += Player.PlayerHeroHeader + '\n'
            for i in range(limit):
                stat = stats[i]
                stat['hero'] = self.dp.heroid2name(stat['heroid'])[:10]
                output += Player.PlayerHeroFormat.format(**stat) + '\n'

        return output

    def lastmatchesinfo(self, ids, statstype, hero, arglimit, count):
        output = ''
        for id_ in ids:
            id_hero = (id_, hero) if hero else None
            matchids = self.dp.matches(id_, statstype)
            limit = arglimit if (arglimit or count) < count else count
            matches = self.dp.fetchmatchdata(matchids, limit=limit, id_hero=id_hero)
            output += self.dp.id2nick(id_) + '\n'
            for mid in sorted(matches.keys(), reverse=True):
                match = Match.creatematch(mid, matches[mid])
                output += match.matchstr(self.dp) + '\n'

        return output

    def heroesinfo(self, arglimit):
        output = ''
        heroesdata = self.dp.heroes()
        heroids = list(heroesdata.keys())
        heroids.sort(key=int)
        limit = arglimit if arglimit else len(heroids)
        for heroidindex in range(limit):
            hero = Hero(heroesdata[heroids[heroidindex]])
            output += hero.herostr() + '\n'

        return output

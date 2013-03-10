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

    def __init__(self, nickname, data):
        self.nickname = nickname
        self.data = data

    def id(self):
        return int(self.data['account_id'])

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

    def str(self, dp, type=Stats.DefaultStatsType):
        return Player.PlayerFormat.format(nick=dp.id2nick(self.id()),
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
    MatchesHeader = "{mid:10s} {gt:2s} {gd:4s} {date:16s} {k:>2s} {d:>2s} {a:>2s} {hero:5s} {wl:3s} {wa:2s} {ck:>3s} {cd:2s} {gpm:3s}"
    MatchesFormat = "{mid:<10d} {gt:2s} {gd:4s} {date:15s} {k:2d} {d:2d} {a:2d} {hero:5s}  {wl:1s}  {wa:2d} {ck:3d} {cd:2d} {gpm:3d}"

    def __init__(self, data):
        self.data = data

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
        options = self.data[1]
        if int(options['ap']) > 0:
            return "AP"
        if int(options['ar']) > 0:
            return "AR"
        return "SD"

    def players(self, team=None):
        if team:
            iteam = 1 if team=="legion" else 2
            return { int(data['account_id']): data for data in self.data[3] if int(data['team'])==iteam }
        return { int(data['account_id']): data for data in self.data[3] }

    def playermatchstats(self, id):
        playerstats = self.data[3]
        for stats in playerstats:
            if int(id) == int(stats['account_id']):
                return stats
        return None

    def playerstat(self, id, stat):
        stats = self.playermatchstats(id)
        return int(stats[stat])

    def mid(self):
        return int(self.data[0]['match_id'])

    def gameduration(self):
        return timedelta(seconds=int(self.data[0]['time_played']))

    def gamedatestr(self):
        date = parsedate(self.data[0]['mdt'])
        return date.astimezone(Local).isoformat(' ')[:16]

    def matchesstr(self, id, dp):
        matchsum = self.data[0]
        return Match.MatchesFormat.format(mid=int(matchsum['match_id']),
            gt=self.gametype(),
            gd=str(self.gameduration())[:4],
            date=self.gamedatestr(),
            k=self.playerstat(id, 'herokills'),
            d=self.playerstat(id, 'deaths'),
            a=self.playerstat(id, 'heroassists'),
            hero=dp.heroid2name(self.playerstat(id, 'hero_id'))[:5],
            wl="W" if int(self.playerstat(id, 'wins')) > 0 else "L",
            wa=self.playerstat(id, 'wards'),
            ck=self.playerstat(id, 'teamcreepkills') + self.playerstat(id, 'neutralcreepkills'),
            cd=self.playerstat(id, 'denies'),
            gpm=int(self.playerstat(id, 'gold') / (self.gameduration().total_seconds()/60)))

    def matchstr(self, dp):
        legionplayers = self.players(team="legion")
        hellbourneplayers = self.players(team='hellbourne')

        outstr = "Match {mid} -- {date} - GD: {gd}\n".format(mid=self.mid(), date=self.gamedatestr(), gd=self.gameduration())
        legion="Legion(W)" if int(legionplayers[next(iter(legionplayers))]['wins']) > 0 else "Legion(L)"
        hellbourne="Hellbourne(W)" if int(hellbourneplayers[next(iter(hellbourneplayers))]['wins']) > 0 else "Hellbourne(L)"
        header = "{legion:14s} {hero:5s} {level:>2s} {kills:>2s} {deaths:>2s} {assists:>2s} "
        header += "{ck:>3s} {cd:>2s} {wards:>2s} {gpm:>3s} {gl2d:>4s}  "
        header += "{hell:14s} {hero:5s} {level:>2s} {kills:>2s} {deaths:>2s} {assists:>2s} "
        header += "{ck:>3s} {cd:>2s} {wards:>2s} {gpm:>3s} {gl2d:>4s}\n"
        outstr += header.format(legion=legion, hero="Hero", level="LV", kills="K", deaths="D", assists="A", hell=hellbourne, ck="CK", cd="CD", wards="W", gpm="GPM", gl2d="GL2D")

        playerformat = "{nick:14s} {hero:5s} {lvl:2d} {k:2d} {d:2d} {a:2d} {ck:3d} {cd:2d} {wa:2d} {gpm:3d} {gl2d:4d}"
        legionstr = []
        for id in legionplayers.keys():
            dp.fetch
            legionstr.append(playerformat.format(
                      nick=dp.id2nick(id),
                      hero=dp.heroid2name(self.playerstat(id, 'hero_id'))[:5],
                      lvl=self.playerstat(id, 'level'),
                      k=self.playerstat(id, 'herokills'),
                      d=self.playerstat(id, 'deaths'),
                      a=self.playerstat(id, 'heroassists'),
                      ck=self.playerstat(id, 'teamcreepkills') + self.playerstat(id, 'neutralcreepkills'),
                      cd=self.playerstat(id, 'denies'),
                      wa=self.playerstat(id, 'wards'),
                      gpm=int(self.playerstat(id, 'gold') / (self.gameduration().total_seconds()/60)),
                      gl2d=self.playerstat(id, 'goldlost2death')
                      ))

        hellstr = []
        for id in hellbourneplayers.keys():
            hellstr.append(playerformat.format(
                      nick=dp.id2nick(id),
                      hero=dp.heroid2name(self.playerstat(id, 'hero_id'))[:5],
                      lvl=self.playerstat(id, 'level'),
                      k=self.playerstat(id, 'herokills'),
                      d=self.playerstat(id, 'deaths'),
                      a=self.playerstat(id, 'heroassists'),
                      ck=self.playerstat(id, 'teamcreepkills') + self.playerstat(id, 'neutralcreepkills'),
                      cd=self.playerstat(id, 'denies'),
                      wa=self.playerstat(id, 'wards'),
                      gpm=int(self.playerstat(id, 'gold') / (self.gameduration().total_seconds()/60)),
                      gl2d=self.playerstat(id, 'goldlost2death')
                      ))

        size = max(len(hellstr),len(legionstr))
        for i in range(0,size):
            if i < len(legionstr):
                outstr += legionstr[i] + "  " + hellstr[i] + '\n'
            else:
                outstr += " " * 34 + hellstr[i]

        return outstr

    def __repr__(self):
        return json.dumps(self.data, indent=2)

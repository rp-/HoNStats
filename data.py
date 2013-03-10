from datetime import timedelta

from datetimeutil import Local, parsedate

class Stats(object):
    DefaultStatsType = 'ranked'
    CacheTime = 60 * 5

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

    def playermatchstats(self, id):
        playerstats = self.data[3]
        for stats in playerstats:
            if int(id) == int(stats['account_id']):
                return stats
        return None

    def playerstat(self, id, stat):
        stats = self.playermatchstats(id)
        return int(stats[stat])

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

    def str(self):
        return self.data[0]['match_id']

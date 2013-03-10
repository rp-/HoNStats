import os
import json
import sqlite3
import urllib.request
from urllib.error import HTTPError
import gzip
import time

DBCREATE = """
CREATE TABLE IF NOT EXISTS player (
id  INTEGER PRIMARY KEY,
nick TEXT
);

CREATE TABLE IF NOT EXISTS hero (
id INTEGER PRIMARY KEY,
name TEXT
);
"""

class DataProvider(object):
    MatchCacheDir = 'match'
    PlayerCacheDir = 'player'
    
    CacheTime = 60 * 5

    HeroNicks = {
        6: "Devo",
        9: "Elec",
        161: "Gladi",
        185: "Sil",
        192: "RA"
    }
    
    @staticmethod
    def nickoraccountid(id):
        try:
            int(id)
            return '/accountid/' + id
        except ValueError:
            return '/nickname/' + id

class HttpDataProvider(DataProvider):

    def __init__(self, url = 'http://api.heroesofnewerth.com/', token=None, cachedir="~/.honstats"):
        self.url = url
        self.token = token
        self.cachedir = os.path.abspath(os.path.expanduser(cachedir))
        if self.cachedir:
            os.makedirs(self.cachedir, exist_ok=True)
            dbfile = os.path.join(self.cachedir, 'stats.db')
            self.db = sqlite3.connect(dbfile)
            self.db.executescript(DBCREATE)

            os.makedirs(os.path.join(self.cachedir, DataProvider.MatchCacheDir), exist_ok=True)
            os.makedirs(os.path.join(self.cachedir, DataProvider.PlayerCacheDir), exist_ok=True)

    def __del__(self):
        self.db.close()

    def nick2id(self, nick):
        cursor = self.db.cursor()
        cursor.execute("SELECT id from player WHERE nick = :nick", { 'nick': nick})
        row = cursor.fetchone()
        cursor.close()
        if row:
            return int(row[0])
        data = self.fetch('player_statistics/ranked/nickname/' + nick)
        self.db.execute('INSERT INTO player VALUES( :id, :nick );',  {'id': int(data['account_id']), 'nick': nick})
        self.db.commit()
        return int(data['account_id'])

    def id2nick(self, id):
        return id

    def heroid2name(self, id):
        if id in DataProvider.HeroNicks:
            return DataProvider.HeroNicks[id]
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM hero WHERE id = :id", { 'id': id})
        row = cursor.fetchone()
        cursor.close()
        if row:
            return row[0]
        data = self.fetch('heroes/id/{id}'.format(id=id))
        name = data['disp_name'].strip()
        self.db.execute('INSERT INTO hero VALUES( :id, :name);',  {'id': id, 'name':name})
        self.db.commit()
        return name

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
        playermatches = os.path.join(playerdir, "{id}_matches_{statstype}.gz".format(id=self.nick2id(id), statstype=statstype))
        if os.path.exists(playermatches) and os.stat(playermatches).st_ctime > time.time() - DataProvider.CacheTime:
            with gzip.open(playermatches, 'rt') as f:
                data = json.load(f)
        else:
            path = 'match_history/' + statstype + DataProvider.nickoraccountid(id)
            data = self.fetch(path)
            with gzip.open(playermatches,'wt+') as f:
                f.write(json.dumps(data))
        return data

    def fetchmatchdata(self, matchid):
        """Fetches match data by id and caches it onto disk
           First checks if the match stats are already cached
        """
        matchdir = os.path.join(self.cachedir,  DataProvider.MatchCacheDir)
        matchpath = os.path.join(matchdir, str(matchid)[0:4])
        os.makedirs(matchpath, exist_ok=True)
        matchpath = os.path.join(matchpath, str(matchid) + ".gz")
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
        return data

class FSDataProvider(DataProvider):
    def __init__(self, url = './sampledata'):
        self.url = os.path.abspath(url)

    def fetch(self, path):
        with open(os.path.join(self.url, path)) as fd:
            return json.load(fd)

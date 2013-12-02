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

import text
from string import Template

from data import Player, Match, Hero


class LinkItem():

    def __init__(self, link, value):
        self.link = link
        self.value = value

    def __str__(self):
        return '<a href="{link}">{value}</a>'.format(link=self.link, value=self.value)


class Html(text.Text):

    def __init__(self, dp):
        text.Text.__init__(self, dp)


    @classmethod
    def loadtemplates(cls):
        with open('/opt/honstats/templates/html_header.tmpl','r') as header:
            tmpl_header = Template(header.read())

        with open('/opt/honstats/templates/html_footer.tmpl', 'r') as footer:
            tmpl_footer = Template(footer.read())
        return tmpl_header, tmpl_footer

    @classmethod
    def list2cols(cls, l, _type='td'):
        ret = ''
        for i in l:
            align = "left" if isinstance(i, str) else "right"
            ret += '<{type_} align="{align}">{item}</{type_}>'.format(item=i, type_=_type, align=align)
        return ret


    def playerinfo(self, ids, statstype):
        tmpl_header, tmpl_footer = Html.loadtemplates()

        output = tmpl_header.substitute()

        output += '<h1>Player stats</h1>'
        output += '<table cellspacing="0" cellpadding="2">'
        output += '<tr>' + Html.list2cols(['Nick','MMR', 'K', 'D', 'A', 'W/G', 'CD', 'KDR', 'GP', 'Wins', 'Losses', 'W%'], 'th') + '</tr>'

        for id_ in ids:
            data = self.dp.fetchplayer(id_, statstype)
            nickname = self.dp.id2nick(int(data['account_id']))
            player = Player(nickname, data)
            pdata = [player.rating(statstype),
                     player.kills(statstype),
                     player.deaths(statstype),
                     player.assists(statstype),
                     round(player.wards(statstype)/player.gamesplayed(statstype), 2),
                     round(player.denies(statstype)/player.gamesplayed(statstype), 2),
                     round(player.kills(statstype)/player.deaths(statstype), 2),
                     player.gamesplayed(statstype),
                     player.wins(statstype),
                     player.losses(statstype),
                     round(player.wins(statstype)/player.gamesplayed(statstype) * 100, 2)]
            output += '<tr><td><a href="/matches/{nick}">{nick}</a></td>'.format(nick=nickname)
            output += Html.list2cols(pdata)
            output += '</tr>'
        output += '</table>'
        output += tmpl_footer.substitute()
        return output

    def matchesinfo(self, ids, statstype, limit):
        tmpl_h, tmpl_f = Html.loadtemplates()

        output = tmpl_h.substitute()

        for id_ in ids:
            output += '<h2>{nick}</h2>'.format(nick=id_)
            output += '<table cellspacing="0" cellpadding="2">'
            output += '<tr>' + Html.list2cols(['MID','GT', 'GD', 'Date', 'K', 'D', 'A', 'KDR', 'Hero', 'WL', 'Wards', 'CK', 'CD', 'GPM'], 'th') + '</tr>'

            matchids = self.dp.matches(id_, statstype)
            avgdata = text.Text.initavgdata()
            limit = limit if limit else len(matchids)

            for i in range(limit):
                matches = self.dp.fetchmatchdata([matchids[i]])
                match = Match.creatematch(matchids[i], matches[matchids[i]])

                if isinstance(match, Match):
                    matchdata = match.matchesdata(self.dp.nick2id(id_), self.dp)
                    avgdata = text.Text.fillavgdata(avgdata, matchdata)

                rowdata = [LinkItem("/match/" + str(matchdata['mid']), matchdata['mid']),
                           matchdata['gt'],
                           matchdata['gd'],
                           matchdata['date'],
                           matchdata['k'],
                           matchdata['d'],
                           matchdata['a'],
                           round(matchdata['kdr'], 2),
                           matchdata['hero'],
                           matchdata['wl'],
                           matchdata['wa'],
                           matchdata['ck'],
                           matchdata['cd'],
                           matchdata['gpm']]
                output += '<tr>' + Html.list2cols(rowdata) + '</tr>'

            output += '</table>'
        return output + tmpl_f.substitute()

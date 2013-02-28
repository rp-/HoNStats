import argparse
import urllib.request
import json

token=""

def nickoraccountid(id):
    try:
        int(id)
        return '/accountid/' + id
    except ValueError:
        return '/nickname/' + id
        
def fetchdata(url):
    resp = urllib.request.urlopen(url)
    return json.loads(resp.read().decode('utf-8'))

def playercommand(args):
    for id in args.id:
        url = args.host + '/player_statistics/' + args.statstype + nickoraccountid(id) + '/?token=' + token
        print(url)
        data = fetchdata(url)
        print(json.dumps(data))
        headerformat = "{nick:<10s} {mmr:<5s} {k:<4s} {d:<4s} {a:<4s} {wg:<3s} {cd:<4s} {kdr:<4s} {mgp:<4s} {wp:<2s}"
        playerformat = "{nick:<10s} {rank:<5d} {k:<4d}/{d:<4d}/{a:<4d}"
        print(headerformat.format(nick="Nick", mmr="MMR", k="K", d="D", a="A", wg="W/G", cd="CD", kdr="KDR", mgp="MGP", wp="W%"))
        print(playerformat.format(nick=id, rank=int(float(data['rnk_amm_team_rating'])), k=int(data['rnk_herokills']), d=int(data['rnk_deaths']), a=int(data['rnk_heroassists'])))
    
def matchescommand(args):
    for id in args.id:
        url = args.host + '/match_history/' + args.statstype + nickoraccountid(id) + '/?token=' + token
        print(url)
        data = fetchdata(url)
        print(json.dumps(data))

def main():
    parser = argparse.ArgumentParser(description='honstats fetches and displays Heroes of Newerth statistics')
    #parser.add_argument('--host', default='http://api.heroesofnewerth.com', help='statistic host provider')
    parser.add_argument('--host', default='http://localhost:1234', help='statistic host provider')
    parser.add_argument('-s', '--statstype', choices=['ranked', 'public', 'casual'], default='ranked', help='Statstype to show')
    #parser.set_defaults(func=None)
    
    subparsers = parser.add_subparsers(help='honstats commands')
    playercmd = subparsers.add_parser('player', help='Show player stats')
    playercmd.set_defaults(func=playercommand)
    playercmd.add_argument('id', nargs='+', help='Player nickname or hon id')
    
    matchescmd = subparsers.add_parser('matches', help='Show matches of a player')
    matchescmd.set_defaults(func=matchescommand)
    matchescmd.add_argument('id', nargs='+', help='Player nickname or hon id')
    
    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

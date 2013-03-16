========
honstats
========

honstats is a command line tool for query the Heroes of Newerth
statistics API written in Python 3.

Requirements
------------
As honstats uses the awesome argparse module it requires
at least Python 3.2.

http://www.python.org

Additionally to be able to fetch data from the Heroes of Newerth API
you need a token and with that a fix IP address.
You can acquire the authentication token from http://api.heroesofnewerth.com

Configuration
-------------
honstats will search for a configuration file in the following
location and order:

1. /etc/honstats
2. $HOME/.config/honstats/config

The configuration file contains the following sections:

[auth]
  *token* Your HoN authentication token.

[cache]
  *directory* Path to your cache directory, default $HOME/.honstats

Example:

::
  [auth]
  token=HON1AUTH2TOKEN3

  [cache]
  directory=~/.honstats

License
-------
The code is license under the GPLv3.
http://www.gnu.org/licenses/gpl.html

# Znayko

Socket server, responding to various questions, for use with botyo and wotsyo mainly

## Avaiable commands

all commands are triggered with */* followed by either full command made up by section:command or part of whole or just the command part. you need at least 3 characters unless the command is only 2, for example `/tv`

Examples:

* `/avat pencho` - will trigger `/avatar:avatar pencho`
* `/wiki shit` - will trigger `/wiki:article shit`, since article is the only avail command
* 

### Avatar

* `avatar` - generates avatar for name using multiavatar lib

### Console

all commands require host/ip, some support additional arguments

* `traceroute` - print result of traceroute command for given host/ip
* `tcptraceroute` - print result of tcptraceroute command fo given host/ip
* `dig` - print result of dig command fo given host/ip and query args
* `whois` - print result of whos command fo given host/ip

### CVE

all commands support query arguments

* `cve` - display last CVE items
* `subscribe` - receive updates for CVE items
* `unsubscribe` - remove CVE sub
* `listsubscriptions` - prints out the active subs for the group


### Name

all commands require query

* `gender` - guess the gender for provided name
* `race` = giess the ethnic for provided name

### Ipify

all commands require query


* `geo` - display geographic information for given host/ip


### Footy

all commands require query


* `standing` - display current live standing for a give league

### Logo

all commands require query


* `team` - tries to find and display logo for a given team name


### Music

all commands require query


* `song` - finds a song by given query and sends it to the group
* `albumart` - find the album art for given album and display it
* `lyrics` - find the lyrics for given song title and display it

### OnTV

* `leagues` - display monitored leagues and competitions
* `facts` - display facts for the provided game query
* `lines` - display lineups for the provided game query
* `livescore` - display livescores of current games or for the provided game query
* `player` - display statistic for the provided player in the current game
* `stats` - display stats for the provided game query
* `tv` - show games available on TV, for channels provide game query
* `subscribe` - receive updates for game query
* `unsubscribe` - remove game query sub
* `listsubscriptions` - prints out the active subs for the group
### Photo

all commands require query


* `fake` - display generated photo for given name

### Wiki

all commands require query

* `article` - fetches article for given query
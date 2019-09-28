# Reg Bot—Bespoke Discord-management bot for a Made in Abyss roleplay server

Reg Bot was made to automate certain administratory  task on the [_- Made In Abyss Rp -_](https://www.reddit.com/r/MadeInAbyss/comments/8wiinr/join_the_made_in_abyss_roleplay_discord/) roleplay Discord server. The tasks being:

* Displaying an activity report of players with active characters to see which players are inactive. (It displays the last time a player has posted.)
* Archiving player characters on demand.
* A stupid function which makes Reg say "irredeemable".

The bot is fully configurable as all configurations are stored in an external database.

If you are a member of our server, don't hesitate to try to improve Reg Bot. If you aren't, well, I don't think this bot would be of much use to you, but I dunno, it might.

## Rad info

Reg Bot is coded in Python using the [discord.py](https://github.com/Rapptz/discord.py) library, it uses a Postgres database to store its configuration, to which it connects using the [asyncpg](https://github.com/MagicStack/asyncpg) library, and it is deployed—to the dismay of many discord.py developers—on Heroku (hey, it works; don't judge).

## Database

I was too lazy to make a create a database-initialisation function or to create a database dump, so here's at least the schema of the database tables:

##### configuaration

| column name | column info |
|-------|-----------------------|
| id    |  integer(auto-increment;primary key) |
| name  | character varying[64] |
| value | character varying[64] |

##### roleplay_channels

| column name | column info |
|------------|-----------------------|
| id    |  integer(auto-increment;primary key) |
| channel_id | character varying[64] |

##### roleplay_roles

| column name | column info |
|------------|-----------------------|
| id    |  integer(auto-increment;primary key) |
| role_id | character varying[64] |

# MIsskey-ebooks-bot
Misskey eBooks Bot with Markov Chain

[Example @roboduck@ente.fun](https://ente.fun/@roboduck)

## Introduction
This small python script is a Markov Chain eBooks bot based on the framework of [mi.py](https://github.com/yupix/Mi.py.git)

It can only read and write from and to Misskey. Reading from Mastodon or Pleroma is not (yet) implemented.

It posts every hour on his own and reacts to mentions. Every 12 hours the bot reloads the notes and recalculates the Markov Chain.

## Operating mode
On the first start up the bot loads a given number of posts into his database and calculates the Markov Chain out of it.
After this he only updates the database with new posts. The upgrading is threaded so the bot itself isn't interrupted while the new markov chain is calulated.

## Installation

### Host Installation
To run `mi.py` you must install `python3.9` and `python3.9-dev` onto your system. (Please be aware of the requirements for mi.py!)
`mi.py` is still under development and a lot of things change there quickly so please be aware that there could be chances that something changed, that I haven't implemented in the bot at the moment.
to install `mi.py`please use the following command.
`pip install git+https://github.com/yupix/Mi.py.git`

For the bot to run you also need two additional packages
```
markovify
configparser
```

or just use the command `pip install -r requirements.txt` in the local folder where you cloned the repo.

Before starting the bot, please copy `example-bot.cfg` to `bot.cfg` and
configure it according to the configuration section below.

The best way to run it would be a `systemd` unit file and run it as a deamon.
Just to test it you can use `nohup python3.9 rdbot.py &` in the directory the bot is located in.

### Docker

To host this image with docker, copy the `docker-compose.yml` file to the directory that you want to host it from.

Next, you'll need to copy the contents of `example-bot.cfg` to `bot.cfg` in the
same directory and configure it according to the configuration section below.
Run `touch markov.json roboduck.db` in order to create the markov and database
files before starting the docker container. These files must already exist
before starting the docker container.

Then, simply run `docker-compose up` to start the app, or `docker-compose up -d`
to start the bot in detached mode!

## Configuration
Following things can be edited:
|Name|Values|Explanation|
|----|----|----|
|instance_read|domain.tld|Put here the domain of the Misskey instance you want to read the notes from. Only domain name and TLD, no `/`,`:` or `https`
|user_read|`username`|The user you want to read the notes from|
|instance_write|domain.tld|Put here the domain of the Misskey instance your bot is running. Only domain name and TLD, no `/`,`:` or `https`
|token|`String`|The token from your bot. Needs right to write notes and read notification|
|min_notes|`interger`|How many posts should be read at the initial start. Please state a number in 100 increments. Higher number means more variety but also more load when loading those and a bigger database and json file. 5000 notes resulted in ~3 MB disk space used. Default `5000`|
|max_notes|`interger`|How many posts should be stored in the database. Everything over this number will be deleted during an update cycle Default `5000`|
|includeReplies|`boolean`|Should replies included into the markov chain? Default `True`|
|includeMyRenotes|`boolean`|Should the notes you renoted be included? So your bot will make sentences you didn't wrote. Default `false`|
|excludeNsfw|`boolean`|Should be Notes included that are behind a CW Tag? Default `False` (Use with caution! The bot not CW any post he makes!)|
|test_output|`boolean`|Should be the created sentence be tested against the following statements? Default `true` (Highly recomended, otherwise sentences could repeat itself, could be very short or very long.)|
|tries|`integer`|How many times the bot tries to make a sentence that meets the given criteria|
|max_overlap_ratio|`float`|How many percent of the created sentence is allowed to be the same as the source text. Lower value means more gibberish, higher value to more exact copies of source material. Can be between `0`and `1`. Default `0.6`|
|max_overlap_total|`integer`|How many words are allowed to be the same? Default `15`|
|min_words|`integer`|How many words the sentence must have at least. Default `None`|
|max_words|`integer`|How many words the sentence must have at maximum. Default `None`|

You can change the configuration while the bot is running. No restart necessary, they take immediate effect.

## Known Quirks
- The startup needs quite some time. On my system about 10 seconds. You knwo that everything runs well when the first Note is posted.
- When the bot is started, it could happen that he runs in a timeout in the first 600 seconds. To prevent that, just mention the bot and he will stay in a loop.

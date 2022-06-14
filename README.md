# Misskey-ebooks-bot
Misskey eBooks Bot with Markov Chain

[Example @roboduck@ente.fun](https://ente.fun/@roboduck)

## Introduction
This small python script is a Markov Chain eBooks bot based on the framework of [MiPA](https://github.com/yupix/MiPA.git)

It can only read and write from and to Misskey. Reading from Mastodon or Pleroma is not (yet) implemented.

It posts every hour on his own and reacts to mention. Every 12 hours the bot reloads the notes and recalculates the Markov Chain.

## Operating mode
On the first start up the bot loads a given number of posts into his database and calculates the Markov Chain out of it.
After this he only updates the database with new posts. The upgrading is threaded so the bot itself isn't interrupted while the new markov chain is calculated.

## Installation

### Host Installation
To run `MiPA` you must install `python3.10`onto your system. (Please be aware that not all programs on your system might work under Python3.10!)
`MiPA` is still under development and a lot of things change there quickly so please be aware that there could be changes, that haven't been implemented in the bot yet! (I try my best to keep it up to date!)
to install `MiPA`please use the following commands:
`python3.10 -m pip install git+https://github.com/yupix/MiPA.git`
`python3.10 -m pip install git+https://github.com/yupix/MiPAC.git`

For the bot to run you also need a few additional packages
```
markovify
configparser
ujson
requests
msgpack
regex
```

or just use the command `python3.10 -m pip install -r requirements.txt` in the local folder where you cloned the repo.

Before starting the bot, please copy `example-bot.cfg` to `bot.cfg` and
configure it according to the configuration section below.

The best way to run it would be a `systemd` unit file and run it as a daemon.
Just to test it you can use `nohup python3.10 rdbot.py &` in the directory the bot is located in.

### Docker (Will be updated later, so might be broken at the moment!)

To host this image with docker, copy the `docker-compose.yml` file to the directory that you want to host it from.

Next, you'll need to copy the contents of `example-bot.cfg` to `bot.cfg` in the
same directory and configure it according to the configuration section below.
Run `touch markov.json roboduck.db` in order to create the markov and database
files before starting the docker container. These files must already exist
before starting the docker container.

Then, simply run `docker-compose up` to start the app, or `docker-compose up -d`
to start the bot in detached mode!

You can find the bot on Dockerhub just use `docker pull fotoente/misskey-ebooks-bot:latest`

## Configuration
Following things can be edited:
|Name|Values|Explanation|
|----|----|----|
|users|`@username1@domain1.tld;@username2@domain2.tld`|The users you want to read the notes from, separated by semicolon (`;`). For single user just provide one `username@domain.tld`|
|instance_write|domain.tld|Put here the domain of the Misskey instance your bot is running. Only domain name and TLD, no `/`,`:` or `https`
|token|`String`|The token from your bot. Needs right to write notes and read notification|
|cw|`String` or `None`|If the markov bot post should be posted with a content warning. Any String given here will show up as CW text. "none" to deactivate.|
|exclude_links|`boolean`|Should every link starting with `http://` and `https://` be removed? `false` as default|
|min_notes|`interger`|How many posts should be read at the initial start. Please state a number in 100 increments. Higher number means more variety but also more load when loading those and a bigger database and json file. 5000 notes resulted in ~3 MB disk space used. Default `5000`|
|max_notes|`interger`|How many posts should be stored in the database. Everything over this number will be deleted during an update cycle Default `5000`|
|includeReplies|`boolean`|Should reply included into the markov chain? Default `True`|
|includeMyRenotes|`boolean`|Should the notes you renoted be included? So your bot will use sentences for the markov chain you haven't written. Default `false`|
|excludeNsfw|`boolean`|Should be Notes included that are behind a CW Tag? Default `False` (Use with caution! The bot not CW any post he makes!)|
|test_output|`boolean`|Should be the created sentence be tested against the following statements? Default `true` (Highly recommended, otherwise sentences could repeat itself, could be very short or very long.)|
|tries|`integer`|How many times the bot tries to make a sentence that meets the given criteria|
|max_overlap_ratio|`float`|How many percent of the created sentence is allowed to be the same as the source text. Lower value means more gibberish, higher value to more exact copies of source material. Can be between `0`and `1`. Default `0.6`|
|max_overlap_total|`integer`|How many words are allowed to be the same? Default `15`|
|min_words|`integer`|How many words the sentence must have at least. Default `None`|
|max_words|`integer`|How many words the sentence must have at maximum. Default `None`|

Changes to the Markov chain section of the .cfg-file will have immediate effect.
Changes to the misskey part of the *.cfg-file, requires a restart of the bot.
If an option is missing from the `misskey` part of the config file, the default values will be used.

## Known Quirks
- The startup needs quite some time. On my system about 10 seconds. You know that everything runs well when the first Note is posted.

## Contributors
[Shibao](https://github.com/shibaobun) - Docker support and bug hunting<br />
[Yupix](https://github.com/yupix) - MiPA framework and clean code<br />
[Nullobsi](https://github.com/nullobsi) - Added multi-user support<br />
[ThatOneCalculator](https://github.com/ThatOneCalculator) - Option to CW the posts<br />

Thank you very much! Without your this project wouldn't be on this level!
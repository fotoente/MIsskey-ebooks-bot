import requests
import json
import os
import sys
import regex
import configparser
import markovify
import sqlite3
from pathlib import Path
from datetime import *
from time import sleep


def check_str_to_bool(text) -> bool:
    if text == "True" or text == "true" or text == "TRUE":
        return True
    elif text == "False" or text == "false" or text == "FALSE":
        return False
    else:
        return True


def get_endpoint(instance: str) -> str:
    # Try Misskey
    url = "https://" + instance + "/api/ping"
    req = requests.post(url)
    if req.status_code == 200:
        return "Misskey"

    # Try Mastodon and Pleroma
    url = "https://" + instance + "/api/v1/instance"  # Pleroma uses the same API as Mastodon
    req = requests.get(url)
    if req.status_code == 200:
        version = req.json()["version"]

        if version.find("(compatible; Pleroma") > 0:  # String only available in Pleroma instances. Mastodon will
            return "Pleroma"
        else:
            return "Mastodon"

    return "unknown"


def misskey_get_user_id(username: str, instance: str) -> str:
    url = "https://" + instance + "/api/users/show"
    try:
        req = requests.post(url, json={"username": username, "host": instance})
        req.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("Couldn't get Username! " + str(err))
        return ""
    return req.json()["id"]


def misskey_get_notes(**kwargs):
    note_id = "k"
    since_id = ""
    min_notes = 0
    notes_list = []
    return_list = []
    username = kwargs["username"]
    instance = kwargs["instance"]

    print("Reading notes for @" + username + "@" + instance + ".")
    if kwargs:
        if "min_notes" in kwargs:
            # print("min_notes found!")
            init = True
            min_notes = kwargs["min_notes"]

        elif "lastnote" in kwargs:
            # print("Lastnote found!")
            init = False
            since_id = kwargs["lastnote"]

        else:
            print("Wrong arguments given!")
            print("Exiting routine!")
            return
    else:
        print("No arguments given!")
        print("Exiting routine")
        return None

    # Load configuration
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'bot.cfg'))
    # print(os.path.join(os.path.dirname(__file__), 'bot.cfg'))

    userid = misskey_get_user_id(username, instance)

    # Read & Sanitize Inputs from Config File
    try:
        include_replies = check_str_to_bool(config.get("markov", "includeReplies"))
    except (TypeError, ValueError, configparser.NoOptionError):
        include_replies = True

    try:
        include_my_renotes = check_str_to_bool(config.get("markov", "includeMyRenotes"))
    except (TypeError, ValueError, configparser.NoOptionError):
        include_my_renotes = False

    try:
        exclude_nsfw = check_str_to_bool(config.get("markov", "excludeNsfw"))
    except (TypeError, ValueError, configparser.NoOptionError):
        exclude_nsfw = True

    try:
        exclude_links = check_str_to_bool(config.get("markov", "exclude_links"))
    except (TypeError, ValueError, configparser.NoOptionError):
        exclude_links = False

    run = True
    oldnote = ""

    while run:

        if (init and len(notes_list) >= min_notes) or (oldnote == note_id):
            break

        if not init:  # sinceid should only be used when updating the database so the json object has to be parsed
            # every time
            api_json = {
                "userId": userid,
                "includeReplies": include_replies,
                "limit": 100,
                "includeMyRenotes": include_my_renotes,
                "withFiles": False,
                "excludeNsfw": exclude_nsfw,
                "untilId": note_id,
                "sinceId": since_id}
        else:
            api_json = {
                "userId": userid,
                "includeReplies": include_replies,
                "limit": 100,
                "includeMyRenotes": include_my_renotes,
                "withFiles": False,
                "excludeNsfw": exclude_nsfw,
                "untilId": note_id}

        try:
            req = requests.post("https://" + instance + "/api/users/notes", json=api_json)
            req.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print("Couldn't get Posts! " + str(err))
            sys.exit(1)

        for jsonObj in req.json():
            notes_list.append(jsonObj)
        if len(notes_list) == 0:
            print("No new notes to load!")
            return []

        oldnote = note_id

        note_id = notes_list[len(notes_list) - 1]["id"]

    print(str(len(notes_list)) + " Notes read.")
    print("Processing notes...")

    for element in notes_list:
        last_time = element["createdAt"]
        last_timestamp = int(datetime.timestamp(datetime.strptime(last_time, '%Y-%m-%dT%H:%M:%S.%f%z')) * 1000)

        content = element["text"]

        if content is None:  # Skips empty notes (I don't know how there could be empty notes)
            continue

        content = regex.sub(r"(?>@(?>[\w\-])+)(?>@(?>[\w\-\.])+)?", '',
                            content)  # Remove instance name with regular expression
        content = content.replace("::", ": :")  # Break long emoji chains
        content = content.replace("@", "@" + chr(8203))

        if exclude_links:
            content = regex.sub(r"(http|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-]))",
                                "", content)

        note_dict = {"id": element["id"], "text": content, "timestamp": last_timestamp, "user_id": userid}
        return_list.append(note_dict)

    return return_list


def mastodon_get_user_id(username: str, instance: str) -> str:
    url = "https://" + instance + "/api/v1/accounts/lookup?acct=" + username

    try:
        req = requests.get(url)
        req.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("Couldn't get Username! " + str(err))
        return ""
    return req.json()["id"]


def mastodon_get_notes():
    print("MASTODON'T NOTES!")  # TODO Write routine to get Mastodon notes (check for limiting commands!)


def pleroma_get_user_id(username: str, instance: str) -> str:
    # Pleroma uses the Mastodon API so as a shortcut I just reuse the Mastodon function
    return mastodon_get_user_id(username, instance)


def pleroma_get_notes():
    print("Pleroma notes!")  # TODO Write routine to get Pleroma notes (check for limiting commands)


def calculate_markov_chain():
    text = ""
    # Load configuration
    config = configparser.ConfigParser()
    config.read(Path(__file__).parent.joinpath('bot.cfg'))
    try:
        max_notes = config.get("markov", "max_notes")
    except (TypeError, ValueError):
        max_notes = "10000"

    databasepath = Path(__file__).parent.joinpath('roboduck.db')
    if not (os.path.exists(databasepath) and os.stat(databasepath).st_size != 0):
        print("Roboduck database not already created!")
        print("Exit initialization!")
        sys.exit(0)

    with open(databasepath, 'r', encoding='utf-8'):
        database = sqlite3.connect(databasepath)

    data = database.cursor()
    data.execute("SELECT text FROM notes ORDER BY timestamp DESC LIMIT " + max_notes + ";")

    rows = data.fetchall()

    for row in rows:
        text += row[0] + "\n"

    markovchain = markovify.Text(text)
    markovchain.compile(inplace=True)

    markov_json = markovchain.to_json()

    with open(Path(__file__).parent.joinpath('markov.json'), "w", encoding="utf-8") as markov:
        json.dump(markov_json, markov)


def clean_database():
    databasepath = Path(__file__).parent.joinpath('roboduck.db')
    if not (os.path.exists(databasepath) and os.stat(databasepath).st_size != 0):
        print("No database found!")
        print("Please run Bot first!")
        sys.exit(0)

    with open(databasepath, "a", encoding="utf-8"):
        database = sqlite3.connect(databasepath)

    # Reading config file bot.cfg with config parser
    config = configparser.ConfigParser()
    config.read(Path(__file__).parent.joinpath('bot.cfg'))
    # print((Path(__file__).parent).joinpath('bot.cfg'))
    try:
        max_notes = config.get("markov", "max_notes")
    except (TypeError, ValueError):
        max_notes = "10000"

    for user in config.get("misskey", "users").split(";"):
        username = user.split("@")[1]
        instance = user.split("@")[2]
        userid = misskey_get_user_id(username, instance)
        data = database.cursor()
        data.execute(
            "DELETE FROM notes WHERE user_id=:user_id AND id NOT IN (SELECT id FROM notes WHERE user_id=:user_id "
            "ORDER BY timestamp DESC LIMIT :max );",
            {"user_id": userid, "max": int(max_notes)})

    database.commit()
    database.close()


def create_sentence():
    with open((os.path.join(Path(__file__).parent, 'markov.json')), "r", encoding="utf-8") as markov:
        markov_json = json.load(markov)

    text_model = markovify.Text.from_json(markov_json)

    # Reading config file bot.cfg with config parser
    config = configparser.ConfigParser()
    config.read(Path(__file__).parent.joinpath('bot.cfg'))
    # print((Path(__file__).parent).joinpath('bot.cfg'))
    # Read & Sanitize Inputs
    try:
        test_output = check_str_to_bool(config.get("markov", "test_output"))
    except (TypeError, ValueError):
        # print("test_output: " + str(err))
        test_output = True

    if test_output:
        try:
            tries = int(config.get("markov", "tries"))
        except (TypeError, ValueError):
            # print("tries: " + str(err))
            tries = 250

        try:
            max_overlap_ratio = float(config.get("markov", "max_overlap_ratio"))
        except (TypeError, ValueError):
            # print("max_overlap_ratio: " + str(err))
            max_overlap_ratio = 0.7

        try:
            max_overlap_total = int(config.get("markov", "max_overlap_total"))
        except (TypeError, ValueError):
            # print("max_overlap_total: " + str(err))
            max_overlap_total = 10

        try:
            max_words = int(config.get("markov", "max_words"))
        except (TypeError, ValueError):
            # print("max_words: " + str(err))
            max_words = None

        try:
            min_words = int(config.get("markov", "min_words"))
        except (TypeError, ValueError):
            # print("min_words: " + str(err))
            min_words = None

        if max_words is not None and min_words is not None:
            if min_words >= max_words:
                # print("min_words ("+str(min_words)+") bigger than max_words ("+str(max_words)+")! Swapping values!")
                swap = min_words
                min_words = max_words
                max_words = swap

    else:
        tries = 250
        max_overlap_ratio = 0.7
        max_overlap_total = 15
        max_words = None
        min_words = None

    """
    #Debug section to print the used values
    print("These values are used:")
    print("test_output: " + str(test_output))
    print("tries: " + str(tries))
    print("max_overlap_ratio: " + str(max_overlap_ratio))
    print("max_overlap_total: " + str(max_overlap_total))
    print("max_words: " + str(max_words))
    print("min_words: " + str(min_words))
    """

    # Applying Inputs
    note = text_model.make_sentence(
        test_output=test_output,
        tries=tries,
        max_overlap_ratio=max_overlap_ratio,
        max_overlap_total=max_overlap_total,
        max_words=max_words,
        min_words=min_words
    )
    if note is not None:
        return note
    else:
        return "Error in markov chain sentence creation: Couldn't calculate sentence!\n\n☹ Please try again! "


def update():
    notes_list = []
    databasepath = Path(__file__).parent.joinpath('roboduck.db')
    if not (os.path.exists(databasepath) and os.stat(databasepath).st_size != 0):
        print("No database found!")
        print("Please run Bot first!")
        sys.exit(0)

    with open(databasepath, "a", encoding="utf-8"):
        database = sqlite3.connect(databasepath)
        print("Connected to roboduck.db succesfull...")

    config = configparser.ConfigParser()
    config.read(Path(__file__).parent.joinpath('bot.cfg'))
    for user in config.get("misskey", "users").split(";"):
        username = user.split("@")[1]
        instance = user.split("@")[2]
        userid = misskey_get_user_id(username, instance)
        data = database.cursor()
        data.execute(
            "SELECT id FROM notes WHERE timestamp = (SELECT MAX(timestamp) FROM notes WHERE user_id=:user_id) AND "
            "user_id=:user_id;",
            {"user_id": userid})

        since_note = data.fetchone()[0]

        notes_list.extend(misskey_get_notes(lastnote=since_note, username=username, instance=instance))

    if notes_list == 0:
        database.close()
        return

    print("Insert new notes to database...")
    database.executemany("INSERT OR IGNORE INTO notes (id, text, timestamp, user_id) VALUES(?, ?, ?, ?)",
                         [(note["id"], note["text"], note["timestamp"], note["user_id"]) for note in notes_list])

    database.commit()
    print("Notes updated!")
    database.close()

    print("Cleaning database...")
    clean_database()
    print("Database cleaned!")

    print("Short sleep to prevent file collison...")
    sleep(10)

    print("Calculating new Markov Chain...")
    calculate_markov_chain()
    print("Markov Chain saved!")

    print("\nUpdate done!")


def init_bot():
    databasepath = Path(__file__).parent.joinpath('roboduck.db')
    if os.path.exists(databasepath) and os.stat(databasepath).st_size != 0:
        print("Roboduck database already created!")
        print("Exit initialization!")
        sys.exit(0)

    print("Creating database...")

    with open(databasepath, "w+", encoding="utf-8"):
        database = sqlite3.connect(databasepath)
        print("Connected to roboduck.db successful...")

    print("Creating Table...")
    database.execute("CREATE TABLE notes (id CHAR(10) PRIMARY KEY, text CHAR(5000), timestamp INT, user_id CHAR(10));")

    print("Table NOTES created...")

    # Load configuration
    config = configparser.ConfigParser()
    config.read(Path(__file__).parent.joinpath('bot.cfg'))
    try:
        initnotes = int(config.get("markov", "min_notes"))
    except (TypeError, ValueError):
        # print(err)
        initnotes = 1000

    for user in config.get("misskey", "users").split(";"):
        print("Try reading first " + str(initnotes) + " notes for " + user + ".")

        notes_list = misskey_get_notes(min_notes=initnotes, username=user.split("@")[1], instance=user.split("@")[2])

        print("Writing notes into database...")

        database.executemany("INSERT INTO notes (id, text, timestamp, user_id) VALUES(?, ?, ?, ?)",
                             [(note["id"], note["text"], note["timestamp"], note["user_id"]) for note in notes_list])

    database.commit()
    database.close()

    print("Notes written...")
    print("Creating Markov Chain")
    calculate_markov_chain()

    print("Markov Chain calculated & saved.\n")
    print("Finished initialization!\n")
    print("The bot will now be started!")

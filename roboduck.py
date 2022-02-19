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
    if (text == "True" or text == "true" or text == "TRUE"):
        return True
    elif (text == "False" or text == "false" or text == "FALSE"):
        return False
    else:
        return True

def get_notes(**kwargs):
    noteid = "k"
    sinceid = ""
    min_notes = 0
    notesList = []
    returnList = []

    if (kwargs):
        if ("min_notes" in kwargs):
            #print("min_notes found!")
            init = True
            min_notes = kwargs["min_notes"]

        elif ("lastnote" in kwargs):
            #print("Lastnote found!")
            init = False
            sinceid = kwargs["lastnote"]

        else:
            print("Wrong arguments given!")
            print("Exiting routine!")
            return
    else:
        print("No arguments given!")
        print("Exiting routine")
        return None

    #Load configuration
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'bot.cfg'))
    #print(os.path.join(os.path.dirname(__file__), 'bot.cfg'))

    url="https://"+config.get("misskey","instance_read")+"/api/users/show"
    host=config.get("misskey","instance_read")
    try:
        req = requests.post(url, json={"username" : config.get("misskey","user_read"), "host" : host})
        req.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("Couldn't get Username! " + str(err))
        sys.exit(1)


    userid = req.json()["id"]

    #Read & Sanitize Inputs from Config File
    try:
        includeReplies = check_str_to_bool(config.get("markov","includeReplies"))
    except (TypeError, ValueError) as err:
        includeReplies = True

    try:
        includeMyRenotes = check_str_to_bool(config.get("markov","includeMyRenotes"))
    except (TypeError, ValueError) as err:
        includeMyRenotes = False

    try:
        excludeNsfw = check_str_to_bool(config.get("markov","excludeNsfw"))
    except (TypeError, ValueError) as err:
        excludeNsfw = True

    run = True
    oldnote=""

    while run:

        if ((init and len(notesList) >= min_notes) or (oldnote == noteid)):
            break

        try:
            req = requests.post("https://"+config.get("misskey","instance_read")+"/api/users/notes", json = {
                                                                            "userId": userid,
                                                                            "includeReplies" : includeReplies,
                                                                            "limit" : 100,
                                                                            "includeMyRenotes" : includeMyRenotes,
                                                                            "withFiles" : False,
                                                                            "excludeNsfw" : excludeNsfw,
                                                                            "untilId" : noteid,
                                                                            "sinceId" : sinceid
                                                                        })
            req.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print("Couldn't get Posts! "+str(err))
            sys.exit(1)

        for jsonObj in req.json():
            notesList.append(jsonObj)
        if (len(notesList) == 0):
            print("No new notes to load!")
            return 0

        oldnote = noteid

        noteid = notesList[len(notesList)-1]["id"]

    print(str(len(notesList)) + " Notes read.")
    print("Processing notes...")

    for element in notesList:
        lastTime = element["createdAt"]
        lastTimestamp = int(datetime.timestamp(datetime.strptime(lastTime, '%Y-%m-%dT%H:%M:%S.%f%z'))*1000)

        content = element["text"]

        if content is None: #Skips empty notes (I don't know how there could be empty notes)
            continue

        content = regex.sub(r"(?>@(?>[\w\-])+)(?>@(?>[\w\-\.])+)?", '', content) #Remove instance name with regular expression
        content = content.replace("::",": :") #Break long emoji chains
        content = content.replace("@", "@"+chr(8203))

        dict = {"id" : element["id"], "text" : content, "timestamp" : lastTimestamp}
        returnList.append(dict)

    return returnList

def calculate_markov_chain():
    text = ""
    #Load configuration
    config = configparser.ConfigParser()
    config.read((Path(__file__).parent).joinpath('bot.cfg'))
    try:
        max_notes = config.get("markov","max_notes")
    except (TypeError, ValueError) as err:
        max_notes = "10000"

    databasepath = (Path(__file__).parent).joinpath('roboduck.db')
    if (not (os.path.exists(databasepath) and os.stat(databasepath).st_size != 0)):
        print("Roboduck database not already created!")
        print("Exit initialization!")
        sys.exit(0)

    with open(databasepath, 'r', encoding='utf-8') as emojilist:
        database = sqlite3.connect(databasepath)

    data = database.cursor()
    data.execute("SELECT text FROM notes ORDER BY timestamp DESC LIMIT " + max_notes + ";")

    rows = data.fetchall()

    for row in rows:
        text += row[0] + "\n"

    markovchain = markovify.Text(text)
    markovchain.compile(inplace = True)

    markov_json = markovchain.to_json()

    with open((Path(__file__).parent).joinpath('markov.json'), "w", encoding="utf-8") as markov:
        json.dump(markov_json, markov)

def clean_database():
    databasepath = (Path(__file__).parent).joinpath('roboduck.db')
    if (not (os.path.exists(databasepath) and os.stat(databasepath).st_size != 0)):
        print("No database found!")
        print("Please run Bot first!")
        sys.exit(0)

    with open(databasepath, "a", encoding="utf-8") as f:
        database = sqlite3.connect(databasepath)

    #Reading config file bot.cfg with config parser
    config = configparser.ConfigParser()
    config.read((Path(__file__).parent).joinpath('bot.cfg'))
    #print((Path(__file__).parent).joinpath('bot.cfg'))
    try:
        max_notes = config.get("markov","max_notes")
    except (TypeError, ValueError) as err:
        max_notes = "10000"

    data = database.cursor()
    data.execute("DELETE FROM notes WHERE id NOT IN (SELECT id FROM notes ORDER BY timestamp DESC LIMIT " + max_notes + ");")

    database.commit()
    database.close()

def create_sentence():
    with open((os.path.join((Path(__file__).parent), 'markov.json')), "r", encoding="utf-8") as markov:
        markov_json = json.load(markov)

    text_model = markovify.Text.from_json(markov_json)

    note=""

    #Reading config file bot.cfg with config parser
    config = configparser.ConfigParser()
    config.read((Path(__file__).parent).joinpath('bot.cfg'))
    #print((Path(__file__).parent).joinpath('bot.cfg'))
    #Read & Sanitize Inputs
    try:
        test_output = check_str_to_bool(config.get("markov","test_output"))
    except (TypeError, ValueError) as err:
        #print("test_output: " + str(err))
        test_output = True

    if (test_output):
        try:
            tries = int(config.get("markov","tries"))
        except (TypeError, ValueError) as err:
            #print("tries: " + str(err))
            tries = 250

        try:
            max_overlap_ratio = float(config.get("markov","max_overlap_ratio"))
        except (TypeError, ValueError) as err:
            #print("max_overlap_ratio: " + str(err))
            max_overlap_ratio = 0.7

        try:
            max_overlap_total = int(config.get("markov","max_overlap_total"))
        except (TypeError, ValueError) as err:
            #print("max_overlap_total: " + str(err))
            max_overlap_total = 10

        try:
            max_words = int(config.get("markov","max_words"))
        except (TypeError, ValueError) as err:
            #print("max_words: " + str(err))
            max_words = None

        try:
            min_words = int(config.get("markov","min_words"))
        except (TypeError, ValueError) as err:
            #print("min_words: " + str(err))
            min_words = None

        if (max_words is not None and min_words is not None):
            if (min_words >= max_words):
                #print("min_words ("+str(min_words)+") bigger than max_words ("+str(max_words)+")! Swapping values!")
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
    #Debug section to rpint the used values
    print("These values are used:")
    print("test_output: " + str(test_output))
    print("tries: " + str(tries))
    print("max_overlap_ratio: " + str(max_overlap_ratio))
    print("max_overlap_total: " + str(max_overlap_total))
    print("max_words: " + str(max_words))
    print("min_words: " + str(min_words))
    """

    #Applying Inputs
    note = text_model.make_sentence(
                                    test_output = test_output,
                                    tries = tries,
                                    max_overlap_ratio = max_overlap_ratio,
                                    max_overlap_total = max_overlap_total,
                                    max_words = max_words,
                                    min_words = min_words
                                    )
    if (note is not None):
        return note
    else:
        return "Error in markov chain sentence creation: Couldn't calculate sentence!\n\n☹ Please try again! "

def update():
    notesList = []
    databasepath = (Path(__file__).parent).joinpath('roboduck.db')
    if (not (os.path.exists(databasepath) and os.stat(databasepath).st_size != 0)):
        print("No database found!")
        print("Please run Bot first!")
        sys.exit(0)

    with open(databasepath, "a", encoding="utf-8") as f:
        database = sqlite3.connect(databasepath)
        print("Connected to roboduck.db succesfull...")

    data = database.cursor()
    data.execute("SELECT id FROM notes WHERE timestamp = (SELECT MAX(timestamp) FROM notes);")

    sinceNote = data.fetchone()[0]

    notesList = get_notes(lastnote = sinceNote)

    if (notesList == 0):
        database.close()
        return

    print("Insert new notes to database...")
    for note in notesList:
        database.execute("INSERT OR IGNORE INTO notes (id, text, timestamp) VALUES(?, ?, ?)", [note["id"], note["text"], note["timestamp"]])

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
    notesList = []
    databasepath = (Path(__file__).parent).joinpath('roboduck.db')
    if (os.path.exists(databasepath) and os.stat(databasepath).st_size != 0):
        print("Roboduck database already created!")
        print("Exit initialization!")
        sys.exit(0)

    print("Creating database...")

    with open(databasepath, "w+", encoding="utf-8") as f:
        database = sqlite3.connect(databasepath)
        print("Connected to roboduck.db succesfull...")

    print("Creating Table...")
    database.execute("CREATE TABLE notes (id CHAR(10) PRIMARY KEY, text CHAR(5000), timestamp INT);")

    print("Table NOTES created...")

    #Load configuration
    config = configparser.ConfigParser()
    config.read((Path(__file__).parent).joinpath('bot.cfg'))
    try:
        initnotes = int(config.get("markov","min_notes"))
    except (TypeError, ValueError) as err:
        #print(err)
        initnotes=1000

    print("Try reading first " + str(initnotes) + " notes.")

    notesList = get_notes(min_notes = initnotes)

    print("Writing notes into database...")

    for note in notesList:
        database.execute("INSERT INTO notes (id, text, timestamp) VALUES(?, ?, ?)", [note["id"], note["text"], note["timestamp"]])

    database.commit()
    database.close()

    print("Notes written...")
    print("Creating Markov Chain")
    calculate_markov_chain()

    print("Markov Chain calculated & saved.\n")
    print("Finished initialization!\n")
    print("The bot will now be started!")

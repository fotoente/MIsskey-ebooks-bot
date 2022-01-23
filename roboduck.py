import requests
import json
import os
import re
import configparser
import markovify

def check_str_to_bool(text) -> bool:
    if (text == "True" or text == "true" or text == "TRUE"):
        return True
    elif (text == "False" or text == "false" or text == "FALSE"):
        return False
    else:
        return True

def read_posts():
    text = "" #Holds the text to build Markov Chain
    textList = [] #The unprocessed text from the notes
    noteid = "" #Holds the last note ID to get more than 100 Notes
    oldnote = "" #Last note id of last cycle to see if the end is reached

    #Load configuration
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'bot.cfg'))
    #print(os.path.join(os.path.dirname(__file__), 'bot.cfg'))

    url="https://"+config.get("misskey","instance_read")+"/api/users/show"
    host=config.get("misskey","instance_read")
    try:
        req = requests.post(url, json={"username": config.get("misskey","user_read"), "host":host})
        req.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("Couldn't get Username! "+str(err))
        sys.exit(1)


    userid = req.json()["id"]

    #Read & Sanitize Inputs from Config File
    try:
        notes_count = int(int(config.get("markov","notes_count"))/100)
    except (TypeError, ValueError) as err:
        #print(err)
        notes_count=10

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

    for i in range(0, notes_count): #How many iterations of 100 notes he should read?
        if (i != 0):
            noteid = textList[len(textList)-1]["id"]
            if (oldnote == noteid): #If the last noteid repeats then break loop
                break



        try:
            req = requests.post("https://"+config.get("misskey","instance_read")+"/api/users/notes", json = {
                                                                            "userId": userid,
                                                                            "includeReplies" : includeReplies,
                                                                            "limit" : 100,
                                                                            "includeMyRenotes" : includeMyRenotes,
                                                                            "withFiles" : False,
                                                                            "excludeNsfw" : excludeNsfw,
                                                                            "untilId" : noteid
                                                                        })
            req.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print("Couldn't get Posts! "+str(err))
            sys.exit(1)

        for jsonObj in req.json():
            textDict = jsonObj
            textList.append(textDict)

        oldnote = noteid


    for item in textList:
        if item["text"] is None: #Skips empty notes (I don't know how there could be empty notes)
            continue

        content = str(item["text"])+"\n" #Gets the text item of every JSON element
        content = re.sub(r"@[\w\-]+(?:@[\w\-\.]+)?", '', content) #Remove instance name with regular expression
        content = content.replace("::",": :") #Break long emoji chains
        text += content.replace("@", "@"+chr(8203))

    text_model = markovify.Text(text) #Create Markov Chain

    return text_model #Give back object with the markov chain. The Text itself won't be stored beyond this point


def create_post(text_model):
    note=""

    #Reading config file bot.cfg with config parser
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'bot.cfg'))
    #print(os.path.join(os.path.dirname(__file__), 'bot.cfg'))

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

    return note

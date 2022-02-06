#!/usr/bin/python3

import lmdb
import random
from entrypoint2 import entrypoint
from linkgrammar import Sentence, ParseOptions, Dictionary
from tqdm import tqdm

gr_po = ParseOptions(min_null_count=0, max_null_count=0, max_parse_time=1, spell_guess=False)
gr_en_dir = Dictionary()

class MarkovDb():
    def __init__(self, dbpath, name=""):
        self.db = lmdb.open(dbpath, map_size=1024**4, writemap=True, metasync=False)
        self.name = name
        self.firsts = None
        self.flen = 0

    def add_pair(self, txn, first, second, follower):
        combined = b" ".join((first, second))
        entry = txn.get(combined)

        if entry == None:
            txn.put(combined, follower)
        else:
            entry = bytes(entry)
            if not entry.endswith(follower):
                txn.put(combined, b" ".join((entry, follower)))

    def get_first_pair(self):
        if not self.firsts:
            with self.db.begin() as txn:
                try:
                    dbf = txn.get(b"\n \n")
                    if len(dbf) != self.flen:
                        self.flen = len(dbf)
                        self.firsts = dbf.split()
                except:
                    raise KeyError("({}) No firsts found.".format(self.name))

        return random.choice(self.firsts)

    def get_follower(self, first, second):
        with self.db.begin() as txn:
            followers = txn.get(b" ".join((first, second)))

            if followers == None:
                raise KeyError("({}) No followers found.".format(self.name))

            follower = random.choice(followers.split(b" "))

            return (follower, follower == b"\n")

    def import_texts(self, texts):
        with self.db.begin(write=True, buffers=True) as txn:
            for txt in tqdm(texts):
                words = [b"\n", b"\n", *[x.encode("utf-8") for x in txt.split()], b"\n"]

                if len(words) == 3:
                    continue

                def triples(w):
                    for i in range(len(w) - 2):
                        yield (w[i], w[i+1], w[i+2])

                for (first, second, follower) in triples(words):
                    self.add_pair(txn, first, second, follower)

    def get_chain(self, min_length=8, max_length=500, max_tries=400, grammar=False):
        while max_tries > 0:
            max_tries -= 1

            words = [b"\n", self.get_first_pair()]

            follower = words[-1]
            last = False
            chain = []
            clen = len(follower)

            while not last:
                chain.append(follower)
                (follower, last) = self.get_follower(words[-2], words[-1])
                clen += len(follower)
                if clen <= max_length:
                    words.append(follower)
                else:
                    break

            if len(chain) >= min_length:
                resp = " ".join((x.decode("utf-8") for x in chain)).strip()

                if grammar:
                    good = True
                    for s in resp.split(". "):
                        sent = Sentence(s, gr_en_dir, gr_po)
                        ld = len(sent.parse())
                        if ld == 0 or ld > 43:
                            good = False
                            break
                    if not good:
                        continue

                return resp
            else:
                continue

        raise KeyError("({}) Could not construct chain of length {}.".format(self.name, min_length))

@entrypoint
def main(inputs=None, grammar=False, num=100):
    texts = MarkovDb("texts.lmdb", "text")

    if inputs:
        with open(inputs, "r") as inf:
            texts.import_texts(inf.readlines())

    for i in range(num):
        print(texts.get_chain(grammar=grammar))

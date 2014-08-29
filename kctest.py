#! /usr/bin/python3
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------------------------
# The test cases of the Python binding
#                                                                Copyright (C) 2009-2010 FAL Labs
# This file is part of Kyoto Cabinet.
# This program is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either version
# 3 of the License, or any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program.
# If not, see <http://www.gnu.org/licenses/>.
# -------------------------------------------------------------------------------------------------


from kyotocabinet import *
import sys
import os
import re
import random
import time
import threading
import shutil


# main routine
def main():
    if len(sys.argv) < 2: usage()
    if sys.argv[1] == "order":
        rv = runorder()
    elif sys.argv[1] == "wicked":
        rv = runwicked()
    elif sys.argv[1] == "misc":
        rv = runmisc()
    else:
        usage()
    return rv


# print the usage and exit
def usage():
    print("{}: test cases of the Python binding".format(progname), file=sys.stderr)
    print("", file=sys.stderr)
    print("usage:", file=sys.stderr)
    print("  {} order [-cc] [-th num] [-rnd] [-etc] path rnum".format(progname), file=sys.stderr)
    print("  {} wicked [-cc] [-th num] [-it num] path rnum".format(progname), file=sys.stderr)
    print("  {} misc path".format(progname), file=sys.stderr)
    print("", file=sys.stderr)
    exit(1)


# generate a random number
def rand(num):
    if num < 2: return 0
    return rndstate.randint(0, num - 1)


# print the error message of the database
def dberrprint(db, func):
    err = db.error()
    print("{}: {}: {}: {}: {}".format(progname, func, err.code(), err.name(), err.message()))


# print members of a database
def dbmetaprint(db, verbose):
    if verbose:
        status = db.status()
        if status is not None:
            for key in status:
                print("{}: {}".format(key, status[key]))
    else:
        print("count: {}".format(db.count()))
        print("size: {}".format(db.size()))


# parse arguments of order command
def runorder():
    path = None
    rnum = None
    gopts = 0
    thnum = 1
    rnd = False
    etc = False
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if path is None and arg.startswith("-"):
            if arg == "-cc":
                gopts |= DB.GCONCURRENT
            elif arg == "-th":
                i += 1
                if i >= len(sys.argv): usage()
                thnum = int(sys.argv[i])
            elif arg == "-rnd":
                rnd = True
            elif arg == "-etc":
                etc = True
            else:
                usage()
        elif path is None:
            path = arg
        elif rnum is None:
            rnum = int(arg)
        else:
            usage()
        i += 1
    if path is None or rnum is None or rnum < 1 or thnum < 1: usage()
    rv = procorder(path, rnum, gopts, thnum, rnd, etc)
    return rv


# parse arguments of wicked command
def runwicked():
    path = None
    rnum = None
    gopts = 0
    thnum = 1
    itnum = 1
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if path is None and arg.startswith("-"):
            if arg == "-cc":
                gopts |= DB.GCONCURRENT
            elif arg == "-th":
                i += 1
                if i >= len(sys.argv): usage()
                thnum = int(sys.argv[i])
            elif arg == "-it":
                i += 1
                if i >= len(sys.argv): usage()
                itnum = int(sys.argv[i])
            else:
                usage()
        elif path is None:
            path = arg
        elif rnum is None:
            rnum = int(arg)
        else:
            usage()
        i += 1
    if path is None or rnum is None or rnum < 1 or thnum < 1 or itnum < 1: usage()
    rv = procwicked(path, rnum, gopts, thnum, itnum)
    return rv


# parse arguments of misc command
def runmisc():
    path = None
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if path is None and arg.startswith("-"):
            usage()
        elif path is None:
            path = arg
        else:
            usage()
        i += 1
    if path is None: usage()
    rv = procmisc(path)
    return rv


# perform order command
def procorder(path, rnum, gopts, thnum, rnd, etc):
    print("<In-order Test>")
    print("  path={}  rnum={}  gopts={}  thnum={}  rnd={}  etc={}".
          format(path, rnum, gopts, thnum, rnd, etc))
    print("")
    err = False
    db = DB(gopts)
    db.tune_exception_rule([Error.SUCCESS, Error.NOIMPL, Error.MISC])
    print("opening the database:")
    stime = time.time()
    if not db.open(path, DB.OWRITER | DB.OCREATE | DB.OTRUNCATE):
        dberrprint(db, "DB::open")
        err = True
    etime = time.time()
    print("time: {:.3f}".format(etime - stime))
    print("setting records:")
    stime = time.time()

    class Setter(threading.Thread):
        def __init__(self, thid):
            threading.Thread.__init__(self)
            self.thid = thid

        def run(self):
            nonlocal err
            base = self.thid * rnum
            rng = rnum * thnum
            for i in range(1, rnum + 1):
                if err: break
                key = "{:08d}".format(rand(rng) + 1 if rnd else base + i)
                if not db.set(key, key):
                    dberrprint(db, "DB::set")
                    err = True
                if self.thid < 1 and rnum > 250 and i % (rnum / 250) == 0:
                    print(".", end="")
                    if i == rnum or i % (rnum / 10) == 0:
                        print(" ({:08d})".format(i))
                    sys.stdout.flush()
    threads = []
    for thid in range(0, thnum):
        th = Setter(thid)
        th.start()
        threads.append(th)
    for th in threads:
        th.join()
    etime = time.time()
    dbmetaprint(db, False)
    print("time: {:.3f}".format(etime - stime))
    if etc:
        print("adding records:")
        stime = time.time()
        class Adder(threading.Thread):
            def __init__(self, thid):
                threading.Thread.__init__(self)
                self.thid = thid
            def run(self):
                nonlocal err
                base = self.thid * rnum
                rng = rnum * thnum
                for i in range(1, rnum + 1):
                    if err: break
                    key = "{:08d}".format(rand(rng) + 1 if rnd else base + i)
                    if not db.add(key, key) and db.error() != Error.DUPREC:
                        dberrprint(db, "DB::add")
                        err = True
                    if self.thid < 1 and rnum > 250 and i % (rnum / 250) == 0:
                        print(".", end="")
                        if i == rnum or i % (rnum / 10) == 0:
                            print(" ({:08d})".format(i))
                        sys.stdout.flush()
        threads = []
        for thid in range(0, thnum):
            th = Adder(thid)
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        etime = time.time()
        dbmetaprint(db, False)
        print("time: {:.3f}".format(etime - stime))
    if etc:
        print("appending records:")
        stime = time.time()
        class Appender(threading.Thread):
            def __init__(self, thid):
                threading.Thread.__init__(self)
                self.thid = thid
            def run(self):
                nonlocal err
                base = self.thid * rnum
                rng = rnum * thnum
                for i in range(1, rnum + 1):
                    if err: break
                    key = "{:08d}".format(rand(rng) + 1 if rnd else base + i)
                    if not db.append(key, key):
                        dberrprint(db, "DB::append")
                        err = True
                    if self.thid < 1 and rnum > 250 and i % (rnum / 250) == 0:
                        print(".", end="")
                        if i == rnum or i % (rnum / 10) == 0:
                            print(" ({:08d})".format(i))
                        sys.stdout.flush()
        threads = []
        for thid in range(0, thnum):
            th = Appender(thid)
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        etime = time.time()
        dbmetaprint(db, False)
        print("time: {:.3f}".format(etime - stime))
    if etc and not (gopts & DB.GCONCURRENT):
        print("accepting visitors:")
        stime = time.time()
        class Accepter(threading.Thread):

            def __init__(self, thid):
                threading.Thread.__init__(self)
                self.thid = thid

            def run(self):
                nonlocal err
                class VisitorImpl(Visitor):
                    def __init__(self):
                        self.cnt = 0
                    def visit_full(self, key, value):
                        self.cnt += 1
                        if self.cnt % 100 == 0: time.sleep(0)
                        rv = self.NOP
                        if rnd:
                            num = rand(7)
                            if num == 0:
                                rv = self.cnt
                            elif num == 1:
                                rv = self.REMOVE
                        return rv
                    def visit_empty(self, key):
                        return self.visit_full(key, key)
                visitor = VisitorImpl()
                base = self.thid * rnum
                rng = rnum * thnum
                for i in range(1, rnum + 1):
                    if err: break
                    key = "{:08d}".format(rand(rng) + 1 if rnd else base + i)
                    if not db.accept(key, visitor, rnd):
                        dberrprint(db, "DB::accept")
                        err = True
                    if self.thid < 1 and rnum > 250 and i % (rnum / 250) == 0:
                        print(".", end="")
                        if i == rnum or i % (rnum / 10) == 0:
                            print(" ({:08d})".format(i))
                        sys.stdout.flush()
        threads = []
        for thid in range(0, thnum):
            th = Accepter(thid)
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        etime = time.time()
        dbmetaprint(db, False)
        print("time: {:.3f}".format(etime - stime))
    print("Getting records:")
    stime = time.time()
    class Getter(threading.Thread):
        def __init__(self, thid):
            threading.Thread.__init__(self)
            self.thid = thid
        def run(self):
            nonlocal err
            base = self.thid * rnum
            rng = rnum * thnum
            for i in range(1, rnum + 1):
                if err: break
                key = "{:08d}".format(rand(rng) + 1 if rnd else base + i)
                if db.get(key) is None and db.error() != Error.NOREC:
                    dberrprint(db, "DB::get")
                    err = True
                if self.thid < 1 and rnum > 250 and i % (rnum / 250) == 0:
                    print(".", end="")
                    if i == rnum or i % (rnum / 10) == 0:
                        print(" ({:08d})".format(i))
                    sys.stdout.flush()
    threads = []
    for thid in range(0, thnum):
        th = Getter(thid)
        th.start()
        threads.append(th)
    for th in threads:
        th.join()
    etime = time.time()
    dbmetaprint(db, False)
    print("time: {:.3f}".format(etime - stime))
    if etc and not (gopts & DB.GCONCURRENT):
        print("traversing the database by the inner iterator:")
        stime = time.time()
        class InnerTraverser(threading.Thread):
            def __init__(self, thid):
                threading.Thread.__init__(self)
                self.thid = thid
            def run(self):
                nonlocal err
                class VisitorImpl(Visitor):
                    def __init__(self, thid):
                        self.thid = thid
                        self.cnt = 0
                    def visit_full(self, key, value):
                        self.cnt += 1
                        if self.cnt % 100 == 0: time.sleep(0)
                        rv = self.NOP
                        if rnd:
                            num = rand(7)
                            if num == 0:
                                rv = str(self.cnt) * 2
                            elif num == 1:
                                rv = self.REMOVE
                        if self.thid < 1 and rnum > 250 and self.cnt % (rnum / 250) == 0:
                            print(".", end="")
                            if self.cnt == rnum or self.cnt % (rnum / 10) == 0:
                                print(" ({:08d})".format(self.cnt))
                            sys.stdout.flush()
                        return rv
                    def visit_empty(self, key):
                        return self.visit_full(key, key)
                visitor = VisitorImpl(self.thid)
                if not db.iterate(visitor, rnd):
                    dberrprint(db, "DB::iterate")
                    err = True
        threads = []
        for thid in range(0, thnum):
            th = InnerTraverser(thid)
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        if rnd: print(" (end)")
        etime = time.time()
        dbmetaprint(db, False)
        print("time: {:.3f}".format(etime - stime))
    if etc and not (gopts & DB.GCONCURRENT):
        print("traversing the database by the outer cursor:")
        stime = time.time()
        class OuterTraverser(threading.Thread):
            def __init__(self, thid):
                threading.Thread.__init__(self)
                self.thid = thid
            def run(self):
                nonlocal err
                class VisitorImpl(Visitor):
                    def __init__(self, thid):
                        self.thid = thid
                        self.cnt = 0
                    def visit_full(self, key, value):
                        self.cnt += 1
                        if self.cnt % 100 == 0: time.sleep(0)
                        rv = self.NOP
                        if rnd:
                            num = rand(7)
                            if num == 0:
                                rv = str(self.cnt) * 2
                            elif num == 1:
                                rv = self.REMOVE
                        if self.thid < 1 and rnum > 250 and self.cnt % (rnum / 250) == 0:
                            print(".", end="")
                            if self.cnt == rnum or self.cnt % (rnum / 10) == 0:
                                print(" ({:08d})".format(self.cnt))
                            sys.stdout.flush()
                        return rv
                    def visit_empty(self, key):
                        return self.visit_full(key, key)
                visitor = VisitorImpl(self.thid)
                cur = db.cursor()
                if not cur.jump() and db.error() != Error.NOREC:
                    dberrprint(db, "Cursor::jump")
                    err = True
                while cur.accept(visitor, rnd, False):
                    if not cur.step() and db.error() != Error.NOREC:
                        dberrprint(db, "Cursor::step")
                        err = True
                if db.error() != Error.NOREC:
                    dberrprint(db, "Cursor::accept")
                    err = True
        threads = []
        for thid in range(0, thnum):
            th = OuterTraverser(thid)
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        if rnd: print(" (end)")
        etime = time.time()
        dbmetaprint(db, False)
        print("time: {:.3f}".format(etime - stime))
    print("Removing records:")
    stime = time.time()
    class Remover(threading.Thread):
        def __init__(self, thid):
            threading.Thread.__init__(self)
            self.thid = thid
        def run(self):
            nonlocal err
            base = self.thid * rnum
            rng = rnum * thnum
            for i in range(1, rnum + 1):
                if err: break
                key = "{:08d}".format(rand(rng) + 1 if rnd else base + i)
                if not db.remove(key) and db.error() != Error.NOREC:
                    dberrprint(db, "DB::remove")
                    err = True
                if self.thid < 1 and rnum > 250 and i % (rnum / 250) == 0:
                    print(".", end="")
                    if i == rnum or i % (rnum / 10) == 0:
                        print(" ({:08d})".format(i))
                    sys.stdout.flush()
    threads = []
    for thid in range(0, thnum):
        th = Remover(thid)
        th.start()
        threads.append(th)
    for th in threads:
        th.join()
    etime = time.time()
    dbmetaprint(db, True)
    print("time: {:.3f}".format(etime - stime))
    print("closing the database:")
    stime = time.time()
    if not db.close():
        dberrprint(db, "DB::close")
        err = True
    etime = time.time()
    print("time: {:.3f}".format(etime - stime))
    print("error" if err else "ok")
    print("")
    return 1 if err else 0


# perform wicked command
def procwicked(path, rnum, gopts, thnum, itnum):
    print("<Wicked Test>")
    print("  path={}  rnum={}  gopts={}  thnum={}  itnum={}".
          format(path, rnum, gopts, thnum, itnum))
    print("")
    err = False
    db = DB(gopts)
    db.tune_exception_rule([Error.SUCCESS, Error.NOIMPL, Error.MISC])
    for itcnt in range(1, itnum + 1):
        if itnum > 1: print("iteration {}:".format(itcnt))
        stime = time.time()
        omode = DB.OWRITER | DB.OCREATE
        if itcnt == 1: omode |= DB.OTRUNCATE
        if not db.open(path, omode):
            dberrprint(db, "DB::open")
            err = True
        class Operator(threading.Thread):
            def __init__(self, thid):
                threading.Thread.__init__(self)
                self.thid = thid
                self.cnt = 0
            def run(self):
                nonlocal err
                class VisitorImpl(Visitor):
                    def __init__(self):
                        self.cnt = 0
                    def visit_full(self, key, value):
                        self.cnt += 1
                        if self.cnt % 100 == 0: time.sleep(0)
                        rv = self.NOP
                        num = rand(7)
                        if num == 0:
                            rv = self.cnt
                        elif num == 1:
                            rv = self.REMOVE
                        return rv
                    def visit_empty(self, key):
                        return self.visit_full(key, key)
                visitor = VisitorImpl()
                cur = db.cursor()
                rng = rnum * thnum
                for i in range(1, rnum + 1):
                    if err: break
                    tran = rand(100) == 0
                    if tran and not db.begin_transaction(rand(rnum) == 0):
                        dberrprint(db, "DB::begin_transaction")
                        tran = False
                        err = True
                    key = "{:08d}".format(rand(rng) + 1)
                    op = rand(12)
                    if op == 0:
                        if not db.set(key, key):
                            dberrprint(db, "DB::set")
                            err = True
                    elif op == 1:
                        if not db.add(key, key) and db.error() != Error.DUPREC:
                            dberrprint(db, "DB::add")
                            err = True
                    elif op == 2:
                        if not db.replace(key, key) and db.error() != Error.NOREC:
                            dberrprint(db, "DB::replace")
                            err = True
                    elif op == 3:
                        if not db.append(key, key):
                            dberrprint(db, "DB::append")
                            err = True
                    elif op == 4:
                        if rand(2) == 0:
                            if db.increment(key, rand(10)) is None and \
                                    db.error() != Error.LOGIC:
                                dberrprint(db, "DB::increment")
                                err = True
                        else:
                            if db.increment_double(key, rand(10000) / 1000.0) is None and \
                                    db.error() != Error.LOGIC:
                                dberrprint(db, "DB::increment_double")
                                err = True
                    elif op == 5:
                        if not db.cas(key, key, key) and db.error() != Error.LOGIC:
                            dberrprint(db, "DB::cas")
                            err = True
                    elif op == 6:
                        if not db.remove(key) and db.error() != Error.NOREC:
                            dberrprint(db, "DB::remove")
                            err = True
                    elif op == 7:
                        if not db.accept(key, visitor, True) and \
                                (not (gopts & DB.GCONCURRENT) or db.error() != Error.INVALID):
                            dberrprint(db, "DB::accept")
                            err = True
                    elif op == 8:
                        if rand(10) == 0:
                            if rand(4) == 0:
                                try:
                                    if not cur.jump_back(key) and db.error() != Error.NOREC:
                                        dberrprint(db, "Cursor::jump_back")
                                        err = True
                                except Error.XNOIMPL as e:
                                    pass
                            else:
                                if not cur.jump(key) and db.error() != Error.NOREC:
                                    dberrprint(db, "Cursor::jump")
                                    err = True
                        cop = rand(6)
                        if cop == 0:
                            if cur.get_key() is None and db.error() != Error.NOREC:
                                dberrprint(db, "Cursor::get_key")
                                err = True
                        elif cop == 1:
                            if cur.get_value() is None and db.error() != Error.NOREC:
                                dberrprint(db, "Cursor::get_value")
                                err = True
                        elif cop == 2:
                            if cur.get() is None and db.error() != Error.NOREC:
                                dberrprint(db, "Cursor::get")
                                err = True
                        elif cop == 3:
                            if not cur.remove() and db.error() != Error.NOREC:
                                dberrprint(db, "Cursor::remove")
                                err = True
                        else:
                            if not cur.accept(visitor, True, rand(2) == 0) and \
                                    db.error() != Error.NOREC and \
                                    (not (gopts & DB.GCONCURRENT) or
                                     db.error() != Error.INVALID):
                                dberrprint(db, "Cursor::accept")
                                err = True
                        if rand(2) == 0:
                            if not cur.step() and db.error() != Error.NOREC:
                                dberrprint(db, "Cursor::step")
                                err = True
                        if rand(rnum / 50 + 1) == 0:
                            prefix = key[0:-1]
                            if db.match_prefix(prefix, rand(10)) is None:
                                dberrprint(db, "DB::match_prefix")
                                err = True
                        if rand(rnum / 50 + 1) == 0:
                            regex = key[0:-1]
                            if db.match_regex(regex, rand(10)) is None and \
                                    db.error() != Error.NOLOGIC:
                                dberrprint(db, "DB::match_regex")
                                err = True
                        if rand(rnum / 50 + 1) == 0:
                            origin = key[0:-1]
                            if db.match_similar(origin, 3, rand(2) == 0, rand(10)) is None:
                                dberrprint(db, "DB::match_similar")
                                err = True
                        if rand(10) == 0:
                            paracur = db.cursor()
                            paracur.jump(key)
                            if not paracur.accept(visitor, True, rand(2) == 0) and \
                                    db.error() != Error.NOREC and \
                                    (not (gopts & DB.GCONCURRENT) or
                                     db.error() != Error.INVALID):
                                dberrprint(db, "Cursor::accept")
                                err = True
                            paracur.disable()
                    else:
                        if db.get(key) is None and db.error() != Error.NOREC:
                            dberrprint(db, "DB::get")
                            err = True
                    if tran and not db.end_transaction(rand(10) > 0):
                        dberrprint(db, "DB::begin_transaction")
                        tran = False
                        err = True
                    if self.thid < 1 and rnum > 250 and i % (rnum / 250) == 0:
                        print(".", end="")
                        if i == rnum or i % (rnum / 10) == 0:
                            print(" ({:08d})".format(i))
                        sys.stdout.flush()
                cur.disable()
        threads = []
        for thid in range(0, thnum):
            th = Operator(thid)
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        dbmetaprint(db, itcnt == itnum)
        if not db.close():
            dberrprint(db, "DB::close")
            err = True
        etime = time.time()
        print("time: {:.3f}".format(etime - stime))
    print("error" if err else "ok")
    print("")
    return 1 if err else 0


# perform misc command
def procmisc(path):
    print("<Miscellaneous Test>")
    print("  path={}".format(path))
    print("")
    err = False
    if conv_bytes("mikio") != b"mikio" or conv_bytes(123.45) != b"123.45":
        print("{}: conv_str: error".format(progname))
        err = True
    print("calling utility functions:")
    atoi("123.456mikio")
    atoix("123.456mikio")
    atof("123.456mikio")
    hash_murmur(path)
    hash_fnv(path)
    levdist(path, "casket")
    dcurs = []
    print("opening the database with functor:")
    def myproc(db):
        nonlocal err
        db.tune_exception_rule([Error.SUCCESS, Error.NOIMPL, Error.MISC])
        repr(db)
        str(db)
        rnum = 10000
        print("setting records:")
        for i in range(0, rnum):
            db[i] = i
        if db.count() != rnum:
            dberrprint(db, "DB::count")
            err = True
        print("deploying cursors:")
        for i in range(1, 101):
            cur = db.cursor()
            if not cur.jump(i):
                dberrprint(db, "Cursor::jump")
                err = True
            num = i % 3
            if num == 0:
                dcurs.append(cur)
            elif num == 1:
                cur.disable()
            repr(cur)
            str(cur)
        print("getting records:")
        for cur in dcurs:
            if cur.get_key() is None:
                dberrprint(db, "Cursor::jump")
                err = True
        print("accepting visitor:")
        def visitfunc(key, value):
            rv = Visitor.NOP
            num = int(key) % 3
            if num == 0:
                if value is None:
                    rv = "empty:{}".format(key.decode())
                else:
                    rv = "full:{}".format(key.decode())
            elif num == 1:
                rv = Visitor.REMOVE
            return rv
        for i in range(0, rnum * 2):
            if not db.accept(i, visitfunc, True):
                dberrprint(db, "DB::access")
                err = True
        print("accepting visitor by iterator:")
        if not db.iterate(lambda key, value: None, False):
            dberrprint(db, "DB::iterate")
            err = True
        if not db.iterate(lambda key, value: str.upper(value.decode()), True):
            dberrprint(db, "DB::iterate")
            err = True
        print("accepting visitor with a cursor:")
        cur = db.cursor()

        def curvisitfunc(key, value):
            rv = Visitor.NOP
            num = int(key) % 7
            if num == 0:
                rv = "cur:full:{}".format(key.decode())
            elif num == 1:
                rv = Visitor.REMOVE
            return rv
        try:
            if not cur.jump_back():
                dberrprint(db, "Cursor::jump_back")
                err = True
            while cur.accept(curvisitfunc, True):
                cur.step_back()
        except Error.XNOIMPL as e:
            if not cur.jump():
                dberrprint(db, "Cursor::jump")
                err = True
            while cur.accept(curvisitfunc, True):
                cur.step()
        print("accepting visitor in bulk:")
        keys = []
        for i in range(1, 11):
            keys.append(i)
        if not db.accept_bulk(keys, visitfunc, True):
            dberrprint(db, "DB::accept_bulk")
            err = True
        recs = {}
        for i in range(1, 11):
            recs[i] = "[{:d}]".format(i)
        if db.set_bulk(recs) < 0:
            dberrprint(db, "DB::set_bulk")
            err = True
        if not db.get_bulk(keys):
            dberrprint(db, "DB::get_bulk")
            err = True
        if not db.get_bulk_str(keys):
            dberrprint(db, "DB::get_bulk_str")
            err = True
        if db.remove_bulk(keys) < 0:
            dberrprint(db, "DB::remove_bulk")
            err = True
        print("synchronizing the database:")

        class FileProcessorImpl(FileProcessor):
            def process(self, path, count, size):
                return True
        fproc = FileProcessorImpl()
        if not db.synchronize(False, fproc):
            dberrprint(db, "DB::synchronize")
            err = True
        if not db.synchronize(False, lambda path, count, size: True):
            dberrprint(db, "DB::synchronize")
            err = True
        if not db.occupy(False, fproc):
            dberrprint(db, "DB::occupy")
            err = True
        print("performing transaction:")

        def commitfunc():
            db["tako"] = "ika"
            return True
        if not db.transaction(commitfunc, False):
            dberrprint(db, "DB::transaction")
            err = True
        if db["tako"].decode() != "ika":
            dberrprint(db, "DB::transaction")
            err = True
        del db["tako"]
        cnt = db.count()
        def abortfunc():
            db["tako"] = "ika"
            db["kani"] = "ebi"
            return False
        if not db.transaction(abortfunc, False):
            dberrprint(db, "DB::transaction")
            err = True
        if db["tako"] is not None or db["kani"] is not None or db.count() != cnt:
            dberrprint(db, "DB::transaction")
            err = True
        print("closing the database:")
    dberr = DB.process(myproc, path, DB.OWRITER | DB.OCREATE | DB.OTRUNCATE)
    if dberr is not None:
        print("{}: DB::process: {}".format(progname, str(dberr)))
        err = True;
    print("accessing dead cursors:")
    for cur in dcurs:
        cur.get_key()
    print("checking the exceptional mode:")
    db = DB(DB.GEXCEPTIONAL)
    try:
        db.open("hoge")
    except Error.XINVALID as e:
        if e.code() != Error.INVALID:
            dberrprint(db, "DB::open")
            err = True
    else:
        dberrprint(db, "DB::open")
        err = True
    print("re-opening the database as a reader:")
    db = DB()
    if not db.open(path, DB.OREADER):
        dberrprint(db, "DB::open")
        err = True
    print("traversing records by iterator:")
    keys = []
    for key in db:
        keys.append(key)
    if db.count() != len(keys):
        dberrprint(db, "DB::count")
        err = True
    print("checking records:")
    for key in keys:
        if db.get(key) is None:
            dberrprint(db, "DB::get")
            err = True
    print("closing the database:")
    if not db.close():
        dberrprint(db, "DB::close")
        err = True
    print("re-opening the database in the concurrent mode:")
    db = DB(DB.GCONCURRENT)
    if not db.open(path, DB.OWRITER):
        dberrprint(db, "DB::open")
        err = True
    if not db.set("tako", "ika"):
        dberrprint(db, "DB::set")
        err = True

    def dummyfunc(key, value):
        raise
    if db.accept(dummyfunc, "tako") or db.error() != Error.INVALID:
        dberrprint(db, "DB::accept")
        err = True
    print("removing records by cursor:")
    cur = db.cursor()
    if not cur.jump():
        dberrprint(db, "Cursor::jump")
        err = True
    cnt = 0
    while True:
        key = cur.get_key(True)
        if not key: break
        if cnt % 10 != 0:
            if not db.remove(key):
                dberrprint(db, "DB::remove")
                err = True
        cnt += 1
    if db.error() != Error.NOREC:
        dberrprint(db, "Cursor::get_key")
        err = True
    cur.disable()
    print("processing a cursor by callback:")

    def curprocfunc(cur):
        if not cur.jump():
            dberrprint(db, "Cursor::jump")
            err = True
        value = "[{}]".format(cur.get_value_str())
        if not cur.set_value(value):
            dberrprint(db, "Cursor::set_value")
            err = True
        if cur.get_value() != value.encode():
            dberrprint(db, "Cursor::get_value")
            err = True
    db.cursor_process(curprocfunc)
    print("dumping records into snapshot:")
    snappath = db.path()
    if re.match(r".*\.(kch|kct)$", snappath):
        snappath = snappath + ".kcss"
    else:
        snappath = "kctest.kcss"
    if not db.dump_snapshot(snappath):
        dberrprint(db, "DB::dump_snapshot")
        err = True
    cnt = db.count()
    print("clearing the database:")
    if not db.clear():
        dberrprint(db, "DB::clear")
        err = True
    print("loading records from snapshot:")
    if not db.load_snapshot(snappath):
        dberrprint(db, "DB::load_snapshot")
        err = True
    if db.count() != cnt:
        dberrprint(db, "DB::load_snapshot")
        err = True
    os.remove(snappath)
    copypath = db.path()
    suffix = None
    if copypath.endswith(".kch"):
        suffix = ".kch"
    elif copypath.endswith(".kct"):
        suffix = ".kct"
    elif copypath.endswith(".kcd"):
        suffix = ".kcd"
    elif copypath.endswith(".kcf"):
        suffix = ".kcf"
    if suffix is not None:
        print("performing copy and merge:")
        copypaths = []
        for i in range(0, 2):
            copypaths.append("{}.{}{}".format(copypath, i + 1, suffix))
        srcary = []
        for copypath in copypaths:
            if not db.copy(copypath):
                dberrprint(db, "DB::copy")
                err = True
            srcdb = DB()
            if not srcdb.open(copypath, DB.OREADER):
                dberrprint(srcdb, "DB::open")
                err = True
            srcary.append(srcdb)
        if not db.merge(srcary, DB.MAPPEND):
            dberrprint(db, "DB::merge")
            err = True
        for srcdb in srcary:
            if not srcdb.close():
                dberrprint(srcdb, "DB::open")
                err = True
        for copypath in copypaths:
            shutil.rmtree(copypath, True)
            try:
                os.remove(copypath)
            except OSError as e:
                pass
    print("shifting records:")
    ocnt = db.count()
    cnt = 0
    while True:
        rec = db.shift() if cnt % 2 == 0 else db.shift_str()
        if rec is None: break
        cnt += 1
    if db.error() != Error.NOREC:
        dberrprint(db, "DB::shift")
        err = True
    if db.count() != 0 or cnt != ocnt:
        dberrprint(db, "DB::shift")
        err = True
    print("closing the database:")
    if not db.close():
        dberrprint(db, "DB::close")
        err = True
    repr(db)
    str(db)
    print("error" if err else "ok")
    print("")
    return 1 if err else 0


# execute main
progname = sys.argv[0]
progname = re.sub(r".*/", "", progname)
rndstate = random.Random()
exit(main())

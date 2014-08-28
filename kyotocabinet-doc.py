#-------------------------------------------------------------------------------------------------
# Python binding of Kyoto Cabinet
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
#-------------------------------------------------------------------------------------------------


"""
Python 3.x Binding of Kyoto Cabinet
===================================

Introduction
------------

Kyoto Cabinet is a library of routines for managing a database.  The database is a simple data file containing records, each is a pair of a key and a value.  Every key and value is serial bytes with variable length.  Both binary data and character string can be used as a key and a value.  Each key must be unique within a database.  There is neither concept of data tables nor data types.  Records are organized in hash table or B+ tree.

The following access methods are provided to the database: storing a record with a key and a value, deleting a record by a key, retrieving a record by a key.  Moreover, traversal access to every key are provided.  These access methods are similar to ones of the original DBM (and its followers: NDBM and GDBM) library defined in the UNIX standard.  Kyoto Cabinet is an alternative for the DBM because of its higher performance.

Each operation of the hash database has the time complexity of "O(1)".  Therefore, in theory, the performance is constant regardless of the scale of the database.  In practice, the performance is determined by the speed of the main memory or the storage device.  If the size of the database is less than the capacity of the main memory, the performance will seem on-memory speed, which is faster than std::map of STL.  Of course, the database size can be greater than the capacity of the main memory and the upper limit is 8 exabytes.  Even in that case, each operation needs only one or two seeking of the storage device.

Each operation of the B+ tree database has the time complexity of "O(log N)".  Therefore, in theory, the performance is logarithmic to the scale of the database.  Although the performance of random access of the B+ tree database is slower than that of the hash database, the B+ tree database supports sequential access in order of the keys, which realizes forward matching search for strings and range search for integers.  The performance of sequential access is much faster than that of random access.

This library wraps the polymorphic database of the C++ API.  So, you can select the internal data structure by specifying the database name in runtime.  This library works on Python 3.x (3.1 or later) only.  Python 2.x requires another dedicated package.

Installation
------------

Install the latest version of Kyoto Cabinet beforehand and get the package of the Python binding of Kyoto Cabinet.

Enter the directory of the extracted package then perform installation.  If your system has the another command except for the "python3" command, edit the Makefile beforehand.::

 make
 make check
 su
 make install

Symbols of the module `kyotocabinet' should be included in each source file of application programs.::

 import kyotocabinet

An instance of the class `DB' is used in order to handle a database.  You can store, delete, and retrieve records with the instance.

Example
-------

The following code is a typical example to use a database.::

 from kyotocabinet import *
 import sys
 
 # create the database object
 db = DB()
 
 # open the database
 if not db.open("casket.kch", DB.OWRITER | DB.OCREATE):
     print("open error: " + str(db.error()), file=sys.stderr)
 
 # store records
 if not db.set("foo", "hop") or \
         not db.set("bar", "step") or \
         not db.set("baz", "jump"):
     print("set error: " + str(db.error()), file=sys.stderr)
 
 # retrieve records
 value = db.get_str("foo")
 if value:
     print(value)
 else:
     print("get error: " + str(db.error()), file=sys.stderr)
 
 # traverse records
 cur = db.cursor()
 cur.jump()
 while True:
     rec = cur.get_str(True)
     if not rec: break
     print(rec[0] + ":" + rec[1])
 cur.disable()
 
 # close the database
 if not db.close():
     print("close error: " + str(db.error()), file=sys.stderr)

The following code is a more complex example, which uses the Visitor pattern.::

 from kyotocabinet import *
 import sys
 
 # create the database object
 db = DB()
 
 # open the database
 if not db.open("casket.kch", DB.OREADER):
     print("open error: " + str(db.error()), file=sys.stderr)
 
 # define the visitor
 class VisitorImpl(Visitor):
     # call back function for an existing record
     def visit_full(self, key, value):
         print("{}:{}".format(key.decode(), value.decode()))
         return self.NOP
     # call back function for an empty record space
     def visit_empty(self, key):
         print("{} is missing".format(key.decode()), file=sys.stderr)
         return self.NOP
 visitor = VisitorImpl()
 
 # retrieve a record with visitor
 if not db.accept("foo", visitor, False) or \
         not db.accept("dummy", visitor, False):
     print("accept error: " + str(db.error()), file=sys.stderr)
 
 # traverse records with visitor
 if not db.iterate(visitor, False):
     print("iterate error: " + str(db.error()), file=sys.stderr)
 
 # close the database
 if not db.close():
     print("close error: " + str(db.error()), file=sys.stderr)

The following code is also a complex example, which is more suited to the Python style.::

 from kyotocabinet import *
 import sys
 
 # define the functor
 def dbproc(db):
 
   # store records
   db[b'foo'] = b'step';  # bytes is fundamental
   db['bar'] = 'hop';     # string is also ok
   db[3] = 'jump';        # number is also ok
 
   # retrieve a record value
   print("{}".format(db['foo'].decode()))
 
   # update records in transaction
   def tranproc():
       db['foo'] = 2.71828
       return True
   db.transaction(tranproc)
 
   # multiply a record value
   def mulproc(key, value):
       return float(value) * 2
   db.accept('foo', mulproc)
 
   # traverse records by iterator
   for key in db:
       print("{}:{}".format(key.decode(), db[key].decode()))
 
   # upcase values by iterator
   def upproc(key, value):
       return value.upper()
   db.iterate(upproc)
 
   # traverse records by cursor
   def curproc(cur):
       cur.jump()
       def printproc(key, value):
           print("{}:{}".format(key.decode(), value.decode()))
           return Visitor.NOP
       while cur.accept(printproc):
           cur.step()
   db.cursor_process(curproc)
 
 # process the database by the functor
 DB.process(dbproc, 'casket.kch')

License
-------

Copyright (C) 2009-2010 FAL Labs.  All rights reserved.

Kyoto Cabinet is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.

Kyoto Cabinet is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
"""


VERSION = "x.y.z"
"""The version information."""

def conv_bytes(obj):
    """
    Convert any object to a string.
    @param obj: the object.
    @return: the result string.
    """

def atoi(str):
    """
    Convert a string to an integer.
    @param str: specifies the string.
    @return: the integer.  If the string does not contain numeric expression, 0 is returned.
    """

def atoix(str):
    """
    Convert a string with a metric prefix to an integer.
    @param str: the string, which can be trailed by a binary metric prefix.  "K", "M", "G", "T", "P", and "E" are supported.  They are case-insensitive.
    @return: the integer.  If the string does not contain numeric expression, 0 is returned.  If the integer overflows the domain, INT64_MAX or INT64_MIN is returned according to the sign.
    """

def atof(str):
    """
    Convert a string to a real number.
    @param str: specifies the string.
    @return: the real number.  If the string does not contain numeric expression, 0.0 is returned.
    """

def hash_murmur(str):
    """
    Get the hash value of a string by MurMur hashing.
    @param str: the string.
    @return: the hash value.
    """

def hash_fnv(str):
    """
    Get the hash value of a string by FNV hashing.
    @param str: the string.
    @return: the hash value.
    """

def levdist(a, b, utf):
    """
    Calculate the levenshtein distance of two strings.
    @param a: one string.
    @param b: the other string.
    @param utf: flag to treat keys as UTF-8 strings.
    @return: the levenshtein distance.

    """


class Error:
    """
    Error data.
    """
    SUCCESS = 0
    """error code: success."""
    NOIMPL = 1
    """error code: not implemented."""
    INVALID = 2
    """error code: invalid operation."""
    NOREPOS = 3
    """error code: no repository."""
    NOPERM = 4
    """error code: no permission."""
    BROKEN = 5
    """error code: broken file."""
    DUPREC = 6
    """error code: record duplication."""
    NOREC = 7
    """error code: no record."""
    LOGIC = 8
    """error code: logical inconsistency."""
    SYSTEM = 9
    """error code: system error."""
    MISC = 15
    """error code: miscellaneous error."""
    def __init__(self, code, message):
        """
        Create an error object.
        @param code: the error code.
        @param message: the supplement message.
        @return: the error object.
        """
    def set(self, code, message):
        """
        Set the error information.
        @param code: the error code.
        @param message: the supplement message.
        @return: always None.
        """
    def code(self):
        """
        Get the error code.
        @return: the error code.
        """
    def name(self):
        """
        Get the readable string of the code.
        @return: the readable string of the code.
        """
    def message(self):
        """
        Get the supplement message.
        @return: the supplement message.
        """
    def __repr__(self):
        """
        Get the representing expression.
        @return: the representing expression.
        """
    def __str__(self):
        """
        Get the string expression.
        @return: the string expression.
        """
    def __cmp__(self, right):
        """
        Generic comparison operator.
        @param right: an error object or an error code.
        @return: boolean value of the comparison result.
        """


class Visitor:
    """
    Interface to access a record.
    """
    NOP = "(magic data)"
    """magic data: no operation."""
    REMOVE = "(magic data)"
    """magic data: remove the record."""
    def visit_full(self, key, value):
        """
        Visit a record.
        @param key: the key.
        @param value: the value.
        @return: If it is a string, the value is replaced by the content.  If it is Visitor.NOP, nothing is modified.  If it is Visitor.REMOVE, the record is removed.
        """
    def visit_empty(self, key):
        """
        Visit a empty record space.
        @param key: the key.
        @return: If it is a string, the value is replaced by the content.  If it is Visitor.NOP or Visitor.REMOVE, nothing is modified.
        """


class FileProcessor:
    """
    Interface to process the database file.
    """
    def process(self, path, size, count):
        """
        Process the database file.
        @param path: the path of the database file.
        @param count: the number of records.
        @param size: the size of the available region.
        @return: true on success, or false on failure.
        """


class Cursor:
    """
    Interface of cursor to indicate a record.
    """
    def disable(self):
        """
        Disable the cursor.
        @return: always None.
        @note: This method should be called explicitly when the cursor is no longer in use.
        """
    def accept(self, visitor, writable = True, step = False):
        """
        Accept a visitor to the current record.
        @param visitor: a visitor object which implements the Visitor interface, or a function object which receives the key and the value.
        @param writable: true for writable operation, or false for read-only operation.
        @param step: true to move the cursor to the next record, or false for no move.
        @return: true on success, or false on failure.
        @note: The operation for each record is performed atomically and other threads accessing the same record are blocked.  To avoid deadlock, any explicit database operation must not be performed in this method.
        """
    def set_value(self, value, step = False):
        """
        Set the value of the current record.
        @param value: the value.
        @param step: true to move the cursor to the next record, 
        @return: true on success, or false on failure.
        """
    def remove(self):
        """
        Remove the current record.
        @return: true on success, or false on failure.
        @note: If no record corresponds to the key, false is returned.  The cursor is moved to the next record implicitly.
        """
    def get_key(self, step = False):
        """
        Get the key of the current record.
        @param step: true to move the cursor to the next record, or false for no move.
        @return: the key of the current record, or None on failure.
        @note: If the cursor is invalidated, None is returned.
        """
    def get_key_str(self, step = False):
        """
        Get the key of the current record.
        @note: Equal to the original Cursor::get_key method except that the return value is string.
        """
    def get_value(self, step = False):
        """
        Get the value of the current record.
        @param step: true to move the cursor to the next record, or false for no move.
        @return: the value of the current record, or None on failure.
        @note: If the cursor is invalidated, None is returned.
        """
    def get_value_str(self, step = False):
        """
        Get the value of the current record.
        @note: Equal to the original Cursor::get_value method except that the return value is string.
        """
    def get(self, step = False):
        """
        Get a pair of the key and the value of the current record.
        @param step: true to move the cursor to the next record, or false for no move.
        @return: a pair of the key and the value of the current record, or None on failure.
        @note: If the cursor is invalidated, None is returned.
        """
    def get_str(self, step = False):
        """
        Get a pair of the key and the value of the current record.
        @note: Equal to the original Cursor::get method except that the return value is string.
        """
    def seize(self):
        """
        Get a pair of the key and the value of the current record and remove it atomically.
        @return: a pair of the key and the value of the current record, or None on failure.
        @note: If the cursor is invalidated, None is returned.  The cursor is moved to the next record implicitly.
        """
    def seize_str(self):
        """
        Get a pair of the key and the value of the current record and remove it atomically.
        @note: Equal to the original Cursor::seize method except that the return value is string.
        """
    def jump(self, key = None):
        """
        Jump the cursor to a record for forward scan.
        @param key: the key of the destination record.  If it is None, the destination is the first record.
        @return: true on success, or false on failure.
        """
    def jump_back(self, key = None):
        """
        Jump the cursor to a record for backward scan.
        @param key: the key of the destination record.  If it is None, the destination is the last record.
        @return: true on success, or false on failure.
        @note: This method is dedicated to tree databases.  Some database types, especially hash databases, will provide a dummy implementation.
        """
    def step(self):
        """
        Step the cursor to the next record.
        @return: true on success, or false on failure.
        """
    def step_back(self):
        """
        Step the cursor to the previous record.
        @return: true on success, or false on failure.
        @note: This method is dedicated to tree databases.  Some database types, especially hash databases, may provide a dummy implementation.
        """
    def db(self):
        """
        Get the database object.
        @return: the database object.
        """
    def error(self):
        """
        Get the last happened error.
        @return: the last happened error.
        """
    def __repr__(self):
        """
        Get the representing expression.
        @return: the representing expression.
        """
    def __str__(self):
        """
        Get the string expression.
        @return: the string expression.
        """
    def __next__(self):
        """
        Get the next key.
        @return: the next key, or None on failure.
        """


class DB:
    """
    Interface of database abstraction.
    """
    GEXCEPTIONAL = 1
    """generic mode: exceptional mode."""
    GCONCURRENT = 2
    """generic mode: concurrent mode."""
    OREADER = 1
    """open mode: open as a reader."""
    OWRITER = 2
    """open mode: open as a writer."""
    OCREATE = 4
    """open mode: writer creating."""
    OTRUNCATE = 8
    """open mode: writer truncating."""
    OAUTOTRAN = 16
    """open mode: auto transaction."""
    OAUTOSYNC = 32
    """open mode: auto synchronization."""
    ONOLOCK = 64
    """open mode: open without locking."""
    OTRYLOCK = 128
    """open mode: lock without blocking."""
    ONOREPAIR = 256
    """open mode: open without auto repair."""
    MSET = 0
    """merge mode: overwrite the existing value."""
    MADD = 1
    """merge mode: keep the existing value."""
    MREPLACE = 2
    """merge mode: modify the existing record only."""
    MAPPEND = 3
    """merge mode: append the new value."""
    def __init__(self, opts = 0):
        """
        Create a database object.
        @param opts: the optional features by bitwise-or: DB.GEXCEPTIONAL for the exceptional mode, DB.GCONCURRENT for the concurrent mode.
        @return: the database object.
        @note: The exceptional mode means that fatal errors caused by methods are reported by exceptions raised.  The concurrent mode means that database operations by multiple threads are performed concurrently without the giant VM lock.  However, it has a side effect that such methods with call back of Python code as DB#accept, DB#accept_bulk, DB#iterate, and Cursor#accept are disabled.
        """
    def error(self):
        """
        Get the last happened error.
        @return: the last happened error.
        """
    def open(self, path = ":", mode = OWRITER | OCREATE):
        """
        Open a database file.
        @param path: the path of a database file.  If it is "-", the database will be a prototype hash database.  If it is "+", the database will be a prototype tree database.  If it is ":", the database will be a stash database.  If it is "*", the database will be a cache hash database.  If it is "%", the database will be a cache tree database.  If its suffix is ".kch", the database will be a file hash database.  If its suffix is ".kct", the database will be a file tree database.  If its suffix is ".kcd", the database will be a directory hash database.  If its suffix is ".kcf", the database will be a directory tree database.  If its suffix is ".kcx", the database will be a plain text database.  Otherwise, this function fails.  Tuning parameters can trail the name, separated by "#".  Each parameter is composed of the name and the value, separated by "=".  If the "type" parameter is specified, the database type is determined by the value in "-", "+", ":", "*", "%", "kch", "kct", "kcd", kcf", and "kcx".  All database types support the logging parameters of "log", "logkinds", and "logpx".  The prototype hash database and the prototype tree database do not support any other tuning parameter.  The stash database supports "bnum".  The cache hash database supports "opts", "bnum", "zcomp", "capcnt", "capsiz", and "zkey".  The cache tree database supports all parameters of the cache hash database except for capacity limitation, and supports "psiz", "rcomp", "pccap" in addition.  The file hash database supports "apow", "fpow", "opts", "bnum", "msiz", "dfunit", "zcomp", and "zkey".  The file tree database supports all parameters of the file hash database and "psiz", "rcomp", "pccap" in addition.  The directory hash database supports "opts", "zcomp", and "zkey".  The directory tree database supports all parameters of the directory hash database and "psiz", "rcomp", "pccap" in addition.  The plain text database does not support any other tuning parameter.
        @param mode: the connection mode.  DB.OWRITER as a writer, DB.OREADER as a reader.  The following may be added to the writer mode by bitwise-or: DB.OCREATE, which means it creates a new database if the file does not exist, DB.OTRUNCATE, which means it creates a new database regardless if the file exists, DB.OAUTOTRAN, which means each updating operation is performed in implicit transaction, DB.OAUTOSYNC, which means each updating operation is followed by implicit synchronization with the file system.  The following may be added to both of the reader mode and the writer mode by bitwise-or: DB.ONOLOCK, which means it opens the database file without file locking, DB.OTRYLOCK, which means locking is performed without blocking, DB.ONOREPAIR, which means the database file is not repaired implicitly even if file destruction is detected.
        @return: true on success, or false on failure.
        @note: The tuning parameter "log" is for the original "tune_logger" and the value specifies the path of the log file, or "-" for the standard output, or "+" for the standard error.  "logkinds" specifies kinds of logged messages and the value can be "debug", "info", "warn", or "error".  "logpx" specifies the prefix of each log message.  "opts" is for "tune_options" and the value can contain "s" for the small option, "l" for the linear option, and "c" for the compress option.  "bnum" corresponds to "tune_bucket".  "zcomp" is for "tune_compressor" and the value can be "zlib" for the ZLIB raw compressor, "def" for the ZLIB deflate compressor, "gz" for the ZLIB gzip compressor, "lzo" for the LZO compressor, "lzma" for the LZMA compressor, or "arc" for the Arcfour cipher.  "zkey" specifies the cipher key of the compressor.  "capcnt" is for "cap_count".  "capsiz" is for "cap_size".  "psiz" is for "tune_page".  "rcomp" is for "tune_comparator" and the value can be "lex" for the lexical comparator, "dec" for the decimal comparator, "lexdesc" for the lexical descending comparator, or "decdesc" for the decimal descending comparator.  "pccap" is for "tune_page_cache".  "apow" is for "tune_alignment".  "fpow" is for "tune_fbp".  "msiz" is for "tune_map".  "dfunit" is for "tune_defrag".  Every opened database must be closed by the PolyDB::close method when it is no longer in use.  It is not allowed for two or more database objects in the same process to keep their connections to the same database file at the same time.
        """
    def close(self):
        """
        Close the database file.
        @return: true on success, or false on failure.
        """
    def accept(self, key, visitor, writable = True):
        """
        Accept a visitor to a record.
        @param key: the key.
        @param visitor: a visitor object which implements the Visitor interface, or a function object which receives the key and the value.
        @param writable: true for writable operation, or false for read-only operation.
        @return: true on success, or false on failure.
        @note: The operation for each record is performed atomically and other threads accessing the same record are blocked.  To avoid deadlock, any explicit database operation must not be performed in this method.
        """
    def accept_bulk(self, keys, visitor, writable = True):
        """
        Accept a visitor to multiple records at once.
        @param keys: specifies a sequence object of the keys.
        @param visitor: a visitor object which implements the Visitor interface, or a function object which receives the key and the value.
        @param writable: true for writable operation, or false for read-only operation.
        @return: true on success, or false on failure.
        @note: The operations for specified records are performed atomically and other threads accessing the same records are blocked.  To avoid deadlock, any explicit database operation must not be performed in this method.
        """
    def iterate(self, visitor, writable = True):
        """
        Iterate to accept a visitor for each record.
        @param visitor: a visitor object which implements the Visitor interface, or a function object which receives the key and the value.
        @param writable: true for writable operation, or false for read-only operation.
        @return: true on success, or false on failure.
        @note: The whole iteration is performed atomically and other threads are blocked.  To avoid deadlock, any explicit database operation must not be performed in this method.
        """
    def set(self, key, value):
        """
        Set the value of a record.
        @param key: the key.
        @param value: the value.
        @return: true on success, or false on failure.
        @note: If no record corresponds to the key, a new record is created.  If the corresponding record exists, the value is overwritten.
        """
    def add(self, key, value):
        """
        Add a record.
        @param key: the key.
        @param value: the value.
        @return: true on success, or false on failure.
        @note: If no record corresponds to the key, a new record is created.  If the corresponding record exists, the record is not modified and false is returned.
        """
    def replace(self, key, value):
        """
        Replace the value of a record.
        @param key: the key.
        @param value: the value.
        @return: true on success, or false on failure.
        @note: If no record corresponds to the key, no new record is created and false is returned.  If the corresponding record exists, the value is modified.
        """
    def append(self, key, value):
        """
        Append the value of a record.
        @param key: the key.
        @param value: the value.
        @return: true on success, or false on failure.
        @note: If no record corresponds to the key, a new record is created.  If the corresponding record exists, the given value is appended at the end of the existing value.
        """
    def increment(self, key, num = 0, orig = 0):
        """
        Add a number to the numeric integer value of a record.
        @param key: the key.
        @param num: the additional number.
        @param orig: the origin number if no record corresponds to the key.  If it is negative infinity and no record corresponds, this method fails.  If it is positive infinity, the value is set as the additional number regardless of the current value.
        @return: the result value, or None on failure.
        @note: The value is serialized as an 8-byte binary integer in big-endian order, not a decimal string.  If existing value is not 8-byte, this method fails.
        """
    def increment_double(self, key, num = 0.0, orig = 0.0):
        """
        Add a number to the numeric double value of a record.
        @param key: the key.
        @param num: the additional number.
        @param orig: the origin number if no record corresponds to the key.  If it is negative infinity and no record corresponds, this method fails.  If it is positive infinity, the value is set as the additional number regardless of the current value.
        @return: the result value, or None on failure.
        @note: The value is serialized as an 16-byte binary fixed-point number in big-endian order, not a decimal string.  If existing value is not 16-byte, this method fails.
        """
    def cas(self, key, oval, nval):
        """
        Perform compare-and-swap.
        @param key: the key.
        @param oval: the old value.  None means that no record corresponds.
        @param nval: the new value.  None means that the record is removed.
        @return: true on success, or false on failure.
        """
    def remove(self, key):
        """
        Remove a record.
        @param key: the key.
        @return: true on success, or false on failure.
        @note: If no record corresponds to the key, false is returned.
        """
    def get(self, key):
        """
        Retrieve the value of a record.
        @param key: the key.
        @return: the value of the corresponding record, or None on failure.
        """
    def get_str(self, key):
        """
        Retrieve the value of a record.
        @note: Equal to the original DB::get method except that the return value is string.
        """
    def check(self, key):
        """
        Check the existence of a record.
        @param key: the key.
        @return: the size of the value, or -1 on failure.
        """
    def seize(self, key):
        """
        Retrieve the value of a record and remove it atomically.
        @param key: the key.
        @return: the value of the corresponding record, or None on failure.
        """
    def seize_str(self, key):
        """
        Retrieve the value of a record and remove it atomically.
        @note: Equal to the original DB::seize method except that the return value is string.
        """
    def set_bulk(self, recs, atomic = True):
        """
        Store records at once.
        @param recs: a map object of the records to store.
        @param atomic: true to perform all operations atomically, or false for non-atomic operations.
        @return: the number of stored records, or -1 on failure.
        """
    def remove_bulk(self, keys, atomic = True):
        """
        Remove records at once.
        @param keys: a sequence object of the keys of the records to remove.
        @param atomic: true to perform all operations atomically, or false for non-atomic operations.
        @return: the number of removed records, or -1 on failure.
        """
    def get_bulk(self, keys, atomic = True):
        """
        Retrieve records at once.
        @param keys: a sequence object of the keys of the records to retrieve.
        @param atomic: true to perform all operations atomically, or false for non-atomic operations.
        @return: a map object of retrieved records, or None on failure.
        """
    def get_bulk_str(self, keys, atomic = True):
        """
        Retrieve records at once.
        @note: Equal to the original DB::get_bulk method except that the return value is string map.
        """
    def clear(self):
        """
        Remove all records.
        @return: true on success, or false on failure.
        """
    def synchronize(self, hard = False, proc = None):
        """
        Synchronize updated contents with the file and the device.
        @param hard: true for physical synchronization with the device, or false for logical synchronization with the file system.
        @param proc: a postprocessor object which implements the FileProcessor interface, or a function object which receives the same parameters.  If it is None, no postprocessing is performed.
        @return: true on success, or false on failure.
        @note: The operation of the processor is performed atomically and other threads accessing the same record are blocked.  To avoid deadlock, any explicit database operation must not be performed in this method.
        """
    def occupy(self, writable = False, proc = None):
        """
        Occupy database by locking and do something meanwhile.
        @param writable: true to use writer lock, or false to use reader lock.
        @param proc: a processor object which implements the FileProcessor interface, or a function object which receives the same parameters.  If it is None, no processing is performed.
        @return: true on success, or false on failure.
        @note: The operation of the processor is performed atomically and other threads accessing the same record are blocked.  To avoid deadlock, any explicit database operation must not be performed in this method.
        """
    def copy(self, dest):
        """
        Create a copy of the database file.
        @param dest: the path of the destination file.
        @return: true on success, or false on failure.
        """
    def begin_transaction(self, hard = False):
        """
        Begin transaction.
        @param hard: true for physical synchronization with the device, or false for logical synchronization with the file system.
        @return: true on success, or false on failure.
        """
    def end_transaction(self, commit = True):
        """
        End transaction.
        @param commit: true to commit the transaction, or false to abort the transaction.
        @return: true on success, or false on failure.
        """
    def transaction(self, proc, hard = False):
        """
        Perform entire transaction by a functor.
        @param proc: the functor of operations during transaction.  If the function returns true, the transaction is committed.  If the function returns false or an exception is thrown, the transaction is aborted.
        @param hard: true for physical synchronization with the device, or false for logical synchronization with the file system.
        @return: true on success, or false on failure.
        """
    def dump_snapshot(self, dest):
        """
        Dump records into a snapshot file.
        @param dest: the name of the destination file.
        @return: true on success, or false on failure.
        """
    def load_snapshot(self, src):
        """
        Load records from a snapshot file.
        @param src: the name of the source file.
        @return: true on success, or false on failure.
        """
    def count(self):
        """
        Get the number of records.
        @return: the number of records, or -1 on failure.
        """
    def size(self):
        """
        Get the size of the database file.
        @return: the size of the database file in bytes, or -1 on failure.
        """
    def path(self):
        """
        Get the path of the database file.
        @return: the path of the database file, or None on failure.
        """
    def status(self):
        """
        Get the miscellaneous status information.
        @return: a dictionary object of the status information, or None on failure.
        """
    def match_prefix(self, prefix, max = -1):
        """
        Get keys matching a prefix string.
        @param prefix: the prefix string.
        @param max: the maximum number to retrieve.  If it is negative, no limit is specified.
        @return: a list object of matching keys, or None on failure.
        """
    def match_regex(self, regex, max = -1):
        """
        Get keys matching a regular expression string.
        @param regex: the regular expression string.
        @param max: the maximum number to retrieve.  If it is negative, no limit is specified.
        @return: a list object of matching keys, or None on failure.
        """
    def match_similar(self, origin, range = 1, utf = False, max = -1):
        """
        Get keys similar to a string in terms of the levenshtein distance.
        @param origin: the origin string.
        @param range: the maximum distance of keys to adopt.
        @param utf: flag to treat keys as UTF-8 strings.
        @param max: the maximum number to retrieve.  If it is negative, no limit is specified.
        @return: a list object of matching keys, or None on failure.
        """
    def merge(self, srcary, mode = MSET):
        """
        Merge records from other databases.
        @param srcary: an array of the source detabase objects.
        @param mode: the merge mode.  DB.MSET to overwrite the existing value, DB.MADD to keep the existing value, DB.MAPPEND to append the new value.
        @return: true on success, or false on failure.
        """
    def cursor(self):
        """
        Create a cursor object.
        @return: the return value is the created cursor object.  Each cursor should be disabled with the Cursor#disable method when it is no longer in use.
        """
    def cursor_process(self, proc) :
        """
        Process a cursor by a functor.
        @param proc: the functor of operations for the cursor.  The cursor is disabled implicitly after the block.
        @return: always None.
        """
    def shift(self):
        """
        Remove the first record.
        @return: a pair of the key and the value of the removed record, or None on failure.
        """
    def shift_str(self):
        """
        Remove the first record.
        @note: Equal to the original DB::shift method except that the return value is string.
        """
    def tune_exception_rule(self, codes):
        """
        Set the rule about throwing exception.
        @param codes: a sequence of error codes.  If each method occurs an error corresponding to one of the specified codes, the error is thrown as an exception.
        @return: true on success, or false on failure.
        """
    def __repr__(self):
        """
        Get the representing expression.
        @return: the representing expression.
        """
    def __str__(self):
        """
        Get the string expression.
        @return: the string expression.
        """
    def __len__(self):
        """
        Alias of the count method.
        """
    def __getitem__(self, key, value):
        """
        Alias of the get method.
        """
    def __setitem__(self, key, value):
        """
        Alias of the set method.
        """
    def __iter__(self):
        """
        Alias of the cursor method.
        """
    def process(proc, path = "*", mode = OWRITER | OCREATE, opts = 0):
        """
        Process a database by a functor. (static method)
        @param proc: the functor to process the database, whose object is passd as the parameter.
        @param path: the same to the one of the open method.
        @param mode: the same to the one of the open method.
        @param opts: the optional features by bitwise-or: DB.GCONCURRENT for the concurrent mode.
        @return: None on success, or an error object on failure.
        """



# END OF FILE

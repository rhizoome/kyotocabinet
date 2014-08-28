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

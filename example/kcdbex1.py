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

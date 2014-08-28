from kyotocabinet import *
import sys
import os
import re
import time

def memoryusage():
    for line in open("/proc/self/status"):
        line = line.rstrip()
        if line.startswith("VmRSS:"):
            line = re.sub(r".*:\s*(\d+).*", r"\1", line)
            return float(line) / 1024
    return -1

musage = memoryusage()
rnum = 1000000
if len(sys.argv) > 1:
    rnum = int(sys.argv[1])

if len(sys.argv) > 2:
    hash = DB()
    if not hash.open(sys.argv[2], DB.OWRITER | DB.OCREATE | DB.OTRUNCATE):
        raise RuntimeError(hash.error())
else:
    hash = {}

stime = time.time()
for i in range(0, rnum):
    key = "{:08d}".format(i)
    value = "{:08d}".format(i)
    hash[key] = value
etime = time.time()

print("Count: {}".format(len(hash)))
print("Time: {:.3f} sec.".format(etime - stime))
print("Usage: {:.3f} MB".format(memoryusage() - musage))

import argparse
import os
import sys
import logging
import errno
from collections import deque
from datetime import datetime
import numpy as np
import Queue
from multiprocessing import Pipe as mpPipe
from multiprocessing import Process

import pathCounter
import asHegemony
import pathMonitor
import graphMonitor


parser = argparse.ArgumentParser()
parser.add_argument("-a","--af", help="address family (4, 6)", type=int, default=4)
parser.add_argument("-N", help="number of hash functions for sketching", type=int, default=16)
parser.add_argument("-M", help="number of sketches per hash function", type=int, default=128)
parser.add_argument("-d","--distThresh", help="simhash distance threshold", type=int, default=3)
parser.add_argument("-r","--minVoteRatio", help="Minimum ratio of sketches to detect anomalies (should be between 0 and 1)", type=float, default=0.5)
parser.add_argument("-H","--historyDuration", help="Time duration of the history for computing the reference (mult 15min)", type=int, default=4)
parser.add_argument("-p", "--proc", help="number of processes", type=int, default=4)
parser.add_argument("-s", "--spatial", help="spatial resolution (0 for prefix, 1 for address)", type=int, default=1)
# parser.add_argument("--filterCountry", help="Filter: country code to monitor", type=str, default=None)
parser.add_argument("-w", "--window", help="Time window: time resolution in seconds (works only with  bgpstream)", type=int, default=900)
parser.add_argument("ribs", help="RIBS files")
parser.add_argument("updates", help="UPDATES files", nargs="+")
# parser.add_argument("output", help="output directory")
args = parser.parse_args()

FORMAT = '%(asctime)s %(processName)s %(message)s'
logging.basicConfig(format=FORMAT, filename='ashash.log', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logging.info("Started: %s" % sys.argv)
logging.info("Arguments: %s" % args)

# ## Parse arguments
# if args.proc is None:
    # args.proc = args.N

# try:
    # os.makedirs(os.path.dirname(args.output))
# except OSError as exc: # Guard against race condition
    # if exc.errno != errno.EEXIST:
        # raise

announceQueue = Queue.Queue(5000)
countQueue = Queue.Queue(10)
hegemonyQueue = Queue.Queue(10)
hegemonyQueuePM = Queue.Queue(10)

nbGM = 5 
pipeGM = []
gm = []

# Analysis Modules
for i in range(nbGM):
    recv, send = mpPipe(False)
    pipeGM.append(send)
    gm.append( Process(target=graphMonitor.graphMonitor, args=(recv, args.N, args.M, args.distThresh, args.minVoteRatio, args.proc), name="GM%s" % i ))
# gm = graphMonitor.graphMonitor(hegemonyQueueGM, args.N, args.M, args.distThresh, args.minVoteRatio, args.proc)
pc = pathCounter.pathCounter(args.ribs, args.updates, announceQueue, countQueue, spatialResolution=args.spatial, af=args.af, timeWindow=args.window)
pm = pathMonitor.pathMonitor(hegemonyQueuePM, announceQueue)
ash = asHegemony.asHegemony(countQueue, hegemonyQueue)

for g in gm:
    g.start()
pm.start()
ash.start()
pc.start()

# Broadcast AS hegemony results to pathMonitor and graphMonitor
while pm.isAlive() or not hegemonyQueue.empty():
    elem = hegemonyQueue.get()
    if elem[1] == "all":
        hegemonyQueuePM.put( elem )
        pipeGM[0].send( elem )
    else:
        pipeGM[int(elem[1])%nbGM].send( elem )

pc.join()
announceQueue.join()
countQueue.join()

logging.info("Good bye!")


# # initialisation for the figures and output
# outFile = open(args.output+"/results_ip.txt","w")
# refAsProb = defaultdict(lambda : deque(maxlen=args.historyDuration*len(root.data)))

# # Update the reference
# for asn, prob in currAsProb.iteritems():
    # refAsProb[asn].extend(prob)

# # read update files
# for updates in args.updates:
            
    # bgpstream = False
    # if updates.startswith("@bgpstream:"):
        # bgpstream = True
        # w = updates.rpartition(":")[2].split(",")
        # ts,te = int(w[0]),int(w[1]) 
        
        # update_files = ["@bgpstream:%s,%s" % (t, t+args.window) for t in range(ts, te, args.window)]

    # else:
        # update_files = glob.glob(updates)
        # update_files.sort()

    # if len(update_files)==0:
        # sys.exit()

    # for fi in update_files:
        # if bgpstream:
            # date = datetime.utcfromtimestamp(int(fi.rpartition(":")[2].partition(",")[0]))
            # date = ".%s%02d%02d.%02d%02d" % (date.year, date.month, date.day, date.hour, date.minute)
            # date = date.split(".")
        # else:
            # filename = fi.rpartition("/")[2]
            # date = filename.split(".")

        # sys.stdout.write("\r %s:%s " % (date[1], date[2]))
        # rtree, updateStats = readupdates(fi, rtree, args.spatial, args.af, filterAS, filterPrefix, args.plot, g)

        # outFile.write("%s:%s | %s | %s | %s | %s | %s | " % (date[1], date[2], updateStats["announce"], \
                # updateStats["withdraw"], np.median(updateStats["prefixLen"]), \
                # np.median(updateStats["pathLen"]), len(updateStats["originAS"]) ) )
        # (currHash, currSketches), currAsProb = computeSimhash(rtree, p, args.N, args.M, args.spatial, outFile, filterAS, filterPrefix)

        # if currHash is None:
            # anomalousAsn = []
            # nbAnoSketch =  np.nan
            # distance = np.nan
        # else:
            # aggProb = aggregateCentrality(refAsProb)
            # refHash, refSketches = sketching(aggProb, p, args.N, args.M)
            # anomalousAsn, nbAnoSketch, distance = compareSimhash(refHash, currHash, refSketches, currSketches, int(args.N*args.minVoteRatio), args.distThresh)


        # sys.stdout.write("%s anomalous sketches (dist=%s), " % (nbAnoSketch, distance))
        # if len(anomalousAsn):
            # sys.stdout.write("%s" % (anomalousAsn))
        # sys.stdout.flush()

        # outFile.write("%s | %s | %s \n" % (nbAnoSketch, distance, anomalousAsn) )
        # outFile.flush()
    
        # if not currHash is None:
            # # Update the reference
            # for asn, prob in currAsProb.iteritems():
                # refAsProb[asn].extend(prob)



#! /usr/bin/env python

import sys, os, time, random, socket

#print 'Argument List:', str(sys.argv)

def usage():
    print("Error! 4 arguments required. Execute %s [number-of-files] [file-size-bytes] [random-file-size-multiplier] [writable-directory]" % sys.argv[0])    

dnalist= list('ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT')

if len(sys.argv) == 5:
    if not os.path.isdir(sys.argv[4]):
        print("folder %s does not exist" % sys.argv[4])
        sys.exit(1)
else:
    usage()
    sys.exit(1)

numfiles=int(sys.argv[1])
bytesize=int(sys.argv[2])
maxmult=int(sys.argv[3])
mydir=sys.argv[4]

kbytesize=float(bytesize)/1024
hostname=socket.gethostname()

print('%s: ... building random DNA sequence of %s KB...' % (hostname,"{0:.3f}".format(kbytesize)))
dnastr = ''
for i in range(bytesize):
    dnastr += random.choice(dnalist)

start = time.time()
wbytes = 0.0
nfiles = 0

print('%s: ... writing %s files with filesizes between %s KB and %s KB ...' % (hostname,numfiles,"{0:.3f}".format(kbytesize),"{0:.3f}".format(kbytesize*maxmult)))

for i in range(numfiles):
    n = random.randint(1,maxmult)
    filename = "scr-%s-file-%s-%s" % (hostname,i,n)
    if not os.path.exists(os.path.join(mydir,hostname)):
        try:
            os.mkdir(os.path.join(mydir,hostname))
        except:
            pass
    #print("open %s ..." % filename)
    fullstr = (str(i)+dnastr+hostname) * n
    fh = open(os.path.join(mydir,hostname,filename), "w")    
    fh.write(fullstr)
    fh.close()
    #print("closed %s ..." % filename)
    wbytes += len(fullstr)
    nfiles += 1

elapsed = time.time() - start

print('%s: %s MB written in %s seconds (%s MB/s, %s files/s)' % (hostname,"{0:.6f}".format(wbytes/1048576),"{0:.3f}".format(elapsed),"{0:.3f}".format(wbytes/1048576/elapsed),int(nfiles/elapsed)))
    

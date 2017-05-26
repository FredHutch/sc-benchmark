#! /usr/bin/env python3

import sys, os, time, random, socket

#print 'Argument List:', str(sys.argv)

def usage():
    print("Error! 4 arguments required. Execute %s [number-of-files] [file-size-bytes] [random-file-size-multiplier] [writable-directory]" % sys.argv[0])    

def generate_random_dna(len):
    bases=list('AGTC')
    dnastr=''
    for i in range(bytesize):
        dnastr+=bases[int(random.random()*4)]
    return dnastr

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

mbytesize=float(bytesize)/1048576
hostname=socket.gethostname()

print('%s: ... building random DNA sequence of %s MB...' % (hostname,"{0:.3f}".format(mbytesize)))

dnastr=generate_random_dna(bytesize)

start = time.time()
wbytes = 0.0
nfiles = 0

print('%s: ... writing %s files with filesizes between %s MB and %s MB ...' % (hostname,numfiles,"{0:.3f}".format(mbytesize),"{0:.3f}".format(mbytesize*maxmult)))

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

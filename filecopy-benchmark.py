#! /usr/bin/env python3

# Script writes random files to temp folder, then copies to remote share,
# measures throughput and saves results to a prometheus node exporter.
# *****  filecopy benchmark dirkpetersen / January 2020 ****
#
# Install Prometheus WMI exporter: 
# > msiexec /i wmi_exporter-0.9.0-amd64.msi ENABLED_COLLECTORS="textfile" TEXTFILE_DIR="C:\metrics\"
# run on Windows (make sure user has permission to C:\metrics)
# > python filecopy-benchmark.py -p "C:\metrics" -d "Y:\scratch\folder"
# go to http://localhost:9182/metrics

import json, sys, os, subprocess, argparse, glob, re, tempfile, shutil, time, socket, random

tests=[[50000,250], [300000,100], [10000000,25], [300000000,3]] # 4 tests with different file sizes 
prom_label = "smb_performance_file_fhcrc_org"

def main():

    currdir = os.getcwd()

    # Parse command-line arguments
    args = parse_arguments()
    hostname=socket.gethostname() + '-' + generate_random_str()
        
    if args.dir == '':
        print ('--dir-to-benchmark argument required.')
        return False

    bdir = os.path.expanduser(args.dir)

    test_results={}

    with tempfile.TemporaryDirectory() as tmpdir:    
        for test in tests:
            outdir = os.path.join(tmpdir,str(test[0]))
            destdir = os.path.join(bdir,hostname,str(test[0])) 
            os.mkdir(outdir)
            #bigstring = generate_random_dna(test[0])
            print('Generate %s byte random string' % test[0])
            bigstring = os.urandom(int(test[0]/3))    
            wsize = write_files(bigstring,test[1],outdir,hostname)
            
            start = time.time()
            if test[0] > 1000000 and os.name == 'nt':
                cmd = '%s "%s" "%s" /s /i' % ('xcopy', outdir, destdir)
                pipe = subprocess.Popen(cmd, shell=True)
                pipe.wait()
            else:
                destination = shutil.copytree(outdir, destdir)
            end = time.time()

            throughput = (wsize/1024/1024) / (end-start)
            test_results = addresult(test_results, 'throughput_mb_s', [test[0], test[1], "{0:.3f}".format(throughput)])
            files_per_sec = test[1] / (end-start)
            test_results = addresult(test_results, 'files_per_sec', [test[0], test[1], "{0:.1f}".format(files_per_sec)])

            print("Throughput (MiB/s):", "{0:.3f}".format(throughput))
            print("FPS:", "{0:.1f}".format(files_per_sec))

            print('Deleting %s files ...' % test[1])
            start = time.time()
            shutil.rmtree(destdir)
            end = time.time()
            delete_files_per_sec = test[1] / (end-start)
            print("Delete FPS:", "{0:.1f}".format(delete_files_per_sec))
            test_results = addresult(test_results, 'delete_files_per_sec', [test[0], test[1], "{0:.1f}".format(delete_files_per_sec)])
    
        os.rmdir(os.path.join(bdir,hostname))

        if args.prometheus_folder:
            with open(os.path.join(args.prometheus_folder, prom_label + '.prom.tmp'), 'w') as fh:

                for key in test_results:
                    fh.write('\n# TYPE ' + prom_label + '_%s gauge\n' % key)
                    for value in test_results[key]:
                        fh.write(prom_label + '_%s{bytes="%s", files="%s"} %s\n' % (key,value[0],value[1],value[2]))

            shutil.move(os.path.join(args.prometheus_folder, prom_label + '.prom.tmp'),
                    os.path.join(args.prometheus_folder, prom_label + '.prom'))


def write_files(strng,numfiles,folder,hostname):
    wbytes=0
    print('Writing %s files..' % numfiles)
    for i in range(numfiles):
        filename = "scr-%s-file-%s.txt" % (hostname,i)
        with open(os.path.join(folder,filename), "w") as fh:                       
           wbytes+=fh.write("%s-%s-" % (str(i),hostname))
           wbytes+=fh.write(str(strng))
    return wbytes

def addresult(mydict,label,value):
    if label in mydict.keys():
        mydict[label].append(value)
    else:
        mydict[label] = [value,]
    return mydict

def folder_size(mypath):
    total_size = 0
    for path, dirs, files in os.walk(mypath):
        for f in files:
            fp = os.path.join(path, f)
            total_size += os.path.getsize(fp)
    return total_size

def generate_random_dna(bytesize):
    bases=list('AGTC')
    dnastr=''
    print('generate random DNA with size %s' % bytesize)
    for i in range(bytesize):
        dnastr+=bases[random.getrandbits(2)]
    return dnastr

def generate_random_str(bytesize=6):
    import string
    chars=string.ascii_uppercase+string.digits
    return ''.join(random.choice(chars) for x in range(bytesize)) 

def parse_arguments():
    """
    Gather command-line arguments.
    """

    parser = argparse.ArgumentParser(prog='filecopy-benchmark',
        description='copy temp files to target folder, measure throughput benchmark' + \
        'and save in prom exporter.')
    parser.add_argument( '--debug', '-g', dest='debug', action='store_true',
        help='show the actual shell commands that are executed (git, chmod, cd)',
        default=False )
    parser.add_argument( '--prometheus-folder', '-p', dest='prometheus_folder',
        action='store', 
        help='directory to copy node exporter files to',
        default='' )
    parser.add_argument( '--dir-to-benchmark', '-d', dest='dir',
        action='store', 
        help='directory on server to copy files to.',
        default='' )
    args = parser.parse_args()
    if args.debug:
        print('***** DEBUG: arguments name space ')
        print(args)
        
    return args

if __name__ == '__main__':
    sys.exit(main())

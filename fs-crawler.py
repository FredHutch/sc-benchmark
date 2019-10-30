#! /usr/bin/env python3

# Script to crawl the file system for changed files 
#
# fs-crawler dirkpetersen / Oct 2019 
#

import sys, os, pwd, argparse, subprocess, re, time, datetime, tempfile, random, threading, filecmp

class KeyboardInterruptError(Exception): pass

def main():

    log = logger('fs-crawler', args.debug)
    log.info('starting to check folder %s for files older than %s days...' % (args.folder, args.days))
    log.debug('Parsed arguments: %s' % args)

    start = time.time()
    interval = 1
    maxinterval = 10

    lastcheck = 0
    lastt = 0
    
    currdir = os.getcwd()
    curruser = pwd.getpwuid(os.getuid()).pw_name
    tmpdir = tempfile.gettempdir()
    days_back_as_secs = time.time() - (args.days * 24 * 3600)
    days_back_datestr = str(datetime.date.today() + datetime.timedelta(args.days * -1)) # e.g. '2014-07-01'

    filedict = {}  # list of files to delete (grouped by key uid)
    infodict = {}  # contains list per uid: numfiles, sizefiles, numwarnfiles, sizewarnfiles
    if args.folder == '/':
        print('root folder not allowed !')
        return False

    numfiles=0
    numfolders=0 

    for root, folders, files in mywalk(args.folder,noparallel=args.noparallel):
        #print(root)
        #for folder in folders:
            #print ('...folder:%s' % folder)
        # check if the user wanted to archive
        numfolders+=1
        numfiles+=len(files)
        check = time.time()
        if lastcheck+interval<check:
            t=numfolders+numfiles
            print ("folders: %s, files: %s, avg objects/s: %s, last objects/s: %s, current path: %s" 
                    % (numfolders, numfiles, "{0:.0f}".format(t/(check-start)), "{0:.0f}".format((t-lastt)/(check-lastcheck)), root))
            lastcheck=check
            lastt=t
            interval+=1
            if maxinterval<=interval:
                interval=maxinterval

        if args.target:
            troot = root.replace(args.folder,args.target)
            if os.path.exists(troot):
                dc = filecmp.dircmp(root, root.replace(args.folder,args.target), ignore=['.snapshot'])
                if dc.left_list:
                    print ('*** Copy -> :', dc.left_list)
                elif dc.right_list:
                    print ('*** Delete -> :', dc.right_list)
            continue

        for f in files:
            p=os.path.join(root,f)
            if args.nostat:
                continue
            stat=getstat(p)
            if not stat:
                continue
            recent_time = stat.st_ctime
            if stat.st_mtime > recent_time:
                recent_time = stat.st_mtime
            if stat.st_uid not in infodict:
                infodict[stat.st_uid] = [0, 0, 0, 0]
            if recent_time >= days_back_as_secs:
                    if stat.st_uid not in filedict:
                        filedict[stat.st_uid] = list()
                    filedict[stat.st_uid].append(p)
                    infodict[stat.st_uid][0]+=1
                    infodict[stat.st_uid][1]+=stat.st_size
        
                    infodict[stat.st_uid][2]+=1
                    infodict[stat.st_uid][3]+=stat.st_size
        
    for k, v in filedict.items():
        user=uid2user(k)
        random.shuffle(v)
        fn=len(v)
        if fn>30:
            fn=30
        print("\n ##### FILES <= %s DAYS OLD ##########################################################" % args.days)
        print("Total of %s files (%s GB total) owned by '%s'" % (infodict[k][0], "{0:.3f}".format(infodict[k][1]/float(1073741824)), user))
        print('List of files that would have been backed up (max 30 randomly selected files):')
        for i in range(fn):
            print(v[i])

    end = time.time()
    print("\nTotal Time: %s sec (%s min)" % ("{0:.1f}".format(end-start),"{0:.1f}".format((end-start)/60)))  

def startswithpath(pathlist, pathstr):
    """ checks if at least one of the paths in a list of paths starts with a string """
    for path in pathlist:
        if (os.path.join(pathstr, '')).startswith(path):
            return True
    return False

def getstartpath(pathlist, pathstr):
    """ return the path from pathlist  that is the frist part of pathstr"""
    for path in pathlist:
        if (os.path.join(pathstr, '')).startswith(path):
            return path
    return ''

                
def getstat(path):
    """ returns the stat information of a file"""
    statinfo=None
    try:
        statinfo=os.lstat(path)
    except (IOError, OSError) as e:   # FileNotFoundError only since python 3.3
        if args.debug:
            sys.stderr.write(str(e))            
    except:
        raise
    return statinfo

def setfiletime(path,attr="atime"):
    """ sets the a time of a file to the current time """
    try:
        statinfo=getstat(path)
        if attr=="atime" or attr=="all":
            os.utime(path,(time.time(),statinfo.st_atime))
        if attr=="mtime" or attr=="all":
            os.utime(path,(time.time(),statinfo.st_mtime))        
        return True
    except Exception as err:
        sys.stderr.write(str(err))
        sys.stderr.write('\n')
        return False

def uid2user(uidNumber):
    """ attempts to convert uidNumber to username """
    import pwd
    try:
        return pwd.getpwuid(int(uidNumber)).pw_name
    except Exception as err:
        sys.stderr.write(str(err))
        sys.stderr.write('\n')
        return str(uidNumber)

def list2file(mylist,path):
    """ dumps a list into a text file, one line per item"""
    try:
        with open(path,'w') as f:
            for item in mylist:
                f.write("{}\r\n".format(item))
        return True
    except Exception as err:
        sys.stderr.write(str(err))
        sys.stderr.write('\n')
        return False

def pathlist2file(mylist,path,root):
    """ dumps a list into a text file, one line per item, but removes
         a root folder from all paths. Used for --files-from feature in rsync"""
    try:
        with open(path,'w') as f:
            for item in mylist:
                f.write("{}\r\n".format(item[len(root):]))
        return True
    except Exception as err:
        sys.stderr.write(str(err))
        sys.stderr.write('\n')
        return False

def mywalk(top, noparallel=False, skipdirs=['.snapshot',]):
    """ returns subset of os.walk  """
    
    if noparallel:
        for root, dirs, files in os.walk(top,topdown=True,onerror=walkerr):
            for skipdir in skipdirs:
                if skipdir in dirs:
                    dirs.remove(skipdir)  # don't visit this directory 
            yield root, dirs, files

    else:
        for root, dirs, files in walk(top):
            for skipdir in skipdirs:
                if skipdir in dirs:
                    dirs.remove(skipdir)  # don't visit this directory 
            yield root, dirs, files 

def walkerr(oserr):    
    sys.stderr.write(str(oserr))
    sys.stderr.write('\n')
    return 0

def walk(top, threads=36):
  """Multi-threaded version of os.walk().
  from here:  https://gist.github.com/jart/0a71cde3ca7261f77080a3625a21672b
  This routine provides multiple orders of a magnitude performance improvement
  when top is mapped to a network filesystem where i/o operations are slow, but
  unlimited. For spinning disks it should still run faster regardless of thread
  count because it uses a LIFO scheduler that guarantees locality. For SSDs it
  will go tolerably slower.
  The more exotic coroutine features of os.walk() can not be supported, such as
  the ability to selectively inhibit recursion by mutating subdirs.
  Args:
    top: Path of parent directory to search recursively.
    threads: Size of fixed thread pool.
  Yields:
    A (path, subdirs, files) tuple for each directory within top, including
    itself. These tuples come in no particular order; however, the contents of
    each tuple itself is sorted.
  """
  if not os.path.isdir(top):
    return
  lock = threading.Lock()
  on_input = threading.Condition(lock)
  on_output = threading.Condition(lock)
  state = {'tasks': 1}
  paths = [top]
  output = []

  def worker():
    while True:
      with lock:
        while True:
          if not state['tasks']:
            output.append(None)
            on_output.notify()
            return
          if not paths:
            on_input.wait()
            continue
          path = paths.pop()
          break
      try:
        dirs = []
        files = []
        for item in os.listdir(path):  #for item in sorted(os.listdir(path))
          subpath = os.path.join(path, item)
          if os.path.isdir(subpath):
            dirs.append(item)
            with lock:
              state['tasks'] += 1
              paths.append(subpath)
              on_input.notify()
          else:
            files.append(item)
        with lock:
          output.append((path, dirs, files))
          on_output.notify()
      except OSError as e:
        print(e, file=sys.stderr)
      finally:
        with lock:
          state['tasks'] -= 1
          if not state['tasks']:
            on_input.notifyAll()

  workers = [threading.Thread(target=worker,
                              name="fastio.walk %d %s" % (i, top))
             for i in range(threads)]
  for w in workers:
    w.start()
  while threads or output:  # TODO(jart): Why is 'or output' necessary?
    with lock:
      while not output:
        on_output.wait()
      item = output.pop()
    if item:
      yield item
    else:
      threads -= 1



def send_mail(to, subject, text, attachments=[], cc=[], bcc=[], smtphost="", fromaddr=""):

    if sys.version_info[0] == 2:
        from email.MIMEMultipart import MIMEMultipart
        from email.MIMEBase import MIMEBase
        from email.MIMEText import MIMEText
        from email.Utils import COMMASPACE, formatdate
        from email import Encoders
    else:
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        from email.utils import COMMASPACE, formatdate
        from email import encoders as Encoders
    from string import Template
    import socket
    import smtplib

    if not isinstance(to,list):
        print("the 'to' parameter needs to be a list")
        return False    
    if len(to)==0:
        print("no 'to' email addresses")
        return False
    
    myhost=socket.getfqdn()

    if smtphost == '':
        smtphost = get_mx_from_email_or_fqdn(myhost)
    if not smtphost:
        sys.stderr.write('could not determine smtp mail host !\n')
        
    if fromaddr == '':
        fromaddr = os.path.basename(__file__) + '-no-reply@' + \
           '.'.join(myhost.split(".")[-2:]) #extract domain from host
    tc=0
    for t in to:
        if '@' not in t:
            # if no email domain given use domain from local host
            to[tc]=t + '@' + '.'.join(myhost.split(".")[-2:])
        tc+=1

    message = MIMEMultipart()
    message['From'] = fromaddr
    message['To'] = COMMASPACE.join(to)
    message['Date'] = formatdate(localtime=True)
    message['Subject'] = subject
    message['Cc'] = COMMASPACE.join(cc)
    message['Bcc'] = COMMASPACE.join(bcc)

    body = Template('This is a notification message from $application, running on \n' + \
            'host $host. Please review the following message:\n\n' + \
            '$notify_text\n\nIf output is being captured, you may find additional\n' + \
            'information in your logs.\n'
            )
    host_name = socket.gethostname()
    full_body = body.substitute(host=host_name.upper(), notify_text=text, application=os.path.basename(__file__))

    message.attach(MIMEText(full_body))

    for f in attachments:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(f, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        message.attach(part)

    addresses = []
    for x in to:
        addresses.append(x)
    for x in cc:
        addresses.append(x)
    for x in bcc:
        addresses.append(x)

    smtp = smtplib.SMTP(smtphost)
    smtp.sendmail(fromaddr, addresses, message.as_string())
    smtp.close()

    return True

def get_mx_from_email_or_fqdn(addr):
    """retrieve the first mail exchanger dns name from an email address."""
    # Match the mail exchanger line in nslookup output.
    MX = re.compile(r'^.*\s+mail exchanger = (?P<priority>\d+) (?P<host>\S+)\s*$')
    # Find mail exchanger of this email address or the current host
    if '@' in addr:
        domain = addr.rsplit('@', 2)[1]
    else:
        domain = '.'.join(addr.rsplit('.')[-2:])
    p = os.popen('/usr/bin/nslookup -q=mx %s' % domain, 'r')
    mxes = list()
    for line in p:
        m = MX.match(line)
        if m is not None:
            mxes.append(m.group('host')[:-1])  #[:-1] just strips the ending dot
    if len(mxes) == 0:
        return ''
    else:
        return mxes[0]
        
def logger(name=None, stderr=False):
    import logging, logging.handlers
    # levels: CRITICAL:50,ERROR:40,WARNING:30,INFO:20,DEBUG:10,NOTSET:0
    if not name:
        name=__file__.split('/')[-1:][0]
    l=logging.getLogger(name)
    l.setLevel(logging.INFO)
    f=logging.Formatter('%(name)s: %(levelname)s:%(module)s.%(lineno)d: %(message)s')
    # logging to syslog
    s=logging.handlers.SysLogHandler('/dev/log')
    s.formatter = f
    l.addHandler(s)
    if stderr:
        l.setLevel(logging.DEBUG)
        # logging to stderr        
        c=logging.StreamHandler()
        c.formatter = f
        l.addHandler(c)
    return l

def parse_arguments():
    """
    Gather command-line arguments.
    """

    parser = argparse.ArgumentParser(prog='fs-crawler',
        description=' walk the file system tree ' + \
        ' ' + \
        ' ')
    parser.add_argument( '--debug', '-g', dest='debug', action='store_true',
        help='show the actual shell commands that are executed (git, chmod, cd)',
        default=False )
    parser.add_argument( '--no-parallel', '-p', dest='noparallel', action='store_true',
        help='just count files, no stat calls',
        default=False )
    parser.add_argument( '--no-stat', '-n', dest='nostat', action='store_true',
        help='just count files, no stat calls',
        default=False )
    parser.add_argument( '--suppress-emails', '-s', dest='suppress_emails', action='store_true',
        help='do not send any emails to end users',
        default=False )
    parser.add_argument( '--email-notify', '-e', dest='email',
        action='store',
        help='notify this email address of any error ',
        default='' )        
    parser.add_argument( '--days', '-d', dest='days',
        action='store',
        type=int,
        help='remove files older than x days (default: 1461 days or 4 years) ',
        default=1461 )
    parser.add_argument( '--folder', '-f', dest='folder',
        action='store', 
        help='search this folder and below for files to remove')
    parser.add_argument( '--target', '-t', dest='target',
        action='store',
        help='targeet directory tree to sync to')
    args = parser.parse_args()
    if not args.folder:
        parser.error('required option --folder not given !')
    if args.debug:
        print('DEBUG: Arguments/Options: %s' % args)    
    return args

if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_arguments()
    sys.exit(main())

 

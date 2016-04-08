import os
import re
import sys
import time
import sched
import datetime
import urllib2
import string
import logging

logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                filename='Autobackup_' + time.strftime('%Y_%m_%d_%H_%M_%S',time.localtime(time.time())) + '.log',
                filemode='w')
sep = os.path.sep
print "url example: http://mirrors.163.com/ubuntu/project/"
home = str(raw_input("Input the server url whitch you need to backup: \n"))
cicle = int(raw_input("Input the cicle day that you need to backup: \n"))
backupfolder = str(raw_input("Input the local backup folder name: \n"))
backuppath = os.getcwd() + sep + backupfolder + sep
s = sched.scheduler(time.time,time.sleep)

class Auto_backup(object):

    def __init__(self):
        #super(Result, self).__init__()
        print "[INFO]Current Time:",time.strftime('%Y-%m-%d,%H:%M',time.localtime(time.time()))
        self.backupfolder = os.getcwd() + sep + backupfolder
        if os.path.isdir(backupfolder):
            print "[DEBUG]backup folder has already exists."
        else:
            print "[INFO]make backup folder %s." % (backupfolder)
            os.mkdir(self.backupfolder)

    def daily_init(self):
        print "[INFO]Current Time:",time.strftime('%Y-%m-%d,%H:%M',time.localtime(time.time()))
        self.logfolder = "logs_" + time.strftime('%Y_%m_%d_%H_%M_%S',time.localtime(time.time()))
        print self.logfolder
        os.mkdir(self.logfolder)

    def remote_dir(self, url, dir):
        sub_url = url + dir
        print sub_url
        return sub_url

    def local_tree(self, localhome, dir):
        sub_localpath = localhome + dir
        print sub_localpath
        if os.path.isdir(sub_localpath):
            print "[DEBUG]%s folder has already exists." % (sub_localpath)
        else:
            print "[INFO]make local tree folder %s." % (sub_localpath)
            os.mkdir(sub_localpath)
        return sub_localpath

    def craw_dir(self, url=home, localpath=backuppath, tmplog="tmp.log"):
        tmplogs=self.logfolder + sep + tmplog
        f = open(tmplogs,'w+')
        m = urllib2.urlopen(url).read()
        f.write(m)
        f.close()
        with open(tmplogs) as buffer:
            for line in buffer.readlines():
                dir_flag = re.compile(r'<a href="(.*)">(.*)</a>(.*) -')
                file_flag = re.compile(r'<a href="(.*)">(.*)</a>(.*)')
                dirmatch = dir_flag.search(line)
                filematch = file_flag.search(line)
                if dirmatch:
                    if dirmatch.groups()[1].find('.')>=0:
                        print "[INFO]Found new file %s, but it could not download now." % (dirmatch.groups()[1])
                        logging.debug("Found new file %s, but it could not download now." % (dirmatch.groups()[1]))
                        pass
                    else:
                        dir_name=dirmatch.groups()[1]
                        dir_date=dirmatch.groups()[2].split()[0]
                        dir_time=dirmatch.groups()[2].split()[1]
                        print "[INFO]Found directory:",dir_name
                        print dir_date, dir_time
                        sub_url=self.remote_dir(url, dir_name)
                        sub_localpath=self.local_tree(localpath, dir_name)
                        self.craw_dir(sub_url, sub_localpath, tmplog=dir_name[:-1])
                elif filematch:
                    if filematch.groups()[1] == "../":
                        pass
                    else:
                        file_name=filematch.groups()[1]
                        file_date=filematch.groups()[2].split()[0]
                        file_time=filematch.groups()[2].split()[1]
                        print '[INFO]Found file:',file_name
                        print file_date, file_time
                        file_time = file_date + ' ' + file_time
                        sub_url=self.remote_dir(url, file_name)
                        file_path=localpath + file_name
                        if self.check_localfile(file_path):
                            self.check_date(sub_url, file_path, file_time)
                        else:
                            self.download_file(sub_url, file_path)
                else:
                    pass

    def check_localfile(self, filepath):
        if os.path.exists(filepath):
            if os.path.isdir(filepath):
                print "[DEBUG]new files comming! Remove the current file directory %s." % (filepath)
                os.rmdir(filepath)
                logging.debug("Remove the temporary file directory %s, start to download." % (filepath))
                return False
            else:
                print "[INFO]%s is exists in local path." % (filepath)
                return True
        else:
            print "[INFO]%s is not exists in local path, start to download." % (filepath)
            return False

    def check_date(self, sub_url, file_path, file_time):
        file_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.mktime(time.strptime(file_time, '%d-%b-%Y %H:%M'))))
        print "[INFO]remote file modify time is:%s" % (file_time)
        cacul_time = (datetime.datetime.now() - datetime.timedelta(days = cicle))
        reference_time = cacul_time.strftime('%Y-%m-%d %H:%M:%S')
        print "[INFO]yesterday reference time is:%s" % (reference_time)
        if self.compare_time(reference_time, file_time):
            print "[INFO]%s did not update in server." % (file_path)
        else:
            print "[INFO]%s is updated in server,so download it." % (file_path)
            self.download_file(sub_url, file_path)

    def download_file(self, sub_url, file_path):
        print "****************************************************************************"
        print "[INFO]Start download %s" % (sub_url)
        try:
            content=urllib2.urlopen(sub_url).read()
            with open(file_path,'wb') as code:
                code.write(content)
            info = "Update: %s" % (file_path)
            logging.info(info)
        except urllib2.HTTPError, e:
            print e.code
            logging.warning(file_path + ' download failed due to Error code:' + str(e.code))
        except urllib2.URLError, e:
            print e.reason
            logging.warning(file_path + ' download failed due to reason:' + e.reason)
        print "****************************************************************************"

    def compare_time(self, reference_t,file_t):
        r_time = time.mktime(time.strptime(reference_t,'%Y-%m-%d %H:%M:%S'))
        f_time = time.mktime(time.strptime(file_t,'%Y-%m-%d %H:%M:%S'))
        if (float(r_time) > float(f_time)):
            return True
        else:
            return False

    def clean_tmplog(self):
        print "[INFO]Clean the temporary log folder."
        __import__('shutil').rmtree(self.logfolder)

backup = Auto_backup()

def perform(inc):
    s.enter(inc,0,perform,(inc,))
    backup.daily_init()
    backup.craw_dir(home, backuppath, "tmp.log")
    backup.clean_tmplog()
    print "[INFO]Current Time:",time.strftime('%Y-%m-%d,%H:%M',time.localtime(time.time()))
    finishinfo="Flags: Current Time is " + time.strftime('%Y-%m-%d,%H:%M',time.localtime(time.time())) + ", Auto backup finished this time."
    logging.info(finishinfo)
    print "****************************************************************************"
    print "Update local backup dir finished.waiting for next circle to backup."
    print "****************************************************************************"

def mymain(inc=86400*cicle):
    s.enter(0,0,perform,(inc,))
    s.run()

if __name__ == "__main__":
    mymain()

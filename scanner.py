# coding = utf-8
# author = PSoul
# version = 2.0
# filename = PScanner.py

import Queue
import threading
import socket
import argparse
import urllib2
import sys

port_list = (80, 8080, 8081, 443, 8090, 9080, 8000, 8001, 8002, 7001, 7002, 7000, 7080, 8443, 9090, 81, 8888)
path_list = ('/robots.txt',
             '/admin',
             '/manager',
             '/editor',
             '/images',
             '/ewebeditor',
             '/fckeditor',
             '/console',
             '/phpinfo.php',
             '/phpmyadmin/',
             '/xampp/',
             '/zabbix/',
             '/jmx-console/',
             '/.svn/entries',
             '/nagios/',
             '/index.action',
             '/login.action',
             '/index.do',
             '/database/',
             '/databases/',
             '/1.asp',
             '/shell.asp',
             '/index.shtml',
             '/www/',
             '/www.zip',
             '/www.rar',
             '/webroot.rar',
             '/webroot.zip',
             '/bak.rar',
             '/bak.zip',
             '/fckeditor/editor/filemanager/connectors/')
port_queue = Queue.Queue()
socket.setdefaulttimeout(3)
header = {"User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWeb'
                        'Kit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25'}


def ip2bin(ip):
    b = ""
    inQuads = ip.split(".")
    outQuads = 4
    for q in inQuads:
        if q != "":
            b += dec2bin(int(q), 8)
            outQuads -= 1
    while outQuads > 0:
        b += "00000000"
        outQuads -= 1
    return b


def dec2bin(n, d=None):
    s = ""
    while n > 0:
        if n & 1:
            s = "1"+s
        else:
            s = "0"+s
        n >>= 1
    if d is not None:
        while len(s) < d:
            s = "0"+s
    if s == "": s = "0"
    return s


def bin2ip(b):
    ip = ""
    for i in range(0, len(b), 8):
        ip += str(int(b[i:i+8], 2))+"."
    return ip[:-1]


def listCIDR(c):
    cidrlist=[]
    parts = c.split("/")
    baseIP = ip2bin(parts[0])
    subnet = int(parts[1])
    if subnet == 32:
        print bin2ip(baseIP)
    else:
        ipPrefix = baseIP[:-(32-subnet)]
        for i in range(2**(32-subnet)):
            cidrlist.append(bin2ip(ipPrefix+dec2bin(i, (32-subnet))))
        return cidrlist[1:-1]


def port_run(target, timeout, filename):
    with open(filename, 'a') as f:
        for port in port_list:
            if port == 443 or port == 8443:
                url = 'https://' + target
            else:
                url = 'http://' + target + ':' + str(port)
            sys.stdout.write(url + '\r')
            sys.stdout.flush()
            try:
                request = urllib2.Request(url)
                request.add_header("User-Agent", 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWeb'
                                                 'Kit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25')
                request.get_method = lambda: 'HEAD'
                urlopen = urllib2.urlopen(request, timeout=timeout)
                sys.stderr.write(url + ' server:' + urlopen.headers['server'] + '\n')
                f.write(url + ' server: ' + urlopen.headers['server'] + '\n')
                f.flush()
                for path in path_list:
                    uri = url + path
                    sys.stderr.write(uri + ' beginning \r')
                    sys.stdout.flush()
                    try:
                        # path_respond = urllib2.urlopen(uri, timeout=timeout)
                        path_req = urllib2.Request(uri)
                        path_req.get_method = lambda: 'HEAD'
                        path_res = urllib2.urlopen(path_req)
                        print uri + ' success'
                        f.write(uri + ' ' + str(path_res.code) + '\n')
                        f.flush()
                    except urllib2.HTTPError, er:
                        if er.code == 403:
                            print uri + ' ' + str(er.code)
                            f.write(uri + ' ' + str(er.code) + '\n')
                            f.flush()
                        continue
                    except Exception, e:
                        print uri + ' ' + str(e)
                        continue
            except urllib2.HTTPError, e:
                f.write(url + ' ' + str(e) + '\n')
                f.flush()
                print url, e
            except:
                pass


def port_worker():
    while True:
        ip, timeout, filename = port_queue.get()
        port_run(ip, timeout, filename)
        port_queue.task_done()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', dest='ip', help='ip target')
    parser.add_argument('-c', '--threads', dest='threadsnum', help='threads num', type=int, default=125)
    parser.add_argument('-t', '--timeout', dest='timeout', type=int, default=4)
    parser.add_argument('-o', dest='filename', default='result.txt')
    args = parser.parse_args()
    threads = []
    if args.ip:
        ips = listCIDR(args.ip)
        for item in range(args.threadsnum):
            t = threading.Thread(target=port_worker)
            t.setDaemon(True)
            t.start()
            threads.append(t)
        for ip in ips:
            port_queue.put((str(ip), args.timeout, args.filename))
        port_queue.join()
        print 'exit'
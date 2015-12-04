#!/usr/bin/env python

import sys
import os.path
from os import getenv
from hashlib import sha1
import hmac
from datetime import datetime, tzinfo, timedelta
import urllib
import urllib2
import json

# Helper class for ISO8601 date string
class simple_utc(tzinfo):
    def tzname(self):
        return 'UTC'
    def utcoffset(self, dt):
        return timedelta(0)

# Main Instant Cloud API class
class InstantCloudClient:
    BASE_URL = 'https://cloud.gurobi.com/api/'
    METHOD = { 'licenses': 'GET', 'machines': 'GET', 'launch': 'POST', 'kill': 'POST' }
    def __init__(self, accessid, secretkey, verbose=False):
        self.accessid  = accessid
        self.secretkey = secretkey
        self.verbose   = verbose

    def sign_request(self, raw_str):
        hashed = hmac.new(self.secretkey, raw_str, sha1)
        return hashed.digest().encode('base64').rstrip('\n')

    def sendcommand(self, command, params):
        method = self.METHOD[command]
        url = self.BASE_URL + command
        if method == 'GET':
            url = url + '?id=' + self.accessid

        request_str = method
        query       = None

        # Add id to input params dict
        params['id'] = self.accessid
        # Iterate over params to construct request and query strings
        for param, val in params.iteritems():
            keyval      = param + '=' + urllib.quote(str(val))
            request_str = request_str + '&' + keyval
            if method == "POST":
                if query is None:
                    query = keyval
                else:
                    query = query + '&' + keyval

        # Add date
        now = datetime.utcnow().replace(tzinfo=simple_utc()).isoformat()
        request_str = request_str + '&' + now

        # Sign request string
        signature = self.sign_request(request_str)
        if self.verbose:
            print 'Request String:', request_str
            print 'Secret Key:', self.secretkey
            print 'Signature:', signature
            print 'Query:', query
            print 'URL:', url

        # Construct headers
        headers = {'X-Gurobi-Signature' : signature,
                   'X-Gurobi-Date' : now }

        req = urllib2.Request(url, query, headers)
        try:
            response = urllib2.urlopen(req)
            the_page = response.read()
        except urllib2.HTTPError, error:
            print "ERROR:", error.code
            print error.read()
            exit(1)

        assert(response.info().getheader('Content-Type') == 'application/json')
        return json.loads(the_page)

    def getlicenses(self):
        return self.sendcommand('licenses', {})

    def getmachines(self):
        return self.sendcommand('machines', {})

    def launchmachines(self, numMachines=None, licenseType=None, \
                       licenseId=None, userPassword=None, region=None, \
                       idleShutdown=None, machineType=None, GRBVersion=None):
        inputargs = locals().copy()  #get dict of input arguments
        params = {}
        # remove self argument and any arguments that are None
        for k, v in inputargs.iteritems():
            if v is not None and k != "self":
                params[k] = v
        machines = self.sendcommand('launch', params)
        return machines

    def killmachines(self, machineids):
        machinestr = [('"%s"' % machine) for machine in machineids]
        machineJSON = '[' + ','.join(machinestr) + ']'
        machines = self.sendcommand('kill', {'machineIds': machineJSON })
        return machines


def getid(cmd_arg):
    if cmd_arg:
        return cmd_arg
    elif getenv('IC_ACCESS_ID') is not None:
        return getenv('IC_ACCESS_ID')
    else:
        print "Could not find access id. Set the access id with --id"
        print "Or by setting the environmental variable IC_ACCESS_ID"
        exit(1)

def getkey(cmd_arg):
    if cmd_arg:
        return cmd_arg
    elif getenv('IC_SECRET_KEY') is not None:
        return getenv('IC_SECRET_KEY')
    else:
        print "Could not find secret key. Set the secret key with --key"
        print "Or by setting the environmental variable IC_SECRET_KEY"
        exit(1)

def printmachines(machines):
    for machine in machines:
        print 'Machine name: ', machine['DNSName']
        print '\tlicense type: ', machine['licenseType']
        print '\tstate: ', machine['state']
        print '\tmachine type: ', machine['machineType']
        print '\tregion: ', machine['region']
        print '\tidle shutdown: ', machine['idleShutdown']
        print '\tuser password: ', machine['userPassword']
        print '\tcreate time: ', machine['createTime']
        print '\tlicense id: ', machine['licenseId']
        print '\tmachine id: ', machine['_id']

def printlicenses(licenses):
    if len(licenses) > 1:
        print 'License Credit  Rate Plan       Expiration'
    for license in licenses:
        print license['licenseId'], '\t', license['credit'], '\t', \
            license['ratePlan'], '\t', license['expiration']

def usage():
    print "instantcloud command [options]"
    print
    print "Here command is one of the following:"
    print "\tlaunch\tLaunch a set of Gurobi machines"
    print "\tkill\tKill a set of Gurobi machines"
    print "\tlicenses\tShow the licenses associated with your account"
    print "\tmachines\tShow currently running machines"
    print
    print "General options:"
    print " --help (-h): this message"
    print " --id   (-I): set your access id"
    print " --key  (-K): set your secret key"

if __name__ == "__main__":
    accessid  = None
    secretkey = None
    command   = None
    commands = ['licenses', 'machines', 'launch', 'kill']
    last_arg = -1
    skip     = -1

    for i, arg in enumerate(sys.argv):
        if i == 0 or i <= skip:
            continue
        if arg == "-h" or arg == "--help":
            usage()
            exit(0)
        elif arg == "-I" or arg == "--id":
            accessid = sys.argv[i+1]
            skip = i+1
        elif arg == "-K" or arg == "--key":
            secretkey = sys.argv[i+1]
            skip = i+1
        elif arg in commands:
            command = arg
        else:
            lastarg = i
            break

    if command is None:
        print "Missing command"
        usage()
        exit(1)

    accessid  = getid(accessid)
    secretkey = getkey(secretkey)

    ic = InstantCloudClient(accessid, secretkey)

    if command == "licenses":
        licenses = ic.getlicenses()
        printlicenses(licenses)
    elif command == "machines":
        machines = ic.getmachines()
        printmachines(machines)
    elif command == "kill":
        if lastarg < 1:
            print "instantcloud kill requires machine ids to kill"
        machines = ic.killmachines(sys.argv[lastarg:])
        print 'Machines Killed'
        printmachines(machines)
    elif command == "launch":
        launchargs = {}
        skip = -1
        for i in xrange(lastarg, len(sys.argv)):
            if i <= skip:
                continue
            arg = sys.argv[i]
            if arg == "-n" or arg == "--nummachines":
                launchargs["numMachines"] = sys.argv[i+1]
                skip = i+1
            elif arg == "-l" or arg == "--licensetype":
                launchargs["licenseType"] = sys.argv[i+1]
                skip = i+1
            elif arg == "-p" or arg == "--password":
                launchargs["userPassword"] = sys.argv[i+1]
                skip = i+1
            elif arg == "-s" or arg == "--idleshutdown":
                launchargs["idleShutdown"] = sys.argv[i+1]
                skip = i+1
            elif arg == "-i" or arg == "--licenseid":
                launchargs["licenseId"] = sys.argv[i+1]
                skip = i+1
            elif arg == "-r" or arg == "--region":
                launchargs["region"] = sys.argv[i+1]
                skip = i+1
            elif arg == "-m" or arg == "--machinetype":
                launchargs["machineType"] = sys.argv[i+1]
                skip = i+1
            elif arg == "-g" or arg == "--gurobiversion":
                launchargs["GRBVersion"] = sys.argv[i+1]
                skip = i+1

        machines = ic.launchmachines(**launchargs)
        print 'Machines Launched'
        printmachines(machines)

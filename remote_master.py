# <*******************
# 
# Copyright 2018 Juniper Networks, Inc. All rights reserved.
# Licensed under the Juniper Networks Script Software License (the "License").
# You may not use this script file except in compliance with the License, which is located at
# http://www.juniper.net/support/legal/scriptlicense/
# Unless required by applicable law or otherwise agreed to in writing by the parties, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# 
# *******************>
import abc, sys, os, subprocess, random, json, time
from yaml import load

#Read Environment config
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = 'master_environment.yaml'

f=open(os.path.join(THIS_DIR,DATA_FILE))
data=f.read()
_INPUT_DATA=load(data)
f.close()

def logger(strLog):
    with open(_INPUT_DATA['MACSEC']['LOG_PATH'], 'a') as target_config:
        target_config.write(strLog+'\n')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), _INPUT_DATA['MACSEC']['INCLUDE_PATH']))
logger('Loading required library from ' + _INPUT_DATA['MACSEC']['INCLUDE_PATH'])

from flask import Flask, request, jsonify, render_template
from config import DevConfig
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from pydblite import Base
from collections import namedtuple

_MLS_DB_FILE_NAME = os.path.join(os.path.dirname(__file__), _INPUT_DATA['MACSEC']['LOCAL_DB_FILE_PATH'])
tuple_MLS_record = namedtuple("tuple_MLS_record", ['leaf_ID','leaf_port','leaf_hostname','spine_ID','spine_port','spine_hostname', 'CKN', 'CAK'])

def KeyGenerator():
    ran_ckn = random.randrange(10**80)
    ran_cak = random.randrange(10**80)
    str_ckn = "%064x" % ran_ckn
    str_cak = "%032x" % ran_cak

    #limit string to 64 characters
    ckn = str_ckn[:64]
    cak = str_cak[:32]

    return ckn, cak

class Interface_DBController():
    __metaclass__ = abc.ABCMeta

    """
    Declare an interface for a type of product object.
    """

    @abc.abstractmethod
    def open(self):
        pass
    
    @abc.abstractmethod
    def insert(self):
        pass
    
    @abc.abstractmethod
    def select(self):
        pass
    
    @abc.abstractmethod
    def commit(self):
        pass

class SimpleDBFactory():
    def __init__(self):
        pass

    def CreatePydblite(self):
        return MLSManager_pydblite(); 
    
    def CreateMySQL(self, DB_IP):
        #return MLSManager_mysql();
        pass 
'''
class MLSManager_mysql(Interface_DBController):
    def __init__(self, DB_IP = _DB_IP):
        pass
    def open(self):
        pass
    def insert(self):
        pass
    def select(self):
        pass
    def commit(self):
        pass
'''

class MLSManager_pydblite(Interface_DBController):
    def __init__(self, DBfilepath='./'):
        self.DBfilepath = DBfilepath #allow customize db file path.
        self.db = Base(_MLS_DB_FILE_NAME)

    def open(self):
        if self.db.exists():
            self.db.open();    
        else:
            self.db.create('leaf_ID','leaf_port','leaf_hostname','spine_ID','spine_port','spine_hostname', 'CKN', 'CAK', 'time');
            self.db.open();

    def insert(self, MLS):
        self.db.insert(MLS.leaf_ID , MLS.leaf_port , MLS.leaf_hostname , MLS.spine_ID, MLS.spine_port, MLS.spine_hostname, MLS.CKN, MLS.CAK, time.time());
    
    def select(self, leaf_ID, leaf_port, spine_ID, spine_port):
        #flag_item_found = False

        ret_CKN = None
        ret_CAK = None

        #Following IF/ELSE hadling partially match, which happens when one switch got MACsec configured, but the other hasn't (LLDP cannot reach each other.).
        if (leaf_ID is None) or (leaf_port is None):
            for rec in (self.db("spine_ID") == spine_ID) & (self.db("spine_port") == spine_port):
                ret_CKN = rec["CKN"]
                ret_CAK = rec["CAK"]
        #        flag_item_found = True;

        elif (spine_ID is None) or (spine_port is None):
            for rec in (self.db("leaf_ID") == leaf_ID) & (self.db("leaf_port") == leaf_port):
                ret_CKN = rec["CKN"]
                ret_CAK = rec["CAK"]
        #        flag_item_found = True;

        else:
            for rec in (self.db("leaf_ID") == leaf_ID) & (self.db("leaf_port") == leaf_port) & (self.db("spine_ID") == spine_ID) & (self.db("spine_port") == spine_port):
                ret_CKN = rec["CKN"]
                ret_CAK = rec["CAK"]
        #        flag_item_found = True;

#        if flag_item_found == False:
#            ret_CKN, ret_CAK = '-1','-1'

        return ret_CKN, ret_CAK

    def delete(self, leaf_ID, leaf_port):
        b_ret_flag = False

        print leaf_ID, leaf_port

        lstTargetRecords = []

        for rec in (self.db("leaf_ID") == leaf_ID) & (self.db("leaf_port") == leaf_port):
            lstTargetRecords.append(rec)

        for rec in (self.db("spine_ID") == leaf_ID) & (self.db("spine_port") == leaf_port):
            lstTargetRecords.append(rec)

        print 'lstTargetRecords:'
        print lstTargetRecords

        try:
            self.db.delete(lstTargetRecords)
            b_ret_flag = True
        except Exception as e:
            print str(e)

        return b_ret_flag

    def selectall(self):
        return self.db

    def commit(self):
        self.db.commit();

app = Flask(__name__, template_folder=os.path.join(_INPUT_DATA['MACSEC']['INCLUDE_PATH'],'templates'), static_folder=os.path.join(_INPUT_DATA['MACSEC']['INCLUDE_PATH'],'static'))
app.config.from_object(DevConfig)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/DeleteCAKCKN', methods=['PUT'])
def DeleteCAKCKN():    
    logger('====> [Flask] /DeleteCAKCKN (PUT)')

    data = request.get_json()

    db.open()
    b_ret = db.delete(data['LocalChassisID'],data['LocalInt'])
    db.commit()

    logger('<==== [Flask] /DeleteCAKCKN (PUT)')

    return json.dumps({"ret_Delete":b_ret})

@app.route('/ListCAKCKN', methods=['GET'])
def ListCAKCKN():
    logger('====> [Flask] /ListCAKCKN (GET)')

    db.open()
    records = db.selectall()

    list_record = []

    for r in records:
        list_record.append(r)

    logger('<==== [Flask] /ListCAKCKN (GET)')

    return json.dumps(list_record)

@app.route('/QueryCAKCKN', methods=['POST'])
def QueryCAKCKN():

    logger('====> [Flask] /QueryCAKCKN (POST)')

    data = request.get_json()

    print 'data:'
    print '----------------------------data---------------------------------'
    print 'data[\'LocalChassisID\']:' + data['LocalChassisID'] if 'LocalChassisID' in data else None
    print 'data[\'LocalInt\']:' + data['LocalInt'] if 'LocalInt' in data else None
    print 'data[\'LocalHostname\']:' + data['LocalHostname'] if 'LocalHostname' in data else None
    print 'data[\'RemoteChassisID\']:' + data['RemoteChassisID'] if 'RemoteChassisID' in data and data['RemoteChassisID'] is not None else None
    print 'data[\'RemoteHostname\']:' + data['RemoteHostname'] if 'RemoteHostname' in data and data['RemoteHostname'] is not None else None
    print 'data[\'RemoteInt\']:' + data['RemoteInt'] if 'RemoteInt' in data and data['RemoteInt'] is not None else None
    print '----------------------------end of data--------------------------'

    logger('data:')
    logger('----------------------------data---------------------------------')
    logger('data[\'LocalChassisID\']:' + data['LocalChassisID'] if 'LocalChassisID' in data else None)
    logger('data[\'LocalInt\']:' + data['LocalInt'] if 'LocalInt' in data else None)
    logger('data[\'LocalHostname\']:' + data['LocalHostname'] if 'LocalHostname' in data else None)
    logger('data[\'RemoteChassisID\']:' + data['RemoteChassisID'] if 'RemoteChassisID' in data and data['RemoteChassisID'] is not None else None)
    logger('data[\'RemoteHostname\']:' + data['RemoteHostname'] if 'RemoteHostname' in data and data['RemoteHostname'] is not None else None)
    logger('data[\'RemoteInt\']:' + data['RemoteInt'] if 'RemoteInt' in data and data['RemoteInt'] is not None else None)
    logger('----------------------------end of data--------------------------')

    db.open()

    #Do check on local chassis ID & local interface first
    ckn, cak = db.select(leaf_ID = data['LocalChassisID'], leaf_port = data['LocalInt'], spine_ID = data['RemoteChassisID'], spine_port = data['RemoteInt'])

    if ckn is None:    
        print 'selected ckn is None'

    if cak is None:
        print 'selected cak is None'

    if ckn == None:

        #Nothing match, check on remote chassis ID and interface.
        ckn, cak = db.select(leaf_ID = data['RemoteChassisID'], leaf_port = data['RemoteInt'], spine_ID = data['LocalChassisID'], spine_port = data['LocalInt'])
            #Generate new CAK&CKN if there's not any record matching the pair.

        if ckn == None:
            if (data['LocalChassisID'] is not None) and (data['LocalInt'] is not None) and (data['RemoteChassisID'] is not None) and (data['RemoteInt'] is not None):
                #When commiting a new pair, we'll have to block any partial match query due to lacking LLDP support after one side has configured MACsec key.
                logger('There\'s not any existing pre-shared key in the database.')
                ckn, cak = KeyGenerator()
                logger('Pre-shared key auto-generation')
                mls = tuple_MLS_record(leaf_ID = data['LocalChassisID'], leaf_port = data['LocalInt'], leaf_hostname = data['LocalHostname'], spine_ID = data['RemoteChassisID'], spine_port = data['RemoteInt'], spine_hostname = data['RemoteHostname'], CKN = ckn, CAK = cak)

                db.insert(mls)
                db.commit()
                logger('Commiting new pre-shared key into database')
            else:
                #In this case, server cannot find any match in db, and thus return (ckn, cak) = (-1,-1).
                pass
 
    logger('<==== [Flask] /QueryCAKCKN (POST)')

    return jsonify(ckn=ckn, cak=cak)

if __name__ == '__main__':
    logger('Get database instance')
    db = SimpleDBFactory().CreatePydblite()
    logger('Start up flask web server')
    app.run(host=_INPUT_DATA['Production']['SERVER_IP'], port=_INPUT_DATA['Production']['SERVER_PORT'], debug=False)

import abc, sys, os, subprocess, random
sys.path.insert(0, '/var/db/scripts/jet')
from flask import Flask, request, jsonify
from config import DevConfig
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from pydblite import Base
from collections import namedtuple

_MLS_DB_FILE_NAME = '/var/db/scripts/jet/MLS_data.pdl'
tuple_MLS_record = namedtuple("tuple_MLS_record", ['leaf_ID','leaf_port','spine_ID','spine_port', 'CKN', 'CAK'])
_DB_IP = '127.0.0.1'

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

class MLSManager_pydblite(Interface_DBController):
    def __init__(self, DBfilepath='./'):
        self.DBfilepath = DBfilepath #allow customize db file path.
        self.db = Base(_MLS_DB_FILE_NAME)

    def open(self):
        if self.db.exists():
            self.db.open();    
        else:
            self.db.create('leaf_ID', 'leaf_port', 'spine_ID','spine_port', 'CAK','CKN');
            self.db.open();

    def insert(self, MLS):
        self.db.insert(MLS.leaf_ID , MLS.leaf_port , MLS.spine_ID, MLS.spine_port, MLS.CAK, MLS.CKN);
    
    def select(self, leaf_ID, leaf_port, spine_ID, spine_port):
        flag_item_found = False

        for rec in (self.db("leaf_ID") == leaf_ID) & (self.db("leaf_port") == leaf_port) & (self.db("spine_ID") == spine_ID) & (self.db("spine_port") == spine_port):
            return rec["CKN"], rec["CAK"]

        if flag_item_found == False:
            return '-1','-1'

    def commit(self):
        self.db.commit();           

app = Flask(__name__)
app.config.from_object(DevConfig)

@app.route('/')
def index():
    return 'Hello World!'

@app.route('/QueryCAKCKN',methods=['POST'])
def QueryCAKCKN():
    print 'data:'
    print '----------------------------data---------------------------------'
    print request.get_json()
    data = request.get_json()
    print 'data[\'LocalChassisID\']:' + data['LocalChassisID']
    print 'data[\'LocalInt\']:' + data['LocalInt']
    print 'data[\'RemoteChassisID\']:' + data['RemoteChassisID']
    print 'data[\'RemoteInt\']:' + data['RemoteInt']
    print 'data[\'CKN\']:' + data['CKN'] if data['CKN'] is not None else 'None'
    print 'data[\'CAK\']:' + data['CAK'] if data['CAK'] is not None else 'None'
    print '----------------------------end of data--------------------------'

    db.open()

    #Do check on local chassis ID & local interface first    
    ckn, cak = db.select(leaf_ID = data['LocalChassisID'], leaf_port = data['LocalInt'], spine_ID = data['RemoteChassisID'], spine_port = data['RemoteInt'])
    
    print 'selected ckn:' + ckn

    if ckn == '-1':
        #Nothing match, check on remote chassis ID and interface.
        ckn, cak = db.select(leaf_ID = data['RemoteChassisID'], leaf_port = data['RemoteInt'], spine_ID = data['LocalChassisID'], spine_port = data['LocalInt'])
            #Generate new CAK&CKN if there's not any record matching the pair.
        if ckn == '-1':
            ckn, cak = KeyGenerator()
            mls = tuple_MLS_record(leaf_ID = data['LocalChassisID'], leaf_port = data['LocalInt'], spine_ID = data['RemoteChassisID'], spine_port = data['RemoteInt'], CKN = ckn, CAK = cak)

            db.insert(mls)
            db.commit()
 
    return jsonify(ckn=ckn, cak=cak)

if __name__ == '__main__':
    db = SimpleDBFactory().CreatePydblite()
    app.run(host='0.0.0.0', port=8080, debug=False)

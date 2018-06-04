'''
Testing scenario:
1. unsupported device/linecard -> TBD
2. half configured configuration (without connection association)
3. complete configuration, preshared key sync with server.
4. complete configuration, preshared key not sync with server.
'''
import os, sys, random, string
from jnpr.junos import Device
from lxml import etree
from collections import namedtuple
sys.path.insert(0, '/var/db/scripts/jet')
import requests, json
from jnpr.junos.utils.config import Config
from datetime import datetime
import jcs
sys.path.insert(0, '/var/db/scripts/jet')

tuple_CKN_CAK = namedtuple('tuple_CKN_CAK', ['ckn', 'cak'])
tuple_Query_CKNCAK = namedtuple('tuple_Query_CKNCAK', ['LocalChassisID','LocalInt','LocalHostname','RemoteChassisID','RemoteInt','RemoteHostname'])

dictConnCKNCAK = {}
dictLocalIntConn = {}
Local_ChassisID = None
lstQueryCKNCAK = []

SERVER_IP = '172.27.169.123'
SERVER_PORT = '8080'

class Decryptor():
    def __init__(self):
        self.MAGIC = "$9$"

        ###################################
        ## letter families

        self.FAMILY = ["QzF3n6/9CAtpu0O", "B1IREhcSyrleKvMW8LXx", "7N-dVbwsY2g4oaJZGUDj", "iHkq.mPf5T"]
        self.EXTRA = dict()
        for x, item in enumerate(self.FAMILY):
            for c in item:
                self.EXTRA[c] = 3 - x

        ###################################
        ## forward and reverse dictionaries

        self.NUM_ALPHA = [x for x in "".join(self.FAMILY)]
        self.ALPHA_NUM = {self.NUM_ALPHA[x]: x for x in range(0, len(self.NUM_ALPHA))}

        ###################################
        ## encoding moduli by position

        self.ENCODING = [[1, 4, 32], [1, 16, 32], [1, 8, 32], [1, 64], [1, 32], [1, 4, 16, 128], [1, 32, 64]]

    def _nibble(self, cref, length):
        nib = cref[0:length]
        rest = cref[length:]
        if len(nib) != length:
            print "Ran out of characters: hit '%s', expecting %s chars" % (nib, length)
            sys.exit(1)
        return nib, rest

    def _gap(self, c1, c2):
        return (self.ALPHA_NUM[str(c2)] - self.ALPHA_NUM[str(c1)]) % (len(self.NUM_ALPHA)) - 1

    def _gap_decode(self, gaps, dec):
        num = 0
        if len(gaps) != len(dec):
            print "Nibble and decode size not the same!"
            sys.exit(1)
        for x in range(0, len(gaps)):
            num += gaps[x] * dec[x]
        return chr(num % 256)

    def juniper_decrypt(self, crypt):
        chars = crypt.split("$9$", 1)[1]
        first, chars = self._nibble(chars, 1)
        toss, chars = self._nibble(chars, self.EXTRA[first])
        prev = first
        decrypt = ""
        while chars:
            decode = self.ENCODING[len(decrypt) % len(self.ENCODING)]
            nibble, chars = self._nibble(chars, len(decode))
            gaps = []
            for i in nibble:
                g = self._gap(prev, i)
                prev = i
                gaps += [g]
            decrypt += self._gap_decode(gaps, decode)
        return decrypt

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def DeployConfig(dev, local_int, ckn, cak, conn_name = None):

    if conn_name is None:
        conn_name = id_generator()

    with Config(dev) as cu:
        cu.load('set security macsec connectivity-association {0} security-mode static-cak'.format(conn_name), format='set')
        cu.load('set security macsec connectivity-association {0} pre-shared-key ckn {1}'.format(conn_name, ckn), format='set')
        cu.load('set security macsec connectivity-association {0} pre-shared-key cak {1}'.format(conn_name, cak), format='set')
        cu.load('set security macsec interfaces {0} connectivity-association {1}'.format(local_int,conn_name), format='set')
        cu.pdiff()
        cu.commit()

def DeployConfig_jcs(local_int, ckn, cak, conn_name = None):

    if conn_name is None:
        conn_name = id_generator()

    script = "system-check.py"
    change_xml = """<security>
                        <macsec>
                            <connectivity-association>
                                <name>{0}</name>
                                <security-mode>static-cak</security-mode>
                                <pre-shared-key>
                                    <ckn>{1}</ckn>
                                    <cak>{2}</cak>
                                </pre-shared-key>
                            </connectivity-association>
                            <interfaces>
                                <name>{3}</name>
                                <connectivity-association>{0}</connectivity-association>
                            </interfaces>
                        </macsec>
                    </security>""".format(conn_name, ckn, cak, local_int)
    jcs.emit_change(change_xml, "change", "xml")

def logger(strLog):
    with open(os.path.join('/var/tmp/','output.txt'), 'a') as target_config:
        target_config.write(strLog+'\n')

def rest_request_post(query):

    response = None

    try:
        headers = {
            "content-type": "application/json"
        }
        response = requests.post(
            url="http://{0}:{1}/QueryCAKCKN".format(SERVER_IP,SERVER_PORT),
            headers=headers,
            data=json.dumps({
                    "LocalChassisID": query.LocalChassisID,
                    "LocalInt": query.LocalInt,
                    "LocalHostname": query.LocalHostname,
                    "RemoteChassisID": query.RemoteChassisID,
                    "RemoteInt": query.RemoteInt,
                    "RemoteHostname": query.RemoteHostname
                }
            )
        )
    except Exception as e:
        jcs.emit_error('Cannot request data from server, please check sever connectivity.')
        sys.exit(-1)
        print str(e)

    return response


class InfoCollector():
    def __init__(self, dev):
        self.dictConnCKNCAK = {}
        self.dictLocalIntConn = {}
        self.dev = dev
        self.dev = dev.open()
        pass

    def getMACsec_conn_key(self):
        data = self.dev.rpc.get_config(
            filter_xml=etree.XML('''
               <configuration>
                   <security>
                       <macsec/>
                   </security>
               </configuration>
               '''
               )
            )

        #get dictionary [conn_name | cak/ckn] for local named tuple(cak,ckn) checking 
        for item in data.findall('security/macsec/connectivity-association'):
            conn_name = item.find('name').text
            ckn = item.find('pre-shared-key/ckn').text
            cak = item.find('pre-shared-key/cak').text

            ckn_cak = tuple_CKN_CAK(ckn, cak)

            self.dictConnCKNCAK[conn_name] = ckn_cak

        #returning data collected to make this module easily to reuse.
        return self.dictConnCKNCAK 

    def getMACsec_interface_conn(self):

        data = self.dev.rpc.get_config(
            filter_xml=etree.XML('''
               <configuration>
                   <security>
                       <macsec/>
                   </security>
               </configuration>
               '''
               )
            )

        #get local interfaces which have macsec configured.
        for item in data.findall('security/macsec/interfaces'):
            #dict['xe-0/0/1'] = cal
            self.dictLocalIntConn[item.find('name').text] = item.find('connectivity-association').text

        #returning data collected to make this module easily to reuse.
        return self.dictLocalIntConn

    '''
    def getLocalChassisID(self):
        #Get chassis ID of current device
        data = self.dev.rpc.get_chassis_mac_addresses()
        #print etree.tostring(data, encoding='unicode')

        if data.find('mac-address-information') is not None:
            #local device is MX series router
            for item in data.findall('mac-address-information'):
                self.Local_ChassisID = item.find('private-base-address').text
        else:
            #local device is EX series switch
            for item in data.findall('chassis-mac-addresses-edge-info/fpc-mac-address'):
                self.Local_ChassisID = item.find('fpc-mac-base').text 
        return self.Local_ChassisID
    '''

    def get_local_id_hostname(self):
        data = self.dev.rpc.get_lldp_local_info()        
        Local_ChassisID = data.find('lldp-local-chassis-id').text
        Local_Hostname = data.find('lldp-local-system-name').text

        return Local_ChassisID, Local_Hostname

    def get_remote_ID_port_by_LLDP(self, local_int):

        #Try to get following info from lldp:
        #   neighbor hostname connected by local interface
        #   neighbor chassis ID connected by local interface
        #   neighbor interface connected with local interface

        remote_chassisID = None
        remote_int = None
        remote_hostname = None

        data = self.dev.rpc.get_lldp_interface_neighbors(interface_device=local_int);
        #print etree.tostring(data, encoding='unicode')

        for item in data.findall('lldp-neighbor-information'):
            remote_chassisID = item.find('lldp-remote-chassis-id').text
            remote_int = item.find('lldp-remote-port-description').text
            remote_hostname = item.find('lldp-remote-system-name').text

        return remote_chassisID, remote_int, remote_hostname

    def __del__(self):
        self.dev.close()


def main():
    dev = Device(
    #host='172.27.169.123', user='lab', passwd='lab123'
    )
    #collecting MACsec info
    info = InfoCollector(dev)
    dictLocalIntConn = info.getMACsec_interface_conn()
    dictConnCKNCAK = info.getMACsec_conn_key()

    #collecting local info
    Local_ChassisID, Local_Hostname = info.get_local_id_hostname()
    
    #compose query for interface which is half configured.
    for local_int in info.dictLocalIntConn:
        remote_chassisID, remote_int, remote_hostname = info.get_remote_ID_port_by_LLDP(local_int)

        query = tuple_Query_CKNCAK(Local_ChassisID, local_int, Local_Hostname, remote_chassisID, remote_int, remote_hostname)

        lstQueryCKNCAK.append(query)

    #Query preshared key from server.
    for query in lstQueryCKNCAK:
        #Get responding ckn & cak
        dict_ServerResponse = json.loads(rest_request_post(query).text)

        #Check existing ckn & cak match or not, if there's any.
        if dictLocalIntConn[query.LocalInt] in dictConnCKNCAK:

            #Get current configured preshared key
            cur_CKNCAK = dictConnCKNCAK[dictLocalIntConn[query.LocalInt]]
            
            if  (
                    (
                        dict_ServerResponse['ckn'] != cur_CKNCAK.ckn or 
                        dict_ServerResponse['cak'] != Decryptor().juniper_decrypt(cur_CKNCAK.cak)
                    )
                    and dict_ServerResponse['ckn'] != None and dict_ServerResponse['cak'] != None
                ):
                #ckn cak needs to be updated.
                jcs.emit_warning("Get latest pre-shared key from server, update it.")
                DeployConfig_jcs(query.LocalInt, dict_ServerResponse['ckn'], dict_ServerResponse['cak'], dictLocalIntConn[query.LocalInt])
            else:
                #ckn & cak matched, do not reconfigured.
                pass
        else:
            #There's not exising pre-shared key, deploy it.
            if dict_ServerResponse['ckn'] != None and dict_ServerResponse['cak'] != None:
                jcs.emit_warning("Automatically generate pre-shared key and deploy it.")
                DeployConfig_jcs(query.LocalInt, dict_ServerResponse['ckn'], dict_ServerResponse['cak'], dictLocalIntConn[query.LocalInt])
            else:
                #display error msg since there's no existing record in Database.
                #Possible scenario:
                #1. User delete the record and macsec configuration accidentally 
                #   -> LLDP is not working. -> Cannot recover from error state.
                #   -> Inform user to delete both side's macsec configuration, and make sure LLDP is up&running, then try again.

                jcs.emit_error("There's not matched pre-shared key in database, please delete both side's macsec configuration and try again.")

if __name__ == "__main__":
    main()
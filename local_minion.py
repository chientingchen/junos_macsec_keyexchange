import os, sys, random, string
from jnpr.junos import Device
from lxml import etree
from collections import namedtuple
sys.path.insert(0, '/var/db/scripts/jet')
import requests, json
from jnpr.junos.utils.config import Config


tuple_CKN_CAK = namedtuple('tuple_CKN_CAK', ['ckn', 'cak'])
tuple_Query_CKNCAK = namedtuple('tuple_Query_CKNCAK', ['LocalChassisID','LocalInt','RemoteChassisID','RemoteInt','CKN','CAK'])
#If CAK & CKN are both None, server would return a CAK/CKN pair. 
#If CAK & CKN are both specified, server would also return latest CAK/CKN pair for this match.
dictConnCKNCAK = {}
dictLocalIntConn = {}
Local_ChassisID = None
lstQueryCKNCAK = []
SERVER_IP = '172.27.169.123'
SERVER_PORT = '8080'


#################################################################
## globals

MAGIC = "$9$"

###################################
## letter families

FAMILY = ["QzF3n6/9CAtpu0O", "B1IREhcSyrleKvMW8LXx", "7N-dVbwsY2g4oaJZGUDj", "iHkq.mPf5T"]
EXTRA = dict()
for x, item in enumerate(FAMILY):
    for c in item:
        EXTRA[c] = 3 - x

###################################
## forward and reverse dictionaries

NUM_ALPHA = [x for x in "".join(FAMILY)]
ALPHA_NUM = {NUM_ALPHA[x]: x for x in range(0, len(NUM_ALPHA))}

###################################
## encoding moduli by position

ENCODING = [[1, 4, 32], [1, 16, 32], [1, 8, 32], [1, 64], [1, 32], [1, 4, 16, 128], [1, 32, 64]]


def _nibble(cref, length):
    nib = cref[0:length]
    rest = cref[length:]
    if len(nib) != length:
        print "Ran out of characters: hit '%s', expecting %s chars" % (nib, length)
        sys.exit(1)
    return nib, rest


def _gap(c1, c2):
    return (ALPHA_NUM[str(c2)] - ALPHA_NUM[str(c1)]) % (len(NUM_ALPHA)) - 1


def _gap_decode(gaps, dec):
    num = 0
    if len(gaps) != len(dec):
        print "Nibble and decode size not the same!"
        sys.exit(1)
    for x in range(0, len(gaps)):
        num += gaps[x] * dec[x]
    return chr(num % 256)


def juniper_decrypt(crypt):
    chars = crypt.split("$9$", 1)[1]
    first, chars = _nibble(chars, 1)
    toss, chars = _nibble(chars, EXTRA[first])
    prev = first
    decrypt = ""
    while chars:
        decode = ENCODING[len(decrypt) % len(ENCODING)]
        nibble, chars = _nibble(chars, len(decode))
        gaps = []
        for i in nibble:
            g = _gap(prev, i)
            prev = i
            gaps += [g]
        decrypt += _gap_decode(gaps, decode)
    return decrypt

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def DeployConfig(dev, local_int, ckn, cak, conn_name=id_generator()):
    with Config(dev, mode='private') as cu:
        cu.load('set security macsec connectivity-association {0} security-mode static-cak'.format(conn_name), format='set')
        cu.load('set security macsec connectivity-association {0} pre-shared-key ckn {1}'.format(conn_name, ckn))
        cu.load('set security macsec connectivity-association {0} pre-shared-key cak {1}'.format(conn_name, cak))
        cu.load('set security macsec interfaces {0} connectivity-association {1}'.format(local_int,conn_name))
        cu.pdiff()
    #    cu.commit()


def main():
    with Device(
        #host='172.27.169.123', user='lab', passwd='lab123'
        ) as dev:
        data = dev.rpc.get_config(
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

            dictConnCKNCAK[conn_name] = ckn_cak


        #get local interfaces which have macsec configured.
        for item in data.findall('security/macsec/interfaces'):
            #dict['xe-0/0/1'] = cal
            dictLocalIntConn[item.find('name').text] = item.find('connectivity-association').text


        #Get chassis ID of current device
        data = dev.rpc.get_chassis_mac_addresses()
        #print etree.tostring(data, encoding='unicode')

        if data.find('mac-address-information') is not None:
            #local device is MX series router
            for item in data.findall('mac-address-information'):
                Local_ChassisID = item.find('private-base-address').text
        else:
            #local device is EX series switch
            for item in data.findall('chassis-mac-addresses-edge-info/fpc-mac-address'):
                Local_ChassisID = item.find('fpc-mac-base').text 


        #Get following info from lldp:
        #   local interface connecting neighbor device
        #   neighbor chassis ID
        #   neighbor interface
        data = dev.rpc.get_lldp_neighbors_information();
        #print etree.tostring(data, encoding='unicode')

        
        for item in data.findall('lldp-neighbor-information'):
            local_int = item.find('lldp-local-port-id').text

            if local_int == 'fxp0' or local_int == 'em0':
                #skip management port.
                continue

            remote_chassisID = item.find('lldp-remote-chassis-id').text

            if item.find('lldp-remote-port-description') is None:
                #MX series router
                remote_int = item.find('lldp-remote-port-id').text
            else:
                #EX series switch
                remote_int = item.find('lldp-remote-port-description').text

            #print local_int
            #print remote_chassisID
            #print remote_int

            #if local interface has already configured CAK/CKN, pull it out from dict
            if local_int in dictLocalIntConn:
                conn = dictLocalIntConn[local_int]
                ckn_cak = dictConnCKNCAK[conn]
                query = tuple_Query_CKNCAK(Local_ChassisID, local_int, remote_chassisID, remote_int, ckn_cak.ckn, ckn_cak.cak)
            else:
            #if local interface hasn't configured CAK/CKN, asking it from server.
                query = tuple_Query_CKNCAK(Local_ChassisID, local_int, remote_chassisID, remote_int, None, None) 
            
            lstQueryCKNCAK.append(query)

        #Query pre-shared key from server by chassis ID with interface name.
        for query in lstQueryCKNCAK:
            
            headers = {
                "content-type": "application/json"
            }
            data = {
                "externalId": "801411",
                "name": "RD Core",
                "description": "Tenant create",
                "subscriptionType": "MINIMAL",
                "features": {
                    "capture": False,
                    "correspondence": True,
                    "vault": False
                }
            }

            response = requests.post(
                url="http://{0}:{1}/QueryCAKCKN".format(SERVER_IP,SERVER_PORT),
                headers=headers,
                data=json.dumps({
                    "LocalChassisID": query.LocalChassisID,
                    "LocalInt": query.LocalInt,
                    "RemoteChassisID": query.RemoteChassisID,
                    "RemoteInt": query.RemoteInt,
                    "CKN": query.CKN,
                    "CAK": query.CAK
                    }
                )
            )
            #Get responding ckn & cak
            dict_ServerResponse = json.loads(response.text)

            #Check existing ckn & cak match or not, if there's any.
            if query.LocalInt in dictLocalIntConn:
                cur_CKNCAK = dictConnCKNCAK[dictLocalIntConn[query.LocalInt]]
                print 'dict_ServerResponse[\'ckn\']:'+dict_ServerResponse['ckn']
                print 'dict_ServerResponse[\'cak\']:'+dict_ServerResponse['cak']
                print 'cur_CKNCAK.ckn:' + cur_CKNCAK.ckn
                print 'cur_CKNCAK.cak:' + cur_CKNCAK.cak
                print 'decrypt: ' + juniper_decrypt(cur_CKNCAK.cak)

                if dict_ServerResponse['ckn'] != cur_CKNCAK.ckn or dict_ServerResponse['cak'] != juniper_decrypt(cur_CKNCAK.cak):
                    #Not match, redeploy the cak & ckn
                    DeployConfig(dev, query.LocalInt, dict_ServerResponse['ckn'], dict_ServerResponse['cak'], dictLocalIntConn[query.LocalInt])
            else:
                #there's not existing ckn & cak for this local int, create a new pair.
                DeployConfig(dev, query.LocalInt, dict_ServerResponse['ckn'], dict_ServerResponse['cak'])


            print response.status_code, response.reason, response.text

def logger(strLog):
    with open(os.path.join('/var/tmp/','output.txt'), 'a') as target_config:
        target_config.write(strLog+'\n')

if __name__ == "__main__":
    main()
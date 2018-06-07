import sys, os
from yaml import load
from local_minion import *

def logger(strLog):
    with open(_INPUT_DATA['MACSEC']['LOG_PATH'], 'a') as target_config:
        target_config.write(strLog+'\n')

#Read Environment config
THIS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../commit/')
DATA_FILE = 'minion_environment.yaml'

f=open(os.path.join(THIS_DIR,DATA_FILE))
data=f.read()
_INPUT_DATA=load(data)
f.close()

logger('Loading required library from ' + _INPUT_DATA['MACSEC']['INCLUDE_PATH'])
logger_macsec.info('Loading required library from ' + _INPUT_DATA['MACSEC']['INCLUDE_PATH'])
sys.path.insert(0, _INPUT_DATA['MACSEC']['INCLUDE_PATH'])

import requests, json
import argparse


arguments = {'ChassisID': 'Device chassis ID which delete macsec configuration resides in', 
             'Interface': 'Device interface which delete macsec configuration resides in'}

SERVER_IP = _INPUT_DATA['Production']['SERVER_IP']
SERVER_PORT = _INPUT_DATA['Production']['SERVER_PORT']


def rest_request_put(ChassisID, Interface, URL_route):
    headers = {
        "content-type": "application/json"
    }
    response = requests.put(
        url="http://{0}:{1}/{2}".format(SERVER_IP,SERVER_PORT,URL_route),
        headers=headers,
        data=json.dumps({
                "LocalChassisID": ChassisID,
                "LocalInt": Interface,
                "LocalHostname": None,
                "RemoteChassisID": None,
                "RemoteInt": None,
                "RemoteHostname": None

                }
            )
        )
    return response

def main():
    parser = argparse.ArgumentParser(description='This is a demo script.')

    #Define the arguments accepted by parser
    # which use the key names defined in the arguments dictionary
    for key in arguments:
        parser.add_argument(('-' + key), required=True, help=arguments[key])
    args = parser.parse_args()

    # Extract the value
    print 'delete record with Chassis ID={0}, Interface={1}'.format(args.ChassisID,args.Interface)

    logger('Sending delete request to server, Chassis ID={0}, Interface={1}'.format(args.ChassisID,args.Interface))
    logger_macsec.info('Sending delete request to server, Chassis ID={0}, Interface={1}'.format(args.ChassisID,args.Interface))

    rest_request_put(args.ChassisID, args.Interface, 'DeleteCAKCKN')

    logger('Delete successful')
    logger_macsec.info('Delete successful')


if __name__ == '__main__':
    main()
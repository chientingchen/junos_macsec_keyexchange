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
import sys, os
from yaml import load
import logging
import logging.handlers

#Read Environment config
THIS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../commit/')
DATA_FILE = 'minion_environment.yaml'

f=open(os.path.join(THIS_DIR,DATA_FILE))
data=f.read()
_INPUT_DATA=load(data)
f.close()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), _INPUT_DATA['MACSEC']['INCLUDE_PATH']))

import requests, json
import argparse

#logger init
log_file = os.path.join(os.path.dirname(__file__), _INPUT_DATA['MACSEC']['LOG_PATH'])

log_file_size = 1638400
log_file_count = 5
log_level = [logging.INFO, logging.DEBUG][_INPUT_DATA['MACSEC']['DEBUG']]

logger = logging.getLogger('delete_MACsec_interface')
logger.setLevel(log_level)
handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=log_file_size, backupCount=log_file_count)
handler.setFormatter(logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S'))
logger.addHandler(handler)

logger.info('Loading required library from ' + _INPUT_DATA['MACSEC']['INCLUDE_PATH'])


arguments = {'ChassisID': 'Device chassis ID which delete macsec configuration resides in', 
             'Interface': 'Device interface which delete macsec configuration resides in'}

SERVER_IP = _INPUT_DATA['Production']['SERVER_IP']
SERVER_PORT = _INPUT_DATA['Production']['SERVER_PORT']


def rest_request_put(ChassisID, Interface, URL_route):
    logger.debug('====> rest_request_put()')

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

    logger.debug('<==== rest_request_put()')

    return response

def main():
    parser = argparse.ArgumentParser(description='This is a demo script.')

    #Define the arguments accepted by parser
    # which use the key names defined in the arguments dictionary
    for key in arguments:
        parser.add_argument(('-' + key), required=True, help=arguments[key])
    args = parser.parse_args()

    print 'delete record with Chassis ID={0}, Interface={1}'.format(args.ChassisID,args.Interface)

    logger.info('Sending delete request to server, Chassis ID={0}, Interface={1}'.format(args.ChassisID,args.Interface))

    try:
        rest_request_put(args.ChassisID, args.Interface, 'DeleteCAKCKN')
    except Exception as e:
        print str(repr(e))
        logger.error(repr(e))

    logger.info('Delete successful')


if __name__ == '__main__':
    main()
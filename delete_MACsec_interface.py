import sys
sys.path.insert(0, '/var/db/scripts/jet')
import requests, json
import argparse

arguments = {'ChassisID': 'Device chassis ID which delete macsec configuration resides in', 
             'Interface': 'Device interface which delete macsec configuration resides in'}

SERVER_IP = '172.27.169.123'
SERVER_PORT = '8080'


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
    print args.ChassisID
    print args.Interface

    rest_request_put(args.ChassisID, args.Interface, 'DeleteCAKCKN')

if __name__ == '__main__':
    main()
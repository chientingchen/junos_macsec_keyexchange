import os
from socket import *
from jnpr.junos import Device
from lxml import etree
import argparse

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-interface_name')
    args = parser.parse_args()

    logger(args.interface_name)

    dev = Device()
    dev.open()

    logger('[LLDP information]:')
    #logger(dev.display_xml_rpc('show lldp neighbor interface ge-0/0/0', format='text'))
    output = dev.cli('show lldp neighbor interface xe-0/0/2', format='xml', warning=False)
    logger('Remote management IP: ' + output.xpath('//lldp-remote-management-address')[0].text)
    remote_addr = output.xpath('//lldp-remote-management-address')[0].text

    output = dev.cli('show lldp local-information', format='xml', warning=False)
    logger('Local management IP: ' + output.xpath('//lldp-local-management-address-address')[0].text)
    mgmt_addr = output.xpath('//lldp-local-management-address-address')[0].text
    
    HOST = mgmt_addr
    PORT = 9999
    
    print 'starting:...'
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind((HOST, PORT))
    with open(os.path.join('/var/tmp/','output_server.txt'), 'a') as f:
        f.write('-----Connected-----\n')
        data1, address = s.recvfrom(1024)
        f.write(data1 + '\n')
        s.sendto('I got ur 1st message', address)
        data2, address = s.recvfrom(1024)
        f.write(data2 + '\n')
        s.sendto('I got ur 2nd message', address)
        data3, address = s.recvfrom(1024)
        f.write(data3 + '\n')
        s.sendto('We cool, bye', address)
        s.close()

    

def logger(strLog):
    with open(os.path.join('/var/tmp/','output.txt'), 'a') as target_config:
        target_config.write(strLog+'\n')

if __name__ == "__main__":
    main()
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

    #etree.tostring(output)

    logger('Remote management IP: ' + output.xpath('//lldp-remote-management-address')[0].text)

    remote_addr = output.xpath('//lldp-remote-management-address')[0].text

    output = dev.cli('show lldp local-information', format='xml', warning=False)

    logger('Local management IP: ' + output.xpath('//lldp-local-management-address-address')[0].text)
    
    mgmt_addr = output.xpath('//lldp-local-management-address-address')[0].text
    
    HOST = remote_addr
    PORT = 9999
    
    print 'starting:...'
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect((HOST, PORT))
    with open(os.path.join('/var/tmp/','output_client.txt'), 'a') as f:
        s.sendall("The 1st message")
        data1 = s.recv(1024)
        f.write(data1 + '\n')
        s.sendall("The 2nd message")
        data2 = s.recv(1024)
        f.write(data2 + '\n')
        s.sendall("Are we cool?")
        data3 = s.recv(1024)
        f.write(data3 + '\n')
        s.close()   

    

def logger(strLog):
    with open(os.path.join('/var/tmp/','output.txt'), 'a') as target_config:
        target_config.write(strLog+'\n')

if __name__ == "__main__":
    main()
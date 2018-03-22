import os
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
    output = dev.cli('show lldp neighbor interface xe-0/0/4', format='xml', warning=False)

    #etree.tostring(output)

    logger('Remote management IP: ' + output.xpath('//lldp-remote-management-address')[0].text)


    output = dev.cli('show lldp local-information', format='xml', warning=False)

    logger('Local management IP: ' + output.xpath('//lldp-local-management-address-address')[0].text)

def logger(strLog):
    with open(os.path.join('/var/tmp/','output.txt'), 'a') as target_config:
        target_config.write(strLog+'\n')

if __name__ == "__main__":
    main()
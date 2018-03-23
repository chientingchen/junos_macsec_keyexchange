import os
from jnpr.junos import Device
from lxml import etree
from jnpr.junos.utils.config import Config

def main():

    sep = '-'    # used for extract device info from device description.
    device_name = ''
    device_list = ['EX3400','EX3400-VC','EX4200','EX4200-VC','EX4300','EX4300-VC','EX4550','EX4550-VC','EX4600','EX4600-VC','EX9200','EX9200-VC','MX240','MX480','MX960','MX2008','MX2010','MX2020','MX10003','QFX5100','QFX5100-VC','QFX10008','QFX10016']
    device_list_license = ['EX4200','EX4200-VC','EX4300','EX4300-VC','EX4550','EX4550-VC','EX4600','EX4600-VC','EX9200','EX9200-VC','QFX5100','QFX5100-VC']
    config = {
       'connectivity_association_name': 'cal12',
       'ckn': 'abcd',
       'cak': 'abc1234',
       'interface_name': 'xe-0/0/4'
    }

    dev = Device()
    dev.open()

    # Step 1: Check if device supports target function.
    chassis_hardware = dev.rpc.get_chassis_inventory()
    device_description = chassis_hardware.xpath(".//description")[0].text
    print ("device_description is: %s" % device_description)
    logger ("device_description is: " + device_description)
    
    device_name = device_description.split(sep,1)[0]
    print ("device_name is: %s" % device_name)
    logger("device_name is: " + device_name)

    if device_name in device_list:
        print ("This device supports the target function!")
        logger ("This device supports the target function!")
    else:
        print ("Oops, this is not the device we wanted...stop checking now")
        logger ("Oops, this is not the device we wanted...stop checking now")
        #return
    
    if device_name in device_list_license:
        print ("This device also requests a licnese to be installed for the target function,start checking required license now...")
        logger ("This device also requests a licnese to be installed for the target function,start checking required license now...")
        licenses = dev.rpc.get_license_summary_information()

        for ifd in licenses.getiterator("feature-summary"):
            if (ifd.find("name").text.strip()=='macsec'):
                print ("Yes we get it!")
                logger("We get the license named: " + ifd.find("name").text.strip())
                logger("Cool, we have installed the license!")
                break
            else:
                print ("Still searching for required license...")
                logger("Still searching for required license...")

    # Step 2: Check if this device already has MACsec configed.
    macsec_connection = dev.rpc.get_macsec_connection_information()
    for ifd in macsec_connection.getiterator("macsec-connection-information"):
        # if we check the " show security macsec connections", and we cannot find info about interface-name, then we can make sure that this is not a succeful macsec connection or deloyment, so we can try to "delete macsec configuration"(no need) and deploy new one.
        if ifd.find("interface-name") == None:
            # Method: using Jinja MACsec template here. [need to be done]
            print ("This MACsec config is not complete or has not be deployed in this device, we can deploy new configuration.")
            conf_file = "/var/tmp/macsec_template.conf"
            with Config(dev, mode='private') as cu:
                cu.load(template_path=conf_file, template_vars=config, merge=True)
                cu.commit()
        else:
            # Check if current interface matches with the interface we want to have macsec deployed, if it does, skip the macsec config; if not, deploy new configuration for the target interface.
            print ("MACsec has been deployed in this Device, have more check here.")
            if (ifd.find("interface-name").text.strip() =='ge-1/0/0'):
                print ("We have correctly deploy macsec.")
            if (ifd.find("interface-name").text.strip()!='ge-1/0/0'):
                print ("MACsec interface does not match, we need to deploy new macsec for new interface")
                conf_file = "/var/tmp/macsec_template.conf"
                with Config(dev, mode='private') as cu:
                    cu.load(template_path=conf_file, template_vars=config, merge=True)
                    cu.commit()

    # Step 3: Check if MKA works
    mka_sessions= dev.rpc.get_mka_session_information()
    for ifd in mka_sessions.getiterator("mka-session-information"):
        if ifd.find("interface-name") == None:
            print ("Oops,MKA is not working")
            # Need deploy again.....?
        elif ifd.find("latest-sak-key-identifier").text.strip()== '000000000000000000000000/0':
            print ("Oops,MKA is not working")
            # Need deploy again.....?
        else:
            print ("Great! MASsec is working")

def logger(strLog):
    with open(os.path.join('/var/tmp/','test.txt'), 'a') as target_config:
        target_config.write(strLog+'\n')

if __name__ == "__main__":
    main()
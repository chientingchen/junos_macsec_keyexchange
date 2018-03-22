# User Guide

Requirement: 
------------
This lab is baed on
* 1 ubuntu server
* 1 vMX.
* [Junos OpenConfig Package](https://www.juniper.net/support/downloads/?p=openconfig#sw) (For x86 vMX, please select the one with upgraded FreeBSD)

Installation:
-------------

0. Install PyEz by following this [link] (https://www.juniper.net/documentation/en_US/junos-pyez/topics/task/installation/junos-pyez-server-installing.html)
1. git clone this repo into ubuntu server.
2. Copy `junos-openconfig-x86-32-0.0.0.9.tgz` to targeting junos system
3. Execute `request system software add junos-openconfig-x86-32-0.0.0.9.tgz`
4. Execute `show version detail | match openconfig` for making sure it's installed successfully. 

```
JUNOS Openconfig [0.0.0.9]
```
    
Usage:
-------------
1. Edit test.yml
    * Put your target device IP, account and password under production section.
    * Put your interface IP and prefixes under TEMPLATE_VARIABLES section.

    ```
    production:
      TARGET_HOST: "172.27.169.156"
      TARGET_HOST_ACCOUNT: "lab"
      TARGET_HOST_PWD: "lab123"
    ```

2. Execute test.py by `python test.py` on ubuntu server

    ```
    OpenConfig:
      CFG_TEMPLATE: "test_template.cfg"
      TARGET_CFG: "candidate.cfg"
      TEMPLATE_VARIABLES:
        ip_address: '172.27.3.4'
        prefixes: '29'
    ```

3. This script will do:
    * Make sure device connection has been set up already.
    * Render OpenConfig configuration file based on value in `test_data.yml` and configuration template `test_template.cfg`
    * Deploy OpenConfig configuration through PyEz
    * Get OpenConfig configuration by PyEz
4. Execute `show | display translation-scripts translated-config` on vMX, you'll see the junos config which traslated by OpenConfig

    ```
    chassis {
        aggregated-devices {
            ethernet {
                device-count 100;
            }
        }
    }
    interfaces {
        ge-0/0/5 {
            description "* to leaf-01";
            enable;
            mtu 9192;
            unit 0 {
                family inet {
                    address 172.16.0.4/31;
                    address 172.27.1.2/30;
                    address 172.27.3.4/29;
                }
            }
        }
    }
    ```
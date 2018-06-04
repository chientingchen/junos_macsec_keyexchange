# User Guide

## Requirement: 
### Minimum requirements

* 2 juniper devices which supporting [MACsec functionality](https://www.juniper.net/support/downloads/?p=openconfig#sw)
* Management network connectivities among all devices

### For remote central server installation:
* 1 Linux server which has ability to executing python.
* Management network connectivity among devices and server
 
### Tested environment

* MX480
* JUNOS 17.3R1.10
* Line card model

## Installation:

### Remote Master
0. Download all files in `MACsec_master_dependencies` to include path and configure the path in `master_environment.cfg`
    (e.g. Junos device: /var/db/script/jet/)
1. For linux server, it's recommend to use screen for executing remote_master at background.

    ```
    root@server# screen
    ```
        
2. Executing `remote_master.py`
    
    ```
    root@server# python remote_master.py
    ```
        
### Local Minion
0. Deploy basic config Basic.conf at each junos devices.
1. Download all files in `MACsec_minion_dependencies` to include path, and configure the path in `minion_environment.cfg`
2. Download `local_minion.py` into `/var/db/scripts/commit/`

Usage:
-------------
0. Finish the cabling between all devices and make sure basic configuration are deployed.
1. Edit macsec configuration as usual, but user doesn't have to configure pre-shared key.
* Set MACsec interface
    
    ```
    junos@MX# set security macsec interfaces <MACsec interface name> connectivity-association <user defined connectivity name>
    ```
    
* Commit the configuration, commit script would auto-complete the key-exchange for you.
    
    ```
    junos@MX# commit
    ```

2. You can always check `http://<remote_server_ip>:<port>` for current connection pre-shared key.



3. For topology changing:
    * Ensure the device connectinity is good.
    * Log into the device(s) which has new connection(s)
    * Execute op script `delete_MACsec_interface.py` for deleting specific interface pre-shared key
    
    ```
        op delete_MACsec_interface.py <Device ChassisID> <Device interface name>
    ```
    
Architecture:
-------------
![Alt text](./docs/MACsec_Architecture.png "Architectural Diagram")


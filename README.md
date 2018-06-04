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
0. Download all dependency files located in `MACsec_master_dependencies` to local file path and configure the include path in `master_environment.yaml`
   <br> (e.g. For junos device, you can put dependency files on at `/var/db/script/jet/` )
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
1. Download all files in `MACsec_minion_dependencies` to include path, and configure the path in `minion_environment.yaml`
2. Download `local_minion.py` into `/var/db/scripts/commit/`

## Usage:

### Pre-shared key auto-gen & deployment:
0. Finish the cabling between all devices and make sure basic configuration are deployed.
1. Edit macsec configuration as usual, but user doesn't have to configure pre-shared key.

    ```
    junos@MX# set security macsec interfaces <MACsec interface name> connectivity-association <user defined connectivity name>
    ```
    
2. Commit the configuration, commit script would auto-complete the key-exchange for you.
    
    ```
    junos@MX# commit
    ```

3. You can always check `http://<remote_server_ip>:<port>` for current connection pre-shared key.

![Alt text](./docs/Pre-shared_key_table.png "Screen shot of pre-shared key table")

### Re-gen pre-shared key due to link issue (Wrong Cabling):
1. Ensure the device cabling is fixed.
2. Log into the device(s) which has new connection(s)
3. Execute op script `delete_MACsec_interface.py` for deleting specific interface pre-shared key

    ```
    op delete_MACsec_interface.py <Device ChassisID> <Device interface name>
    ```

4. Once again, edit macsec configuration as usual, don't have to configure pre-shared key.

    ```
    junos@MX# set security macsec interfaces <MACsec interface name> connectivity-association <user defined connectivity name>
    ```
    
5. Commit the configuration, commit script would auto-complete the key-exchange for you.
    
    ```
    junos@MX# commit
    ```
    
Architecture:
-------------
![Alt text](./docs/MACsec_Architecture.png "Architectural Diagram")


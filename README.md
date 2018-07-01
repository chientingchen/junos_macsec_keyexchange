# Problem Statement
* MACsec is one of the encryption function which can be performed by Juniper networking devices. However, it would require operators to manually copy pre-shared key between devices, which can leads to *manually configuration mistake or long workings hours*.
As a result, this tool is trying to making operator's life easiser by **automatically generate and deploy the MACsec pre-shared key** in a well controlled network environment.

# Architecture
<a name="archi"></a>
![Alt text](./docs/MACsec_Architecture.png "Architectural Diagram")

# Design Considerations

### Why not netconf?
* This tool was design for minimize the user input, including device login credentials, as a result this tool is using local script to perform configuration deployment, instead of use netconf for deploy pre-shared key pairs remotely.

### Why there's no HTTPS?
* For current release, this tool doesn't support HTTPS connections for trasmitting CKN/CAK data since it would require user to generate self-signed certificate for each environment. However, if user have a good feedback on this very first version of pre-shared key exchanging tool, HTTPS is definitely one of the most important feature to add on.

# FAQ

### DO I need to configure the same connectivity-association name in neighbored juniper devices?
* connectivity-association name in Junos is just locally refereneced, it won't affect MACsec connection estabilished if the names are different in neighbored devices.
  As a result, user can feel free to edit any meaningful name for them on each junos device.
  <br/> e.g. 
    
    ```
    connectivity-association ANY_MEANINGFUL_NAME {
        security-mode static-cak;
        pre-shared-key {
            ckn 10bcd3519acf9b53a58072fb30ff3cc3c8eaf35e5644c2a91e7e091a0777b8a0;
            cak "$9$wmYJGP5Q6/tf56A0BEhylKWLNY2aZDievX-dboa/CAu0IcylKWLz3lKvWx7VwYgoGkqfQ36iHp0BIrlLxNbwgik.F694a"; ## SECRET-DATA
        }
    }
    interfaces {
        ge-0/2/1 {
            connectivity-association ANY_MEANINGFUL_NAME;
        }
    }
    ```

### Is the default MACsec configuration different from each Junos user?
* Not at all, MACsec configuration are shared among all users of Junos

# User Guide

## Requirement: 
### Minimum requirements

* 2 juniper devices which supporting [MACsec functionality](https://apps.juniper.net/feature-explorer/search.html#q=MACsec)
* Management network connectivities among all devices

### For remote central server installation:
* 1 Linux server which has ability to executing python.
* Management network connectivity among devices and server
 
## Tested environment

* Device model: MX480
* Junos Version: JUNOS 17.3R1.10
* Line card model: MIC-3D-20GE-SFP-E

## Introduction:

* As **[architecture diagram](#archi)** shown, this tool would have a script(`remote_master.py`) running as a server and the other script(`local_minion.py`) running as a client.

* **Module `remote_master.py`:**
    * It's allow to running on linux server or juniper device.
    * it's designed as central storage of all MACsec pre-shared keys.

* **Module `local_minion.py`:**
    * It's only allow to execute on top of juniper device
    * it's designed for deploy MACsec keys to local device. For any device which require automatic MACsec key exchange would have to equipped with this script.

* **Execution mode:**
    * **[On-box mode](#onbox-installation):**
        * In this mode, `remote_server.py` would running on top of juniper device, in other words, one of the juniper device in user's environemnt would acting as a server 
        * In the same time, `local_minion.py` would also executing on all the juniper devices(including the same one acting as a server.) in user's environment.

    * **[Off-box mode](#offbox-installation):**
        * In this mode, `remote_server.py` would running on top of any linux server in user's environment, as a central storage.
        * In the same time, `local_minion.py` would execute on all the juniper devices in user's environment.

## Installation:

### Installer:
* `Installer.py` provided automatically deployment of **On-box mode**, it's recommend for user who target on use it with On-box mode can leverage this installer to deploy MACsec exchanger.

0. Download all files within this repository to `/var/db/scripts/op` on the juniper device which is going to acting as server.
1. Edit `devices.yaml`, fill in the master and minion information as below:
    
    ```
    master:
      - host_IP: 172.27.169.122
        usr: root
        pwd: lab123
        port: 8888
        
    minion:
      - host_IP: 172.27.170.123
        usr: root
        pwd: lab123
        
      - host_IP: 172.27.170.124
        usr: root
        pwd: lab123
    ```
    * `host_IP` is the field which indicate device IP address
    * `usr` is the field which indicate what user account can be used to deploy this tool
    * `pwd` is the field which indicate the password of deployment user account
    * `port` is the field which indicate which port would be used at the juniper device which is going to acting as server.
    
2. Enter the configuration mode of master junos device, set up configuration as below:
    
    ```
    junos@MX480# set system scripts language python
    junos@MX480# set system scripts op file installer.py
    junos@MX480# commit
    ```
    
3. Enter the operation mode of master junos device, execute installer.py

    ```
    junos@MX480> op installer.py
    ```
4. You shall see the following output, and this tool is already up/running at user's environment.


<a name="onbox-installation"></a>    
### On-box mode:

0. Download folder `MACsec_master_dependencies` to `/var/db/scripts/jet` on the juniper device which is going to acting as server.
1. Download `remote_master.py`, `master_environment.yaml` to `/var/db/scripts/jet` on the juniper device which is going to acting as server.
2. Download folder `MACsec_minion_dependencies` to `/var/db/scripts/commit` on all juniper device.
3. Download `local_minion.py` and `minion_environment.yaml` to `/var/db/scripts/commit` on all juniper device.
4. Download `delete_MACsec_interface.py` to `/var/db/scripts/op` on all juniper devices
5. Editing `master_envionment.yaml`:
    
    ```
    MACSEC:
      INCLUDE_PATH: "/var/db/scripts/op/MACsec_master_dependencies"
      LOCAL_DB_FILE_PATH: "/var/db/scripts/op/MLS_data.pdl"
      LOG_PATH: "/var/db/scripts/op/AutoMACsec.log"
      DEBUG: TRUE

    Production:
      SERVER_PORT: "8888"
    ```
    * `INCLUDE_PATH` is the field which indicate where the `MACsec_master_dependencies` located
    * `LOCAL_DB_FILE_PATH` is the field which indicate where should database file located
    * `LOG_PATH` is the field which indicate where should log being stored at.
    * `DEBUG` is the field which indicate LOG debug level, only `TRUE` or `FALSE` are options here.
    * `SERVER_PORT` is the port which allow `remote_master.py` to accept/response HTTP requests.
    
6. Editing `minion_environment.yaml`:
    
    ```
    MACSEC:
      INCLUDE_PATH: "/var/db/scripts/commit/MACsec_minion_dependencies"
      LOG_PATH: "/var/db/scripts/commit/AutoMACsec.log"  
      DEBUG: TRUE
    
    Production:
      SERVER_IP: "172.27.169.122"
      SERVER_PORT: "8888"
    ```
    * `INCLUDE_PATH` is the field which indicate where the `MACsec_minion_dependencies` located
    * `LOG_PATH` is the field which indicate where should log being stored at.
    * `DEBUG` is the field which indicate LOG debug level, only `TRUE` or `FALSE` are options here.
    * `SERVER_IP` is IP address of the device which `remote_master.py` would running at.
    * `SERVER_PORT` is the port which allow `remote_master.py` to accept/response HTTP requests.

7. Deploy base config `BaseConfigs/OnBox/Onbox_remote_master_Basic.conf` to juniper device which acting as sever.
8. Deploy base config `BaseConfigs/OnBox/Onbox_local_minion_Basic.conf` to all juniper devices.

<a name="offbox-installation"></a>    
### Off-box mode:

0. Create a folder `MACsec_remote_master` on linux server
1. Download folder `MACsec_master_dependencies` to folder `MACsec_remote_master` on linux server
2. Download `remote_master.py` and `master_environment.yaml` to folder `MACsec_remote_master` on linux server
3. Download folder `MACsec_minion_dependencies` to `/var/db/scripts/commit` on all juniper devices
4. Download `local_minion.py`, `minion_environment.yaml` to `/var/db/scripts/commit` on all juniper devices
5. Download `delete_MACsec_interface.py` to `/var/db/scripts/op` on all juniper devices 
6. Editing `master_envionment.yaml`:
    
    ```
    MACSEC:
      INCLUDE_PATH: "/home/lab/MACsec/MACsec_master_dependencies"
      LOCAL_DB_FILE_PATH: "/home/lab/MACsec/MLS_data.pdl"
      LOG_PATH: "/home/lab/MACsec/AutoMACsec.log"  
      DEBUG: TRUE

    Production:
      SERVER_PORT: "8888"
    ```
    
    * `INCLUDE_PATH` is the field which indicate where the `MACsec_master_dependencies` located
    * `LOCAL_DB_FILE_PATH` is the field which indicate where should database file located
    * `LOG_PATH` is the field which indicate where should log being stored at.
    * `DEBUG` is the field which indicate LOG debug level, only `TRUE` or `FALSE` are options here.
    * `SERVER_IP` is IP address of the device which `remote_master.py` would running at.
    * `SERVER_PORT` is the port which allow `remote_master.py` to accept/response HTTP requests.
    
7. Editing `minion_environment.yaml`:

    ```
    MACSEC:
      INCLUDE_PATH: "/var/db/scripts/commit/MACsec_minion_dependencies"
      LOG_PATH: "/var/db/scripts/commit/AutoMACsec.log"  
      DEBUG: TRUE
    
    Production:
      SERVER_IP: "172.27.169.122"
      SERVER_PORT: "8888"
    ```
    * `INCLUDE_PATH` is the field which indicate where the `MACsec_minion_dependencies` located
    * `LOG_PATH` is the field which indicate where should log being stored at.
    * `DEBUG` is the field which indicate LOG debug level, only `TRUE` or `FALSE` are options here.
    * `SERVER_IP` is IP address of the device which `remote_master.py` would running at.
    * `SERVER_PORT` is the port which allow `remote_master.py` to accept/response HTTP requests.
    
8. Deploy base config `BaseConfigs/OffBox/Offbox_local_minion_Basic.conf` to all juniper devices.

## Usage:

### On-box mode:

#### Remote master:
1. If base config `BaseConfigs/OnBox/Onbox_remote_master_Basic.conf` is deployed successfully, `remote_master.py` would be up and running immediately when configuration is deployed. 
2. Please check `remote_master.py` status by following junos command, if there's nothing shown at the output, please refer to debug log for troubleshooting.

    ```
    root@MX480-X1> show extension-service status remote_master.py
    Extension service application details:
    Name : remote_master
    Process-id: 75157
    Stack-Segment-Size: 16777216B
    Data-Segment-Size: 134217728B
    ```
    
3. For troubleshooting, user can manually start `remote_master.py` by following junos command.

    ```
    root@MX480-X1> request extension-service start remote_master.py
    Extension-service application 'remote_master.py' started with PID: 75157
     * Serving Flask app "remote_master" (lazy loading)
     * Environment: production
       WARNING: Do not use the development server in a production environment.
       Use a production WSGI server instead.
     * Debug mode: off
     * Running on http://0.0.0.0:8888/ (Press CTRL+C to quit)
    ```
    * **Note that manually starting `remote_master.py` is only recommend for troubleshooting.**
    
#### Local minion:
1. ssh to junos cli at each juniper device which `local_minion.py` located.
2. Edit macsec configuration as usual, but user doesn't have to configure pre-shared key.

    ```
    junos@MX# set security macsec interfaces <MACsec interface name> connectivity-association <user defined connectivity name>
    ```
    * Please make sure LLDP is up and running at all juniper devices and cabling are done correctly before commit.

3. Commit the configuration, `local_minion.py` would complete the configuration for you.

    ```
    junos@MX# commit
    ```
4. The output below should appear, which indicates key is automatically generated and deployed.
<br><br/>
![Alt text](./docs/local_minion_commit.png "Local minion console commit screenshot")
<br><br/>

### Off-box mode:

#### Remote master:
1. ssh to linux server cli (Ubuntu 14.04 cli is shown here as example).
2. Go to the file path which `remote_master.py` located
3. Executing script `remote_master.py`
```
root@Ubuntu:~/python remote_master.py
```
3. The following message should show up, please leave the session here alive.
<br><br/>
![Alt text](./docs/remote_master_console.png "Remote master console screenshot")
<br><br/>
    * If user don't prefer to keep session terminal at all time, please take advantage on `screen` linux command.

#### Local minion:
1. ssh to junos cli at each juniper device which `local_minion.py` located.
2. Edit macsec configuration as usual, but user doesn't have to configure pre-shared key.

    ```
    junos@MX# set security macsec interfaces <MACsec interface name> connectivity-association <user defined connectivity name>
    ```
    * Please make sure LLDP is up and running at all juniper devices and cabling are done correctly before commit.

3. Commit the configuration, `local_minion.py` would complete the configuration for you.

    ```
    junos@MX# commit
    ```
4. The output below should appear, which indicates key is automatically generated and deployed.
<br><br/>
![Alt text](./docs/local_minion_commit.png "Local minion console commit screenshot")
<br><br/>

### Monitoring pre-shared key pair at web page.
* You can always check `http://<remote_server_ip>:<port>` for current connection pre-shared key.

![Alt text](./docs/Pre-shared_key_table.png "Screen shot of pre-shared key table")

### Re-gen pre-shared key due to link issue (Wrong Cabling):
1. Ensure the device cabling is fixed.
2. Log into the device(s) which has new connection(s)
3. Execute op script `delete_MACsec_interface.py` for deleting specific interface pre-shared key

    ```
    junos@MX> op delete_MACsec_interface.py ChassisID <Device ChassisID> Interface <Device interface name>
    ```
4. Following output should appear to indicate delete action is done.
![Alt text](./docs/delete_output.png "delete_MACsec_interface output screenshot")

5. Delete orginal wrong MACsec configuration on specific interface
    
    ```
    junos@MX# delete security macsec interfaces <MACsec interface name>
    ```
    
6. Once again, edit macsec configuration as usual, don't have to configure pre-shared key.

    ```
    junos@MX# set security macsec interfaces <MACsec interface name> connectivity-association <user defined connectivity name>
    ```
    
7. Commit the configuration, commit script would auto-complete the key-exchange for you.
    
    ```
    junos@MX# commit
    ```

8. The output below should appear, which indicates key is automatically generated and deployed.
<br><br/>
![Alt text](./docs/local_minion_commit.png "Local minion console commit screenshot")
<br><br/>


import yaml
import paramiko
import sys
import os
from scp.scp import SCPClient
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import ConnectError
from jnpr.junos.exception import LockError
from jnpr.junos.exception import UnlockError
from jnpr.junos.exception import ConfigLoadError
from jnpr.junos.exception import CommitError
from jnpr.junos.utils.start_shell import StartShell
from shutil import copytree, rmtree, copyfile

def configure_env(file, SERVER_IP, SERVER_PORT):
    print ("Configuring "+file)
    try:
        f = open(file,'r')
        config = yaml.load(f)
        f.close()
        if SERVER_IP == 'localhost':
            config['Production']['SERVER_IP'] = '172.27.169.122'
        else:
            config['Production']['SERVER_IP'] = SERVER_IP
        config['Production']['SERVER_PORT'] = SERVER_PORT
        config = yaml.dump(config, default_flow_style=False)

        f = open(file,'w')
        f.write(config)
        f.close()
    except Exception as err:
        print (err)
        return

def cpdir(src, dest):
    try:
        if os.path.exists(dest):
            rmtree(dest)
            copytree(src, dest)
        else:
            copytree(src, dest)
    except Exception as err:
        print (err)
        return

def download_files_to_master(host,usr,pwd):
    if host == 'localhost':
        print('copying MACsec_master_dependencies to /var/db/scripts/jet/MACsec_master_dependencies...')
        cpdir('MACsec_master_dependencies','/var/db/scripts/jet/MACsec_master_dependencies')
        print('copying remote_master.py to /var/db/scripts/jet/...')
        copyfile('remote_master.py','/var/db/scripts/jet/remote_master.py')
        print('copying master_environment.yaml to /var/db/scripts/jet/...')
        copyfile('master_environment.yaml','/var/db/scripts/jet/master_environment.yaml')

        print('copying MACsec_minion_dependencies to /var/db/scripts/commit/...')
        cpdir('MACsec_minion_dependencies','/var/db/scripts/commit/MACsec_minion_dependencies')
        print('copying local_minion.py to /var/db/scripts/commit/...')
        copyfile('local_minion.py','/var/db/scripts/commit/local_minion.py')
        print('minion_environment.yaml to /var/db/scripts/commit/...')
        copyfile('minion_environment.yaml','/var/db/scripts/commit/minion_environment.yaml')
    else:
        ssh = paramiko.SSHClient()
        try:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=usr, password=pwd)
            scp = SCPClient(ssh.get_transport(), progress = progress)

            scp.put('MACsec_master_dependencies', recursive=True, remote_path="/var/db/scripts/op")
            scp.put('MACsec_master_dependencies', recursive=True, remote_path="/var/db/scripts/jet")
            # scp.put('MACsec_master_dependencies.tgz', remote_path="/var/db/scripts/op")
            # scp.put('MACsec_master_dependencies.tgz', remote_path="/var/db/scripts/jet")
            scp.put('remote_master.py', remote_path="/var/db/scripts/op")
            scp.put('remote_master.py', remote_path="/var/db/scripts/jet")
            scp.put('master_environment.yaml', remote_path="/var/db/scripts/op")
            scp.put('master_environment.yaml', remote_path="/var/db/scripts/jet")

            scp.put('MACsec_minion_dependencies', recursive=True, remote_path="/var/db/scripts/commit")
            # scp.put('MACsec_minion_dependencies.tgz', remote_path="/var/db/scripts/commit")
            scp.put('local_minion.py', remote_path="/var/db/scripts/commit")
            scp.put('minion_environment.yaml', remote_path="/var/db/scripts/commit")
            scp.put('delete_MACsec_interface.py', remote_path="/var/db/scripts/op")

            # scp.close()
            # ssh.exec_command("cd /var/db/scripts/op; tar -xzf /var/db/scripts/op/MACsec_master_dependencies.tgz")
            # ssh.exec_command("cd /var/db/scripts/op; rm *.tgz")
            # ssh.exec_command("cd /var/db/scripts/jet; tar -xzf /var/db/scripts/jet/MACsec_master_dependencies.tgz")
            # ssh.exec_command("cd /var/db/scripts/jet; rm *.tgz")

            # ssh.exec_command("cd /var/db/scripts/commit; tar -xzf /var/db/scripts/commit/MACsec_minion_dependencies.tgz")
            # ssh.exec_command("cd /var/db/scripts/commit; rm *.tgz")

            ssh.close()
        except Exception as err:
            print (err)
            return
        else:
            ssh.close()


def download_files_to_minion(host,usr,pwd):
    ssh = paramiko.SSHClient()
    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=usr, password=pwd)
        scp = SCPClient(ssh.get_transport(), progress = progress)

        scp.put('MACsec_minion_dependencies', recursive=True, remote_path="/var/db/scripts/commit")
        # scp.put('MACsec_minion_dependencies.tgz', remote_path="/var/db/scripts/commit")
        scp.put('local_minion.py', remote_path="/var/db/scripts/commit")
        scp.put('minion_environment.yaml', remote_path="/var/db/scripts/commit")
        scp.put('delete_MACsec_interface.py', remote_path="/var/db/scripts/op")

        # scp.close()
        # ssh.exec_command("cd /var/db/scripts/commit; tar -xzf /var/db/scripts/commit/MACsec_minion_dependencies.tgz")
        # ssh.exec_command("cd /var/db/scripts/commit; rm *.tgz")

        ssh.close()
    except Exception as err:
        print (err)
        return
    else:
        ssh.close()

def progress(filename, size, sent):
    sys.stdout.write("%s\'s progress: %.2f%% \r" % (filename, float(sent)/float(size)*100) )

def download_files(Master,Minion):
    for master in Master:
        download_files_to_master(master['host'],master['usr'], master['pwd'])
    for minion in Minion:
        download_files_to_minion(minion['host'],minion['usr'], minion['pwd'])
    return

def load_merge_config(Deivces,config_file):
    for deivce in Deivces:
        try:
            dev = Device(host=deivce['host'], user=deivce['usr'], passwd=deivce['pwd'])
            dev.open()
        except ConnectError as err:
            print (deivce['host']+":Cannot connect to device: {0}".format(err))
            return
        dev.bind(cu=Config)

        print (deivce['host']+":Locking the configuration")
        try:
            dev.cu.lock()
        except LockError as err:
            print (deivce['host']+":Unable to lock configuration: {0}".format(err))
            dev.close()
            return

        print (deivce['host']+"::Loading configuration changes")
        try:
            dev.cu.load(path=config_file, merge=True)
        except (ConfigLoadError, Exception) as err:
            print (deivce['host']+":Unable to load configuration changes: {0}".format(err))
            print (deivce['host']+":Unlocking the configuration")
            try:
                dev.cu.unlock()
            except UnlockError:
                print (deivce['host']+":Unable to unlock configuration: {0}".format(err))
            dev.close()
            return

        print (deivce['host']+":Committing the configuration")
        try:
            dev.cu.commit()
        except CommitError as err:
            print (deivce['host']+":Unable to commit configuration: {0}".format(err))
            print (deivce['host']+":Unlocking the configuration")
            try:
                dev.cu.unlock()
            except UnlockError as err:
                print (deivce['host']+":Unable to unlock configuration: {0}".format(err))
            dev.close()
            return

        print (deivce['host']+":Unlocking the configuration")
        try:
            dev.cu.unlock()
        except UnlockError as err:
            print (deivce['host']+":Unable to unlock configuration: {0}".format(err))
        dev.close()
    return

def init_master(devices):
    print('init master...')
    if 'master' in devices and devices['master']:

        if type(devices['master']) == list:
            if 'host' not in devices['master'][0]:
                devices['master'][0]['host']='localhost'
            if 'usr' not in devices['master'][0]:
                devices['master'][0]['usr']=None
            if 'pwd' not in devices['master'][0]:
                devices['master'][0]['pwd']=None
            if 'port' not in devices['master'][0]:
                devices['master'][0]['port']=8888
            return devices
        else:
            print('master should be a list')
            return -1

    else:
        devices['master']=[]
        devices['master'].append({})
        devices['master'][0]['host']='localhost'
        devices['master'][0]['usr']=None
        devices['master'][0]['pwd']=None
        devices['master'][0]['port']=8888
        return devices

def main():
    conf_file_master = 'BaseConfigs/OnBox/Onbox_remote_master_Basic.conf'
    conf_file_minion = 'BaseConfigs/OnBox/Onbox_local_minion_Basic.conf'
    daemonize_app = 'BaseConfigs/OnBox/daemonize_app.conf'

    f = open("devices.yaml")
    devices = yaml.safe_load(f)
    devices = init_master(devices)
    print devices
    if devices:
        print('start deploying...')
        configure_env('master_environment.yaml',devices['master'][0]['host'],devices['master'][0]['port'])
        configure_env('minion_environment.yaml',devices['master'][0]['host'],devices['master'][0]['port'])
        download_files(devices['master'],devices['minion'])
        load_merge_config(devices['master'],conf_file_master)
        load_merge_config(devices['minion'],conf_file_minion)
        load_merge_config(devices['master'],daemonize_app)
    return
if __name__ == "__main__":
    main()


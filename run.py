#!/usr/bin/python3
import configparser
import os

outDir = 'output'
envfile = 'env.ini'
dockerfile_base = 'Dockerfile-base.template'
copyFile = ['check.sql']

config = configparser.ConfigParser()
config.read(envfile)
cluster_type = config['CLUSTER']['TYPE']

def genDockerfile():
    cmdStr = ['sed']
    for k, v in config['DockerfileBase'].items():
        k = '$' + k.upper()
        cmdStr.append('-e s@\%s@%s@g' % (k, v))
    cmdStr.append(dockerfile_base)
    cmdStr.append('> %s/Dockerfile' % (outDir))
    os.system(' '.join(cmdStr))

def genDockerComposeFile():
    filepath = os.path.join(outDir, 'docker-compose.yaml')
    with open (filepath, 'w') as f:
        tmpStr = []
        tmpStr.append("version: '3'")
        tmpStr.append("networks:")
        networkName = config['DockerfileBase']['PGUSER']
        tmpStr.append("  %s:" % (networkName))
        tmpStr.append("    driver: bridge")
        tmpStr.append("services:")
        
        tmpStr.append("  %s:" % ("gtmmaster1"))
        tmpStr.append("    build:")
        tmpStr.append("      context: .")
        tmpStr.append("      dockerfile: Dockerfile")
        tmpStr.append("    volumes:")
        for file in copyFile:
            tmpStr.append('''      - "./%s:/%s"''' % (file, file))
            
        if config[cluster_type]['GTM_SLAVE'] == 'y':
            tmpStr.append("  %s:" % ('gtmslave1'))
            tmpStr.append("    build:")
            tmpStr.append("      context: .")
            tmpStr.append("      dockerfile: Dockerfile")            
  
        keyList = ['CN_MASTER', 'DN_MASTER']
        for key in keyList:
            for num in range(1, int(config[cluster_type][key]) + 1):
                tmpName = key.replace('_', '').lower() + str(num)
                tmpStr.append("  %s:" % (tmpName))
                tmpStr.append("    build:")
                tmpStr.append("      context: .")
                tmpStr.append("      dockerfile: Dockerfile")
                
                slaveMode = key.replace('MASTER', 'SLAVE')
                if config[cluster_type][slaveMode] == 'y':
                    tmpName = key.replace('MASTER', 'SLAVE').replace('_', '').lower() + str(num)
                    tmpStr.append("  %s:" % (tmpName))
                    tmpStr.append("    build:")
                    tmpStr.append("      context: .")
                    tmpStr.append("      dockerfile: Dockerfile")                

        f.writelines("\n".join(tmpStr))
       
def genPgxcConf():
    filepath = os.path.join(outDir, 'pgxc_ctl.conf')
    with open(filepath, 'w') as f:
        cn_num = config[cluster_type]['CN_MASTER']
        dn_num = config[cluster_type]['DN_MASTER']
            
        tmpstr = []
        tmpstr.append('#!/usr/bin/env bash')
        tmpstr.append('pgxcInstallDir=$HOME/pgxc')
        tmpstr.append('#---- OVERALL -----------------------------------------------')
        tmpstr.append('pgxcOwner=$USER')
        tmpstr.append('pgxcUser=$pgxcOwner')
        tmpstr.append('tmpDir=/tmp')
        tmpstr.append('localTmpDir=$tmpDir')
        tmpstr.append('configBackup=n')
        tmpstr.append('configBackupHost=pgxc-linker')	
        tmpstr.append('configBackupDir=$HOME/pgxc')		
        tmpstr.append('configBackupFile=pgxc_ctl.bak')	
        tmpstr.append('dataDirRoot=$HOME/DATA/pgxl/nodes')

        tmpstr.append('\n\n#---- GTM -----------------------------------------------')
        tmpstr.append('\n#---- Overall -------')
        tmpstr.append('gtmName=(gtmmaster1)')
        tmpstr.append('\n#---- GTM Master -----------------------------------------------')
        tmpstr.append('\n#---- Overall -------')
        tmpstr.append('gtmMasterServer=(gtmmaster1)')
        tmpstr.append('gtmMasterPort=(%s)' % (config[cluster_type]['GTM_PORT']))
        tmpstr.append('gtmMasterDir=($pgxcInstallDir/gtmmaster1)')
        tmpstr.append('\n#---- Configuration ---')
        tmpstr.append('gtmExtraConfig=()')
        tmpstr.append('gtmMasterSpecificExtraConfig=()')

        tmpstr.append('\n\n#---- GTM Standby -----------------------------------------------')
        if config[cluster_type]['GTM_SLAVE'] == 'y':
            tmpstr.append('\n#---- Overall ------')
            tmpstr.append('gtmSlave=y')
            tmpstr.append('gtmSlaveName=(gtmslave1)')
            tmpstr.append('gtmSlaveServer=(gtmslave1)')
            tmpstr.append('gtmSlavePort=(%s)' % (config[cluster_type]['GTM_PORT']))
            tmpstr.append('gtmSlaveDir=($pgxcInstallDir/gtmslave1)')
            tmpstr.append('\n#---- Configuration ----')
            tmpstr.append('gtmSlaveSpecificExtraConfig=()')
        else:
            tmpstr.append('gtmSlave=n')

        tmpstr.append('\n\n#---- GTM Proxy ---------------')
        if config[cluster_type]['GTM_PROXY'] == 'y':
            tmpstr.append('\n#---- Overall ------')
            tmpstr.append('gtmProxy=y')
            gtm_proxy_name = ' '.join(['gtmproxy' + str(num) for num in range(1, int(cn_num) + 1)])
            tmpstr.append('gtmProxyNames=(%s)' % (gtm_proxy_name))
            cn_master_name = ' '.join(['cnmaster' + str(num) for num in range(1, int(cn_num) + 1)])
            tmpstr.append('gtmProxyServers=(%s)' % (cn_master_name))
            gtm_proxy_port = ' '.join([str(int(config[cluster_type]['GTM_PORT']) + 1) for num in range(1, int(cn_num) + 1)])
            tmpstr.append('gtmProxyPorts=(%s)' % (gtm_proxy_port))
            tmpstr.append('gtmProxyDir=$pgxcInstallDir/gtmproxy')
            gtm_proxy_dir = ' '.join(['$gtmProxyDir' for num in range(1, int(cn_num) + 1)])
            tmpstr.append('gtmProxyDirs=(%s)' % (gtm_proxy_dir))
            tmpstr.append('\n#---- Configuration ----')
            tmpstr.append('gtmPxyExtraConfig=()')        
        else:
            tmpstr.append('gtmProxy=n')
           
        tmpstr.append('\n\n#---- Coordinators -----------------------------------------------')
        tmpstr.append('\n#---- shortcuts ----------')
        tmpstr.append('coordMasterDir=$dataDirRoot/coord_master')
        tmpstr.append('coordSlaveDir=$HOME/coord_slave')
        tmpstr.append('coordArchLogDir=$HOME/coord_archlog')
        tmpstr.append('\n#---- Overall ------------')
        
        cn_master_name = ' '.join(['cnmaster' + str(num) for num in range(1, int(cn_num) + 1)])
        tmpstr.append('coordNames=(%s)' % (cn_master_name))
        cn_port = ' '.join([config[cluster_type]['CN_PORT'] for num in range(1, int(cn_num) + 1)])
        tmpstr.append('coordPorts=(%s)' % (cn_port))
        pool_port = ' '.join([str(int(config[cluster_type]['CN_PORT']) + 1) for num in range(1, int(cn_num) + 1)])
        tmpstr.append('poolerPorts=(%s)' % (pool_port))
        tmpstr.append('coordPgHbaEntries=(0.0.0.0/0)')
        
        tmpstr.append('\n#---- Master -------------')
        tmpstr.append('coordMasterServers=(%s)' % (cn_master_name))
        cn_master_dir = ' '.join(['$coordMasterDir' for num in range(1, int(cn_num) + 1)])
        tmpstr.append('coordMasterDirs=(%s)' % (cn_master_dir))
        tmpstr.append('coordMaxWALsender=%s' % (str(int(cn_num) + int(dn_num))))
        cn_max_wal_sender = ' '.join(['$coordMaxWALsender' for num in range(1, int(cn_num) + 1)])
        tmpstr.append('coordMaxWALSenders=(%s)' % (cn_max_wal_sender))

        tmpstr.append('\n\n#---- Slave -------------')
        if config[cluster_type]['CN_SLAVE'] == 'y':
            tmpstr.append('coordSlave=y')
            tmpstr.append('coordSlaveSync=y')
            tmpstr.append('coordUserDefinedBackupSettings=n')
            cn_slave_name = ' '.join(['cnslave' + str(num) for num in range(1, int(cn_num) + 1)])
            tmpstr.append('coordSlaveServers=(%s)' % (cn_slave_name))
            tmpstr.append('coordSlavePorts=(%s)' % (cn_port))
            tmpstr.append('coordSlavePoolerPorts=(%s)' % (pool_port))
            cn_slave_dir = ' '.join(['$coordSlaveDir' for num in range(1, int(cn_num) + 1)])
            tmpstr.append('coordSlaveDirs=(%s)' % (cn_slave_dir))
            cn_arch_dir = ' '.join(['$coordArchLogDir' for num in range(1, int(cn_num) + 1)])
            tmpstr.append('coordArchLogDirs=(%s)' % (cn_arch_dir))
        else:
            tmpstr.append('coordSlave=n')
   
        tmpstr.append('\n\n#---- Configuration files---')
        tmpstr.append('coordExtraConfig=coordExtraConfig')
        tmpstr.append('cat > $coordExtraConfig <<EOF')
        tmpstr.append('log_destination = \'stderr\'')
        tmpstr.append('logging_collector = on')
        tmpstr.append('log_directory = \'pg_log\'')
        tmpstr.append('listen_addresses = \'*\'')
        tmpstr.append('max_connections = 100')
        tmpstr.append('hot_standby = off')
        tmpstr.append('EOF')
        tmpstr.append('coordSpecificExtraConfig=()')
        tmpstr.append('coordSpecificExtraPgHba=()')
        
        tmpstr.append('\n\n#---- Datanodes -----------------------------------------------')
        tmpstr.append('\n#---- Shortcuts --------------')
        tmpstr.append('datanodeMasterDir=$dataDirRoot/dn_master')
        tmpstr.append('datanodeSlaveDir=$dataDirRoot/dn_slave')
        tmpstr.append('datanodeArchLogDir=$dataDirRoot/datanode_archlog')
        
        tmpstr.append('\n\n#---- Overall ---------------')
        tmpstr.append('primaryDatanode=dn1')
        dn_master = ' '.join(['dnmaster' + str(num) for num in range(1, int(dn_num) + 1)])
        dn_port = ' '.join([config[cluster_type]['DN_PORT'] for num in range(1, int(dn_num) + 1)])
        dn_pool_port = ' '.join([str(int(config[cluster_type]['DN_PORT']) + 1) for num in range(1, int(dn_num) + 1)])
        tmpstr.append('datanodeNames=(%s)' % (dn_master))
        tmpstr.append('datanodePorts=(%s)' % (dn_port))
        tmpstr.append('datanodePoolerPorts=(%s)' % (dn_pool_port))
        tmpstr.append('datanodePgHbaEntries=(0.0.0.0/0)')
        
        tmpstr.append('\n\n#---- Master ----------------')
        tmpstr.append('datanodeMasterServers=(%s)' % (dn_master))
        dn_master_dir = ' '.join(['$datanodeMasterDir' for num in range(1, int(dn_num) + 1)])
        tmpstr.append('datanodeMasterDirs=(%s)' % (dn_master_dir))
        tmpstr.append('datanodeMaxWalSender=%s' % (str(int(cn_num) + int(dn_num))))
        dn_max_wal_sender = ' '.join(['$datanodeMaxWalSender' for num in range(1, int(dn_num) + 1)])
        tmpstr.append('datanodeMaxWALSenders=(%s)' % (dn_max_wal_sender))

        tmpstr.append('\n\n#---- Slave -------------')
        if config[cluster_type]['DN_SLAVE'] == 'y':
            tmpstr.append('datanodeSlave=y')
            tmpstr.append('datanodeSlaveSync=y')
            tmpstr.append('datanodeUserDefinedBackupSettings=n')
            dn_slave = ' '.join(['dnslave' + str(num) for num in range(1, int(dn_num) + 1)])
            tmpstr.append('datanodeSlaveServers=(%s)' % (dn_slave))
            tmpstr.append('datanodeSlavePorts=(%s)' % (dn_port))
            tmpstr.append('datanodeSlavePoolerPorts=(%s)' % (dn_pool_port))
            dn_slave_dir = ' '.join(['$datanodeSlaveDir' for num in range(1, int(dn_num) + 1)])
            tmpstr.append('datanodeSlaveDirs=(%s)' % (dn_slave_dir))
            dn_arch_dir = ' '.join(['$datanodeArchLogDir' for num in range(1, int(dn_num) + 1)])
            tmpstr.append('datanodeArchLogDirs=(%s)' % (dn_arch_dir))
        else:
            tmpstr.append('datanodeSlave=n')
        
        tmpstr.append('# ---- Configuration files ---')
        tmpstr.append('datanodeExtraConfig=datanodeExtraConfig	')
        tmpstr.append('cat > $datanodeExtraConfig <<EOF')
        tmpstr.append('log_destination = \'stderr\'')
        tmpstr.append('logging_collector = on')
        tmpstr.append('log_directory = \'pg_log\'')
        tmpstr.append('listen_addresses = \'*\'')
        tmpstr.append('max_connections = 100')
        tmpstr.append('hot_standby = off')
        tmpstr.append('EOF')
        tmpstr.append('datanodeSpecificExtraConfig=()')
        tmpstr.append('datanodeSpecificExtraPgHba=()')

        f.writelines("\n".join(tmpstr))

def startCluster():
    pass


if not os.path.exists(outDir):
    os.mkdir(outDir)
for file in copyFile:
    cmdStr = 'cp ./%s %s' % (file, os.path.join(outDir, file))
    os.system(cmdStr)

genDockerfile()
genDockerComposeFile()
genPgxcConf()

# ## 启动docker-compose
# cmd_str = 'cd output && docker-compose up -d'
# os.system(cmd_str)


### 
### docker exec -it output_gtm1_1 bash
### su - pgxc
### pgxc_ctl -c /pgxc_ctl.conf init all
### psql -h cn1 -p 5555 -U pgxc -d postgres -f /check.sql

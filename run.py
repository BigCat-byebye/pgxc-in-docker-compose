#!/usr/bin/python3
import configparser
import os

if not os.path.exists('output'):
    os.mkdir('output')

config = configparser.ConfigParser()
config.read('env.ini')

sed_str = ['sed']
for key in config['DockerfileBase']:
    key = key.upper()
    value = config['DockerfileBase'][key]
    sed_str.append('-e s@\%s@%s@g' % ('$' + key, value))
sed_str.append('Dockerfile-base.template > output/Dockerfile')
sed_str = ' '.join(sed_str)

os.system(sed_str)

# 构建docker-compose.yaml
def generate_compose_yaml(config: dict, session_name: str):
    with open('output/docker-compose.yaml', 'w') as f:
        tmpstr = []
        tmpstr.append("version: '3'")
        tmpstr.append("networks:")
        tmpstr.append("  pgxc:")
        tmpstr.append("    driver: bridge")
        tmpstr.append("services:")
        

        tmpstr.append("  %s:" % ("gtm1"))
        tmpstr.append("    build:")
        tmpstr.append("      context: .")
        tmpstr.append("      dockerfile: Dockerfile")
        tmpstr.append("    volumes:")
        tmpstr.append('''      - "%s/output/pgxc_ctl.conf:/pgxc_ctl.conf"''' % (os.getcwd()))
        tmpstr.append('''      - "%s/output/check.sql:/check.sql"''' % (os.getcwd()))
        
        if config[session_name]['GTM_SLAVE'] == 'y':
            for num in range(1, int(config[session_name]['GTM_MASTER']) + 1):
                tmpstr.append("  %s:" % ("gtmslave" + str(num)))
                tmpstr.append("    build:")
                tmpstr.append("      context: .")
                tmpstr.append("      dockerfile: Dockerfile")
        
        # 暂时不判断gtm proxy

        for num in range(1, int(config[session_name]['CN_MASTER']) + 1):
            name = "cn" + str(num)
            tmpstr.append("  %s:" % (name))
            tmpstr.append("    build:")
            tmpstr.append("      context: .")
            tmpstr.append("      dockerfile: Dockerfile")
        if config[session_name]['CN_SLAVE'] == 'y':
            for num in range(1, int(config[session_name]['CN_MASTER']) + 1):
                name = "cnslave" + str(num)
                tmpstr.append("  %s:" % (name))
                tmpstr.append("    build:")
                tmpstr.append("      context: .")
                tmpstr.append("      dockerfile: Dockerfile")
        
        for num in range(1, int(config[session_name]['DN_MASTER']) + 1):
            name = "dn" + str(num)
            tmpstr.append("  %s:" % (name))
            tmpstr.append("    build:")
            tmpstr.append("      context: .")
            tmpstr.append("      dockerfile: Dockerfile")
        if config[session_name]['DN_SLAVE'] == 'y':
            for num in range(1, int(config[session_name]['DN_MASTER']) + 1):
                name = "dnslave" + str(num)
                tmpstr.append("  %s:" % (name))
                tmpstr.append("    build:")
                tmpstr.append("      context: .")
                tmpstr.append("      dockerfile: Dockerfile")
        f.writelines("\n".join(tmpstr))

cluster_type = config['CLUSTER']['TYPE']
generate_compose_yaml(config, cluster_type)

## 生成pgxc_ctl.conf
def generate_pgxc_conf(config: dict, session_name: str):
    with open('output/pgxc_ctl.conf', 'w') as f:
        cn_num = config[session_name]['CN_MASTER']
        dn_num = config[session_name]['DN_MASTER']
            
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
        tmpstr.append('gtmName=(gtm)')
        tmpstr.append('\n#---- GTM Master -----------------------------------------------')
        tmpstr.append('\n#---- Overall -------')
        tmpstr.append('gtmMasterServer=(gtm1)')
        tmpstr.append('gtmMasterPort=(%s)' % (config[session_name]['GTM_PORT']))
        tmpstr.append('gtmMasterDir=($pgxcInstallDir/gtm1)')
        tmpstr.append('\n#---- Configuration ---')
        tmpstr.append('gtmExtraConfig=()')
        tmpstr.append('gtmMasterSpecificExtraConfig=()')

        tmpstr.append('\n\n#---- GTM Slave -----------------------------------------------')
        if config[session_name]['GTM_SLAVE'] == 'y':
            tmpstr.append('\n#---- Overall ------')
            tmpstr.append('gtmSlave=y')
            tmpstr.append('gtmSlaveName=(gtmslave1)')
            tmpstr.append('gtmSlaveServer=(gtmslave1)')
            tmpstr.append('gtmSlavePort=(%s)' % (config[session_name]['GTM_PORT']))
            tmpstr.append('gtmSlaveDir=($pgxcInstallDir/gtmslave1)')
            tmpstr.append('\n#---- Configuration ----')
            tmpstr.append('gtmSlaveSpecificExtraConfig=()')
        else:
            tmpstr.append('gtmSlave=n')

        tmpstr.append('\n\n#---- GTM Proxy ---------------')
        tmpstr.append('\n\n#---- GTM Proxy ---------------')
           
        tmpstr.append('\n\n#---- Coordinators -----------------------------------------------')
        tmpstr.append('\n#---- shortcuts ----------')
        tmpstr.append('coordMasterDir=$dataDirRoot/coord_master')
        tmpstr.append('coordSlaveDir=$HOME/coord_slave')
        tmpstr.append('coordArchLogDir=$HOME/coord_archlog')
        tmpstr.append('\n#---- Overall ------------')
        
        cn_master_name = ' '.join(['cn' + str(num) for num in range(1, int(cn_num) + 1)])
        tmpstr.append('coordNames=(%s)' % (cn_master_name))
        cn_port = ' '.join([config[session_name]['CN_PORT'] for num in range(1, int(cn_num) + 1)])
        tmpstr.append('coordPorts=(%s)' % (cn_port))
        pool_port = ' '.join([str(int(config[session_name]['CN_PORT']) + 1) for num in range(1, int(cn_num) + 1)])
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
        if config[session_name]['CN_SLAVE'] == 'y':
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
        dn_master = ' '.join(['dn' + str(num) for num in range(1, int(dn_num) + 1)])
        dn_port = ' '.join([config[session_name]['DN_PORT'] for num in range(1, int(dn_num) + 1)])
        dn_pool_port = ' '.join([str(int(config[session_name]['DN_PORT']) + 1) for num in range(1, int(dn_num) + 1)])
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
        if config[session_name]['DN_SLAVE'] == 'y':
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

generate_pgxc_conf(config, cluster_type)

cmd_str = 'cp ./check.sql output/'
os.system(cmd_str)

## 启动docker-compose
cmd_str = 'cd output && docker-compose up -d'
os.system(cmd_str)


### 
### docker exec -it output_gtm1_1 bash
### su - pgxc
### pgxc_ctl -c /pgxc_ctl.conf init all
### psql -h cn1 -p 5555 -U pgxc -d postgres -f /check.sql

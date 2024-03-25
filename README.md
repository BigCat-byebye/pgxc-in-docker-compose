# pgxc-in-docker-compose
create pgxc cluster with docker-compose

## Usage
1. change CLUSTER.TYPE in env.ini
2. python3 run.py ---- it will print some command for create , you can copy and use it at step 4
3. cd output && docker-compose up -d 
4. paste the command of step 2

## How to clean
1. cd output && docker-compose down && rm -rf *

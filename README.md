# pgxc-in-docker-compose
create pgxc cluster with docker-compose

## Usage
1. change CLUSTER.TYPE in env.ini
2. python3 run.py
3. docker exec -it output_gtm1_1 bash
4. su - pgxc
5. pgxc_ctl -c /pgxc_ctl.conf init all
6. psql -h cn1 -p 5555 -U pgxc -d postgres -f /check.sql

## How to clean
1. cd output && docker-compose down && rm -rf *

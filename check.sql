\! echo "########################### Test pgxc cluster by pgxc_ctl monitor all ###########################";
\! pgxc_ctl -c /pgxc_ctl.conf  monitor all

\! echo "########################### Test GET NODE FROM PGXC_NODE ########################################";
SELECT * FROM PGXC_NODE;


\! echo "########################### Test DISTRIBUTE BY HASH #############################################";
CREATE TABLE disttab(col1 int, col2 int, col3 text) DISTRIBUTE BY HASH(col1);
\d+ disttab
INSERT INTO disttab SELECT generate_series(1,100), generate_series(101, 200), 'foo';
SELECT xc_node_id, count(*) FROM disttab GROUP BY xc_node_id;


\! echo "########################### Test DISTRIBUTE BY REPLICATION #####################################";
CREATE TABLE repltab (col1 int, col2 int) DISTRIBUTE BY REPLICATION;
\d+ repltab
INSERT INTO repltab SELECT generate_series(1,100), generate_series(101, 200);
SELECT xc_node_id, count(*) FROM repltab GROUP BY xc_node_id;

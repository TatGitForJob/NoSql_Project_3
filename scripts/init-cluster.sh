#!/usr/bin/env bash
set -euo pipefail

wait_for_mongo() {
  local host="$1"
  local port="$2"
  until mongosh --host "$host" --port "$port" --quiet --eval "db.adminCommand({ ping: 1 })" >/dev/null 2>&1; do
    sleep 2
  done
}

wait_for_primary() {
  local host="$1"
  local port="$2"
  until mongosh --host "$host" --port "$port" --quiet --eval "quit(db.hello().isWritablePrimary ? 0 : 1)" >/dev/null 2>&1; do
    sleep 2
  done
}

wait_for_mongo configsvr 27019
wait_for_mongo shard1 27018
wait_for_mongo shard2 27018

mongosh --host configsvr --port 27019 --quiet --eval '
try {
  rs.status()
} catch (e) {
  rs.initiate({
    _id: "cfgrs",
    configsvr: true,
    members: [{ _id: 0, host: "configsvr:27019" }]
  })
}
'

mongosh --host shard1 --port 27018 --quiet --eval '
try {
  rs.status()
} catch (e) {
  rs.initiate({
    _id: "shard1rs",
    members: [{ _id: 0, host: "shard1:27018" }]
  })
}
'

mongosh --host shard2 --port 27018 --quiet --eval '
try {
  rs.status()
} catch (e) {
  rs.initiate({
    _id: "shard2rs",
    members: [{ _id: 0, host: "shard2:27018" }]
  })
}
'

wait_for_primary configsvr 27019
wait_for_primary shard1 27018
wait_for_primary shard2 27018
wait_for_mongo mongos 27017

mongosh --host mongos --port 27017 --quiet --eval '
const shardNames = db.adminCommand({ listShards: 1 }).shards.map((shard) => shard._id);
if (!shardNames.includes("shard1rs")) {
  sh.addShard("shard1rs/shard1:27018");
}
if (!shardNames.includes("shard2rs")) {
  sh.addShard("shard2rs/shard2:27018");
}
sh.enableSharding("university");
db = db.getSiblingDB("university");
db.students.createIndex({ student_id: "hashed" });
sh.shardCollection("university.students", { student_id: "hashed" });
db.students.createIndex({ student_id: 1 }, { unique: true });
'

echo "MongoDB sharded cluster initialized."

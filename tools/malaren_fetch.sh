#!/bin/sh
# Mälaren: Genesis tiles inside tools/malaren_polygon.json (tools/PLAN_KARTFORMAT.md), in parallel shards,
# never stitched (too big -- the renderer reads the tiles in blocks). Zoom 14-17: all layers; zoom 18: only
# the lines (t) -- the bases come from zoom 17. Cached: run again to fill gaps.
cd "$(dirname "$0")/.."
export FF_CLIP=tools/malaren_polygon.json
B="59.295 59.505 17.455 17.712"
for z in 14 15 16; do for L in a b t v c; do py -3 tools/genesis_tiles.py malaren $z $B $L; done; done > raw/malaren_fetch_low.log 2>&1 &
for L in a b t v c; do for k in 0 1 2; do
  FF_SHARD=$k/3 py -3 tools/genesis_tiles.py malaren 17 $B $L > /dev/null 2>&1 &
done; done
for k in 0 1 2 3 4 5; do FF_SHARD=$k/6 py -3 tools/genesis_tiles.py malaren 18 $B t > /dev/null 2>&1 & done
wait
echo done

#!/bin/sh
# Gryts Skärgård: Genesis tiles inside tools/gryt_polygon.json, like tools/malaren_fetch.sh. Only Djupfärger
# (Filip 2026-11-08): zoom 14-16 aerial + lines, zoom 17 all layers (depth, vegetation + hardness for
# Kartanalys), zoom 18 only the lines. Cached: run again to fill gaps.
cd "$(dirname "$0")/.."
export FF_CLIP=tools/gryt_polygon.json
B="58.055 58.210 16.580 16.945"
for z in 14 15 16; do for L in a t; do py -3 tools/genesis_tiles.py gryt $z $B $L; done; done > raw/gryt_fetch_low.log 2>&1 &
for L in a b t v c; do for k in 0 1 2; do
  FF_SHARD=$k/3 py -3 tools/genesis_tiles.py gryt 17 $B $L > /dev/null 2>&1 &
done; done
for k in 0 1 2 3 4 5; do FF_SHARD=$k/6 py -3 tools/genesis_tiles.py gryt 18 $B t > /dev/null 2>&1 & done
wait
echo done

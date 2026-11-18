#!/usr/bin/env bash
# Full pipeline: rebuild -> silhouette compare -> clay renders -> circulation check -> export -> web walk test -> mood render
#   ./run_all.sh                       (re-scores current params, no tuning)
#   COMPARE_ROUNDS=6 ./run_all.sh      (run the auto-tuning loop first; rewrites params.json + compare_log.md)
#   SKIP_FINAL=1 / SKIP_CLAY=1         skip the slow Cycles renders
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$(pwd); BL=${BLENDER:-blender}; GT=${GLTF_TRANSFORM:-/workspace/tools/gltf/node_modules/.bin/gltf-transform}
PORT=${PORT:-8765}; mkdir -p logs
step(){ echo; echo "=== $* ==="; }

step "1/8 reference silhouettes"
[ -f compare/ref_front_sil.png ] || python3 compare/ref_extract.py

step "2/8 silhouette compare (rounds=${COMPARE_ROUNDS:-0})"
if [ "${COMPARE_ROUNDS:-0}" -gt 0 ]; then
  ROUNDS=$COMPARE_ROUNDS python3 compare/compare_loop.py | tee logs/compare.log
else
  ROUNDS=0 COMPARE_LOG=compare/score_check.md python3 compare/compare_loop.py > logs/compare.log; grep -A3 "## Final" compare/score_check.md
fi
python3 tools_params_table.py

step "3/8 full build (exterior + interior) -> building.blend / building.glb / spaces.json"
$BL -b -P build.py > logs/build.log 2>&1; grep "BUILD OK" logs/build.log

step "4/8 clay renders"
if [ -z "${SKIP_CLAY:-}" ]; then
  $BL -b building.blend -P src/render_clay.py > logs/clay.log 2>&1
  (cd renders && python3 ../flatten.py front.png rear.png left.png right.png top.png perspective_hero.png && python3 ../sheet.py)
fi
[ -f renders/front.png ] && python3 compare/side_by_side.py

step "5/8 circulation check (+ negative test)"
$BL -b building.blend -P check/circulation_check.py -- --out "$ROOT/circulation_report" > logs/circulation.log 2>&1
grep CIRCULATION logs/circulation.log
grep -q "CIRCULATION PASS | negative test caught: True" logs/circulation.log || { echo "circulation check failed"; exit 1; }

step "6/8 export: gltf-transform (webp textures + meshopt + GPU instancing of repeated windows)"
$GT optimize building.glb web/building_opt.glb --compress meshopt --texture-compress webp \
    --join-named false --simplify false --flatten false --instance true --instance-min 5 2>&1 | tail -1
cp spaces.json web/spaces.json

step "7/8 web walk test (headless Chrome)"
python3 -m http.server $PORT --directory web > logs/http.log 2>&1 & SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1
python3 walk/walk_test.py --url http://localhost:$PORT/index.html | tee logs/walk.log
grep -q "WALK PASS" logs/walk.log || { echo "walk test failed"; exit 1; }

step "8/8 final mood render"
[ -n "${SKIP_FINAL:-}" ] || $BL -b building.blend -P src/final_render.py > logs/final.log 2>&1
echo; echo "ALL DONE"

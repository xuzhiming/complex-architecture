#!/usr/bin/env bash
# Full pipeline: rebuild -> silhouette compare -> clay renders -> circulation check -> styled export -> web walk/fly/door/style tests -> mood render -> v14 style renders
#   ./run_all.sh                       (re-scores current params, no tuning)
#   COMPARE_ROUNDS=6 ./run_all.sh      (run the auto-tuning loop first; rewrites params.json + compare_log.md)
#   SKIP_FINAL=1 / SKIP_CLAY=1 / SKIP_STYLE=1   skip the slow Cycles renders
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$(pwd); BL=${BLENDER:-blender}; GT=${GLTF_TRANSFORM:-/workspace/tools/gltf/node_modules/.bin/gltf-transform}
PORT=${PORT:-8765}; mkdir -p logs
step(){ echo; echo "=== $* ==="; }

step "1/9 reference silhouettes"
[ -f compare/ref_front_sil.png ] || python3 compare/ref_extract.py

step "2/9 silhouette compare (rounds=${COMPARE_ROUNDS:-0})"
if [ "${COMPARE_ROUNDS:-0}" -gt 0 ]; then
  ROUNDS=$COMPARE_ROUNDS python3 compare/compare_loop.py | tee logs/compare.log
else
  ROUNDS=0 COMPARE_LOG=compare/score_check.md python3 compare/compare_loop.py > logs/compare.log; grep -A3 "## Final" compare/score_check.md
fi
python3 tools_params_table.py

step "3/9 full build (exterior + interior) -> building.blend / building.glb / spaces.json"
$BL -b -P build.py > logs/build.log 2>&1; grep "BUILD OK" logs/build.log

step "4/9 clay renders"
if [ -z "${SKIP_CLAY:-}" ]; then
  $BL -b building.blend -P src/render_clay.py > logs/clay.log 2>&1
  (cd renders && python3 ../flatten.py front.png rear.png left.png right.png top.png perspective_hero.png && python3 ../sheet.py)
fi
[ -f renders/front.png ] && python3 compare/side_by_side.py

step "5/9 circulation check (+ negative test)"
$BL -b building.blend -P check/circulation_check.py -- --out "$ROOT/circulation_report" > logs/circulation.log 2>&1
grep CIRCULATION logs/circulation.log
grep -q "CIRCULATION PASS | negative test caught: True" logs/circulation.log || { echo "circulation check failed"; exit 1; }

step "6/9 export: style materials (v14) + gltf-transform (webp textures + meshopt + GPU instancing of repeated windows)"
$BL -b building.blend -P tools/export_style_glb.py > logs/style_glb.log 2>&1; grep "STYLE GLB OK" logs/style_glb.log
$GT optimize building_style.glb web/building_opt.glb --compress meshopt --texture-compress webp \
    --join-named false --simplify false --flatten false --instance true --instance-min 5 2>&1 | tail -1
cp spaces.json web/spaces.json

step "7/9 web walk + fly tests (headless Chrome)"
python3 -m http.server $PORT --directory web > logs/http.log 2>&1 & SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1
python3 walk/walk_test.py --url http://localhost:$PORT/index.html | tee logs/walk.log
grep -q "WALK PASS" logs/walk.log || { echo "walk test failed"; exit 1; }
python3 walk/fly_test.py --url http://localhost:$PORT/index.html | tee logs/fly.log
grep -q "FLY PASS" logs/fly.log || { echo "fly test failed"; exit 1; }
python3 -c "import os,sys; s=os.path.getsize('web/building_opt.glb'); print('glb MB', round(s/1e6,2)); sys.exit(s > 8e6)" || { echo "glb too big"; exit 1; }
python3 walk/style_shots.py --url http://localhost:$PORT/index.html | tee logs/style_shots.log
grep -q "STYLE SHOTS PASS" logs/style_shots.log || { echo "style shots failed"; exit 1; }

step "8/9 final mood render"
[ -n "${SKIP_FINAL:-}" ] || $BL -b building.blend -P src/final_render.py > logs/final.log 2>&1

step "9/9 v14 stylised Cycles renders (front / aerial / courtyard) + post (grain, chroma, vignette) + style_vs_ref"
if [ -z "${SKIP_STYLE:-}" ]; then
  $BL -b building.blend -P src/render_style.py > logs/style_render.log 2>&1; grep "STYLE RENDER" logs/style_render.log
  python3 src/style_post.py renders
fi
echo; echo "ALL DONE"

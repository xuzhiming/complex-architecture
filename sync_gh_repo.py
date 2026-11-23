# copy the current pipeline outputs into gh_repo/ (deployable static site in web/, sources, docs); no reference images
import os, shutil, glob
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, "gh_repo")
def cp(src, dst=None):
    s = os.path.join(H, src); d = os.path.join(R, dst or src)
    os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy2(s, d)
for f in ["build.py", "run_all.sh", "params.json", "params_initial.json", "params_table.md", "sources.json", "tools_params_table.py",
          "flatten.py", "sheet.py", "package.py", "compare_log.md", "circulation_report.md", "circulation_report.json", "sync_gh_repo.py"]:
    if os.path.exists(os.path.join(H, f)): cp(f)
for f in glob.glob(os.path.join(R, "src", "*.py")): os.remove(f)
for f in ["geom.py", "detail.py", "crescent_geom.py", "render_sil.py", "render_clay.py", "final_render.py", "render_style.py", "style_post.py"]: cp(f"src/{f}")
for f in glob.glob(os.path.join(H, "compare", "*.py")): cp(os.path.relpath(f, H))
for f in glob.glob(os.path.join(H, "check", "*.py")): cp(os.path.relpath(f, H))
cp("walk/walk_test.py"); cp("walk/fly_test.py"); cp("walk/style_shots.py"); cp("tools/export_style_glb.py")
for f in ["walk_result.json", "trajectory.png"]: cp(f"walk/{f}", f"docs/walk/{f}")
# fly mode: test result + two screenshots
for f in glob.glob(os.path.join(R, "docs", "fly", "*")): os.remove(f)
for f in ["fly_result.json", "fly_03_over_crown.png", "fly_05_in_courtyard.png"]:
    if os.path.exists(os.path.join(H, "walk", f)): cp(f"walk/{f}", f"docs/fly/{f}")
# v13 auto doors: door-opening screenshots
for f in glob.glob(os.path.join(R, "docs", "doors", "*")): os.remove(f)
for f in ["door_opening_door.png", "door_opening_ext_door.png", "door_opening_lift_door.png", "door_open_fly.png"]:
    if os.path.exists(os.path.join(H, "walk", f)): cp(f"walk/{f}", f"docs/doors/{f}")
# v14 style renders (NOT style_vs_ref.png: it contains the user's reference image) + web style screenshots
for f in glob.glob(os.path.join(R, "docs", "style", "*")): os.remove(f)
for f in ["renders/style_front.png", "renders/style_aerial.png", "renders/style_courtyard.png",
          "walk/web_style_render_front.png", "walk/web_style_render_aerial.png", "walk/web_style_clay_front.png", "walk/style_shots.json"]:
    if os.path.exists(os.path.join(H, f)): cp(f, "docs/style/" + os.path.basename(f))
# static site
for f in ["index.html", "main.js", "spaces.json", "building_opt.glb", "README.md"]: cp(f"web/{f}")
shutil.rmtree(os.path.join(R, "web", "vendor"), ignore_errors=True)
shutil.copytree(os.path.join(H, "web", "vendor"), os.path.join(R, "web", "vendor"))
# docs
for f in glob.glob(os.path.join(R, "docs", "*.png")): os.remove(f)
for f in ["renders/four_views.png", "renders/perspective_hero.png", "renders/perspective_hero_low.png", "renders/detail_tower.png", "renders/crown_detail.png",
          "renders/top.png", "final_render.png", "final_vs_ref.png", "compare/final/overlay_sheet.png", "compare/final/side_by_side.png", "renders/arch_view_before_after.png"]:
    if os.path.exists(os.path.join(H, f)): cp(f, "docs/" + os.path.basename(f))
cp("gh_readme.md", "README.md")
for f in ["CHANGES_v5.md", "CHANGES_v6.md", "CHANGES_v7.md", "CHANGES_v8.md", "CHANGES_v9.md", "CHANGES_v10.md", "CHANGES_v11.md", "CHANGES_v12.md", "CHANGES_v13.md", "CHANGES_v14.md"]:
    if os.path.exists(os.path.join(H, f)): cp(f, "docs/" + f)
big = [f for f in glob.glob(os.path.join(R, "**", "*"), recursive=True) if os.path.isfile(f) and os.path.getsize(f) > 25*1024*1024 and "/.git/" not in f]
print("synced; files > 25 MiB:", big, "| glb MB:", round(os.path.getsize(os.path.join(R, "web", "building_opt.glb"))/1e6, 2))

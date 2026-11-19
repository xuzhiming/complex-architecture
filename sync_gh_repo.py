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
for f in ["geom.py", "detail.py", "render_sil.py", "render_clay.py", "final_render.py"]: cp(f"src/{f}")
for f in glob.glob(os.path.join(H, "compare", "*.py")): cp(os.path.relpath(f, H))
for f in glob.glob(os.path.join(H, "check", "*.py")): cp(os.path.relpath(f, H))
cp("walk/walk_test.py")
for f in ["walk_result.json", "trajectory.png"]: cp(f"walk/{f}", f"docs/walk/{f}")
# static site
for f in ["index.html", "main.js", "spaces.json", "building_opt.glb", "README.md"]: cp(f"web/{f}")
shutil.rmtree(os.path.join(R, "web", "vendor"), ignore_errors=True)
shutil.copytree(os.path.join(H, "web", "vendor"), os.path.join(R, "web", "vendor"))
# docs
for f in glob.glob(os.path.join(R, "docs", "*.png")): os.remove(f)
for f in ["renders/four_views.png", "renders/perspective_hero.png", "renders/perspective_hero_low.png", "renders/detail_tower.png", "renders/crown_detail.png",
          "renders/top.png", "final_render.png", "final_vs_ref.png", "compare/final/overlay_sheet.png", "compare/final/side_by_side.png"]:
    if os.path.exists(os.path.join(H, f)): cp(f, "docs/" + os.path.basename(f))
cp("gh_readme.md", "README.md")
for f in ["CHANGES_v5.md", "CHANGES_v6.md", "CHANGES_v7.md", "CHANGES_v8.md", "CHANGES_v9.md", "CHANGES_v10.md"]:
    if os.path.exists(os.path.join(H, f)): cp(f, "docs/" + f)
big = [f for f in glob.glob(os.path.join(R, "**", "*"), recursive=True) if os.path.isfile(f) and os.path.getsize(f) > 25*1024*1024 and "/.git/" not in f]
print("synced; files > 25 MiB:", big, "| glb MB:", round(os.path.getsize(os.path.join(R, "web", "building_opt.glb"))/1e6, 2))

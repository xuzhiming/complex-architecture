# Build deliver/ + gothic_deliver_v5.zip (python zipfile/shutil only; no zip binary)
import os, re, shutil, zipfile, glob
H = os.path.dirname(os.path.abspath(__file__)); os.chdir(H)
D = "deliver"; shutil.rmtree(D, ignore_errors=True); os.makedirs(D)
def cp(src, dst=None):
    dst = os.path.join(D, dst or src); os.makedirs(os.path.dirname(dst) or D, exist_ok=True); shutil.copy2(src, dst)
for f in ["building.blend", "building.glb", "web/building_opt.glb", "circulation_report.json", "circulation_report.md", "compare_log.md",
          "final_render.png", "final_vs_ref.png", "params.json", "params_table.md", "CHANGES_v5.md", "CHANGES_v6.md", "CHANGES_v7.md", "CHANGES_v8.md", "CHANGES_v9.md", "CHANGES_v10.md", "CHANGES_v11.md"]:
    cp(f, os.path.basename(f))
cp("renders/four_views.png", "four_views.png")
for f in ["overlay_sheet.png", "scores.json", "side_by_side.png"]: cp(f"compare/final/{f}", f"compare/{f}")
for f in glob.glob("renders/*.png"): cp(f)
for f in glob.glob("walk/cp_*.png") + ["walk/trajectory.csv", "walk/trajectory.png", "walk/walk_result.json"]: cp(f)
def zdir(zpath, files, root):
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files: z.write(f, os.path.join(root, os.path.relpath(f, H)))
web = [f for f in glob.glob("web/**/*", recursive=True) if os.path.isfile(f)]
zdir(os.path.join(D, "web_preview.zip"), web, "gothic_web_preview")
src = ["build.py", "flatten.py", "sheet.py", "tools_params_table.py", "package.py", "params.json", "params_initial.json", "run_all.sh",
       *glob.glob("compare/*.py"), *glob.glob("check/*.py"), "walk/walk_test.py", *[f for f in glob.glob("src/*.py") if not re.search(r"_(r|v)\d", os.path.basename(f))],
       "web/index.html", "web/main.js", "web/README.md", "compare_log.md", "CHANGES_v5.md", "CHANGES_v6.md", "CHANGES_v7.md", "CHANGES_v8.md", "CHANGES_v9.md", "CHANGES_v10.md", "sources.json", "gh_readme.md"]
zdir(os.path.join(D, "pipeline_src.zip"), src, "gothic_pipeline")
out = shutil.make_archive(os.path.join(H, "gothic_deliver_v11"), "zip", root_dir=H, base_dir=D)
print("packaged", out, round(os.path.getsize(out)/1e6, 1), "MB")

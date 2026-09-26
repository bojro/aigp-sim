# Handoff: film the AI Grand Prix racing policies on this Windows laptop

## Goal

Produce videos of two trained racing policies flying in Isaac Sim, each frame showing the chase view beside the drone's onboard camera with two overlays: the corners the policy is fed (green) and the real hand497 detector's detections on the same rendered frame (cyan). Then copy them to my Mac. Everything needed is in the private repo https://github.com/bojro/aigp-sim (GitHub account: bojro). The one-script path is `scripts\windows\record_race_pov.ps1`. Read its header and `scripts\diag\record_race_pov.py` before running anything.

## Context you should know

- This laptop (RTX 4060, Windows with WSL) was the team's Isaac Sim machine on 16 Sep 2026 and has not been used for this project since. Expect stale state. Two Isaac installs may exist: a Windows-native venv, historically `D:\isaacsim_venv` with the repo copy at `D:\Code\Competitions\AIGP\isaac_drone_racer`, and a WSL one behind `~/aigp/isaac_env.sh` (Isaac Sim 4.5, Isaac Lab 2.1, skrl 1.4.2, Python 3.10). Use the **Windows-native** one: the recorder needs camera rendering, which is fragile under WSL2. Find it first (`Get-ChildItem D:\ -Directory`, look for `isaacsim_venv`, `python.exe` with `isaaclab` importable); do not reinstall Isaac unless it is genuinely gone.
- `aigp-sim` is a cleaned-up fork of the old `isaac_drone_racer` tree. Package names (`contract`, `tasks`, `utils`, `dynamics`, `assets`) are unchanged. `README.md` and `docs/` explain the layout; `docs/RUNBOOK_RUNPOD.md` has the Isaac setup sequence if something must be installed. Old copies of the repo on this machine are NOT to be used; clone fresh.
- The two checkpoints are committed in `checkpoints/` (race40_best_agent.pt, race40drop_best_agent.pt; both 40 Hz, v2 contract, 1760 inputs). `checkpoints/README.md` has their provenance. Run them with `AIGP_POLICY_HZ=40`; the ps1 sets this.
- The cyan overlay needs the sibling repo https://github.com/bojro/aigp-perception (private) and `onnxruntime-gpu`; the ps1 handles both. If onnxruntime-gpu will not install against this CUDA, fall back to `onnxruntime` (CPU) or pass `-NoDetector`.
- The recorder has never run on a live Isaac install (the pod it was written for is gone). Expect to fix small things: import paths, the tiled-camera key name, the skrl reset re-arm, imageio needing ffmpeg. Fix them in place, keep the fixes minimal, and commit them with a clear message. Do not rewrite the script.
- Isaac's exit code is meaningless. The `RECORDED=` line printed by the recorder, and `SMOKE_RESULT=PASS` from the smoke test, are the results.
- Do not touch anything to do with the drone, Betaflight, MSP, or the Code-Red-Cables/AI_GP repository. This task is simulation only.
- What I want is the best-looking footage of the policy flying: a run that leaves the pad and threads several gates, with the overlays on the onboard pane (green = the corners the policy is fed, cyan = the hand497 YOLO detections on the same frame). Both overlays if the detector installs; green only is acceptable if onnxruntime will not install. Record more attempts than the default (`-Attempts 6`, `-Seconds 40`) for both checkpoints, keep every file, and tell me which one or two look best and why (gates passed, how far it got, no static frames). Do not trim or edit the videos; I will cut them on the Mac.
- Reference footage is in the clone: `paper/videos/stack_run_02.mp4` is the look to match (chase view beside the drone's own camera with corners drawn, a status line), and `paper/videos/race_start_from_pad.mp4` is an earlier chase-only recording of the policy made on the pod with `scripts/diag/record_start.py`, which the new recorder was built from. Watch stack_run_02 before recording so you know what a good result looks like.
- Pull before anything else. If a clone of aigp-sim or aigp-perception already exists on this machine, run `git pull --ff-only` in each; the repos changed a lot after 22 Sep and stale copies will not have the recorder or the checkpoints. The ps1 also pulls, but confirm it did.

## Steps

1. Authenticate to GitHub if needed (`gh auth login` or a credential helper); the repos are private.
2. `git lfs install`, then `git clone https://github.com/bojro/aigp-sim.git D:\aigp-sim` (or another drive with ~5 GB free; the drone USD is 98 MB in LFS).
3. Locate the Isaac venv python. Verify with `<python> -c "import isaaclab, isaaclab_tasks, skrl; print(skrl.__version__)"` (should print 1.4.x). If the venv is missing or broken, stop and report what you found before installing anything large.
4. `cd D:\aigp-sim`, `git pull --ff-only`, then `.\scripts\windows\record_race_pov.ps1 -Python <that python> -Attempts 6 -Seconds 40`. Watch for `SMOKE_RESULT=PASS`, then the two recording runs (race40drop under dropout, then race40 with perfect corners). Keep the laptop on AC power and awake; each run is a few minutes on this GPU.
5. If a run fails, read the traceback, make the minimal fix, rerun that run only (`-SkipSmoke` once the smoke test has passed). Commit fixes to aigp-sim main and push.
6. Look at one output video (open it) and confirm: two panes, left chase view, right onboard camera with green corners (and cyan hand497 detections if the detector ran), a status line, and the drone actually leaving the pad. A file that plays but shows a static scene means the skrl reset trap (see record_start.py's docstring).
7. Zip the output directory and say where the zip is. Do not try to copy it to the Mac over the network; the Mac does not accept SSH or scp.

## Report back

- Which python/venv was used and its Isaac Sim / Isaac Lab / skrl versions.
- The `SMOKE_RESULT=` line and every `RECORDED=` line, verbatim.
- Every fix you had to make, as commit hashes.
- Where the videos are, with sizes; which one or two look best and why (gates passed, seconds flown); and whether hand497 detected the simulated gates at all (the cyan count in the legend line).

## What the 26 September run found

The recordings came back the same day: `paper/videos/race40drop_pov.mp4` (the best of eight `race40drop` attempts, 38 gates) and `paper/videos/stack_pov.mp4` (the stack, nine gates then a crash at 127 s), both 640×720 with the chase view above the onboard camera, real time. Seven more `race40drop` attempts (7 to 17 gates), an 8 s `race40` clip and a 90 s stack run without a crash stayed on the laptop.

* No native Isaac existed on the laptop and WSL2 cannot render (no NVIDIA Vulkan there). A native environment was built: conda Python 3.10, Isaac Sim 4.5, Isaac Lab 2.1, skrl 1.4.2.
* NVIDIA driver 596.36 (the R590 branch) crashes `rtx.scenedb` when the renderer starts, on every Isaac version tried. Known bug, no workaround. Driver 581.80 works; keep it on that machine while recording.
* The recorder needed fixes to run there: vertical layout instead of side by side, mean actions, the CUDA execution provider for the detector, a `cv2` scoping bug, the traceback printed before the app closes, 40 Hz by decimation from the training config, the camera at the real mount (12 cm forward, 2 cm right, 1.3 cm up, 20° up-tilt, near clip 35 cm so the airframe stays out of frame), reset under inference mode, the episode cap equal to `--seconds`, and EULA, import, stderr and live-log fixes in the PowerShell script. These are commits on the laptop's clone and are not on `origin/main` yet; the laptop's own README in its output folder has the full log.

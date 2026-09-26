"""Animated GIFs of the recordings in videos/, for inline display on GitHub, plus a still frame for the PDF.

Each GIF is a short cut of the best stretch of its video, because GitHub stops rendering an image above
10 MB and a minute of 640x720 at 40 fps is far past that. The two 26 Sep recordings (the race40drop policy
and the classical stack, each already stacked chase view over onboard camera) are quantised against a
shared 64-colour palette with the overlay colours forced in, so the green, cyan and red corner marks keep
their colour instead of being averaged into the orange and grey of the scene.

OpenCV reads the mp4 (needs a Python with cv2); Pillow writes the GIF (needs a Python with PIL). On the
team Mac those are two interpreters, so the frame dump and the assembly are separate steps:

    ~/dev/ai-grand-prix/.venv_mac/bin/python make_gifs.py dump
    python3 make_gifs.py assemble
"""
import os, sys, glob, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(tempfile.gettempdir(), "aigp_gif_frames")
OVERLAY = [(0, 255, 0), (0, 255, 255), (255, 0, 0), (255, 255, 255), (255, 220, 0)]
CLIPS = [  # name, source video, start s, end s, width px, fps, colours, restack side-by-side to vertical, forced palette
    ("race_start_from_pad", "race_start_from_pad.mp4", 0.0, 6.7, 800, 10, 64, False, False),
    ("race40drop_pov", "race40drop_pov.mp4", 34.0, 44.0, 640, 6, 64, False, True),   # gates 22 to 29 of attempt 4
    ("stack_pov", "stack_pov.mp4", 54.0, 64.0, 640, 6, 64, False, True),             # stage, settle and pass gate 4, on to 5
]

def restack(fr):
    """A 2:1 side-by-side frame becomes the two panes one above the other."""
    import numpy as np
    h, w = fr.shape[:2]; half = w // 2
    return np.vstack([fr[:, :half], fr[:, half:]])

def dump():
    import cv2
    for name, src, t0, t1, width, fps_out, _, stack, _ in CLIPS:
        d = os.path.join(TMP, name); os.makedirs(d, exist_ok=True)
        for f in glob.glob(os.path.join(d, "*.png")): os.remove(f)
        cap = cv2.VideoCapture(os.path.join(HERE, "videos", src)); fps = cap.get(cv2.CAP_PROP_FPS)
        n = 0
        for k in range(int((t1 - t0) * fps_out)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int((t0 + k / fps_out) * fps)); ok, fr = cap.read()
            if not ok: break
            if stack: fr = restack(fr)
            h = int(fr.shape[0] * width / fr.shape[1]); fr = cv2.resize(fr, (width, h), interpolation=cv2.INTER_AREA)
            cv2.imwrite(os.path.join(d, f"{k:04d}.png"), fr); n += 1
        print(name, n, "frames")

def shared_palette(paths, colours):
    """Median cut over four frames of the clip plus a strip of the overlay colours, so those survive."""
    from PIL import Image, ImageDraw
    ims = [Image.open(p).convert("RGB") for p in paths[::max(1, len(paths) // 4)][:4]]
    W, H = ims[0].size; sheet = Image.new("RGB", (W, H * len(ims) + 60))
    for i, im in enumerate(ims): sheet.paste(im, (0, i * H))
    d = ImageDraw.Draw(sheet); n = len(OVERLAY)
    for i, c in enumerate(OVERLAY): d.rectangle([i * W // n, H * len(ims), (i + 1) * W // n, H * len(ims) + 60], fill=c)
    return sheet.quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)

def assemble():
    from PIL import Image
    for name, _, _, _, _, fps_out, colours, _, forced in CLIPS:
        paths = sorted(glob.glob(os.path.join(TMP, name, "*.png")))
        if forced:
            # the Isaac renders are flat colour: no dithering, or the dark grid turns to speckle
            pal = shared_palette(paths, colours)
            frames = [Image.open(p).convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE) for p in paths]
        else:
            frames = [Image.open(p).convert("RGB").quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG) for p in paths]
        out = os.path.join(HERE, "figures", name + ".gif")
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=int(1000 / fps_out), loop=0, optimize=True)
        Image.open(paths[len(paths) // 3]).convert("RGB").save(os.path.join(HERE, "figures", name + "_still.png"))
        print(name, len(frames), "frames,", round(os.path.getsize(out) / 1e6, 1), "MB")

if __name__ == "__main__":
    {"dump": dump, "assemble": assemble}[sys.argv[1]]()

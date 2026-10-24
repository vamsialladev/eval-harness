"""Record the captioned demo video from the LIVE dashboard: real saved results, nothing staged.

python scripts/record_demo.py                       # record + build docs/video/demo.mp4, docs/images/demo.gif
python scripts/record_demo.py --rebuild             # rebuild from the last recording
python scripts/record_demo.py --web-out ../vamsi-portfolio/videos/eval-harness-demo.mp4   # + web copy
python scripts/record_demo.py --app http://localhost:8501/                                # rehearse locally

Follows docs/DEMO_SCRIPT.md: the overview of both projects' gates, the regression demo on "Runs over time" and its
failure reasons, a failing case (q13 in the demo run) drilled down to its verdicts, then judge calibration. The
dashboard is read-only and calls no API, so recording costs nothing. Also saves README screenshots
(docs/images/overview.png, case.png, calibration.png) from the same session.

No narration: the video is a silent screen recording with burned-in step captions. I record my own voice
over it from docs/VIDEO_SCRIPT.md (no AI voice); scripts/make_captions.py then captions my voice.
Also writes a WebVTT track of the captions and a LinkedIn copy (--linkedin-out).

Dev-only: needs Playwright (requirements-dev.txt) and ffmpeg on PATH. docs/video/ is git-ignored.
"""

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "video"
WORK = OUT / "work"
IMAGES = ROOT / "docs" / "images"
GIF = IMAGES / "demo.gif"
APP = "https://eval-harness.streamlit.app/~/+/"  # the app itself, without Streamlit Cloud's frame
SIZE = (1280, 720)
VIEW = (1280, 640)  # the app; the 80 px band under it holds the captions, so they never cover the UI
FPS = 30
GREEN, BRASS, CREAM, INK = "#1E4636", "#94702C", "#F4F1EA", "#FFFFFF"
LINKS = [
    ("Portfolio", "vamsialla.com"),
    ("Live dashboard", "eval-harness.streamlit.app"),
    ("GitHub", "github.com/vamsialladev/eval-harness"),
]
TITLE = "Eval Harness"
SUBTITLE = "Simulated client engagement · synthetic data · no live API calls"
TITLE_SECONDS = 3
LEAD, GAP = 0.4, 0.35
GIF_STEP = "case"

CAPTIONS = {
    "overview": "Both assistants, one harness: same cases, metrics and gates.",
    "gates": "Published numbers reproduced; fresh re-runs pass every gate.",
    "demo": "Bad change on a throwaway branch: top-k 5 → 2.",
    "caught": "Caught: q13 and q35 always passed, now always fail. Never merged.",
    "case": "Drill-down: the expected passage, the answers, every verdict.",
    "judge": "Judge vs 70 blind hand labels: best kappa 0.29. Not trusted, never a gate.",
}


# ---------------------------------------------------------------- recording
class Recorder:
    """Times each step. Times are video seconds (after the title card)."""

    def __init__(self, page, durations: dict):
        self.page, self.t0, self.steps, self.durations = page, time.monotonic(), [], durations
        self.trim = None
        self.cursor = LEAD + durations.get("title", 0) + GAP

    def now(self) -> float:
        return round(time.monotonic() - self.t0, 2)

    def video_time(self) -> float:
        return self.now() - self.trim + TITLE_SECONDS

    def step(self, key: str):
        start = self.video_time()
        audio = max(start + LEAD, self.cursor)
        self.cursor = audio + self.durations.get(key, 0) + GAP
        self.steps.append({"key": key, "caption": CAPTIONS[key], "start": self.now(), "audio": round(audio, 2)})

    def settle(self, at_least: float):
        self.pause(at_least)
        while self.video_time() < self.cursor - GAP:
            self.page.wait_for_timeout(100)

    def pause(self, seconds: float):
        self.page.wait_for_timeout(int(seconds * 1000))

    def scroll(self, pixels: int, steps: int = 12):
        self.page.mouse.move(800, 400)
        for _ in range(steps):
            self.page.mouse.wheel(0, pixels / steps)
            self.page.wait_for_timeout(45)


def ready(page):
    page.wait_for_selector("h1.gra-title", timeout=240_000)
    page.wait_for_timeout(1500)


def show(page, text: str):
    page.get_by_text(text, exact=False).locator("visible=true").first.evaluate(
        "el => el.scrollIntoView({block: 'start', behavior: 'smooth'})"
    )
    page.wait_for_timeout(900)


def nav(page, label: str, title: str):
    page.locator("[data-testid=stSidebarNav] a", has_text=label).first.click()
    page.wait_for_selector(f"h1.gra-title:has-text('{title}')", timeout=60_000)
    page.wait_for_timeout(1200)


def choose(page, widget: str, index: int, option: str):
    """Pick an option in the index-th selectbox or multiselect (Streamlit renders options in a popover list)."""
    page.locator(f"[data-testid={widget}]").nth(index).click()
    page.wait_for_timeout(500)
    page.get_by_role("option", name=option, exact=True).first.click()
    page.wait_for_timeout(1500)


def shot(page, name: str):
    IMAGES.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(WORK / f"{name}.png"))


def record(durations: dict, app: str) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        warm = browser.new_page()  # not recorded: wake the free app if it sleeps
        warm.goto(app, timeout=240_000)
        ready(warm)
        warm.close()

        ctx = browser.new_context(
            viewport={"width": VIEW[0], "height": VIEW[1]},
            record_video_dir=str(WORK),
            record_video_size={"width": VIEW[0], "height": VIEW[1]},
            color_scheme="light",
        )
        page = ctx.new_page()
        r = Recorder(page, durations)
        page.goto(app, timeout=240_000)
        ready(page)
        r.trim = r.now()

        r.step("overview")
        r.pause(2)
        shot(page, "overview")
        r.scroll(380, 16)
        r.settle(1)

        r.step("gates")
        show(page, "Project 2 · Guest Request Agent")
        r.scroll(200)
        r.settle(1)

        r.step("demo")
        nav(page, "Runs over time", "Runs over time")
        choose(page, "stSelectbox", 1, "Strict retrieval")
        r.scroll(260)
        r.settle(1)

        r.step("caught")
        show(page, "Every saved run")
        page.locator("[data-testid=stExpander] summary", has_text="p1-demo-topk2-live").first.click()
        r.pause(1)
        r.scroll(300)
        r.settle(1)

        r.step("case")
        nav(page, "Cases", "Cases")
        choose(page, "stSelectbox", 1, "p1-demo-topk2-live")
        choose(page, "stMultiSelect", 2, "fail")
        page.keyboard.press("Escape")
        grid = page.locator("[data-testid=stDataFrame]").first
        grid.scroll_into_view_if_needed()
        box = grid.bounding_box()
        page.mouse.click(box["x"] + 15, box["y"] + 52)  # first row: q13
        page.get_by_text("Case q13", exact=False).first.wait_for(timeout=30_000)
        show(page, "Case q13")
        r.pause(1.5)
        shot(page, "case")
        r.scroll(420, 16)
        r.settle(1)

        r.step("judge")
        nav(page, "Judge calibration", "Can the judge be trusted?")
        r.pause(1)
        shot(page, "calibration")
        r.scroll(420, 16)
        r.settle(1.5)
        end = r.now()

        video = page.video
        ctx.close()
        raw = Path(video.path())
        browser.close()
    raw.rename(WORK / "raw.webm")
    for name in ("overview", "case", "calibration"):
        shutil.copy(WORK / f"{name}.png", IMAGES / f"{name}.png")
    timeline = {"trim": r.trim, "end": end, "steps": r.steps, "durations": durations, "end_audio": None}
    (WORK / "timeline.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    return timeline


# ---------------------------------------------------------------- building
def font(name: str, size: int):
    for candidate in (name, "arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def centered(draw, y, text, fnt, fill):
    width = draw.textlength(text, font=fnt)
    draw.text(((SIZE[0] - width) / 2, y), text, font=fnt, fill=fill)


def title_card(path: Path):
    img = Image.new("RGB", SIZE, GREEN)
    d = ImageDraw.Draw(img)
    d.rectangle([0, SIZE[1] - 14, SIZE[0], SIZE[1]], fill=BRASS)
    centered(d, 250, TITLE, font("georgiab.ttf", 58), INK)
    centered(d, 340, "Vamsi Alla", font("georgia.ttf", 38), "#E8D9B5")
    centered(d, 430, SUBTITLE, font("arial.ttf", 24), CREAM)
    img.save(path)


def end_card(path: Path):
    img = Image.new("RGB", SIZE, GREEN)
    d = ImageDraw.Draw(img)
    d.rectangle([0, SIZE[1] - 14, SIZE[0], SIZE[1]], fill=BRASS)
    centered(d, 150, "See the dashboard, the code and the decisions", font("georgiab.ttf", 44), INK)
    label_font, link_font = font("arialbd.ttf", 26), font("arial.ttf", 32)
    for i, (label, url) in enumerate(LINKS):
        y = 260 + i * 90
        centered(d, y, label.upper(), label_font, "#E8D9B5")
        centered(d, y + 34, url, link_font, INK)
    img.save(path)


def ass_time(seconds: float) -> str:
    seconds = max(seconds, 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def vtt_time(seconds: float) -> str:
    seconds = max(seconds, 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def captions(timeline: dict, offset: float) -> str:
    """ASS subtitles: white text in the dark band under the app, one caption per step.
    `offset` shifts them past the title card."""
    head = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1280\nPlayResY: 720\nWrapStyle: 0\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        # White bold text, no outline, centered in the 80 px band (colours are &HAABBGGRR)
        "Style: Cap,Arial,28,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,2,40,40,24,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    steps, lines = timeline["steps"], []
    for i, step in enumerate(steps):
        start = step["start"] - timeline["trim"] + offset
        stop = (steps[i + 1]["start"] if i + 1 < len(steps) else timeline["end"]) - timeline["trim"] + offset
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(stop - 0.05)},Cap,,0,0,0,,{step['caption']}")
    return head + "\n".join(lines) + "\n"


def caption_cues(timeline: dict, offset: float) -> list[tuple[float, float, str]]:
    """(start, end, caption) per step in video time: the same words as the burned-in captions, for the web
    copy's WebVTT track."""
    steps, cues = timeline["steps"], []
    for i, step in enumerate(steps):
        start = step["start"] - timeline["trim"] + offset
        stop = (steps[i + 1]["start"] if i + 1 < len(steps) else timeline["end"]) - timeline["trim"] + offset
        cues.append((round(start, 2), round(stop - 0.05, 2), step["caption"]))
    return cues


VTT_POSITION = "line:6% position:50% align:center"  # top of the frame: the burned-in captions are at the bottom


def webvtt(cues) -> str:
    return "WEBVTT\n\n" + "\n".join(f"{vtt_time(a)} --> {vtt_time(b)} {VTT_POSITION}\n{text}\n" for a, b, text in cues)


def ffmpeg(*args: str):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True, cwd=WORK)


def build(timeline: dict) -> Path:
    length = timeline["end"] - timeline["trim"]
    end_seconds = 6.0
    total = TITLE_SECONDS + length + end_seconds
    title_card(WORK / "title.png")
    end_card(WORK / "end.png")
    (WORK / "captions.ass").write_text(captions(timeline, TITLE_SECONDS), encoding="utf-8")
    scale = f"scale={SIZE[0]}:{SIZE[1]},fps={FPS},format=yuv420p,setsar=1"
    band = f"scale={VIEW[0]}:{VIEW[1]},pad={SIZE[0]}:{SIZE[1]}:0:0:color=0x111111,fps={FPS},format=yuv420p,setsar=1"
    graph = (
        f"[0:v]{scale},fade=t=out:st={TITLE_SECONDS - 0.4}:d=0.4[t];"
        f"[1:v]{band},fade=t=in:st=0:d=0.4[m];"
        f"[2:v]{scale},fade=t=in:st=0:d=0.4[e];"
        "[t][m][e]concat=n=3:v=1:a=0,subtitles=captions.ass[v]"
    )
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "demo.mp4"
    ffmpeg(
        *("-loop", "1", "-t", str(TITLE_SECONDS), "-i", "title.png"),
        *("-ss", f"{timeline['trim']:.2f}", "-t", f"{length:.2f}", "-i", "raw.webm"),
        *("-loop", "1", "-t", f"{end_seconds:.2f}", "-i", "end.png"),
        *("-filter_complex", graph, "-map", "[v]"),
        *("-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart"),
        *("-t", f"{total:.2f}"),
        str(out),
    )
    (OUT / "demo.vtt").write_text(webvtt(caption_cues(timeline, TITLE_SECONDS)), encoding="utf-8")
    (WORK / "timeline.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    return out


def gif(timeline: dict, step_key: str = GIF_STEP):
    """10-15 s GIF of one step for the top of the README (captions included, 960 px wide, no sound)."""
    steps = timeline["steps"]
    i = next(n for n, s in enumerate(steps) if s["key"] == step_key)
    start = steps[i]["start"] - timeline["trim"] + TITLE_SECONDS
    length = min(max(steps[i + 1]["start"] - steps[i]["start"], 10), 15)
    palette = (
        "fps=10,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer"
    )
    ffmpeg("-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(OUT / "demo.mp4"), "-vf", palette, str(GIF))


def web_copy(src: Path, dest: Path):
    """Smaller H.264 + AAC copy for the portfolio site (starts playing at once), a poster from the title card,
    and the captions track."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg(
        *("-i", str(src), "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-profile:v", "high"),
        *("-an", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dest)),
    )
    ffmpeg("-ss", "1.5", "-i", str(src), "-frames:v", "1", "-q:v", "3", str(dest.with_suffix(".jpg")))
    if (OUT / "demo.vtt").exists():
        shutil.copy(OUT / "demo.vtt", dest.with_suffix(".vtt"))


def linkedin_copy(dest: Path):
    """A copy for LinkedIn (it autoplays muted; the step captions are burned in) and a 1200x627 thumbnail."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(OUT / "demo.mp4", dest)  # the step captions are already burned in
    card = Image.open(WORK / "title.png").convert("RGB")
    width = round(card.height * 1200 / 627)
    left = (card.width - width) // 2
    thumb = card.crop((left, 0, left + width, card.height)).resize((1200, 627))
    thumb.save(dest.with_name("thumbnail.jpg"), quality=88)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rebuild", action="store_true", help="reuse the last recording")
    parser.add_argument("--web-out", type=Path, help="also write a web copy (+ .jpg poster and .vtt) here")
    parser.add_argument("--linkedin-out", type=Path, help="also write a LinkedIn copy and thumbnail here")
    parser.add_argument("--app", default=APP, help="dashboard URL to record (default: the live app)")
    args = parser.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found. Install it (winget install Gyan.FFmpeg) and open a new terminal.")
    if args.rebuild:
        timeline = json.loads((WORK / "timeline.json").read_text(encoding="utf-8"))
    else:
        shutil.rmtree(WORK, ignore_errors=True)
        WORK.mkdir(parents=True)
        timeline = record({}, args.app)
    out = build(timeline)
    gif(timeline)
    print(f"saved {out.relative_to(ROOT)} and {GIF.relative_to(ROOT)}")
    if args.web_out:
        web_copy(out, args.web_out.resolve())
        print(f"saved {args.web_out} with its .jpg poster and .vtt captions")
    if args.linkedin_out:
        linkedin_copy(args.linkedin_out.resolve())
        print(f"saved {args.linkedin_out} and thumbnail.jpg")


if __name__ == "__main__":
    main()

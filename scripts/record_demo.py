"""Record the narrated, captioned demo video from the LIVE dashboard: real saved results, nothing staged.

python scripts/record_demo.py                       # record + build docs/video/demo.mp4, docs/images/demo.gif
python scripts/record_demo.py --rebuild             # rebuild from the last recording
python scripts/record_demo.py --no-voice            # captions only, no narration
python scripts/record_demo.py --web-out ../vamsi-portfolio/videos/eval-harness-demo.mp4   # + web copy
python scripts/record_demo.py --app http://localhost:8501/                                # rehearse locally

Follows docs/DEMO_SCRIPT.md: the overview of both projects' gates, the regression demo on "Runs over time" and its
failure reasons, a failing case (q13 in the demo run) drilled down to its verdicts, then judge calibration. The
dashboard is read-only and calls no API, so recording costs nothing. Also saves README screenshots
(docs/images/overview.png, case.png, calibration.png) from the same session.

Narration: an AI voice from Piper (open source, offline, no voice cloning), timed to each step. Mixed to about
-16 LUFS, AAC. Writes a WebVTT captions track, the narration text and a burned-in-captions copy for LinkedIn
(--linkedin-out). Reuses Project 2's downloaded voice model when it is there.

Dev-only: needs Playwright, piper-tts (requirements-dev.txt) and ffmpeg on PATH. docs/video/ is git-ignored.
"""

import argparse
import json
import re
import shutil
import subprocess
import time
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "video"
WORK = OUT / "work"
VOICES = OUT / "voices"
SHARED_VOICES = ROOT.parent / "guest-request-agent" / "docs" / "video" / "voices"
VOICE = "en_US-lessac-high"
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
SPEED = 1.08
GIF_STEP = "case"

NARRATION = {
    "title": "Eval Harness: a simulated client project, part three of five.",
    "overview": "One harness now checks both of the hotel group's assistants the same way: the same cases, metrics "
    "and gates, with ninety-five percent intervals on every rate.",
    "gates": "It reproduces both projects' published numbers from their own recordings, and fresh re-runs at the "
    "pinned versions pass every gate.",
    "demo": "Then I made a realistic bad change on a throwaway branch: two passages instead of five, to save tokens. "
    "Retrieval only fell from ninety-eight to ninety-three percent, inside the interval.",
    "caught": "The gate still failed, because two questions that always passed now always fail. The message names "
    "them. The branch was never merged.",
    "case": "Here is one: a spa question about a sixteen-year-old. The right passage dropped out, and every metric "
    "shows it.",
    "judge": "An AI judge rates tone and clarity. I labelled seventy replies by hand, in two blind rounds, the second "
    "one full of failures on purpose. Its best kappa was point two nine, well under the bar of point six. So no "
    "judge score is trusted, and none is a gate.",
    "end": "The code, the reports and every decision are linked on screen.",
}
CAPTIONS = {
    "overview": "Both assistants, one harness: same cases, metrics and gates.",
    "gates": "Published numbers reproduced; fresh re-runs pass every gate.",
    "demo": "Bad change on a throwaway branch: top-k 5 → 2.",
    "caught": "Caught: q13 and q35 always passed, now always fail. Never merged.",
    "case": "Drill-down: the expected passage, the answers, every verdict.",
    "judge": "Judge vs 70 blind hand labels: best kappa 0.29. Not trusted, never a gate.",
}


# ---------------------------------------------------------------- narration
def voice_model() -> Path:
    model = VOICES / f"{VOICE}.onnx"
    if not model.exists():
        VOICES.mkdir(parents=True, exist_ok=True)
        shared = SHARED_VOICES / f"{VOICE}.onnx"
        if shared.exists():
            for f in SHARED_VOICES.glob(f"{VOICE}.onnx*"):
                shutil.copy(f, VOICES / f.name)
        else:
            subprocess.run(["python", "-m", "piper.download_voices", VOICE, "--download-dir", str(VOICES)], check=True)
    return model


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def synthesize(lines: dict, folder: Path) -> dict:
    from piper import PiperVoice, SynthesisConfig

    voice = PiperVoice.load(str(voice_model()))
    config = SynthesisConfig(length_scale=SPEED)
    folder.mkdir(parents=True, exist_ok=True)
    durations = {}
    for key, text in lines.items():
        path = folder / f"{key}.wav"
        with wave.open(str(path), "wb") as w:
            voice.synthesize_wav(text, w, syn_config=config)
        durations[key] = round(wav_seconds(path), 2)
    return durations


# ---------------------------------------------------------------- recording
class Recorder:
    """Keeps the screen and the narration in step. Times are video seconds (after the title card)."""

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


def end_card(path: Path, narrated: bool = True):
    img = Image.new("RGB", SIZE, GREEN)
    d = ImageDraw.Draw(img)
    d.rectangle([0, SIZE[1] - 14, SIZE[0], SIZE[1]], fill=BRASS)
    centered(d, 150, "See the dashboard, the code and the decisions", font("georgiab.ttf", 44), INK)
    label_font, link_font = font("arialbd.ttf", 26), font("arial.ttf", 32)
    for i, (label, url) in enumerate(LINKS):
        y = 260 + i * 90
        centered(d, y, label.upper(), label_font, "#E8D9B5")
        centered(d, y + 34, url, link_font, INK)
    if narrated:
        centered(d, 600, "Narration: AI voice (Piper, open source)", font("arial.ttf", 22), CREAM)
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


def narration_cues(timeline: dict) -> list[tuple[float, float, str]]:
    """(start, end, text) for every spoken line, in video time, split into sentences (timed by length)."""
    durations = timeline["durations"]
    lines = [(LEAD, "title")] + [(s["audio"], s["key"]) for s in timeline["steps"]]
    if timeline.get("end_audio") is not None:
        lines.append((timeline["end_audio"], "end"))
    cues = []
    for start, key in lines:
        text, length = NARRATION[key], durations.get(key, 0)
        sentences = [s for s in re.split(r"(?<=[.:?!])\s+(?=[A-Z])", text) if s]  # not after "p.m. checkout"
        total, t = sum(len(s) for s in sentences), start
        for s in sentences:
            span = length * len(s) / total
            cues.append((round(t, 2), round(t + span, 2), s))
            t += span
    return cues


VTT_POSITION = "line:6% position:50% align:center"  # top of the frame: the burned-in captions are at the bottom


def webvtt(cues) -> str:
    return "WEBVTT\n\n" + "\n".join(f"{vtt_time(a)} --> {vtt_time(b)} {VTT_POSITION}\n{text}\n" for a, b, text in cues)


def script_text(cues) -> str:
    out = [
        f"{TITLE}: demo narration (exact words, with start times in the video).",
        "Read these lines over docs/video/demo.mp4 to record your own voice version.",
        "",
    ]
    out += [f"[{int(a // 60)}:{a % 60:04.1f}] {text}" for a, _, text in cues]
    return "\n".join(out) + "\n"


def ffmpeg(*args: str):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True, cwd=WORK)


def mix_narration(timeline: dict, total: float) -> Path:
    """Place each line at its time, then normalise loudness to about -16 LUFS (true peak -1.5 dB), AAC."""
    clips = [("title", LEAD)] + [(s["key"], s["audio"]) for s in timeline["steps"]] + [("end", timeline["end_audio"])]
    inputs, chains = [], []
    for i, (key, at) in enumerate(clips):
        inputs += ["-i", f"voice/{key}.wav"]
        ms = int(at * 1000)
        chains.append(f"[{i}:a]adelay={ms}|{ms},aresample=48000[a{i}]")
    graph = ";".join(chains) + ";" + "".join(f"[a{i}]" for i in range(len(clips)))
    graph += f"amix=inputs={len(clips)}:normalize=0,apad=whole_dur={total:.2f},loudnorm=I=-16:TP=-1.5:LRA=11[out]"
    ffmpeg(
        *inputs,
        "-filter_complex",
        graph,
        "-map",
        "[out]",
        "-t",
        f"{total:.2f}",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-ar",
        "48000",
        "narration.m4a",
    )
    return WORK / "narration.m4a"


def build(timeline: dict, voice: bool) -> Path:
    length = timeline["end"] - timeline["trim"]
    durations = timeline["durations"]
    end_audio = TITLE_SECONDS + length + LEAD if voice else None
    end_seconds = max(6.0, (durations.get("end", 0) + LEAD + 1.2) if voice else 6.0)
    timeline["end_audio"] = end_audio
    total = TITLE_SECONDS + length + end_seconds
    title_card(WORK / "title.png")
    end_card(WORK / "end.png", narrated=voice)
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
    audio = ["-i", str(mix_narration(timeline, total)), "-map", "3:a", "-c:a", "copy"] if voice else []
    ffmpeg(
        *("-loop", "1", "-t", str(TITLE_SECONDS), "-i", "title.png"),
        *("-ss", f"{timeline['trim']:.2f}", "-t", f"{length:.2f}", "-i", "raw.webm"),
        *("-loop", "1", "-t", f"{end_seconds:.2f}", "-i", "end.png"),
        *audio[:2],
        *("-filter_complex", graph, "-map", "[v]"),
        *audio[2:],
        *("-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart"),
        *("-t", f"{total:.2f}"),
        str(out),
    )
    if voice:
        cues = narration_cues(timeline)
        (OUT / "demo.vtt").write_text(webvtt(cues), encoding="utf-8")
        (OUT / "narration-script.txt").write_text(script_text(cues), encoding="utf-8")
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
    and the narration captions track."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg(
        *("-i", str(src), "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-profile:v", "high"),
        *("-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dest)),
    )
    ffmpeg("-ss", "1.5", "-i", str(src), "-frames:v", "1", "-q:v", "3", str(dest.with_suffix(".jpg")))
    if (OUT / "demo.vtt").exists():
        shutil.copy(OUT / "demo.vtt", dest.with_suffix(".vtt"))


def linkedin_copy(dest: Path):
    """A copy with the narration captions burned in at the top (LinkedIn autoplays muted; the step captions stay in
    the band at the bottom) and a 1200x627 thumbnail. The captions go through SRT because libass misplaces the
    WebVTT position hints; Alignment=6 is top-centre in the legacy numbering libass uses for SRT."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    cues = narration_cues(json.loads((WORK / "timeline.json").read_text(encoding="utf-8")))
    srt = "".join(
        f"{i}\n{vtt_time(a).replace('.', ',')} --> {vtt_time(b).replace('.', ',')}\n{text}\n\n"
        for i, (a, b, text) in enumerate(cues, 1)
    )
    (OUT / "demo.srt").write_text(srt, encoding="utf-8")
    style = (
        "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,BackColour=&H99000000,BorderStyle=4,Alignment=6,MarginV=14"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            "demo.mp4",
            "-vf",
            f"subtitles=demo.srt:force_style='{style}'",
            "-c:v",
            "libx264",
            "-crf",
            "22",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(dest),
        ],
        check=True,
        cwd=OUT,
    )
    card = Image.open(WORK / "title.png").convert("RGB")
    width = round(card.height * 1200 / 627)
    left = (card.width - width) // 2
    thumb = card.crop((left, 0, left + width, card.height)).resize((1200, 627))
    thumb.save(dest.with_name("thumbnail.jpg"), quality=88)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rebuild", action="store_true", help="reuse the last recording and narration")
    parser.add_argument("--no-voice", action="store_true", help="captions only, no narration")
    parser.add_argument("--web-out", type=Path, help="also write a web copy (+ .jpg poster and .vtt) here")
    parser.add_argument("--linkedin-out", type=Path, help="also write a burned-in-captions copy here")
    parser.add_argument("--app", default=APP, help="dashboard URL to record (default: the live app)")
    args = parser.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found. Install it (winget install Gyan.FFmpeg) and open a new terminal.")
    voice = not args.no_voice
    if args.rebuild:
        timeline = json.loads((WORK / "timeline.json").read_text(encoding="utf-8"))
    else:
        shutil.rmtree(WORK, ignore_errors=True)
        WORK.mkdir(parents=True)
        durations = synthesize(NARRATION, WORK / "voice") if voice else {}
        timeline = record(durations, args.app)
    out = build(timeline, voice)
    gif(timeline)
    print(f"saved {out.relative_to(ROOT)} and {GIF.relative_to(ROOT)}")
    if args.web_out:
        web_copy(out, args.web_out.resolve())
        print(f"saved {args.web_out} with its .jpg poster and .vtt captions")
    if args.linkedin_out and voice:
        linkedin_copy(args.linkedin_out.resolve())
        print(f"saved {args.linkedin_out} and thumbnail.jpg")


if __name__ == "__main__":
    main()

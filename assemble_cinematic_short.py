"""Assemble AI-generated shots against measured Hindi speech timing; fail closed."""
import json
import subprocess
from pathlib import Path

job = json.loads(Path("selected_job.json").read_text(encoding="utf-8"))
timeline = json.loads(Path("speech_timeline.json").read_text(encoding="utf-8"))
clips = sorted(Path("cinematic_clips").glob("S*.mp4"))
assert len(clips) == len(timeline) == len(job["dialogue"]), "All generated scenes and dialogue required"
assert Path("voice.mp3").is_file(), "Hindi audio missing"
total = float(timeline[-1]["end"])
assert 18 <= total <= 22, f"Hindi speech duration {total:.2f}s is not approximately 20s"
parts = Path("cinematic_parts")
parts.mkdir(exist_ok=True)
for i, (clip, line) in enumerate(zip(clips, timeline)):
    assert clip.name == f"S{i+1:02d}.mp4", "Missing or incorrectly ordered cinematic shot"
    assert line["speaker"] == job["dialogue"][i]["speaker_id"], "Speaker mismatch"
    duration = float(line["end"]) - float(line["start"])
    assert 0.4 < duration <= 12, "Invalid speech segment duration"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(clip),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,"
               "tpad=stop_mode=clone:stop_duration=12,"
               f"trim=duration={duration:.4f},setpts=PTS-STARTPTS",
        "-an", "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
        "-pix_fmt", "yuv420p", str(parts / f"{i:03d}.mp4")
    ], check=True)
with (parts / "concat.txt").open("w") as f:
    for i in range(len(clips)):
        f.write(f"file '{i:03d}.mp4'\n")
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
    "-i", str(parts / "concat.txt"), "-i", "voice.mp3",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
    "-c:a", "aac", "-b:a", "160k", "-pix_fmt", "yuv420p",
    "-t", str(total), "final_short.mp4"
], check=True)
data = json.loads(subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries",
    "format=duration:stream=codec_type,width,height", "-of", "json", "final_short.mp4"
]))
duration = float(data["format"]["duration"])
assert 18 <= duration <= 22, f"Rendered duration invalid: {duration}"
assert abs(duration - total) < 0.35, "Speech/video duration mismatch"
assert any(x.get("codec_type") == "video" and x.get("width") == 1080 and x.get("height") == 1920 for x in data["streams"])
assert any(x.get("codec_type") == "audio" for x in data["streams"])
assert Path("final_short.mp4").stat().st_size > 500000
print("CINEMATIC_TECHNICAL_QA_PASS", len(clips), round(duration, 2))

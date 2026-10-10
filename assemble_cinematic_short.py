"""Build a 20-second vertical Short from actual AI-generated scene clips and Hindi voice."""
import json, subprocess
from pathlib import Path
job=json.loads(Path("selected_job.json").read_text(encoding="utf-8"))
clips=sorted(Path("cinematic_clips").glob("S*.mp4"))
assert len(clips)==len(job["dialogue"]), "All scenes must be AI generated"
assert Path("voice.mp3").is_file(), "Hindi voice missing"
parts=Path("cinematic_parts")
parts.mkdir(exist_ok=True)
for i,clip in enumerate(clips):
    output=parts/f"{i:03d}.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(clip),"-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1","-t",str(20/len(clips)),"-an","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",str(output)],check=True)
with (parts/"concat.txt").open("w") as f:
    for i in range(len(clips)):
        f.write(f"file '{i:03d}.mp4'\n")
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(parts/"concat.txt"),"-i","voice.mp3","-t","20","-c:v","libx264","-c:a","aac","-pix_fmt","yuv420p","final_short.mp4"],check=True)
data=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json","final_short.mp4"]))
assert 18<=float(data["format"]["duration"])<=21
assert any(x.get("codec_type")=="video" and x.get("width")==1080 and x.get("height")==1920 for x in data["streams"])
assert any(x.get("codec_type")=="audio" for x in data["streams"])
print("CINEMATIC_20_SECOND_ASSEMBLY_COMPLETE")

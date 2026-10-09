"""Generate per-speaker Hindi audio and exact segment boundaries for animated Shorts."""
import asyncio,json,os,subprocess,wave,math,struct
from pathlib import Path
import edge_tts
job=json.load(open("selected_job.json",encoding="utf-8"))
dialogue=job.get("dialogue") or [{"speaker_id":s.get("speaker","mother"),"text":s["text"]} for s in job["scenes"]]
voices={"mother":"hi-IN-SwaraNeural","father":"hi-IN-MadhurNeural","child":"hi-IN-SwaraNeural"}
Path("speech_segments").mkdir(exist_ok=True)
def stamp(seconds):
    ms=round(seconds*1000)
    return f"{ms//3600000:02}:{(ms//60000)%60:02}:{(ms//1000)%60:02}.{ms%1000:03}"
async def create():
    for i,line in enumerate(dialogue):
        voice=voices.get(line["speaker_id"],voices["mother"])
        rate="+12%" if line["speaker_id"]=="child" else "-5%"
        await edge_tts.Communicate(line["text"],voice=voice,rate=rate).save(f"speech_segments/{i:03}.mp3")
asyncio.run(create())
timeline=[];start=0.0
with open("captions.vtt","w",encoding="utf-8") as vtt:
    vtt.write("WEBVTT\n\n")
    for i,line in enumerate(dialogue):
        source=f"speech_segments/{i:03}.mp3"
        target=f"speech_segments/{i:03}.wav"
        subprocess.run(["ffmpeg","-nostdin","-loglevel","error","-y","-i",source,"-ar","16000","-ac","1","-c:a","pcm_s16le",target],check=True)
        with wave.open(target,"rb") as wav:
            raw=wav.readframes(wav.getnframes())
            samples=struct.unpack("<"+str(len(raw)//2)+"h",raw)
            length=len(samples)/16000
            # Audio-energy driven mouth animation at 20ms resolution.
            envelope=[]
            for j in range(0,len(samples),320):
                block=samples[j:j+320]
                rms=math.sqrt(sum(x*x for x in block)/max(1,len(block)))/32768
                envelope.append(round(min(1,max(0,(rms-0.008)*10)),3))
        end=start+length
        timeline.append({"speaker":line["speaker_id"],"text":line["text"],"start":round(start,4),"end":round(end,4),"mouth_energy_20ms":envelope})
        vtt.write(f"{i+1}\n{stamp(start)} --> {stamp(end)}\n{line['text']}\n\n")
        start=end
with open("speech_segments/concat.txt","w") as f:
    for i in range(len(dialogue)):
        f.write(f"file '{i:03}.wav'\n")
subprocess.run(["ffmpeg","-nostdin","-loglevel","error","-y","-f","concat","-safe","0","-i","speech_segments/concat.txt","-c:a","pcm_s16le","speech_segments/all.wav"],check=True)
subprocess.run(["ffmpeg","-nostdin","-loglevel","error","-y","-i","speech_segments/all.wav","-c:a","libmp3lame","-q:a","3","voice.mp3"],check=True)
json.dump(timeline,open("speech_timeline.json","w",encoding="utf-8"),ensure_ascii=False)
print("HINDI_DIALOGUE_SEGMENTS",len(timeline),"DURATION",round(start,2))

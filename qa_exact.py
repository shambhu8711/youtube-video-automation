import json,re
from faster_whisper import WhisperModel
j=json.load(open("ffprobe.json")); s=j["streams"]
v=next((x for x in s if x["codec_type"]=="video"),None)
a=next((x for x in s if x["codec_type"]=="audio"),None)
assert v and a and (v["width"],v["height"])==(1080,1920), "Expected 1080x1920 video plus audio"
duration=float(j["format"]["duration"])
assert 18 <= duration <= 60, f"Bad duration {duration}"
model=WhisperModel("tiny.en",device="cpu",compute_type="int8")
segs,_=model.transcribe("exact_audio.wav")
transcript=" ".join(x.text for x in segs).strip()
open("transcript.txt","w").write(transcript)
words=lambda x: re.findall(r"[a-z0-9]+",x.lower())
intended=open("intended.txt").read().strip()
iw=words(intended); tw=words(transcript)
iset=set(iw); tset=set(tw)
coverage=sum(1 for w in iw if w in tset)/max(1,len(iw))
precision=sum(1 for w in tw if w in iset)/max(1,len(tw))
score=2*coverage*precision/max(1e-9,coverage+precision)
open("transcript_score.txt","w").write(str(score))
assert coverage>=0.70 and score>=0.72,(coverage,score,transcript)
print("EXACT_FINAL_SPEECH_QA_PASS",coverage,score)

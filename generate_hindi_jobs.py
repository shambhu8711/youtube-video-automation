"""Build scheduled Hindi Shorts jobs from the user's original script bank."""
import json,os,glob
from datetime import datetime,timedelta,timezone
IST=timezone(timedelta(hours=5,minutes=30))
today=datetime.now(IST).date()
records=[]
for path in sorted(glob.glob("script_bank/hindi_family_comedy_batch_*.json")):
    records.extend(json.load(open(path,encoding="utf-8"))["scripts"])
if not records: raise SystemExit("No Hindi scripts imported")
records.sort(key=lambda s:s["sequence_index"])
os.makedirs("jobs",exist_ok=True)
for offset in (-1,0):
    day=today+timedelta(days=offset)
    for i,h in enumerate(range(0,24,2)):
        # Distinct script per slot; interleaved premise ordering in source.
        idx=((day.toordinal()-datetime(2026,10,9).date().toordinal())*12+i)
        if idx < 0 or idx >= len(records): continue
        script=records[idx]
        key=f"{day:%Y%m%d}-{h:02d}00-{script['script_id'].lower()}"
        path="jobs/"+key+".json"
        if os.path.exists(path): continue
        dialogue=script["dialogue"]
        job={"job_key":key,"source_script_id":script["script_id"],"concept_id":script["concept_id"],
          "language":"hi-IN","title":script["youtube_metadata"]["title"],"description":script["youtube_metadata"]["description"],
          "script":" ".join(d["text"] for d in dialogue),"dialogue":dialogue,
          "scenes":[{"text":d["text"],"speaker":d["speaker_id"],"visual":script["setting_hi"]} for d in dialogue],
          "category_id":"24","tags":script["youtube_metadata"]["tags"],"target_duration_seconds":script["target_duration_seconds"]}
        json.dump(job,open(path,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("HINDI_JOBS_READY",len(records))

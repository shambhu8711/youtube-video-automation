import glob,json,os,re
from datetime import datetime, timezone, timedelta

manual=os.environ.get("MANUAL_JOB","").strip()
files=sorted(glob.glob("jobs/*.json"))
done=set()
for legacy in ("rendered_jobs.txt","published_jobs.txt"):
    if os.path.exists(legacy):
        done.update(x.strip() for x in open(legacy) if x.strip())
for p in glob.glob("state/uploads/*.json"):
    try:
        s=json.load(open(p,encoding="utf-8"))
        if s.get("upload_accepted") and s.get("job_key"): done.add(s["job_key"])
    except Exception: pass

if manual:
    p=manual if manual.startswith("jobs/") else "jobs/"+manual
    if p not in files: raise SystemExit("Requested job not found: "+p)
    mj=json.load(open(p,encoding="utf-8"))
    if mj.get("job_key") in done:
        print("MANUAL_JOB_ALREADY_DONE",mj.get("job_key"))
        open("no_fresh_job","w").write("1")
        raise SystemExit(0)
else:
    now=datetime.now(timezone(timedelta(hours=5,minutes=30)))
    candidates=[]
    for p in files:
        j=json.load(open(p,encoding="utf-8"))
        key=j.get("job_key","")
        m=re.match(r"^(\\d{8})-(\\d{4})-",key)
        if not m or key in done: continue
        due=datetime.strptime(m.group(1)+m.group(2),"%Y%m%d%H%M").replace(tzinfo=now.tzinfo)
        if due <= now: candidates.append((due,p))
    if not candidates:
        print("NO_DUE_FRESH_JOB")
        open("no_fresh_job","w").write("1")
        raise SystemExit(0)
    p=sorted(candidates)[0][1]

j=json.load(open(p,encoding="utf-8"))
for k in ("job_key","title","script","scenes"): assert j.get(k), "Missing "+k
assert len(j["script"].split()) >= 20, "Script too short"
assert len(j["scenes"]) >= 3, "Need at least 3 scenes"
json.dump(j,open("selected_job.json","w"),ensure_ascii=False)
print("SELECTED",j["job_key"],j["title"])

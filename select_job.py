import glob,json,os
manual=os.environ.get("MANUAL_JOB","").strip()
files=sorted(glob.glob("jobs/*.json"))
if manual:
    p=manual if manual.startswith("jobs/") else "jobs/"+manual
    if p not in files: raise SystemExit("Requested job not found: "+p)
else:
    # Treat existing successful workflow artifacts as completed jobs.
    # Recovery jobs can also be explicitly marked here after publication.
    done=set()
    if os.path.exists("published_jobs.txt"):
        done={x.strip() for x in open("published_jobs.txt") if x.strip()}
    candidates=[]
    for p in files:
        j=json.load(open(p))
        if j["job_key"] not in done: candidates.append(p)
    if not candidates: raise SystemExit("No fresh job available; refusing duplicate render")
    p=candidates[0]
j=json.load(open(p))
for k in ("job_key","title","script","scenes"):
    assert j.get(k), "Missing "+k
json.dump(j,open("selected_job.json","w"))
print("SELECTED",j["job_key"],j["title"])

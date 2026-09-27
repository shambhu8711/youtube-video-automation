import glob,json,os
manual=os.environ.get("MANUAL_JOB","").strip()
files=sorted(glob.glob("jobs/*.json"))
rendered=set()
if os.path.exists("rendered_jobs.txt"):
    rendered={x.strip() for x in open("rendered_jobs.txt") if x.strip()}
published=set()
if os.path.exists("published_jobs.txt"):
    published={x.strip() for x in open("published_jobs.txt") if x.strip()}
done=rendered|published
if manual:
    p=manual if manual.startswith("jobs/") else "jobs/"+manual
    if p not in files: raise SystemExit("Requested job not found: "+p)
else:
    candidates=[]
    for p in files:
        j=json.load(open(p))
        if j["job_key"] not in done: candidates.append(p)
    if not candidates:
        print("NO_FRESH_JOB")
        open("no_fresh_job","w").write("1")
        raise SystemExit(0)
    p=candidates[0]
j=json.load(open(p))
for k in ("job_key","title","script","scenes"):
    assert j.get(k), "Missing "+k
assert len(j["script"].split()) >= 20, "Script too short"
assert len(j["scenes"]) >= 3, "Need at least 3 scenes"
json.dump(j,open("selected_job.json","w"))
print("SELECTED",j["job_key"],j["title"])

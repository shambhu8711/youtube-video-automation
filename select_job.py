"""Choose only original Hindi Shorts; fail closed on repeat scripts and concepts."""
import glob,json,os,re,hashlib
from datetime import datetime,timezone,timedelta

def normalize(text):
    return re.sub(r"\s+"," ",str(text).casefold()).strip()
def digest(text):
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()
def job_for(key):
    path="jobs/"+key+".json"
    return json.load(open(path,encoding="utf-8")) if os.path.isfile(path) else None

manual=os.environ.get("MANUAL_JOB","").strip()
files=sorted(glob.glob("jobs/*.json"))
done=set()
published_slugs=set()
published_hashes=set()
published_concepts=set()
published_source_ids=set()
for legacy in ("rendered_jobs.txt","published_jobs.txt"):
    if os.path.exists(legacy):
        done.update(line.strip() for line in open(legacy,encoding="utf-8") if line.strip())
for path in glob.glob("state/uploads/*.json"):
    try:
        state=json.load(open(path,encoding="utf-8"))
        if not state.get("upload_accepted"): continue
        key=state.get("job_key") or os.path.basename(path).removesuffix(".json")
        if not key: continue
        done.add(key)
        published_slugs.add(re.sub(r"^\d{8}-\d{4}-","",key))
        old=job_for(key)
        if old:
            published_hashes.add(digest(old.get("script","")))
            if old.get("concept_id"): published_concepts.add(old["concept_id"])
            if old.get("source_script_id"): published_source_ids.add(old["source_script_id"])
    except (ValueError,OSError,KeyError): continue

now=datetime.now(timezone(timedelta(hours=5,minutes=30)))
candidates=[]
for path in files:
    job=json.load(open(path,encoding="utf-8"))
    key=job.get("job_key","")
    m=re.match(r"^(\d{8})-(\d{4})-",key)
    if not m or job.get("language")!="hi-IN": continue
    if manual and path not in (manual,"jobs/"+manual): continue
    if key in done: continue
    slug=re.sub(r"^\d{8}-\d{4}-","",key)
    if slug in published_slugs or digest(job.get("script","")) in published_hashes:
        print("SKIP_REPEAT_SCRIPT",key); continue
    if job.get("source_script_id") in published_source_ids:
        print("SKIP_REPEAT_SOURCE",key); continue
    # The 1000-script bank has multiple variants per underlying premise.
    # Never publish another variant of a concept already uploaded.
    if job.get("concept_id") and job["concept_id"] in published_concepts:
        print("SKIP_REPEAT_PREMISE",key); continue
    due=datetime.strptime(m.group(1)+m.group(2),"%Y%m%d%H%M").replace(tzinfo=now.tzinfo)
    if due<=now: candidates.append((due,path))
if not candidates:
    print("NO_DUE_UNIQUE_HINDI_JOB")
    open("no_fresh_job","w").write("1")
    raise SystemExit(0)
_,path=min(candidates)
job=json.load(open(path,encoding="utf-8"))
for field in ("job_key","title","script","scenes","source_script_id","concept_id"):
    assert job.get(field), "Missing "+field
assert len(job["script"].split())>=20, "Script too short"
assert len(job["scenes"])>=3, "Need at least 3 scenes"
json.dump(job,open("selected_job.json","w",encoding="utf-8"),ensure_ascii=False)
print("SELECTED_UNIQUE_HINDI",job["job_key"],job["source_script_id"],job["concept_id"])

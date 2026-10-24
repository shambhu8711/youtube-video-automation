"""Daily Reel queue and hourly YouTube publisher. Only publicly accessible, authorized Reels."""
import argparse,json,os,subprocess,sys,datetime
from pathlib import Path
ROOT=Path("reel_queue")
PROFILE="https://www.instagram.com/tinygiggleai07/"
def run(args,timeout=600):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 if p.returncode: raise RuntimeError("Command failed: "+args[0]+" "+p.stderr[-1200:])
 return p.stdout
def discover(entries,seen,limit=24):
 found=[]
 for e in reversed(entries):
  if not isinstance(e,dict): continue
  rid=str(e.get("id") or "")
  url=str(e.get("webpage_url") or e.get("url") or "")
  if rid and rid not in seen and "/reel/" in url:
   seen.add(rid);found.append({"id":rid,"url":url,"title":(e.get("title") or "Funny Short")[:90]})
  if len(found)>=limit: break
 return found
def collect():
 ROOT.mkdir(exist_ok=True)
 history={p.stem for p in Path("state/instagram_uploads").glob("*.json")}
 data=json.loads(run(["yt-dlp","--flat-playlist","--dump-single-json","--playlist-end","150",PROFILE]))
 entries=discover(data.get("entries") or [],history)
 valid=[]
 for item in entries:
  try:
   target=ROOT/(item["id"]+".mp4")
   run(["yt-dlp","--no-playlist","--merge-output-format","mp4","--recode-video","mp4","-o",str(ROOT/(item["id"]+".%(ext)s")),item["url"]])
   if not target.exists() or target.stat().st_size<1024: raise ValueError("MP4 missing")
   probe=json.loads(run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(target)]))
   video=next((s for s in probe.get("streams",[]) if s.get("codec_type")=="video"),None)
   duration=float(probe.get("format",{}).get("duration",0))
   if not video or not (0<duration<=180) or video.get("height",0)<video.get("width",0):
    target.unlink(missing_ok=True);continue
   valid.append(item)
  except Exception as exc:
   print("SKIP_REEL",item["id"],str(exc),file=sys.stderr)
 (ROOT/"manifest.json").write_text(json.dumps({"date_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"reels":valid},indent=2))
 print("DAILY_QUEUE_READY",len(valid))
 if not valid: raise RuntimeError("No accessible valid Reels available for queue")
def publish():
 manifest=json.loads((ROOT/"manifest.json").read_text())
 history={p.stem for p in Path("state/instagram_uploads").glob("*.json")}
 candidate=next((x for x in manifest["reels"] if x["id"] not in history and (ROOT/(x["id"]+".mp4")).is_file()),None)
 if not candidate:
  print("QUEUE_EXHAUSTED");return
 for key in ("YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN"):
  if not os.getenv(key): raise RuntimeError("Missing secret: "+key)
 from google.oauth2.credentials import Credentials
 from google.auth.transport.requests import Request
 from googleapiclient.discovery import build
 from googleapiclient.http import MediaFileUpload
 creds=Credentials(token=None,refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["YOUTUBE_CLIENT_ID"],client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],scopes=["https://www.googleapis.com/auth/youtube.upload"])
 creds.refresh(Request())
 youtube=build("youtube","v3",credentials=creds,cache_discovery=False)
 body={"snippet":{"title":candidate["title"],"description":"Source: "+candidate["url"]+"\n#Shorts","categoryId":"23"},"status":{"privacyStatus":"private","selfDeclaredMadeForKids":False}}
 response=youtube.videos().insert(part="snippet,status",body=body,media_body=MediaFileUpload(str(ROOT/(candidate["id"]+".mp4")),mimetype="video/mp4",resumable=True)).execute()
 record={"instagram_reel_id":candidate["id"],"youtube_video_id":response["id"],"source_url":candidate["url"],"upload_accepted":True,"privacy":"private","publication_verified":False}
 Path("instagram_upload_record.json").write_text(json.dumps(record,indent=2))
 print("PRIVATE_UPLOAD_ACCEPTED",response["id"])
def test():
 items=[{"id":"a","url":"https://www.instagram.com/reel/a/"},{"id":"b","url":"https://www.instagram.com/reel/b/"}]
 assert [x["id"] for x in discover(items,{"a"})]==["b"]
 assert discover(items,{"a","b"})==[]
 print("QUEUE_SELF_TEST_PASSED")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("mode",choices=["collect","publish","self-test"]);args=p.parse_args()
 try: {"collect":collect,"publish":publish,"self-test":test}[args.mode]()
 except Exception as exc: print("PIPELINE_FAILED",str(exc),file=sys.stderr);sys.exit(1)

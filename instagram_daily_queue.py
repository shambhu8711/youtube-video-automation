"""Daily Reel queue and two-hour YouTube publisher. Only publicly accessible, authorized Reels."""
import argparse,json,os,subprocess,sys,datetime,time
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
 # Public Instagram profile enumeration may be blocked by Instagram.
 # Allow a newline-separated, user-maintained list of exact Reel URLs as a fallback.
 urls=[u.strip() for u in os.getenv("INSTAGRAM_REEL_URLS","").splitlines() if "/reel/" in u]
 if urls:
  entries=discover([{"id":u.split("/reel/")[1].split("/")[0].split("?")[0],"url":u} for u in urls],history)
 else:
  try:
   # Instaloader enumerates profile posts; yt-dlp profile URLs are not reliable playlists.
   import instaloader
   loader=instaloader.Instaloader(download_pictures=False,download_videos=False,download_video_thumbnails=False,save_metadata=False,quiet=True,max_connection_attempts=1,request_timeout=20)
   if os.getenv("INSTAGRAM_SESSION_USERNAME") and os.getenv("INSTAGRAM_SESSION_FILE") and Path(os.environ["INSTAGRAM_SESSION_FILE"]).is_file():
    loader.load_session_from_file(os.environ["INSTAGRAM_SESSION_USERNAME"],os.environ["INSTAGRAM_SESSION_FILE"])
   profile=instaloader.Post.from_shortcode(loader.context,"De4iEVhyYrV").owner_profile
   if profile.username!="tinygiggleai07": raise RuntimeError("Reel owner does not match configured source")
   posts=[]
   for post in profile.get_reels():
    if post.is_video:
     posts.append({"id":post.shortcode,"url":"https://www.instagram.com/reel/"+post.shortcode+"/","title":(post.caption or "Funny Short")[:90]})
    if len(posts)>=24: break
   entries=discover(posts,history)
   print("LIVE_DISCOVERY_READY",len(entries))
  except Exception as exc:
   source=Path("sources/instagram-reels.json")
   if not source.is_file():
    raise RuntimeError("INSTAGRAM_DISCOVERY_FAILED: No usable profile feed or saved Reel source. "+str(exc)) from exc
   saved=json.loads(source.read_text())
   if saved.get("profile")!="tinygiggleai07": raise RuntimeError("Unexpected fallback source profile")
   entries=discover(saved.get("reels",[]),history)
   print("DISCOVERY_FALLBACK: Using finite browser-observed Reel list; automatic profile discovery remains unavailable.",file=sys.stderr)
   if not entries: raise RuntimeError("SOURCE_EXHAUSTED: Refresh saved Reel source or restore authenticated profile discovery") from exc
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
  raise RuntimeError("QUEUE_EXHAUSTED: No unpublished video available in queue")
 for key in ("YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN"):
  if not os.getenv(key): raise RuntimeError("Missing secret: "+key)
 from google.oauth2.credentials import Credentials
 from google.auth.transport.requests import Request
 from googleapiclient.discovery import build
 from googleapiclient.http import MediaFileUpload
 creds=Credentials(token=None,refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["YOUTUBE_CLIENT_ID"],client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],scopes=["https://www.googleapis.com/auth/youtube.upload","https://www.googleapis.com/auth/youtube.readonly"])
 creds.refresh(Request())
 youtube=build("youtube","v3",credentials=creds,cache_discovery=False)
 body={"snippet":{"title":candidate["title"],"description":"Source: "+candidate["url"]+"\n#Shorts","categoryId":"23"},"status":{"privacyStatus":"public","selfDeclaredMadeForKids":False}}
 response=youtube.videos().insert(part="snippet,status",body=body,media_body=MediaFileUpload(str(ROOT/(candidate["id"]+".mp4")),mimetype="video/mp4",resumable=True)).execute()
 record={"instagram_reel_id":candidate["id"],"youtube_video_id":response["id"],"source_url":candidate["url"],"upload_accepted":True,"privacy":"public","publication_verified":False}
 Path("instagram_upload_record.json").write_text(json.dumps(record,indent=2))
 
 # Verify YouTube reports the requested public visibility. Upload acceptance alone is not publication.
 try:
  for attempt in range(7):
   details=youtube.videos().list(part="status,processingDetails",id=response["id"]).execute().get("items",[])
   if details:
    status=details[0].get("status",{})
    processing=details[0].get("processingDetails",{}).get("processingStatus","unknown")
    record["youtube_privacy"]=status.get("privacyStatus","unknown")
    record["processing_status"]=processing
    record["publication_verified"]=status.get("privacyStatus")=="public" and processing=="succeeded"
   Path("instagram_upload_record.json").write_text(json.dumps(record,indent=2))
   if record["publication_verified"] or record.get("processing_status") in ("failed","terminated"): break
   if attempt < 6: time.sleep(10)
 except Exception as exc:
  print("PUBLICATION_VERIFICATION_PENDING",str(exc),file=sys.stderr)
 print("PUBLIC_UPLOAD_ACCEPTED",response["id"],"VERIFIED",record["publication_verified"])
def verify_existing():
 from google.oauth2.credentials import Credentials
 from google.auth.transport.requests import Request
 from googleapiclient.discovery import build
 creds=Credentials(token=None,refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["YOUTUBE_CLIENT_ID"],client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],scopes=["https://www.googleapis.com/auth/youtube.readonly"])
 creds.refresh(Request())
 youtube=build("youtube","v3",credentials=creds,cache_discovery=False)
 path=Path("state/instagram_uploads/De4iEVhyYrV.json")
 record=json.loads(path.read_text())
 items=youtube.videos().list(part="status,processingDetails",id=record["youtube_video_id"]).execute().get("items",[])
 if not items: raise RuntimeError("Uploaded video was not returned by YouTube")
 status=items[0].get("status",{})
 processing=items[0].get("processingDetails",{}).get("processingStatus","unknown")
 record.update(youtube_privacy=status.get("privacyStatus","unknown"),processing_status=processing,publication_verified=status.get("privacyStatus")=="public" and processing=="succeeded",verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 path.write_text(json.dumps(record,indent=2)+"\n")
 print("EXISTING_VIDEO_VERIFICATION",json.dumps(record))
 if not record["publication_verified"]: raise RuntimeError("Video is not yet public and successfully processed")
def test():
 items=[{"id":"a","url":"https://www.instagram.com/reel/a/"},{"id":"b","url":"https://www.instagram.com/reel/b/"}]
 assert [x["id"] for x in discover(items,{"a"})]==["b"]
 assert discover(items,{"a","b"})==[]
 assert len(discover(items,set(),limit=1))==1
 print("QUEUE_SELF_TEST_PASSED")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("mode",choices=["collect","publish","self-test","verify"]);args=p.parse_args()
 try: {"collect":collect,"publish":publish,"self-test":test,"verify":verify_existing}[args.mode]()
 except Exception as exc: print("PIPELINE_FAILED",str(exc),file=sys.stderr);sys.exit(1)

"""Authorized public Instagram Reel intake; one PRIVATE test upload per run.
Never claim public publication without independent verification.
"""
import argparse, json, os, subprocess, sys, tempfile, time
from pathlib import Path
PROFILE="https://www.instagram.com/tinygiggleai07/"
STATE=Path("state/instagram_uploads")
def command(*args):
    p=subprocess.run(args,text=True,capture_output=True,timeout=240)
    if p.returncode:
        raise RuntimeError(f"{args[0]} failed ({p.returncode}): {p.stderr[-1200:]}")
    return p.stdout
def choose(entries, done):
    for e in reversed(entries):
        if not isinstance(e,dict): continue
        rid=str(e.get("id") or "")
        url=str(e.get("webpage_url") or e.get("url") or "")
        if rid and rid not in done and "/reel/" in url: return rid,url,e
    return None
def selftest():
    items=[{"id":"1","url":"https://www.instagram.com/reel/1/"},{"id":"2","url":"https://www.instagram.com/reel/2/"}]
    assert choose(items,{"1"})[0]=="2"
    assert choose(items,{"1","2"}) is None
    assert choose([{"id":"3","url":"https://example.org/x"}],set()) is None
    print("LOCAL_SELF_TEST_PASSED")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test: return selftest()
    for k in ("YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN"):
        if not os.getenv(k): raise RuntimeError("Missing secret: "+k)
    data=json.loads(command("yt-dlp","--flat-playlist","--dump-single-json","--playlist-end","100",PROFILE))
    done={p.stem for p in STATE.glob("*.json")}
    candidate=choose(data.get("entries") or [],done)
    if not candidate:
        print("NO_NEW_ACCESSIBLE_REELS")
        return
    rid,url,entry=candidate
    with tempfile.TemporaryDirectory() as temp:
        command("yt-dlp","--no-playlist","--merge-output-format","mp4","--recode-video","mp4","-o",str(Path(temp)/"reel.%(ext)s"),url)
        video=Path(temp)/"reel.mp4"
        if not video.is_file() or video.stat().st_size<1024: raise RuntimeError("Valid MP4 missing after download")
        probe=json.loads(command("ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(video)))
        streams=[s for s in probe.get("streams",[]) if s.get("codec_type")=="video"]
        duration=float(probe.get("format",{}).get("duration",0))
        if not streams or duration<=0 or duration>180: raise RuntimeError("Video failed Shorts duration/stream validation")
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        creds=Credentials(token=None,refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["YOUTUBE_CLIENT_ID"],client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],scopes=["https://www.googleapis.com/auth/youtube.upload"])
        creds.refresh(Request())
        youtube=build("youtube","v3",credentials=creds,cache_discovery=False)
        title=(entry.get("title") or "Funny Short")[:90]
        body={"snippet":{"title":title,"description":"Original Reel: "+url+"\n#Shorts","categoryId":"23"},"status":{"privacyStatus":"private","selfDeclaredMadeForKids":False}}
        upload=youtube.videos().insert(part="snippet,status",body=body,media_body=MediaFileUpload(str(video),mimetype="video/mp4",resumable=True)).execute()
        vid=upload["id"]
        # Immediately persist acceptance. Avoid a blind retry on subsequent API verification failure.
        record={"instagram_reel_id":rid,"source_url":url,"youtube_video_id":vid,"upload_accepted":True,"privacy":"private","publication_verified":False}
        Path("instagram_upload_record.json").write_text(json.dumps(record,indent=2))
        try:
            status=youtube.videos().list(part="status,processingDetails",id=vid).execute().get("items",[])
            record["youtube_found"]=bool(status)
            record["processing_status"]=(status[0].get("processingDetails",{}).get("processingStatus") if status else "unknown")
            Path("instagram_upload_record.json").write_text(json.dumps(record,indent=2))
        except Exception as e:
            print("VERIFY_DEFERRED",str(e),file=sys.stderr)
        print("PRIVATE_UPLOAD_ACCEPTED",vid,"PUBLICATION_NOT_VERIFIED")
if __name__=="__main__":
    try: main()
    except Exception as e:
        print("REEL_PIPELINE_FAILED",str(e),file=sys.stderr)
        sys.exit(1)

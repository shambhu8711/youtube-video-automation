"""Stage one publicly accessible Instagram Reel privately on YouTube."""
import argparse,json,os,subprocess,sys,tempfile
from pathlib import Path
PROFILE="https://www.instagram.com/tinygiggleai07/"
STATE=Path("state/instagram_uploads")
def run(*args):
    return subprocess.run(args,check=True,capture_output=True,text=True).stdout
def find_new(entries,uploaded):
    for e in reversed(entries):
        if not isinstance(e,dict): continue
        url=e.get("webpage_url") or e.get("url") or ""
        rid=str(e.get("id") or "")
        if rid and rid not in uploaded and ("/reel/" in url or "/reels/" in url):
            return rid,url,e
    return None
def self_test():
    sample=[{"id":"old","url":"https://www.instagram.com/reel/old/"},{"id":"new","url":"https://www.instagram.com/reel/new/"}]
    assert find_new(sample,{"old"})[0]=="new"
    assert find_new(sample,{"old","new"}) is None
    assert find_new([{"id":"x","url":"https://example.com/x"}],set()) is None
    print("LOCAL_SELF_TEST_PASSED")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test: return self_test()
    for key in ("YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN"):
        if not os.getenv(key): raise RuntimeError("Missing YouTube credential: "+key)
    data=json.loads(run("yt-dlp","--flat-playlist","--dump-single-json","--playlist-end","30",PROFILE))
    choice=find_new(data.get("entries") or [],{p.stem for p in STATE.glob("*.json")})
    if choice is None:
        print("NO_NEW_ACCESSIBLE_REELS")
        return
    rid,url,entry=choice
    with tempfile.TemporaryDirectory() as tmp:
        run("yt-dlp","--no-playlist","-f","bv*+ba/b","--merge-output-format","mp4","--recode-video","mp4","-o",str(Path(tmp)/"reel.%(ext)s"),url)
        video=Path(tmp)/"reel.mp4"
        if not video.is_file(): raise RuntimeError("Downloaded Reel is not MP4: "+url)
        # Import Google dependencies only for actual upload, not local smoke testing.
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        creds=Credentials(token=None,refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["YOUTUBE_CLIENT_ID"],client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],scopes=["https://www.googleapis.com/auth/youtube.upload"])
        creds.refresh(Request())
        yt=build("youtube","v3",credentials=creds,cache_discovery=False)
        body={"snippet":{"title":(entry.get("title") or "Funny Short")[:90],"description":"Original Reel: "+url+"\n#Shorts","categoryId":"23"},"status":{"privacyStatus":"private","selfDeclaredMadeForKids":False}}
        result=yt.videos().insert(part="snippet,status",body=body,media_body=MediaFileUpload(str(video),mimetype="video/mp4",resumable=True)).execute()
        Path("instagram_upload_record.json").write_text(json.dumps({"instagram_reel_id":rid,"source_url":url,"youtube_video_id":result["id"],"privacy":"private","publication_verified":False},indent=2))
        print("PRIVATE_UPLOAD_ACCEPTED",result["id"],"PUBLICATION_NOT_VERIFIED")
if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("REEL_PIPELINE_FAILED",str(exc),file=sys.stderr)
        sys.exit(1)

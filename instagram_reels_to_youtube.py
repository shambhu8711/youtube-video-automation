"""Publish at most one accessible, authorized Instagram Reel per run.
No Instagram login bypass; fail closed when the public profile cannot be read.
"""
import json, os, subprocess, sys, pathlib, tempfile, hashlib
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PROFILE="https://www.instagram.com/tinygiggleai07/"
STATE=pathlib.Path("state/instagram_uploads")
def run(*args):
    return subprocess.run(args,check=True,text=True,capture_output=True).stdout
def main():
    for key in ("YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN"):
        if not os.getenv(key):
            raise RuntimeError("Missing YouTube credential: "+key)
    # yt-dlp uses only publicly accessible content; do not provide browser cookies.
    data=json.loads(run("yt-dlp","--flat-playlist","--dump-single-json","--playlist-end","30",PROFILE))
    entries=data.get("entries") or []
    uploaded={p.stem for p in STATE.glob("*.json")}
    choices=[]
    for entry in entries:
        url=entry.get("webpage_url") or entry.get("url") or ""
        reel_id=str(entry.get("id") or "")
        if reel_id and reel_id not in uploaded and ("/reel/" in url or entry.get("_type")=="url"):
            choices.append((reel_id,url,entry))
    if not choices:
        print("NO_NEW_ACCESSIBLE_REELS")
        return
    reel_id,url,entry=choices[-1]
    with tempfile.TemporaryDirectory() as temp:
        video=str(pathlib.Path(temp)/"reel.mp4")
        run("yt-dlp","--no-playlist","--merge-output-format","mp4","-o",video,url)
        if not pathlib.Path(video).exists():
            raise RuntimeError("No downloadable MP4: "+url)
        creds=Credentials(token=None,refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["YOUTUBE_CLIENT_ID"],client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],scopes=["https://www.googleapis.com/auth/youtube.upload"])
        creds.refresh(Request())
        yt=build("youtube","v3",credentials=creds,cache_discovery=False)
        title=(entry.get("title") or "Funny Short")[:90]
        body={"snippet":{"title":title,"description":"Original Reel: "+url+"\n#Shorts","categoryId":"23"},"status":{"privacyStatus":"private","selfDeclaredMadeForKids":False}}
        result=yt.videos().insert(part="snippet,status",body=body,media_body=MediaFileUpload(video,mimetype="video/mp4",resumable=True)).execute()
        record={"instagram_reel_id":reel_id,"source_url":url,"youtube_video_id":result["id"],"privacy":"private","publication_verified":False}
        pathlib.Path("instagram_upload_record.json").write_text(json.dumps(record,indent=2))
        print("PRIVATE_UPLOAD_ACCEPTED",result["id"],"PUBLICATION_NOT_VERIFIED")
if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("REEL_PIPELINE_FAILED",str(exc),file=sys.stderr)
        sys.exit(1)

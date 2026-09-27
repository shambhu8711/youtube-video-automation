import argparse, json, os, sys, time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

SCOPE="https://www.googleapis.com/auth/youtube.upload"
REQUIRED=("YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN")

def require_env():
    missing=[k for k in REQUIRED if not os.environ.get(k,"").strip()]
    if missing:
        raise SystemExit("CONFIG_ERROR missing GitHub Actions secrets: "+", ".join(missing))

def creds():
    require_env()
    c=Credentials(token=None,refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],scopes=[SCOPE])
    c.refresh(Request())
    return c

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--video",required=True); p.add_argument("--job",required=True)
    p.add_argument("--privacy",default="public",choices=["public","unlisted","private"])
    p.add_argument("--thumbnail")
    p.add_argument("--result",default="youtube_result.json")
    p.add_argument("--state",default="youtube_upload_state.json")
    a=p.parse_args()
    job=json.load(open(a.job,encoding="utf-8"))
    yt=build("youtube","v3",credentials=creds(),cache_discovery=False)

    # Idempotency inside a run: if YouTube already accepted this job, never upload it again.
    if os.path.exists(a.state):
        state=json.load(open(a.state))
        vid=state.get("video_id")
        if vid:
            out={"video_id":vid,"url":"https://www.youtube.com/watch?v="+vid,
                 "privacy":a.privacy,"processing":"verification_pending",
                 "upload_accepted":True,"job_key":job.get("job_key")}
            json.dump(out,open(a.result,"w"),indent=2)
            print("UPLOAD_ALREADY_ACCEPTED",vid,flush=True)
            return

    body={"snippet":{"title":job["title"][:100],
        "description":job.get("description","") or "#Shorts",
        "categoryId":str(job.get("category_id","22")),
        "tags":job.get("tags",["Shorts"])},
        "status":{"privacyStatus":a.privacy,"selfDeclaredMadeForKids":False}}
    media=MediaFileUpload(a.video,mimetype="video/mp4",chunksize=8*1024*1024,resumable=True)
    req=yt.videos().insert(part="snippet,status",body=body,media_body=media,notifySubscribers=False)
    response=None
    while response is None:
        status,response=req.next_chunk()
        if status: print(f"UPLOAD {int(status.progress()*100)}%",flush=True)
    vid=response["id"]
    state={"video_id":vid,"job_key":job.get("job_key"),"created_at":time.time(),
           "privacy_requested":a.privacy,"upload_accepted":True}
    json.dump(state,open(a.state,"w"),indent=2)
    out={"video_id":vid,"url":"https://www.youtube.com/watch?v="+vid,
         "privacy":a.privacy,"processing":"verification_pending",
         "upload_accepted":True,"job_key":job.get("job_key")}
    json.dump(out,open(a.result,"w"),indent=2)
    if a.thumbnail and os.path.exists(a.thumbnail):
        tmedia=MediaFileUpload(a.thumbnail,mimetype="image/jpeg",resumable=False)
        yt.thumbnails().set(videoId=vid,media_body=tmedia).execute()
        state["thumbnail_uploaded"]=True
        json.dump(state,open(a.state,"w"),indent=2)
        print("THUMBNAIL_ACCEPTED",vid,flush=True)
    print("UPLOAD_ACCEPTED",vid,flush=True)

if __name__=="__main__":
    try:
        main()
    except RefreshError as e:
        print("OAUTH_ERROR",str(e),file=sys.stderr,flush=True); sys.exit(78)
    except HttpError as e:
        code=getattr(e.resp,"status",None)
        print("YOUTUBE_API_ERROR",code,str(e),file=sys.stderr,flush=True)
        sys.exit(75 if code in (429,500,502,503,504) else 78)

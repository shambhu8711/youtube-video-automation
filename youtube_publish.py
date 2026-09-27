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

def verify(yt,vid,privacy,result,job_key,timeout=900):
    deadline=time.time()+timeout
    last={}
    while time.time()<deadline:
        r=yt.videos().list(part="status,processingDetails",id=vid).execute()
        if not r.get("items"): raise RuntimeError("Uploaded video not returned by videos.list: "+vid)
        last=r["items"][0]
        proc=last.get("processingDetails",{}).get("processingStatus","unknown")
        st=last.get("status",{})
        upload_status=st.get("uploadStatus")
        actual_privacy=st.get("privacyStatus")
        print("VERIFY",vid,proc,actual_privacy,upload_status,flush=True)
        if proc=="failed" or upload_status in ("failed","rejected"):
            raise RuntimeError("YouTube rejected/failed video: "+json.dumps(last))
        if proc=="succeeded" and upload_status=="processed":
            if actual_privacy!=privacy:
                raise RuntimeError(f"Requested {privacy} but YouTube reports {actual_privacy}. API project may require YouTube compliance audit.")
            out={"video_id":vid,"url":"https://www.youtube.com/watch?v="+vid,
                 "privacy":actual_privacy,"processing":"succeeded","job_key":job_key}
            json.dump(out,open(result,"w"),indent=2)
            print("PUBLISHED",vid,flush=True)
            return
        time.sleep(15)
    raise TimeoutError("YouTube processing did not reach verified processed state: "+json.dumps(last))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--video",required=True); p.add_argument("--job",required=True)
    p.add_argument("--privacy",default="public",choices=["public","unlisted","private"])
    p.add_argument("--result",default="youtube_result.json")
    p.add_argument("--state",default="youtube_upload_state.json")
    a=p.parse_args()
    job=json.load(open(a.job,encoding="utf-8"))
    yt=build("youtube","v3",credentials=creds(),cache_discovery=False)

    if os.path.exists(a.state):
        state=json.load(open(a.state))
        vid=state.get("video_id")
        if vid:
            print("RESUME_VERIFY",vid,flush=True)
            return verify(yt,vid,a.privacy,a.result,job.get("job_key"))

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
    json.dump({"video_id":vid,"job_key":job.get("job_key"),"created_at":time.time()},open(a.state,"w"),indent=2)
    print("UPLOADED",vid,flush=True)
    verify(yt,vid,a.privacy,a.result,job.get("job_key"))

if __name__=="__main__":
    try:
        main()
    except RefreshError as e:
        print("OAUTH_ERROR",str(e),file=sys.stderr,flush=True); sys.exit(78)
    except HttpError as e:
        code=getattr(e.resp,"status",None)
        print("YOUTUBE_API_ERROR",code,str(e),file=sys.stderr,flush=True)
        sys.exit(75 if code in (429,500,502,503,504) else 78)

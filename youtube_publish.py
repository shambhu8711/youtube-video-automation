import argparse, json, os, sys, time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

SCOPE="https://www.googleapis.com/auth/youtube.upload"

def creds():
    c=Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=[SCOPE],
    )
    c.refresh(Request())
    return c

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--video",required=True)
    p.add_argument("--job",required=True)
    p.add_argument("--privacy",default="public",choices=["public","unlisted","private"])
    p.add_argument("--result",default="youtube_result.json")
    a=p.parse_args()
    job=json.load(open(a.job,encoding="utf-8"))
    yt=build("youtube","v3",credentials=creds(),cache_discovery=False)
    body={"snippet":{
        "title":job["title"][:100],
        "description":job.get("description","") or "#Shorts",
        "categoryId":str(job.get("category_id","22")),
        "tags":job.get("tags",["Shorts"])
    },"status":{"privacyStatus":a.privacy,"selfDeclaredMadeForKids":False}}
    media=MediaFileUpload(a.video,mimetype="video/mp4",chunksize=8*1024*1024,resumable=True)
    req=yt.videos().insert(part="snippet,status",body=body,media_body=media)
    response=None
    while response is None:
        status,response=req.next_chunk()
        if status: print(f"UPLOAD {int(status.progress()*100)}%",flush=True)
    vid=response["id"]
    print("UPLOADED",vid,flush=True)
    deadline=time.time()+900
    last={}
    while time.time()<deadline:
        r=yt.videos().list(part="status,processingDetails",id=vid).execute()
        if not r.get("items"): raise RuntimeError("Uploaded video not returned by videos.list")
        last=r["items"][0]
        proc=last.get("processingDetails",{}).get("processingStatus","unknown")
        privacy=last.get("status",{}).get("privacyStatus")
        upload_status=last.get("status",{}).get("uploadStatus")
        print("VERIFY",proc,privacy,upload_status,flush=True)
        if proc=="failed": raise RuntimeError("YouTube processing failed: "+json.dumps(last))
        if proc=="succeeded" and upload_status=="processed":
            if privacy!=a.privacy:
                raise RuntimeError(f"Requested {a.privacy} but YouTube reports {privacy}")
            out={"video_id":vid,"url":"https://www.youtube.com/watch?v="+vid,"privacy":privacy,"processing":"succeeded","job_key":job.get("job_key")}
            json.dump(out,open(a.result,"w"),indent=2)
            print("PUBLISHED",vid,flush=True)
            return
        time.sleep(15)
    raise TimeoutError("YouTube processing did not reach verified processed state within 15 minutes: "+json.dumps(last))

if __name__=="__main__":
    main()

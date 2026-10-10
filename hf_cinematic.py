"""Fail-closed Hugging Face ZeroGPU cinematic scene generator.

Usage:
  HF_TOKEN=... HF_SPACE=zerogpu-aoti/wan2-2-fp8da-aoti-faster \
  HF_API_NAME=/generate HF_IMAGE_URL=https://... \
  python hf_cinematic.py

The endpoint and argument layout are NOT assumed: call --inspect first, then
configure HF_API_NAME and HF_INPUT_JSON using the published Gradio API schema.
HF_INPUT_JSON must be a JSON array of positional arguments with literal
"{{PROMPT}}" and optionally "{{IMAGE}}" placeholders. The Space may change
its schema without warning. Never silently substitute cartoon footage.
"""
import argparse
import json
import os
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--plan", default="cinematic_shot_plan.json")
    parser.add_argument("--out", default="cinematic_clips")
    args = parser.parse_args()
    try:
        from gradio_client import Client, handle_file
    except ImportError as exc:
        raise SystemExit("Install gradio_client: pip install gradio_client") from exc
    space = os.getenv("HF_SPACE", "zerogpu-aoti/wan2-2-fp8da-aoti-faster")
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        raise SystemExit("HF_TOKEN is required; configure GitHub Actions secret")
    client = Client(space, token=token)
    if args.inspect:
        client.view_api()
        return
    api_name = os.getenv("HF_API_NAME", "").strip()
    template = os.getenv("HF_INPUT_JSON", "").strip()
    if not api_name or not template:
        raise SystemExit("Set HF_API_NAME and HF_INPUT_JSON after inspecting the actual Space API")
    try:
        inputs = json.loads(template)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid HF_INPUT_JSON: {exc}") from exc
    if not isinstance(inputs, list) or not any("{{PROMPT}}" in str(v) for v in inputs):
        raise SystemExit("HF_INPUT_JSON must be a JSON list containing {{PROMPT}}")
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    if plan.get("render_mode") != "cinematic_ai_only" or not plan.get("shots"):
        raise SystemExit("Invalid cinematic shot plan")
    image_url = os.getenv("HF_IMAGE_URL", "").strip()
    if any("{{IMAGE}}" in str(v) for v in inputs) and not image_url:
        raise SystemExit("HF_IMAGE_URL reference image is required for image-to-video Space")
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    from shutil import copyfile
    for shot in plan["shots"]:
        shot_id = shot["shot_id"]
        target = output / f"{shot_id}.mp4"
        if target.exists() and target.stat().st_size > 100_000:
            print("SKIP_EXISTING_CLIP", shot_id)
            continue
        values = []
        for v in inputs:
            if isinstance(v, str):
                v = v.replace("{{PROMPT}}", shot["visual_prompt"])
                if "{{IMAGE}}" in v:
                    if v != "{{IMAGE}}":
                        raise SystemExit("{{IMAGE}} must be a standalone argument")
                    v = handle_file(image_url)
            values.append(v)
        print("SUBMIT_CINEMATIC_SHOT", shot_id, flush=True)
        result = client.predict(*values, api_name=api_name)
        candidates = result if isinstance(result, (tuple, list)) else [result]
        video_path = None
        for item in candidates:
            if isinstance(item, dict):
                item = item.get("video") or item.get("path") or item.get("name")
            if isinstance(item, str) and item.lower().split("?")[0].endswith(".mp4"):
                video_path = item
                break
        if not video_path:
            raise RuntimeError(f"No MP4 output returned for {shot_id}: {str(result)[:250]}")
        path = Path(video_path)
        if not path.is_file():
            raise RuntimeError(f"Space returned inaccessible video for {shot_id}")
        copyfile(path, target)
        if target.stat().st_size < 100_000:
            target.unlink(missing_ok=True)
            raise RuntimeError(f"Invalid video size for {shot_id}")
        print("CINEMATIC_SHOT_SAVED", shot_id, target, flush=True)
    print("ALL_CINEMATIC_CLIPS_GENERATED; NOT PUBLISHED; QA STILL REQUIRED")

if __name__ == "__main__":
    main()

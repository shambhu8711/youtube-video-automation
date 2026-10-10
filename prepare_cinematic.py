"""Provider-neutral cinematic scene manifest. No AI video is fabricated here.

Reads selected_job.json, validates source and dialogue, emits a reproducible
9:16 cinematic shot plan. This module intentionally never uploads or renders
Pillow cartoons when no real video provider is configured.
"""
import hashlib
import json
import os
import re
from pathlib import Path

JOB = Path(os.environ.get("JOB_FILE", "selected_job.json"))
OUT = Path(os.environ.get("SHOT_PLAN", "cinematic_shot_plan.json"))
STYLE = (
    "Vertical 9:16 cinematic high-quality 3D animation, original Indian family "
    "characters, physically believable movement, consistent facial identity, "
    "expressive eyes and hands, natural cinematic lighting, textured Indian "
    "home or village environment, smooth camera motion, clear uncluttered "
    "composition, no embedded text, no watermark, no duplicate frames."
)
CHARACTERS = {
    "mother": "Indian mother, adult, teal clothing, dark tied-back hair",
    "father": "Indian father, adult, warm orange shirt, short dark hair",
    "child": "Indian child, yellow clothing, short dark hair",
}

def main():
    job = json.loads(JOB.read_text(encoding="utf-8"))
    for key in ("job_key", "source_script_id", "concept_id", "title", "dialogue"):
        if not job.get(key):
            raise ValueError(f"Missing {key}")
    dialogue = job["dialogue"]
    if not isinstance(dialogue, list) or len(dialogue) < 3:
        raise ValueError("At least three dialogue segments required")
    scene_data = job.get("scenes") or []
    if len(scene_data) != len(dialogue):
        raise ValueError("Scenes and dialogue count differ")
    shots = []
    for i, (line, scene) in enumerate(zip(dialogue, scene_data)):
        speaker = line.get("speaker_id")
        spoken = str(line.get("text", "")).strip()
        if speaker not in CHARACTERS or not spoken:
            raise ValueError(f"Invalid speaker or empty dialogue at shot {i+1}")
        if scene.get("text") != spoken:
            raise ValueError(f"Scene/dialogue mismatch at shot {i+1}")
        visual = re.sub(r"\s+", " ", str(scene.get("visual", ""))).strip()
        if not visual:
            raise ValueError(f"Missing visual at shot {i+1}")
        prompt = (
            f"{STYLE} Character: {CHARACTERS[speaker]}. "
            f"Setting: {visual}. The character is visibly speaking in Hindi "
            "with natural lip movements, purposeful gestures and changing "
            "facial expression. Medium close-up with gentle cinematic "
            "camera movement. Maintain identical character identity across "
            "all shots. Match the action to the spoken story, no generic "
            "intro or repeated stock movement."
        )
        shots.append({
            "shot_id": f"S{i+1:02d}", "speaker_id": speaker,
            "dialogue_hi": spoken, "visual_prompt": prompt,
            "aspect_ratio": "9:16", "requires_lipsync": True,
            "requires_motion": True
        })
    output = {
        "schema_version": 1, "job_key": job["job_key"],
        "source_script_id": job["source_script_id"],
        "concept_id": job["concept_id"],
        "title": job["title"], "render_mode": "cinematic_ai_only",
        "style": STYLE, "characters": CHARACTERS, "shots": shots,
        "source_sha256": hashlib.sha256(
            json.dumps(job, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("CINEMATIC_SHOT_PLAN_READY", job["job_key"], len(shots))

if __name__ == "__main__":
    main()

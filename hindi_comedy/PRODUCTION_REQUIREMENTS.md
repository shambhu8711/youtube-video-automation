# Hindi Family Comedy Shorts — production requirements

## Visual style
Use photorealistic, original fictional Indian family characters, not 2D cartoons. Keep face, hair, clothing, body proportions and props consistent within and across shots. Use reference images and stable character IDs.

## Hindi speech and lip sync
Generate separate Hindi TTS segments for each dialogue speaker_id and retain per-segment audio and timestamps. Drive facial animation from the actual final speech audio (prefer phoneme/viseme alignment); no generic mouth loops. Only the active speaker's mouth should articulate speech; listeners blink and react naturally. Preserve pauses, timing and expressions. Align subtitles to final speech timing.

## Output
Vertical 9:16 at 1080x1920. Natural camera movement, gestures and eye contact. Use licensed/original music and SFX beneath intelligible speech. Preserve punchline and reaction.

## Mandatory pre-publish QA
- Verify voice-to-character mapping and Hindi pronunciation.
- Inspect all dialogue segments for lip-sync offset, drift, frozen mouths and wrong-speaker mouth movement.
- Check face/wardrobe/prop consistency and unnatural expressions.
- Verify captions follow spoken dialogue and safe margins.
- Block upload on any failed check; do not silently downgrade to cartoon slides or generic narration.
- Log script_id, concept_id, output hash and YouTube video_id to prevent duplicates.

## Deployment
Existing render.py is a stylized English text-and-icon renderer and cannot satisfy these requirements. Implement and validate a photorealistic video and lip-sync pipeline on this feature branch before enabling production publishing. Do not claim lip-sync quality has been verified until rendered footage has been inspected.

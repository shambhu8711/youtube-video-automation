# Free cloud cinematic Shorts: deployment status

## Requirements
- Mobile-only operation; no user's computer, no paid video subscription.
- Original Hindi comedy, cinematic animated people, scene-specific opening, synchronized Hindi dialogue, no duplicate scripts or uploads.
- Delayed publishing is acceptable; poor-quality fallback publishing is not.

## Honest infrastructure limitation
GitHub-hosted ubuntu-latest runners have no guaranteed NVIDIA GPU and cannot render production-quality Wan/ComfyUI cinematic clips. Free public hosted video tools have limited quotas and generally do not provide a stable, unattended, authorized generation API. ChatGPT Plus is not an API video-generation quota.

**No functioning unlimited free cloud video-generation provider is currently connected to this repository.** Do not mark this pipeline production-ready or resume the Pillow cartoon renderer.

## Safe architecture when a supported free provider is connected
1. Scheduled GitHub Actions discovers due jobs and reserves unique job_key / source_script_id / concept_id.
2. Submit script scenes, character references, aspect ratio 9:16 to a provider through its documented, authorized API (no website scraping or bypassing quotas).
3. If unavailable, rate-limited, or out of credits: retain the job and retry on the next schedule, without uploading.
4. Download completed original animated scenes and assemble with Hindi per-speaker audio.
5. Check scene-to-script match, character consistency, actual movement, audio duration, lip-sync, originality, watermarks, and platform policies. If a check cannot be automated reliably, fail closed.
6. Only then publish once and record the YouTube video ID in state/uploads.

## Current deployment
The publish workflow deliberately fails before rendering/uploading until a verified cloud cinematic generator and QA are integrated. Do not remove this safeguard to claim a free automated solution.

## Next unblocker
A verified provider with a genuinely free unattended API, sufficient ongoing quotas, and commercial posting rights, or a donated GPU runner. Either must be tested end-to-end before scheduled publishing resumes.

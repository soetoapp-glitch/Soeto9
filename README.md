# MotionStock Mobile — starter skill

A runnable Claude Code skill starter for iPad/mobile cloud workflows. Reads XLSX or CSV, generates English prompts and Shutterstock-shaped metadata CSV, and renders **generic abstract MP4 preview** clips using Pillow + FFmpeg.

**Important limitation:** generic previews do not depict each idea. They are not finished, semantically accurate stock submissions. The skill instructions tell Claude Code to implement concept-specific scenes before calling them final. Metadata is a draft pending content verification and marketplace category/flag review. No automatic Shutterstock uploading is included.

## Setup
1. Create a GitHub repository and upload/unzip this package into it.
2. Open Claude Code on the web/mobile and select the repository.
3. Install Python dependencies with `pip install -r requirements.txt`; install FFmpeg and FFprobe in the cloud environment.
4. Upload your input XLSX/CSV into `inputs/`.
5. Ask Claude Code: `Use the motionstock skill. Run a one-item render test, verify MP4, then implement unique icon-specific animations for every source idea. Validate output and metadata.`

## CLI
`python scripts/produce.py --input inputs/ideas.xlsx --output outputs --limit 1 --render --width 640 --height 360 --duration 3`

Without `--render`, prompts and draft metadata are generated without MP4. `--render` generates generic MP4 previews, not semantic final videos. Production 4K uses `--width 3840 --height 2160` after testing; it requires significantly more resources.

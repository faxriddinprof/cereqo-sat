# Cereqo SAT demo

Cereqo is a mobile-first Django demo for a connected SAT study journey. The desktop experience uses a top navigation bar and a separate contextual sidebar inside each course. The demo catalog includes a complete 8-week SAT course plus focused Math and Reading & Writing courses. Every course follows a clear course → section → lesson → final test → result structure. Video lessons, homework autosave/submission, profile results, points, ranking, and the course-generated schedule remain connected throughout the flow. The interface supports Uzbek and English, along with persistent light and dark themes.

## Run locally on macOS

```bash
cd /path/to/cereqo-sat
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The sample learner is Alex Morgan; registration is intentionally not required.

Reset all demo progress to the initial checkpoint states with:

```bash
python manage.py seed_demo --reset
```

The lesson video is stored locally in `static/cereqo/video/demo-lesson-video.mp4`; there is no runtime media dependency. It is a 30-second excerpt from *Big Buck Bunny* by Blender Foundation, used under CC BY 3.0; see `THIRD_PARTY_NOTICES.md`.

## Verification

```bash
python manage.py check
python manage.py test
```

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for AdminHMD and bundled asset attribution.

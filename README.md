# Cereqo SAT demo

Cereqo is a mobile-first Django demo for a connected SAT study journey: lesson, video, homework autosave/submission, points and ranking, plus attendance. The interface supports Uzbek and English, along with persistent light and dark themes.

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

Reset all demo progress to the initial four homework states with:

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

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

Open <http://127.0.0.1:8000/>. The homepage and course catalog are public. Course content, tasks, ranking, schedule, and profiles require login.

## Share a temporary public preview from your Mac

This mode keeps Django bound to your laptop and publishes it through a temporary
Cloudflare Quick Tunnel URL. It is intended for demos and testing, not permanent
production hosting.

Install the tunnel client once:

```bash
brew install cloudflared
```

Start Django in the first terminal:

```bash
cd /path/to/cereqo-sat
source .venv/bin/activate
export CEREQO_PUBLIC_TUNNEL=1
export CEREQO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
python manage.py runserver 127.0.0.1:8000 --insecure
```

Start the tunnel in a second terminal:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Share the generated `https://...trycloudflare.com` URL. Keep both terminals open;
stopping either process closes the preview. Anyone with the URL can see the demo
login credentials and change the shared demo account's progress.

## Demo login

The seed command creates and refreshes this account automatically:

```text
Username: demo
Password: CereqoDemo2026!
```

You can override the credentials before running `seed_demo`:

```bash
export CEREQO_DEMO_USERNAME="demo"
export CEREQO_DEMO_PASSWORD="your-local-demo-password"
python manage.py seed_demo
```

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

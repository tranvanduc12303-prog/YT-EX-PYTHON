import yt_dlp
import json

ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': 'in_playlist'}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info('https://www.youtube.com/@VincentDoAI', download=False)
    entries = info.get('entries', [])
    for i, e in enumerate(entries[:5]):
        print(f"entry type: {e.get('_type')}, title: {e.get('title')}, url: {e.get('url')}")

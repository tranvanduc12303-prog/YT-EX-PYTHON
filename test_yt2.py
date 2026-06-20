import yt_dlp
import sys
sys.stdout.reconfigure(encoding='utf-8')

ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}

def get_all_videos(url):
    videos = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            print("Error", e)
            return videos
            
        def extract_entries(entries):
            for entry in entries:
                if not entry: continue
                # if entry is a playlist (like Videos or Shorts tab), we need to extract it too
                # wait, if extract_flat is True, entries might be playlists?
                _type = entry.get('_type')
                if _type == 'playlist' or 'entries' in entry:
                    # sometimes the url is in 'url'
                    tab_url = entry.get('url') or entry.get('webpage_url')
                    if tab_url:
                        # re-extract
                        try:
                            tab_info = ydl.extract_info(tab_url, download=False)
                            if 'entries' in tab_info:
                                extract_entries(tab_info['entries'])
                        except:
                            pass
                    elif 'entries' in entry:
                         extract_entries(entry['entries'])
                elif _type == 'url' or entry.get('url'):
                    # individual video
                    v_url = entry.get('url') or entry.get('webpage_url')
                    if v_url and not v_url.startswith("http"):
                        v_url = f"https://www.youtube.com/watch?v={v_url}"
                    videos.append({
                        'title': entry.get('title', 'No title'),
                        'url': v_url
                    })
                    
        if 'entries' in info:
            extract_entries(info['entries'])
        else:
            v_url = info.get('url') or info.get('webpage_url')
            if v_url and not v_url.startswith("http"):
                v_url = f"https://www.youtube.com/watch?v={v_url}"
            videos.append({'title': info.get('title'), 'url': v_url})
            
    return videos

vids = get_all_videos('https://www.youtube.com/@VincentDoAI')
print(f"Total videos: {len(vids)}")
if vids:
    print(vids[0])

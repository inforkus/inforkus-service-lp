# Instagram の自分の投稿を最大6件取り、instagram.json と ig/ID.jpg に保存する（GitHub Actions から実行）
import json, os, sys, pathlib, urllib.parse, urllib.request

tok = os.environ.get('IG_TOKEN')
if not tok:
    print('IG_TOKEN が未登録のため終了'); sys.exit(0)
q = urllib.parse.urlencode({'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp', 'limit': '6', 'access_token': tok})
data = json.load(urllib.request.urlopen('https://graph.instagram.com/me/media?' + q, timeout=30))['data']
out = pathlib.Path('ig'); out.mkdir(exist_ok=True)
items, keep = [], set()
for m in data:
    src = m.get('thumbnail_url') if m.get('media_type') == 'VIDEO' else m.get('media_url')
    if not src:
        continue
    f = out / f"{m['id']}.jpg"; keep.add(f.name)
    if not f.exists():
        f.write_bytes(urllib.request.urlopen(src, timeout=30).read())
    items.append({'permalink': m['permalink'], 'image': f'ig/{f.name}', 'caption': (m.get('caption') or '')[:120], 'timestamp': m['timestamp']})
for f in out.glob('*.jpg'):
    if f.name not in keep:
        f.unlink()
pathlib.Path('instagram.json').write_text(json.dumps(items, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(len(items), '件を保存')

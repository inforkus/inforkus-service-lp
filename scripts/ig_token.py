# Instagram（Meta）のトークンの残り日数を確かめ、必要なら延ばす。トークンそのものはログに出さない。
import os, sys, json, subprocess, urllib.request, urllib.parse, urllib.error, datetime

API = 'https://graph.facebook.com/v26.0/'
tok = os.environ.get('IG_TOKEN')
if sys.argv[1:] == ['pat']:
    # GH_PAT の期限は、GitHub の応答のヘッダーに入っている
    pat = os.environ.get('GH_TOKEN')
    if not pat:
        print('GH_PAT が未登録のため省略'); sys.exit(0)
    req = urllib.request.Request('https://api.github.com/repos/' + os.environ['GITHUB_REPOSITORY'],
                                 headers={'Authorization': 'Bearer ' + pat})
    try:
        h = urllib.request.urlopen(req, timeout=30).headers.get('github-authentication-token-expiration')
    except urllib.error.HTTPError as e:
        print(f'::error::GH_PAT が使えません（HTTP {e.code}）。作り直してください'); sys.exit(1)
    if not h:
        print('GH_PAT の期限：なし'); sys.exit(0)
    d, t, z = h.split()
    end = datetime.datetime.fromisoformat(f'{d}T{t}' + ('+00:00' if z == 'UTC' else f'{z[:3]}:{z[3:]}'))
    jst = datetime.timezone(datetime.timedelta(hours=9))
    left = (end - datetime.datetime.now(jst)).days
    print(f'GH_PAT の期限：{end.astimezone(jst):%Y-%m-%d %H:%M}（日本時間）／残り {left} 日')
    if left <= 7:
        print(f'::error::GH_PAT が残り {left} 日です。作り直して登録し直してください'); sys.exit(1)
    if left <= 14:
        print(f'::warning::GH_PAT が残り {left} 日です')
    sys.exit(0)
if not tok:
    print('IG_TOKEN が未登録のため終了'); sys.exit(0)

def get(path, **q):
    try:
        return json.load(urllib.request.urlopen(API + path + '?' + urllib.parse.urlencode(q), timeout=30))
    except urllib.error.HTTPError as e:
        try: msg = json.load(e)['error'].get('message', '')
        except Exception: msg = ''
        print(f'HTTP {e.code}: {msg}'); return None

app, sec = os.environ.get('META_APP_ID'), os.environ.get('META_APP_SECRET')

if sys.argv[1:] == ['check']:
    if not (app and sec):
        print('::warning::META_APP_ID と META_APP_SECRET が未登録のため、期限を確かめられません'); sys.exit(0)
    d = (get('debug_token', input_token=tok, access_token=f'{app}|{sec}') or {}).get('data')
    if not d:
        print('::warning::トークンの期限を確かめられませんでした'); sys.exit(0)
    exp = d.get('expires_at') or 0
    print('種類:', d.get('type'), '／有効:', d.get('is_valid'), '／権限:', ', '.join(d.get('scopes', [])))
    if not exp:
        print('期限：なし'); sys.exit(0)
    jst = datetime.timezone(datetime.timedelta(hours=9))
    end = datetime.datetime.fromtimestamp(exp, jst)
    left = (end - datetime.datetime.now(jst)).days
    print(f'期限：{end:%Y-%m-%d %H:%M}（日本時間）／残り {left} 日')
    if left <= 7:
        print(f'::error::Instagram のトークンが残り {left} 日です。延ばすか作り直してください'); sys.exit(1)
    if left <= 14:
        print(f'::warning::Instagram のトークンが残り {left} 日です')

elif sys.argv[1:] == ['refresh']:
    if not (app and sec and os.environ.get('GH_TOKEN')):
        print('META_APP_ID・META_APP_SECRET・GH_PAT のどれかが未登録のため省略'); sys.exit(0)
    r = get('oauth/access_token', grant_type='fb_exchange_token', client_id=app, client_secret=sec,
            set_token_expires_in_60_days='true', fb_exchange_token=tok)
    new = (r or {}).get('access_token')
    if not new:
        print('::error::トークンを延ばせませんでした（古いトークンは期限まで使えます）'); sys.exit(1)
    print('::add-mask::' + new)
    subprocess.run(['gh', 'secret', 'set', 'IG_TOKEN', '--repo', os.environ['GITHUB_REPOSITORY']],
                   input=new.encode(), check=True)
    print(f'延ばしました（新しい期限まで {int(r.get("expires_in", 0)) // 86400} 日）')

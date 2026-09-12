"""List an author's mods for one game via the Nexus v2 GraphQL API.

The v1 API has no by-author endpoint and the profile page is client-rendered,
so a plain fetch gets a 403 and an empty shell. v2 exposes a mods query with an
uploader filter, which is what the profile page itself uses.
"""
import json
import sys
import urllib.request

KEY = json.load(open(r'C:\Users\danjo\source\repos\crusader-de-tweaker\scripts\nexus\nexus.local.json'))['ApiKey']
URL = 'https://api.nexusmods.com/v2/graphql'

QUERY = """
query AuthorMods($filter: ModsFilter, $count: Int) {
  mods(filter: $filter, count: $count, sort: { endorsements: { direction: DESC } }) {
    nodes {
      modId
      name
      summary
      version
      endorsements
      downloads
      createdAt
      updatedAt
      adult
      status
      game { domainName }
      uploader { name memberId }
      modCategory { name }
    }
    totalCount
  }
}
"""


def run(author, game_id=1704, count=50):
    body = json.dumps({
        'query': QUERY,
        'variables': {
            'filter': {
                'uploader': [{'value': author, 'op': 'EQUALS'}],
                'gameId': [{'value': str(game_id), 'op': 'EQUALS'}],
            },
            'count': count,
        },
    }).encode()
    req = urllib.request.Request(URL, data=body, headers={
        'Content-Type': 'application/json',
        'apikey': KEY,
        'User-Agent': 'SkyrimModAssistant/0.1',
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


if __name__ == '__main__':
    author = sys.argv[1]
    game = int(sys.argv[2]) if len(sys.argv) > 2 else 1704
    try:
        data = run(author, game)
    except Exception as exc:
        print('request failed:', type(exc).__name__, exc)
        body = getattr(exc, 'read', None)
        if body:
            print(body()[:900].decode('utf-8', 'replace'))
        sys.exit(1)

    if data.get('errors'):
        print('graphql errors:')
        print(json.dumps(data['errors'], indent=1)[:1500])
        sys.exit(1)

    nodes = data['data']['mods']['nodes']
    print('%s: %d mod(s) on game %d' % (author, data['data']['mods']['totalCount'], game))
    for n in nodes:
        print('%7s  %-46s  end %-6s dl %-8s  %s  upd %s' % (
            n['modId'], (n['name'] or '')[:46], n['endorsements'], n['downloads'],
            (n['modCategory'] or {}).get('name', '?'), (n['updatedAt'] or '')[:10]))
        if n.get('summary'):
            print('         %s' % n['summary'][:150])

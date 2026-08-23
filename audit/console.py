"""Write a console batch file the game can run with `bat claude`.

Skyrim's own `bat` command reads a text file from the game root and executes
each line in the console, so no mod, plugin or polling loop is needed. The
agent writes the file; the player runs one short command.

  py -3 audit/console.py "player.additem f 1000" "tgm"
  py -3 audit/console.py --file setup-dev      # writes setup-dev.txt instead
  py -3 audit/console.py --show                # print what is queued
  py -3 audit/console.py --preset devstart     # a named, reusable batch

In game, open the console with the key left of 1 and type:  bat claude

Lines are executed in order. A leading ';' is a comment. Commands that need a
target take a RefID prefix (`player.` or a selected reference), because `bat`
has no notion of what you are looking at.
"""
import os, sys, io, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

GAME = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'

PRESETS = {
    # a character that can go anywhere and survive long enough to test things
    'devstart': [
        'tgm',                      'player.setav speedmult 200',
        'player.additem f 50000',   'player.setlevel 50',
        'psb',                      'player.advskill sneak 50000',
    ],
    # undo the above
    'devoff': [
        'tgm', 'player.setav speedmult 100',
    ],
    # where am I, what am I standing on, what is my cell
    'whereami': [
        'player.getpos x', 'player.getpos y', 'player.getpos z',
        'player.getangle z', 'gcs',
    ],
    # free the camera to look around without moving the character
    'flycam': ['tfc 1', 'tm'],
    'flycamoff': ['tfc 0', 'tm'],
}


def write(lines, name='claude'):
    path = os.path.join(GAME, f'{name}.txt')
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    body = [f'; written {stamp}'] + list(lines)
    # Skyrim's parser is happiest with CRLF and a trailing newline
    with open(path, 'w', encoding='ascii', errors='replace', newline='\r\n') as fh:
        fh.write('\n'.join(body) + '\n')
    print(f'wrote {len(lines)} command(s) to {path}')
    for l in lines:
        print(f'   {l}')
    print(f'\nin game:  bat {name}')
    return path


def show(name='claude'):
    path = os.path.join(GAME, f'{name}.txt')
    if not os.path.exists(path):
        print(f'{path} does not exist yet')
        return
    print(f'{path}:')
    print(open(path, encoding='ascii', errors='replace').read())


if __name__ == '__main__':
    a = sys.argv[1:]
    name = 'claude'
    if '--file' in a:
        i = a.index('--file'); name = a[i + 1]; a = a[:i] + a[i + 2:]
    if not a or a[0] == '--show':
        show(name)
    elif a[0] == '--preset':
        key = a[1] if len(a) > 1 else ''
        if key not in PRESETS:
            print('presets:', ', '.join(sorted(PRESETS)))
        else:
            write(PRESETS[key], name)
    else:
        write(a, name)

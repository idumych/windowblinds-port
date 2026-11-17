# windowblinds-port

A [Claude Code](https://claude.com/claude-code) skill for porting classic
WindowBlinds skins (Stardock's `.uis` bitmap skins from WinCustomize) to
another desktop, with Haiku/Renku window decorators and control looks as the
worked target.

- `SKILL.md`: the procedure: get the skin and its preview, read the `.uis`
  layout, mock it up and match the preview before writing code, port the
  pictures, theme every control, test against the preview.
- `references/haiku.md`: the Haiku/Renku side: an app_server decorator that
  draws the skin's pixels, a control look, wiring into
  [Power Theme](https://github.com/idumych/power-theme), building and testing.
- `scripts/wb-fetch.sh ID DIR`: download a skin and its preview from
  WinCustomize.
- `scripts/wb-skin.py info|split|mockup|header SKIN_DIR ...`: read a `.uis`,
  cut its pictures into states, compose an active and an inactive window as
  WindowBlinds lays them out, or write every state as a C++ pixel table.

Install it by cloning into `~/.claude/skills/windowblinds-port`.

```sh
sh scripts/wb-fetch.sh 72 /tmp/skin72
python3 -I scripts/wb-skin.py info /tmp/skin72/skin
python3 -I scripts/wb-skin.py mockup /tmp/skin72/skin mock.png --desk '#ffffff' --scale 3
```

The scripts need Python 3 with Pillow, curl and a shell. Skins belong to their
authors; check a skin's terms before shipping its art.

MIT licence (see `LICENSE`).

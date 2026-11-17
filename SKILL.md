---
name: windowblinds-port
description: Port a classic WindowBlinds skin (Stardock's .uis/.wba bitmap skins, 1998-2003, as on WinCustomize) to another desktop - a Haiku/Renku window decorator and control look (for example a Power Theme theme), or any toolkit that can draw pixels. Covers finding and downloading the skin, reading its .uis layout (edge ends and repeats, frame order, button coordinates, magenta transparency, push button/check box/radio strips), a mockup that must match the skin's own preview before any code, turning its bitmaps into C++ tables, drawing them in a decorator, theming the controls the skin has no pictures for, and testing. Use it whenever the user links a wincustomize.com WindowBlinds page or a .wba/.uis file, or asks to "port this skin", "add this WindowBlinds theme" or "make a theme from this skin", even if they don't say WindowBlinds.
---

# Porting a WindowBlinds skin

WindowBlinds (Stardock, 1998 on) skinned Windows 9x/NT with bitmaps laid out by
a text file, the `.uis`. Thousands of skins survive on WinCustomize. The old
ones (UIS version 2, before WindowBlinds 3's .wba XML-ish formats) are small
bitmap sets that port well: you can draw their own pixels.

This skill is the procedure. `scripts/` does the mechanical parts:

- `wb-fetch.sh ID DIR` - download skin ID from WinCustomize with its preview
- `wb-skin.py info|split|mockup|header SKIN_DIR ...` - read the .uis, cut the
  pictures into states, compose a mockup, write a C++ header of every state

`references/haiku.md` covers the Haiku/Renku side (app_server decorator,
BControlLook, Power Theme wiring and tests). Read it when the target is Haiku.

## 1. Get the skin and its preview

`sh scripts/wb-fetch.sh 72 <scratch>/skin72` (72 is the number in
`wincustomize.com/explore/windowblinds/72/`). It needs a browser user agent
(the site answers 403 otherwise); guests get a few downloads a day. The
download is a zip whatever its extension (`.wba`, `.zip`). Unpack it into its
own empty folder: it's untrusted data, run Python on it with `-I`.

**The preview picture is the reference**, not the bitmaps: it shows how
WindowBlinds put them together. Keep it; every check below compares against
it at the same scale.

Note the author from the page (the .uis `SkinAuthor` is often left over from
the template the skin was made from) and the licence. Most skins have none
beyond "free download". Ask the user whether to ship the original art or to
redraw it; record their answer and credit the author either way.

## 2. Read the layout

`python3 -I scripts/wb-skin.py info SKIN_DIR` prints what WindowBlinds reads.
The rules it uses, confirmed by matching a skin's preview pixel for pixel:

- **Left and Right run the window's whole height**; Top (the title bar) and
  Bottom sit between them. Getting this wrong gives square corners where the
  skin has a binding or rounded edge running past the title bar.
- `TopTopHeight`/`TopBotHeight` are the **widths** of the title bar's left and
  right ends (drawn as they are); the part between repeats, or stretches with
  `TopStretch=1`. Same for Bottom. For Left and Right they are the heights of
  their top and bottom ends.
- **States**: Top and Bottom hold theirs one above the other, Left and Right
  side by side; frame 0 active, frame 1 inactive (`TopFrame=2` and so on).
- **Buttons** (`[Button0]`...): `XCoord` from the window's **outer** left
  (`Align=0`) or right (`Align=1`) edge, binding included; `YCoord` from its
  top. `Action`: 0 close, 1 maximize, 2 minimize, 3 help, 4 roll up. With
  `TripleImages=1` each button strip has 6 states: normal, pressed, hover, and
  the same for an inactive window.
- **Title**: `TextAlignment` (0 left, 1 centre, 2 right), `TextShift`,
  `TextShiftVert` (pixels up), colours `ActiveTextR/G/B`, `InactiveText*`.
- **Controls** (`[Buttons]`): `Bitmap` is the push button strip (5 states seen:
  normal, pressed, disabled, focused, default), `CheckButton` and
  `RadioButton` 4 (off, on, disabled off, disabled on); each followed by the
  edges kept when stretching (`TopHeight`, `LeftWidth`...).
- `menubar` (the menu bar's background, with `MenuR/G/B` the selection) and
  `DialogBmp` (a texture for dialogs) are extras.
- **Pure magenta (255, 0, 255) is transparent.** In a binding, magenta holes
  show the desktop; the preview was usually taken on white, so they look white
  there.

A skin may differ; when the mockup disagrees with the preview, believe the
preview and fix the rule (and this file).

## 3. Mock it up before writing code

`python3 -I scripts/wb-skin.py mockup SKIN_DIR mock.png --size WxH --desk
'#ffffff' --title "<the preview's title>" --scale 3`, with W and H the
preview's size, then put the preview (scaled the same) beside it and look.
The frame, corners, buttons and title position must match. Show the user this
comparison early.

## 4. Port it

- `wb-skin.py header SKIN_DIR Art.h` writes every state as ARGB tables
  (magenta = 0) for code that draws pixels; `split` writes PNGs and
  `layout.json` for anything else. In a project, copy the art into the tree
  (e.g. `third_party/<skin>/art`) and keep a small generator script there, so
  the headers can be made again.
- Lay the frame out by the rules above. The window's content sits inside
  Left's width, Top's height, Right's width and Bottom's height, so the
  borders are uneven: a binding 20 pixels wide on one side, 7 on the other.
- Leave transparent pixels out of the window's shape (its footprint, region
  or mask) so holes and rounded corners really show what's behind.
- Windows with a border but no title bar (taskbars, menus) shouldn't get the
  whole frame: give them a thin line in the skin's outline colour.

## 5. Theme every control

A skin has pictures for push buttons, check boxes and radio buttons at most.
**Don't leave the rest in the toolkit's default look**: pop-up menus, text
fields, boxes, tabs, scroll bars, sliders, progress bars, menus and list
headers must look drawn in the same style, or the port looks unthemed (a user
rejected exactly that). Build them from the skin's own pieces: the push
button's picture stretched with its kept edges is an outline for fields,
boxes and tabs; its pressed state for held scroll arrows; the menu bar
picture's rule under menu bars; the skin's colours for selections. Draw
arrows small, in the outline's darkest colour.

What can't be reproduced, say so: a dialog texture usually can't become a
panel colour; fonts of the period (often a bitmap face) aren't there.

## 6. Test against the preview

Build, apply, open a window with every kind of control, an inactive window
and the taskbar, screenshot, and compare with the preview at the same scale
(crop the same region, enlarge both 3x, side by side). Check the corners, the
binding or edges at the title bar, the button positions, the title's place
and colour, and that inactive windows use frame 1. Report what still differs
and why.

## Traps

- Guessing the layout from the bitmaps alone: the first Notebook port ran the
  title bar across the full width and was wrong. Always mock up and compare.
- `TopTopHeight` is a width for Top and Bottom, a height for Left and Right.
- Button X is from the outer edge, not from the title bar's start.
- The hover and inactive button states look alike in many skins; take the
  inactive one from the second half of the strip.
- Many skins repeat a texture (paper grain, brushed metal) across the title
  bar: draw each row's main colour once and only the other pixels over it, or
  a wide title bar costs thousands of fills.

# A WindowBlinds skin on Haiku / Renku

A skin becomes two add-ons: an app_server **window decorator** (the frame) and
a libbe **control look** (the controls). Power Theme
(github.com/idumych/power-theme) ships many; its Notebook theme
(`src/third_party/notebook`) is a complete WindowBlinds port to copy from, and
AmigaOS 3 (`src/third_party/amigaos3`) another pixel-art one.

## Decorator

Subclass `Decorator` (app_server private API, `src/servers/app/decorator`).

- **Draw the pixels as runs of one colour with `fDrawingEngine->FillRect`**,
  not as a `ServerBitmap`. On Renku the decorator can be built once as a
  "style" through Power Theme's shim (`src/styles/shim`), which records
  rectangles and lines but has no pixel bitmaps. Fill each row's opaque spans
  with the paper/main colour, then draw only the other runs over it.
- Describe the frame as a list of pieces (picture, source rectangle, place,
  clip) built by one function, and use it for drawing and for the footprint,
  so they never disagree.
- `_DoLayout`: `fLeftBorder`/`fRightBorder` from the title bar's top to the
  bottom's (WindowBlinds' rule), `fTopBorder` only for windows without a
  title, `fBottomBorder` between the sides, `fTitleBarRect` and each tab's
  `tabRect` between the sides, `fBorderRect` round it all. `fBorderWidth` is
  one number: set it to the narrowest side.
- Buttons: `closeRect`, `minimizeRect`, `zoomRect` from the .uis X/Y, made
  relative to the title bar (subtract Left's width or Right's width).
- `_GetFootprint`: the side pieces' opaque pixels only, merging rows that are
  opaque in the same places into one rectangle; the title bar and bottom as
  rectangles. Holes then show the desktop.
- `B_BORDERED_WINDOW_LOOK` (the Deskbar): a 1-pixel line, not the frame.
- `RegionAt`: buttons first, then the base class (tab), then the bottom-right
  stretch of the bottom and right edges as `REGION_RIGHT_BOTTOM_CORNER`.
- Copy the rest (`_MoveBy`, `_ResizeBy` invalidating old and new footprints,
  tab add/remove/move, `_SetFocus`, `_UpdateFont`) from an existing
  decorator of the same project.

## Control look

Subclass the project's `ForwardingControlLook` (Power Theme's
`src/controllook-kit`), which forwards everything to the default look, and
override what the skin should draw. Pictures become `BBitmap`s once
(B_RGBA32 takes the ARGB words as they are) and are drawn with `B_OP_ALPHA`
and `B_PIXEL_ALPHA`, stretched nine-patch style without smoothing.

Override at least: `DrawButtonFrame`, `DrawButtonBackground` (also used by
Tracker's column headers and Deskbar menu items), `DrawCheckBox`,
`DrawRadioButton`, `DrawMenuBarBackground` (skip the rule for Tracker's
`CountVw`), `DrawMenuFieldFrame` and both `DrawMenuFieldBackground`s,
`DrawMenuBackground`, `DrawMenuItemBackground`, `DrawTextControlBorder`,
`DrawBorder`, `DrawScrollViewFrame`, `DrawGroupFrame`, the scroll bar calls
(`Border`, `Button`, both `Background`s, `Thumb`), `DrawSliderBar`,
`DrawSliderThumb`, `DrawSliderTriangle`, `DrawStatusBar`, `DrawTabFrame`,
`DrawActiveTab` and `DrawInactiveTab`. Keep each method's rect insets the
same as the default look's (2 for fancy frames, 1 for plain), or layouts move.

## Power Theme wiring

A new theme touches: `src/themes/build-decorators.sh` (the add-on list, which
`tools/build-styles.sh` and `build-prebuilt-looks.sh` read too), `Makefile`
(variables, `all`, `decorator-source` folders and copies, build rules),
`data/themes/<Name>/theme.settings` and `preview.png` (480x315),
`packaging/zip/uninstall.sh`, the description in
`packaging/hpkg/build-hpkg.sh`, README (theme list, screenshot table at
1024x768, details section, credits), `release/test-plan.md` and the
`EVIDENCE_*`/`FEATURE_CHECKS` lines in `haiku-app.env`. Not
`Theme.cpp`'s BeOS-tab list unless the decorator draws BeOS tabs.

## Building and testing

- Cross-compile objects on Linux to catch errors early: the project Makefile
  with `SYSROOT=` a Haiku sysroot and `FREETYPE_HEADERS=` FreeType's headers;
  the style build with the shim flags from `tools/build-styles.sh`.
- In a Haiku R1/beta6 VM (QEMU/KVM can boot a VirtualBox .vdi directly with
  `-drive file=...vdi,format=vdi`): copy the tree, run
  `sh src/themes/build-decorators.sh --source=$HOME/<tree>`, put the theme in
  `~/config/non-packaged/data/themes/`, `powertheme --apply=<Name>` (add
  `--parts=...,wallpaper` to clear an old wallpaper), open the controls demo
  (`tools/controls-demo.cpp`), Tracker windows and the Deskbar, place them
  with `hey Tracker set Frame of Window <name> to "BRect(...)"`, and take a
  screenshot with QEMU's `screendump`.
- Compare with the skin's preview as SKILL.md says before showing anyone.

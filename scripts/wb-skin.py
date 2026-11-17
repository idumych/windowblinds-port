#!/usr/bin/env python3
"""Read a WindowBlinds .uis skin (version 2, the 1998-2000 bitmap skins) and
show, cut apart or mock up its pictures.

    python3 -I wb-skin.py info   SKIN_DIR
    python3 -I wb-skin.py split  SKIN_DIR OUT_DIR
    python3 -I wb-skin.py mockup SKIN_DIR OUT.png [--size 420x260]
                                 [--desk '#5a7896'] [--title Text] [--scale 3]
    python3 -I wb-skin.py header SKIN_DIR OUT.h [--guard NAME]

SKIN_DIR holds the unpacked skin: one .uis file and its .bmp files. Paths in
the .uis are Windows paths relative to WindowBlinds' skin folder
("notebook\\top.bmp"); only the file name is used, matched without case.

info    the layout as WindowBlinds reads it, and each picture's frames
split   each part's states as PNGs (magenta made transparent) and layout.json
mockup  an active and an inactive window put together as WindowBlinds lays
        them out, to compare with the skin's preview at the same scale
        BEFORE writing any decorator code
header  every state as C++ (struct Art { int32 width, height; const uint32*
        pixels; }, ARGB, magenta = 0), for an add-on that draws the pixels

The layout rules (checked against a skin's own preview, see SKILL.md):
- Left and Right run the window's whole height; Top and Bottom go between them.
- Top's TopTopHeight/TopBotHeight are the widths of its left and right ends,
  drawn as they are; the part between repeats (or stretches, TopStretch=1).
  Bottom's BottomTopHeight/BottomBotHeight likewise. Left's and Right's
  *TopHeight/*BotHeight are the heights of their top and bottom ends.
- States: Top and Bottom hold theirs one above the other, Left and Right side
  by side, buttons side by side. Frame 0 is active, frame 1 inactive.
- Button N: XCoord from the window's left (Align=0) or right (Align=1) outer
  edge, YCoord from its top. With TripleImages=1 a button has 6 states side by
  side: normal, pressed, hover, then the same for an inactive window.
- Action: 0 close, 1 maximize, 2 minimize, 3 help, 4 roll up (shade).
- Pure magenta (255, 0, 255) is transparent.
"""

import json
import os
import sys

from PIL import Image

KEY = (255, 0, 255)
ACTIONS = {0: "close", 1: "maximize", 2: "minimize", 3: "help", 4: "rollup"}


def parse_uis(path):
	"""Sections in order, each a list of (key, value): [Buttons] repeats keys."""
	sections = []
	current = None
	with open(path, encoding="latin-1") as f:
		for raw in f:
			line = raw.split(";", 1)[0].strip()
			if not line:
				continue
			if line.startswith("[") and line.endswith("]"):
				current = (line[1:-1].strip(), [])
				sections.append(current)
			elif "=" in line and current is not None:
				key, value = line.split("=", 1)
				current[1].append((key.strip(), value.strip()))
	return sections


class Skin:
	def __init__(self, folder):
		self.folder = folder
		files = os.listdir(folder)
		uis = [f for f in files if f.lower().endswith(".uis")]
		if len(uis) != 1:
			sys.exit("expected one .uis in %s, found %s" % (folder, uis))
		self.uis = os.path.join(folder, uis[0])
		self.files = {f.lower(): os.path.join(folder, f) for f in files}
		self.sections = parse_uis(self.uis)
		self.p = {}
		for name, items in self.sections:
			if name.lower() in ("personality", "titlebarskin"):
				for k, v in items:
					self.p[k.lower()] = v
		self.buttons = []
		for name, items in self.sections:
			if name.lower().startswith("button") and name.lower() != "buttons":
				b = {k.lower(): v for k, v in items}
				self.buttons.append(b)
		self.controls = []
		for name, items in self.sections:
			if name.lower() == "buttons":
				entry = None
				for k, v in items:
					if k.lower() in ("checkbutton", "radiobutton", "bitmap"):
						entry = {"kind": k.lower(), "image": v}
						self.controls.append(entry)
					elif entry is not None:
						entry[k.lower()] = v

	def num(self, key, default=0):
		try:
			return int(self.p.get(key.lower(), default))
		except ValueError:
			return default

	def image(self, ref):
		if not ref:
			return None
		name = ref.replace("\\", "/").split("/")[-1].lower()
		path = self.files.get(name)
		if path is None:
			print("missing picture:", ref, file=sys.stderr)
			return None
		return Image.open(path).convert("RGB")

	def frames(self, ref, count, across):
		im = self.image(ref)
		if im is None:
			return []
		count = max(1, count)
		out = []
		for i in range(count):
			if across:
				w = im.width // count
				box = (i * w, 0, (i + 1) * w, im.height)
			else:
				h = im.height // count
				box = (0, i * h, im.width, (i + 1) * h)
			out.append(keyed(im.crop(box)))
		return out

	def edges(self):
		"""Each edge's states and its fixed ends."""
		e = {}
		for part, across in (("top", False), ("bottom", False),
				("left", True), ("right", True)):
			e[part] = {
				"frames": self.frames(self.p.get(part), self.num(part + "frame",
					2), across),
				"start": self.num(part + "topheight"),
				"end": self.num(part + "botheight"),
				"stretch": self.num(part + "stretch") == 1,
			}
		return e

	def button_states(self, b):
		im = self.image(b.get("buttonimage"))
		if im is None:
			return []
		count = 6 if self.num("tripleimages") == 1 else 4
		# a non-square strip tells its own count
		if im.width % im.height == 0 and im.width // im.height not in (count,):
			count = im.width // im.height
		return self.frames(b.get("buttonimage"), count, True)


def keyed(im):
	im = im.convert("RGBA")
	px = im.load()
	for y in range(im.height):
		for x in range(im.width):
			if px[x, y][:3] == KEY:
				px[x, y] = (0, 0, 0, 0)
	return im


def colour(skin, prefix):
	try:
		return tuple(skin.num(prefix + c) for c in "RGB")
	except Exception:
		return (0, 0, 0)


def info(skin):
	print("skin file:", skin.uis)
	for k in ("skinname", "skinauthor"):
		if k in skin.p:
			print("%s: %s" % (k, skin.p[k]))
	print("title: align %s (0 left, 1 centre, 2 right), shift %s, up %s" % (
		skin.p.get("textalignment"), skin.p.get("textshift"),
		skin.p.get("textshiftvert")))
	print("text colours: active %s, inactive %s, menu %s, menu selection %s" % (
		colour(skin, "activetext"), colour(skin, "inactivetext"),
		colour(skin, "menutext"), colour(skin, "menu")))
	for part, e in skin.edges().items():
		size = e["frames"][0].size if e["frames"] else None
		print("%-6s %d states of %s, ends %d and %d, %s" % (part,
			len(e["frames"]), size, e["start"], e["end"],
			"stretched" if e["stretch"] else "repeated"))
	for b in skin.buttons:
		states = skin.button_states(b)
		action = ACTIONS.get(int(b.get("action", -1)), b.get("action"))
		print("button %-8s %d states of %s at %s from the %s, %s down" % (action,
			len(states), states[0].size if states else None, b.get("xcoord"),
			"right" if b.get("align") == "1" else "left", b.get("ycoord")))
	for c in skin.controls:
		im = skin.image(c["image"])
		print("control %-11s %s %s, edges l%s r%s t%s b%s" % (c["kind"],
			c["image"], im.size if im else None, c.get("leftwidth"),
			c.get("rightwidth"), c.get("topheight"), c.get("bottomheight")))
	for k in ("menubar", "dialogbmp"):
		if k in skin.p:
			im = skin.image(skin.p[k])
			print("%s: %s %s" % (k, skin.p[k], im.size if im else None))


def split(skin, out):
	os.makedirs(out, exist_ok=True)
	layout = {"edges": {}, "buttons": [], "controls": []}
	for part, e in skin.edges().items():
		for i, im in enumerate(e["frames"]):
			im.save(os.path.join(out, "%s-%d.png" % (part, i)))
		layout["edges"][part] = {"states": len(e["frames"]),
			"start": e["start"], "end": e["end"], "stretch": e["stretch"]}
	for b in skin.buttons:
		action = ACTIONS.get(int(b.get("action", -1)), "button")
		states = skin.button_states(b)
		for i, im in enumerate(states):
			im.save(os.path.join(out, "%s-%d.png" % (action, i)))
		layout["buttons"].append({"action": action, "states": len(states),
			"x": int(b.get("xcoord", 0)), "y": int(b.get("ycoord", 0)),
			"from": "right" if b.get("align") == "1" else "left"})
	for c in skin.controls:
		im = skin.image(c["image"])
		if im is None:
			continue
		keyed(im).save(os.path.join(out, "control-%s.png" % c["kind"]))
		layout["controls"].append(c)
	with open(os.path.join(out, "layout.json"), "w") as f:
		json.dump(layout, f, indent=1)
	print("wrote", out)


def paste_edge(win, im, start, end, area, along_x, stretch):
	"""An edge picture over area (x0, y0, x1, y1): ends as they are, middle
	repeated or stretched."""
	x0, y0, x1, y1 = area
	length = (x1 - x0) if along_x else (y1 - y0)
	size = im.width if along_x else im.height
	start = min(start, length)
	end = min(end, max(0, length - start))
	def crop(a, b):
		return im.crop((a, 0, b, im.height)) if along_x else \
			im.crop((0, a, im.width, b))
	def put(piece, offset):
		win.alpha_composite(piece, (x0 + offset, y0) if along_x
			else (x0, y0 + offset))
	if start:
		put(crop(0, start), 0)
	middle = crop(start, size - end)
	room = length - start - end
	mid_len = size - start - end
	if room > 0 and mid_len > 0:
		if stretch:
			put(middle.resize((room, im.height) if along_x else
				(im.width, room), Image.NEAREST), start)
		else:
			for o in range(0, room, mid_len):
				n = min(mid_len, room - o)
				put(crop(start, start + n), start + o)
	if end:
		put(crop(size - end, size), length - end)


def window(skin, width, height, state, title):
	e = skin.edges()
	def frame(part):
		f = e[part]["frames"]
		return f[min(state, len(f) - 1)] if f else None
	top, bottom, left, right = (frame(p) for p in
		("top", "bottom", "left", "right"))
	lw = left.width if left else 0
	rw = right.width if right else 0
	th = top.height if top else 0
	bh = bottom.height if bottom else 0
	win = Image.new("RGBA", (width, height), (0, 0, 0, 0))
	from PIL import ImageDraw
	ImageDraw.Draw(win).rectangle((lw, th, width - rw - 1, height - bh - 1),
		fill=(255, 255, 255, 255))
	if top:
		paste_edge(win, top, e["top"]["start"], e["top"]["end"],
			(lw, 0, width - rw, th), True, e["top"]["stretch"])
	if bottom:
		paste_edge(win, bottom, e["bottom"]["start"], e["bottom"]["end"],
			(lw, height - bh, width - rw, height), True, e["bottom"]["stretch"])
	if left:
		paste_edge(win, left, e["left"]["start"], e["left"]["end"],
			(0, 0, lw, height), False, e["left"]["stretch"])
	if right:
		paste_edge(win, right, e["right"]["start"], e["right"]["end"],
			(width - rw, 0, width, height), False, e["right"]["stretch"])
	for b in skin.buttons:
		states = skin.button_states(b)
		if not states:
			continue
		im = states[0 if state == 0 else min(len(states) - 1,
			len(states) // 2)]
		x = int(b.get("xcoord", 0))
		if b.get("align") == "1":
			x = width - x
		win.alpha_composite(im, (x, int(b.get("ycoord", 0))))
	if title:
		d = ImageDraw.Draw(win)
		c = colour(skin, "activetext" if state == 0 else "inactivetext")
		w = d.textlength(title)
		align = skin.num("textalignment", 1)
		x = lw + 8 if align == 0 else (width - rw - 8 - w if align == 2
			else (width - w) / 2)
		d.text((x + skin.num("textshift"), th / 2 - 6 - skin.num("textshiftvert")),
			title, fill=c + (255,))
	return win


def mockup(skin, out, size, desk, title, scale):
	w, h = size
	pad = 20
	desk = tuple(int(desk.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
	bg = Image.new("RGBA", (w + 2 * pad, 2 * h + 3 * pad), desk + (255,))
	bg.alpha_composite(window(skin, w, h, 0, title), (pad, pad))
	bg.alpha_composite(window(skin, w, h, 1, title), (pad, h + 2 * pad))
	bg = bg.convert("RGB")
	if scale > 1:
		bg = bg.resize((bg.width * scale, bg.height * scale), Image.NEAREST)
	bg.save(out)
	print("wrote", out)


def emit(out, ident, im):
	px = im.load()
	out.write("static const uint32 %sPixels[] = {\n" % ident)
	for y in range(im.height):
		row = []
		for x in range(im.width):
			r, g, b, a = px[x, y]
			row.append(0 if a == 0 else (0xff000000 | (r << 16) | (g << 8) | b))
		out.write("\t" + ", ".join("0x%08x" % p for p in row) + ",\n")
	out.write("};\nstatic const Art %s = { %d, %d, %sPixels };\n\n"
		% (ident, im.width, im.height, ident))


def header(skin, path, guard):
	def ident(*parts):
		return "k" + "".join(p[:1].upper() + p[1:] for p in parts)
	with open(path, "w") as out:
		out.write("/*\n * Generated by wb-skin.py from %s.\n */\n#ifndef %s\n"
			"#define %s\n\n#include <SupportDefs.h>\n\n\n"
			"// a picture: its size, and its pixels as ARGB, row by row\n"
			"struct Art {\n\tint32\t\t\twidth;\n\tint32\t\t\theight;\n"
			"\tconst uint32*\tpixels;\n};\n\n\n" % (os.path.basename(skin.uis),
			guard, guard))
		for part, e in skin.edges().items():
			for i, im in enumerate(e["frames"]):
				emit(out, ident(part, str(i)), im)
		for b in skin.buttons:
			action = ACTIONS.get(int(b.get("action", -1)), "button")
			for i, im in enumerate(skin.button_states(b)):
				emit(out, ident(action, str(i)), im)
		for c in skin.controls:
			im = skin.image(c["image"])
			if im is not None:
				emit(out, ident(c["kind"]), keyed(im))
		out.write("#endif\t// %s\n" % guard)
	print("wrote", path)


def option(args, name, default):
	if name in args:
		i = args.index(name)
		value = args[i + 1]
		del args[i:i + 2]
		return value
	return default


def main():
	args = sys.argv[1:]
	if len(args) < 2:
		sys.exit(__doc__)
	cmd, folder = args[0], args[1]
	rest = args[2:]
	skin = Skin(folder)
	if cmd == "info":
		info(skin)
	elif cmd == "split" and rest:
		split(skin, rest[0])
	elif cmd == "mockup" and rest:
		out = rest.pop(0)
		size = tuple(int(v) for v in option(rest, "--size", "420x260").split("x"))
		desk = option(rest, "--desk", "#5a7896")
		title = option(rest, "--title", skin.p.get("skinname", "Window"))
		scale = int(option(rest, "--scale", "2"))
		mockup(skin, out, size, desk, title, scale)
	elif cmd == "header" and rest:
		out = rest.pop(0)
		guard = option(rest, "--guard", "WB_SKIN_ART_H")
		header(skin, out, guard)
	else:
		sys.exit(__doc__)


if __name__ == "__main__":
	main()

#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import re
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd2in13_V4
import time
from PIL import Image, ImageDraw, ImageFont
import traceback
import math

# Turn into class instead?

logging.basicConfig(level=logging.DEBUG)

def parse_svg_paths_to_polygons(paths):
    """
    Minimal SVG path parser for QR-style paths.
    Supports M/m, H/h, V/v, L/l, Z/z. Produces a list of polygons (each a list of (x,y) tuples).
    Assumes each subpath is closed with Z and axis-aligned (typical for QR rectangles).
    """
    if not paths:
        return []

    if isinstance(paths, str):
        path_list = [paths]
    else:
        path_list = list(paths)

    token_re = re.compile(r'[MmHhVvLlZz]|-?\d+(?:\.\d+)?')

    polygons = []

    for raw in path_list:
        s = raw.replace(',', ' ').strip()
        if not s:
            continue
        tokens = token_re.findall(s)
        i = 0

        cx = cy = None
        sx = sy = None
        pts = []

        def read_number():
            nonlocal i
            if i >= len(tokens):
                raise ValueError("Expected number, got end of tokens")
            val = float(tokens[i])
            i += 1
            return val

        while i < len(tokens):
            t = tokens[i]; i += 1

            if t in ('M', 'm'):
                # Start a new subpath
                # If there was an unfinished polygon, discard it (we only draw on Z)
                x = read_number(); y = read_number()
                if t == 'm':
                    if cx is None or cy is None:
                        cx = 0.0; cy = 0.0
                    cx += x; cy += y
                else:
                    cx, cy = x, y
                sx, sy = cx, cy
                pts = [(cx, cy)]

            elif t in ('H', 'h'):
                x = read_number()
                if cx is None or cy is None:
                    continue
                if t == 'h':
                    cx = cx + x
                else:
                    cx = x
                pts.append((cx, cy))

            elif t in ('V', 'v'):
                y = read_number()
                if cx is None or cy is None:
                    continue
                if t == 'v':
                    cy = cy + y
                else:
                    cy = y
                pts.append((cx, cy))

            elif t in ('L', 'l'):
                x = read_number(); y = read_number()
                if cx is None or cy is None:
                    continue
                if t == 'l':
                    cx = cx + x; cy = cy + y
                else:
                    cx, cy = x, y
                pts.append((cx, cy))

            elif t in ('Z', 'z'):
                # Close current polygon
                if pts and (pts[0][0] != pts[-1][0] or pts[0][1] != pts[-1][1]):
                    pts.append(pts[0])
                if len(pts) >= 4:
                    polygons.append(pts[:])
                pts = []
                cx = cy = sx = sy = None

            else:
                # Unknown token: ignore gracefully
                pass

        # If a path wasn't explicitly closed, we won't draw it (QR subpaths should be closed)
        # This avoids drawing incomplete shapes.

    return polygons

def compute_bbox(polygons):
    if not polygons:
        return None
    xs = []
    ys = []
    for poly in polygons:
        for (x, y) in poly:
            xs.append(x); ys.append(y)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return (min_x, min_y, max_x, max_y)

def transform_and_draw(draw, polygons, img_w, img_h, margin=8):
    """
    Scale (integer factor) and center polygons onto the given canvas.
    Draw in black (0) on 1-bit image.
    """
    if not polygons:
        return

    bbox = compute_bbox(polygons)
    if not bbox:
        return
    min_x, min_y, max_x, max_y = bbox
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0:
        return

    avail_w = max(1, img_w - 2 * margin)
    avail_h = max(1, img_h - 2 * margin)

    # Integer scale to keep QR modules crisp
    scale = max(1, int(math.floor(min(avail_w / width, avail_h / height))))

    # Centering translation
    scaled_w = width * scale
    scaled_h = height * scale
    tx = int(round((img_w - scaled_w) / 2 - min_x * scale))
    ty = int(round((img_h - scaled_h) / 2 - min_y * scale))

    for poly in polygons:
        sp = [(int(round(x * scale + tx)), int(round(y * scale + ty))) for (x, y) in poly]
        # Draw filled polygon for each subpath
        draw.polygon(sp, fill=0)

def clear_qr_code():
    epd = epd2in13_V4.EPD()
    epd.Clear(0xFF)

def draw_qr_code(svg_paths):
    try:
        logging.info("epd2in13_V4 Demo - Vector Path Display")

        epd = epd2in13_V4.EPD()
        logging.info("init and Clear")
        epd.init()
        epd.Clear(0xFF)

        # Create blank image
        # Note: Original code used (epd.height, epd.width); keep this if your hardware expects it.
        # If orientation is wrong, you can switch to (epd.width, epd.height) or rotate at the end.
        image = Image.new('1', (epd.height, epd.width), 255)  # 255: white background
        draw = ImageDraw.Draw(image)

        logging.info("Drawing vector paths...")

        # Vector path data (leave empty; supply your full QR path string or a list of strings)
        #svg_paths = "M4 4h7v1H4zM12 4h6v1H12zM19 4h8v1H19zM30 4h1v1H30zM32 4h1v1H32zM34 4h1v1H34zM36 4h2v1H36zM44 4h1v1H44zM46,4 h7v1H46zM4 5h1v1H4zM10 5h1v1H10zM13 5h1v1H13zM15 5h1v1H15zM17 5h2v1H17zM22 5h1v1H22zM24 5h1v1H24zM26 5h1v1H26zM29 5h3v1H29zM37 5h3v1H37zM41 5h4v1H41zM46 5h1v1H46zM52,5 h1v1H52zM4 6h1v1H4zM6 6h3v1H6zM10 6h1v1H10zM13 6h3v1H13zM17 6h1v1H17zM20 6h3v1H20zM24 6h2v1H24zM27 6h2v1H27zM30 6h2v1H30zM33 6h4v1H33zM38 6h2v1H38zM43 6h2v1H43zM46 6h1v1H46zM48 6h3v1H48zM52,6 h1v1H52zM4 7h1v1H4zM6 7h3v1H6zM10 7h1v1H10zM15 7h5v1H15zM21 7h2v1H21zM29 7h3v1H29zM33 7h3v1H33zM37 7h5v1H37zM43 7h1v1H43zM46 7h1v1H46zM48 7h3v1H48zM52,7 h1v1H52zM4 8h1v1H4zM6 8h3v1H6zM10 8h1v1H10zM12 8h1v1H12zM14 8h3v1H14zM18 8h1v1H18zM20 8h3v1H20zM24 8h1v1H24zM26 8h5v1H26zM34 8h3v1H34zM39 8h1v1H39zM41 8h1v1H41zM46 8h1v1H46zM48 8h3v1H48zM52,8 h1v1H52zM4 9h1v1H4zM10 9h1v1H10zM12 9h1v1H12zM16 9h1v1H16zM19 9h2v1H19zM22 9h3v1H22zM26 9h1v1H26zM30 9h1v1H30zM32 9h2v1H32zM35 9h6v1H35zM42 9h1v1H42zM46 9h1v1H46zM52,9 h1v1H52zM4 10h7v1H4zM12 10h1v1H12zM14 10h1v1H14zM16 10h1v1H16zM18 10h1v1H18zM20 10h1v1H20zM22 10h1v1H22zM24 10h1v1H24zM26 10h1v1H26zM28 10h1v1H28zM30 10h1v1H30zM32 10h1v1H32zM34 10h1v1H34zM36 10h1v1H36zM38 10h1v1H38zM40 10h1v1H40zM42 10h1v1H42zM44 10h1v1H44zM46,10 h7v1H46zM13 11h2v1H13zM17 11h7v1H17zM25 11h2v1H25zM30 11h2v1H30zM33 11h2v1H33zM37 11h2v1H37zM40 11h5v1H40zM5 12h7v1H5zM13 12h1v1H13zM15 12h1v1H15zM17 12h1v1H17zM22 12h1v1H22zM25 12h7v1H25zM33 12h5v1H33zM39 12h1v1H39zM41 12h1v1H41zM43 12h2v1H43zM47 12h2v1H47zM52,12 h1v1H52zM4 13h3v1H4zM11 13h2v1H11zM19 13h1v1H19zM21 13h2v1H21zM25 13h1v1H25zM27 13h2v1H27zM31 13h1v1H31zM33 13h2v1H33zM36 13h2v1H36zM46 13h3v1H46zM9 14h9v1H9zM21 14h2v1H21zM26 14h4v1H26zM35 14h5v1H35zM41 14h3v1H41zM45 14h1v1H45zM50,14 h3v1H50zM4 15h1v1H4zM6 15h1v1H6zM11 15h1v1H11zM13 15h1v1H13zM15 15h1v1H15zM17 15h1v1H17zM19 15h2v1H19zM22 15h2v1H22zM26 15h1v1H26zM31 15h9v1H31zM42 15h1v1H42zM44 15h2v1H44zM48 15h1v1H48zM5 16h3v1H5zM10 16h4v1H10zM16 16h2v1H16zM24 16h1v1H24zM26 16h1v1H26zM28 16h2v1H28zM33 16h2v1H33zM37 16h1v1H37zM40 16h2v1H40zM43 16h5v1H43zM49 16h2v1H49zM52,16 h1v1H52zM6 17h1v1H6zM11 17h2v1H11zM15 17h2v1H15zM18 17h2v1H18zM21 17h5v1H21zM27 17h4v1H27zM32 17h4v1H32zM39 17h2v1H39zM43 17h1v1H43zM45 17h3v1H45zM49 17h1v1H49zM51 17h1v1H51zM10 18h2v1H10zM13 18h2v1H13zM17 18h2v1H17zM20 18h1v1H20zM22 18h1v1H22zM25 18h2v1H25zM28 18h1v1H28zM32 18h1v1H32zM35 18h1v1H35zM37 18h2v1H37zM41 18h4v1H41zM48 18h1v1H48zM52,18 h1v1H52zM6 19h1v1H6zM8 19h1v1H8zM11 19h2v1H11zM16 19h3v1H16zM21 19h1v1H21zM24 19h7v1H24zM32 19h1v1H32zM34 19h4v1H34zM39 19h1v1H39zM43 19h3v1H43zM48 19h2v1H48zM52,19 h1v1H52zM4 20h1v1H4zM6 20h1v1H6zM9 20h2v1H9zM13 20h2v1H13zM16 20h2v1H16zM20 20h1v1H20zM22 20h1v1H22zM26 20h3v1H26zM30 20h1v1H30zM33 20h2v1H33zM40 20h2v1H40zM43 20h1v1H43zM47 20h1v1H47zM52,20 h1v1H52zM4 21h1v1H4zM7 21h1v1H7zM9 21h1v1H9zM11 21h2v1H11zM19 21h1v1H19zM21 21h4v1H21zM26 21h4v1H26zM31 21h2v1H31zM34 21h1v1H34zM36 21h2v1H36zM40 21h1v1H40zM44 21h2v1H44zM48 21h4v1H48zM4 22h1v1H4zM7 22h2v1H7zM10 22h1v1H10zM13 22h1v1H13zM15 22h4v1H15zM21 22h8v1H21zM30 22h1v1H30zM33 22h3v1H33zM39 22h3v1H39zM43 22h2v1H43zM46 22h4v1H46zM51,22 h2v1H51zM5 23h2v1H5zM13 23h5v1H13zM19 23h2v1H19zM22 23h1v1H22zM24 23h1v1H24zM26 23h1v1H26zM29 23h3v1H29zM34 23h1v1H34zM36 23h1v1H36zM41 23h2v1H41zM44 23h1v1H44zM46 23h3v1H46zM51,23 h2v1H51zM4 24h2v1H4zM7 24h4v1H7zM12 24h1v1H12zM14 24h4v1H14zM20 24h1v1H20zM22 24h4v1H22zM28 24h3v1H28zM32 24h1v1H32zM35 24h1v1H35zM38 24h5v1H38zM44 24h1v1H44zM46 24h2v1H46zM50,24 h3v1H50zM8 25h1v1H8zM11 25h1v1H11zM13 25h5v1H13zM20 25h6v1H20zM27 25h2v1H27zM33 25h5v1H33zM39 25h1v1H39zM43 25h1v1H43zM45 25h2v1H45zM4 26h1v1H4zM7 26h8v1H7zM20 26h2v1H20zM23 26h1v1H23zM26 26h5v1H26zM37 26h3v1H37zM42 26h1v1H42zM44 26h6v1H44zM51,26 h2v1H51zM4 27h1v1H4zM6 27h1v1H6zM8 27h1v1H8zM12 27h5v1H12zM18 27h1v1H18zM22 27h2v1H22zM26 27h1v1H26zM30 27h2v1H30zM33 27h1v1H33zM36 27h1v1H36zM38 27h1v1H38zM41 27h2v1H41zM44 27h1v1H44zM48 27h2v1H48zM51 27h1v1H51zM4 28h5v1H4zM10 28h1v1H10zM12 28h2v1H12zM15 28h1v1H15zM17 28h3v1H17zM22 28h2v1H22zM25 28h2v1H25zM28 28h1v1H28zM30 28h1v1H30zM32 28h2v1H32zM35 28h1v1H35zM38 28h7v1H38zM46 28h1v1H46zM48,28 h5v1H48zM4 29h3v1H4zM8 29h1v1H8zM12 29h2v1H12zM15 29h2v1H15zM19 29h4v1H19zM24 29h3v1H24zM30 29h6v1H30zM39 29h3v1H39zM43 29h2v1H43zM48 29h1v1H48zM50 29h1v1H50zM52,29 h1v1H52zM5 30h9v1H5zM16 30h1v1H16zM19 30h1v1H19zM21 30h2v1H21zM26 30h5v1H26zM32 30h1v1H32zM35 30h1v1H35zM38 30h1v1H38zM42 30h7v1H42zM50 30h2v1H50zM4 31h1v1H4zM8 31h1v1H8zM11 31h4v1H11zM17 31h1v1H17zM19 31h1v1H19zM24 31h4v1H24zM30 31h1v1H30zM33 31h1v1H33zM36 31h1v1H36zM38 31h2v1H38zM41 31h2v1H41zM45 31h1v1H45zM47 31h1v1H47zM4 32h1v1H4zM7 32h1v1H7zM10 32h1v1H10zM14 32h1v1H14zM16 32h1v1H16zM18 32h1v1H18zM20 32h1v1H20zM24 32h1v1H24zM28 32h4v1H28zM33 32h3v1H33zM38 32h3v1H38zM42 32h4v1H42zM47 32h1v1H47zM50 32h2v1H50zM4 33h1v1H4zM7 33h1v1H7zM9 33h1v1H9zM11 33h3v1H11zM19 33h1v1H19zM24 33h5v1H24zM30 33h1v1H30zM33 33h2v1H33zM36 33h1v1H36zM39 33h1v1H39zM41 33h1v1H41zM43 33h1v1H43zM45 33h1v1H45zM51 33h1v1H51zM4 34h1v1H4zM7 34h2v1H7zM10 34h1v1H10zM12 34h1v1H12zM14 34h1v1H14zM17 34h4v1H17zM23 34h3v1H23zM29 34h1v1H29zM31 34h1v1H31zM35 34h6v1H35zM42 34h2v1H42zM46 34h2v1H46zM49 34h1v1H49zM52,34 h1v1H52zM7 35h1v1H7zM9 35h1v1H9zM11 35h2v1H11zM14 35h3v1H14zM18 35h3v1H18zM22 35h1v1H22zM25 35h1v1H25zM33 35h3v1H33zM38 35h4v1H38zM44 35h1v1H44zM49 35h1v1H49zM51,35 h2v1H51zM5 36h1v1H5zM8 36h4v1H8zM14 36h3v1H14zM22 36h1v1H22zM24 36h1v1H24zM28 36h1v1H28zM31 36h1v1H31zM34 36h1v1H34zM40 36h1v1H40zM42 36h2v1H42zM45 36h2v1H45zM48 36h1v1H48zM50 36h1v1H50zM52,36 h1v1H52zM5 37h2v1H5zM9 37h1v1H9zM12 37h2v1H12zM15 37h1v1H15zM23 37h1v1H23zM26 37h5v1H26zM34 37h2v1H34zM37 37h1v1H37zM39 37h3v1H39zM44 37h2v1H44zM49 37h1v1H49zM51 37h1v1H51zM4 38h3v1H4zM9 38h3v1H9zM16 38h1v1H16zM18 38h1v1H18zM22 38h1v1H22zM28 38h2v1H28zM31 38h1v1H31zM38 38h1v1H38zM40 38h1v1H40zM42 38h1v1H42zM45 38h3v1H45zM52,38 h1v1H52zM4 39h1v1H4zM8 39h2v1H8zM12 39h2v1H12zM15 39h1v1H15zM18 39h3v1H18zM22 39h3v1H22zM26 39h4v1H26zM31 39h1v1H31zM33 39h2v1H33zM36 39h2v1H36zM39 39h1v1H39zM42 39h1v1H42zM44 39h1v1H44zM49 39h1v1H49zM52,39 h1v1H52zM5 40h3v1H5zM9 40h2v1H9zM12 40h2v1H12zM16 40h1v1H16zM18 40h1v1H18zM22 40h1v1H22zM28 40h1v1H28zM30 40h1v1H30zM32 40h1v1H32zM35 40h1v1H35zM37 40h2v1H37zM40 40h2v1H40zM43 40h2v1H43zM46 40h1v1H46zM48 40h1v1H48zM50 40h1v1H50zM52,40 h1v1H52zM4 41h3v1H4zM8 41h1v1H8zM11 41h2v1H11zM19 41h3v1H19zM23 41h1v1H23zM25 41h2v1H25zM29 41h1v1H29zM31 41h2v1H31zM34 41h4v1H34zM40 41h1v1H40zM44 41h2v1H44zM47 41h1v1H47zM50 41h2v1H50zM5 42h1v1H5zM9 42h2v1H9zM12 42h1v1H12zM14 42h1v1H14zM16 42h2v1H16zM19 42h2v1H19zM23 42h1v1H23zM25 42h2v1H25zM28 42h3v1H28zM32 42h1v1H32zM34 42h1v1H34zM38 42h5v1H38zM44,42 h9v1H44zM5 43h3v1H5zM11 43h1v1H11zM17 43h3v1H17zM23 43h2v1H23zM26 43h1v1H26zM31 43h3v1H31zM35 43h2v1H35zM38 43h1v1H38zM41 43h2v1H41zM50 43h1v1H50zM52,43 h1v1H52zM4 44h3v1H4zM10 44h1v1H10zM13 44h2v1H13zM16 44h1v1H16zM18 44h2v1H18zM22 44h2v1H22zM26 44h5v1H26zM37 44h4v1H37zM42 44h8v1H42zM52,44 h1v1H52zM12 45h3v1H12zM16 45h3v1H16zM23 45h4v1H23zM30 45h1v1H30zM33 45h1v1H33zM38 45h2v1H38zM41 45h2v1H41zM44 45h1v1H44zM48 45h1v1H48zM4 46h7v1H4zM12 46h6v1H12zM19 46h1v1H19zM21 46h2v1H21zM24 46h3v1H24zM28 46h1v1H28zM30 46h1v1H30zM32 46h1v1H32zM34 46h2v1H34zM37 46h1v1H37zM40 46h1v1H40zM44 46h1v1H44zM46 46h1v1H46zM48 46h2v1H48zM51,46 h2v1H51zM4 47h1v1H4zM10 47h1v1H10zM12 47h1v1H12zM14 47h2v1H14zM20 47h7v1H20zM30 47h1v1H30zM32 47h3v1H32zM36 47h1v1H36zM38 47h7v1H38zM48 47h1v1H48zM4 48h1v1H4zM6 48h3v1H6zM10 48h1v1H10zM12 48h4v1H12zM17 48h1v1H17zM21 48h3v1H21zM25 48h7v1H25zM34 48h2v1H34zM37 48h12v1H37zM50 48h2v1H50zM4 49h1v1H4zM6 49h3v1H6zM10 49h1v1H10zM12 49h2v1H12zM19 49h2v1H19zM22 49h4v1H22zM28 49h2v1H28zM32 49h3v1H32zM36 49h1v1H36zM39 49h1v1H39zM41 49h1v1H41zM46 49h1v1H46zM48 49h1v1H48zM50,49 h3v1H50zM4 50h1v1H4zM6 50h3v1H6zM10 50h1v1H10zM12 50h1v1H12zM16 50h2v1H16zM20 50h3v1H20zM31 50h1v1H31zM35 50h9v1H35zM45 50h1v1H45zM47 50h1v1H47zM49,50 h4v1H49zM4 51h1v1H4zM10 51h1v1H10zM12 51h6v1H12zM20 51h2v1H20zM25 51h4v1H25zM32 51h1v1H32zM34 51h1v1H34zM36 51h1v1H36zM41 51h1v1H41zM46 51h3v1H46zM52,51 h1v1H52zM4 52h7v1H4zM13 52h1v1H13zM15 52h3v1H15zM21 52h1v1H21zM24 52h1v1H24zM26 52h1v1H26zM28 52h1v1H28zM30 52h1v1H30zM33 52h3v1H33zM38 52h6v1H38zM45 52h1v1H45zM49,52 h4v1H49z"  # e.g., "M4 4h7v1H4zM12 4h2v1H12z..." or ["M...", "M...", ...]

        # Parse, scale, center, and draw
        polygons = parse_svg_paths_to_polygons(svg_paths)
        transform_and_draw(draw, polygons, image.size[0], image.size[1], margin=8)

        # If you need rotation to match your display orientation, uncomment:
        # image = image.rotate(180, expand=False)

        logging.info("Displaying image...")
        epd.display(epd.getbuffer(image))
        #time.sleep(10)

        #logging.info("Clear...")
        #epd.init()
        #epd.Clear(0xFF)

        #logging.info("Goto Sleep...")
        #epd.sleep()

    except IOError as e:
        logging.info(f"IO Error: {e}")

    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        epd2in13_V4.epdconfig.module_exit(cleanup=True)
        exit()

    except Exception as e:
        logging.info(f"Unexpected error: {e}")
        traceback.print_exc()
        epd2in13_V4.epdconfig.module_exit(cleanup=True)

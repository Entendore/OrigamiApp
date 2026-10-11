#!/usr/bin/env python3
"""
Origami Master - Enhanced Interactive Origami Learning Application
Built with PySide6 and Python
Features: 3D Fold Animations, Marching Ants Fold Lines, Practice Timer,
          Theme Toggle, Step Notes, Keyboard Shortcuts, Fun Facts, and more.
"""

import sys
import math
import json
import random
from datetime import date
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# ============================================================
# THEME & COLORS
# ============================================================
DARK_THEME = {
    'primary': '#6C63FF', 'primary_light': '#8B85FF', 'primary_dark': '#4A42CC',
    'secondary': '#FF6584', 'accent': '#43E97B',
    'bg': '#0D1117', 'bg_card': '#161B22', 'bg_surface': '#21262D',
    'bg_hover': '#30363D', 'text': '#F0F6FC', 'text_sec': '#8B949E',
    'text_muted': '#484F58', 'border': '#30363D',
    'paper': '#FFEAA7', 'paper2': '#FFECD2', 'paper_shadow': '#C8A84E',
    'fold_valley': '#3498DB', 'fold_mountain': '#E74C3C',
    'arrow': '#2ECC71', 'crease': '#95A5A6',
    'easy': '#43E97B', 'medium': '#F39C12', 'hard': '#E74C3C', 'star': '#FFD700',
    'toast_bg': '#1F2937',
}

LIGHT_THEME = {
    'primary': '#6C63FF', 'primary_light': '#8B85FF', 'primary_dark': '#4A42CC',
    'secondary': '#FF6584', 'accent': '#27AE60',
    'bg': '#F5F7FA', 'bg_card': '#FFFFFF', 'bg_surface': '#EDF0F5',
    'bg_hover': '#DDE1E8', 'text': '#1A1A2E', 'text_sec': '#5A6178',
    'text_muted': '#9CA3AF', 'border': '#D1D5DB',
    'paper': '#FFEAA7', 'paper2': '#FFECD2', 'paper_shadow': '#C8A84E',
    'fold_valley': '#2980B9', 'fold_mountain': '#C0392B',
    'arrow': '#27AE60', 'crease': '#7F8C8D',
    'easy': '#27AE60', 'medium': '#E67E22', 'hard': '#C0392B', 'star': '#F39C12',
    'toast_bg': '#FFFFFF',
}

C = dict(DARK_THEME)

def set_theme(is_dark):
    global C
    C = dict(DARK_THEME if is_dark else LIGHT_THEME)

def apply_stylesheet(app):
    app.setStyleSheet(f"""
        QMainWindow {{ background: {C['bg']}; }}
        QWidget {{ color: {C['text']}; font-family: 'Segoe UI', Arial; }}
        QLabel {{ color: {C['text']}; }}
        QScrollBar:vertical {{ background: {C['bg_card']}; width: 8px; border-radius: 4px; }}
        QScrollBar::handle:vertical {{ background: {C['bg_hover']}; border-radius: 4px; min-height: 30px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """)

# ============================================================
# ANIMATION GLOBAL
# ============================================================
_ANIM_OFFSET = 0.0

# ============================================================
# DRAWING HELPERS
# ============================================================
def draw_arrow(painter, x1, y1, x2, y2, color=None, width=2.5):
    color = color or C['arrow']
    painter.save()
    pen = QPen(QColor(color), width)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    angle = math.atan2(y2 - y1, x2 - x1)
    sz = 12
    p1 = QPointF(x2 - sz * math.cos(angle - math.pi / 6), y2 - sz * math.sin(angle - math.pi / 6))
    p2 = QPointF(x2 - sz * math.cos(angle + math.pi / 6), y2 - sz * math.sin(angle + math.pi / 6))
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(QPolygonF([QPointF(x2, y2), p1, p2]))
    painter.restore()

def draw_fold(painter, x1, y1, x2, y2, fold_type='valley', width=2):
    painter.save()
    pen = QPen()
    pen.setColor(QColor(C['fold_valley'] if fold_type == 'valley' else C['fold_mountain']))
    pen.setStyle(Qt.DashLine if fold_type == 'valley' else Qt.DashDotLine)
    pen.setWidth(width)
    pen.setDashOffset(_ANIM_OFFSET * (1 if fold_type == 'valley' else -1)) # Animate fold lines
    painter.setPen(pen)
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    painter.restore()

def draw_crease(painter, x1, y1, x2, y2, width=1.5):
    painter.save()
    pen = QPen(QColor(C['crease']), width, Qt.DotLine)
    pen.setDashOffset(_ANIM_OFFSET * 0.5) # Animate creases
    painter.setPen(pen)
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    painter.restore()

def draw_paper(painter, points, color=None, outline_color=None):
    color = color or C['paper']
    outline_color = outline_color or C['paper_shadow']
    painter.save()
    poly = QPolygonF([QPointF(x, y) for x, y in points])
    off = 4
    shadow = QPolygonF([QPointF(x + off, y + off) for x, y in points])
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(0, 0, 0, 30))
    painter.drawPolygon(shadow)
    painter.setBrush(QColor(color))
    painter.setPen(QPen(QColor(outline_color), 1.5))
    painter.drawPolygon(poly)
    painter.restore()

def draw_dot(painter, x, y, color=None, size=5):
    painter.save()
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color or C['fold_mountain']))
    painter.drawEllipse(QPointF(x, y), size, size)
    painter.restore()

def draw_text_label(painter, text, x, y, color=None, size=11, bold=False):
    painter.save()
    font = QFont('Segoe UI', size)
    font.setBold(bold)
    painter.setFont(font)
    painter.setPen(QColor(color or C['text_sec']))
    painter.drawText(QPointF(x, y), text)
    painter.restore()

def draw_curved_arrow(painter, cx, cy, r, start_angle, sweep, color=None, width=2):
    color = color or C['arrow']
    painter.save()
    pen = QPen(QColor(color), width)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    rect = QRectF(cx - r, cy - r, r * 2, r * 2)
    painter.drawArc(rect, int(start_angle * 16), int(sweep * 16))
    end_angle = math.radians(start_angle + sweep)
    ex, ey = cx + r * math.cos(end_angle), cy - r * math.sin(end_angle)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    sz = 10
    a1 = end_angle + math.pi * 0.8
    a2 = end_angle - math.pi * 0.8
    p1 = QPointF(ex + sz * math.cos(a1), ey - sz * math.sin(a1))
    p2 = QPointF(ex + sz * math.cos(a2), ey - sz * math.sin(a2))
    painter.drawPolygon(QPolygonF([QPointF(ex, ey), p1, p2]))
    painter.restore()

# ============================================================
# ORIGAMI STEP DRAWING FUNCTIONS
# ============================================================
def draw_airplane_s1(p, w, h):
    cx, cy = w / 2, h / 2; rw, rh = w * 0.6, h * 0.45
    draw_paper(p, [(cx - rw/2, cy - rh/2), (cx + rw/2, cy - rh/2), (cx + rw/2, cy + rh/2), (cx - rw/2, cy + rh/2)])
    draw_fold(p, cx, cy - rh/2, cx, cy + rh/2, 'valley'); draw_arrow(p, cx + 30, cy - rh/2 + 10, cx - 30, cy - rh/2 + 10)
    draw_text_label(p, "Fold in half vertically", cx - 55, cy + rh/2 + 25, C['text_sec'], 10)

def draw_airplane_s2(p, w, h):
    cx, cy = w / 2, h / 2; rw, rh = w * 0.3, h * 0.45
    draw_paper(p, [(cx - rw/2, cy - rh/2), (cx + rw/2, cy - rh/2), (cx + rw/2, cy + rh/2), (cx - rw/2, cy + rh/2)])
    draw_fold(p, cx - rw/2, cy - rh/2, cx, cy, 'valley'); draw_fold(p, cx + rw/2, cy - rh/2, cx, cy, 'valley')
    draw_arrow(p, cx - rw/2 + 10, cy - rh/4, cx - 5, cy - rh/4); draw_arrow(p, cx + rw/2 - 10, cy - rh/4, cx + 5, cy - rh/4)
    draw_text_label(p, "Fold corners to center line", cx - 65, cy + rh/2 + 25, C['text_sec'], 10)

def draw_airplane_s3(p, w, h):
    cx, cy = w / 2, h / 2; rw, rh = w * 0.3, h * 0.45
    draw_paper(p, [(cx - rw/2, cy - rh/2), (cx, cy - rh/2 + rh * 0.3), (cx, cy - rh/2), (cx + rw/2, cy - rh/2), (cx + rw/2, cy + rh/2), (cx - rw/2, cy + rh/2)])
    draw_fold(p, cx - rw/2, cy - rh/2 + rh * 0.3, cx, cy - rh/2 + rh * 0.6, 'valley'); draw_fold(p, cx + rw/2, cy - rh/2 + rh * 0.3, cx, cy - rh/2 + rh * 0.6, 'valley')
    draw_arrow(p, cx - rw/4, cy, cx, cy - rh/4); draw_arrow(p, cx + rw/4, cy, cx, cy - rh/4)
    draw_text_label(p, "Fold edges to center again", cx - 65, cy + rh/2 + 25, C['text_sec'], 10)

def draw_airplane_s4(p, w, h):
    cx, cy = w / 2, h / 2
    pts = [(cx, cy - h * 0.25), (cx + w * 0.3, cy + h * 0.1), (cx + w * 0.05, cy + h * 0.1), (cx + w * 0.05, cy + h * 0.25), (cx - w * 0.05, cy + h * 0.25), (cx - w * 0.05, cy + h * 0.1), (cx - w * 0.3, cy + h * 0.1)]
    draw_paper(p, pts, '#FFEAA7', '#C8A84E'); draw_curved_arrow(p, cx - w*0.15, cy - h*0.05, 25, 30, -120, C['arrow']); draw_curved_arrow(p, cx + w*0.15, cy - h*0.05, 25, 150, 120, C['arrow'])
    draw_text_label(p, "✈ Fold wings out — Done!", cx - 70, cy + h * 0.25 + 25, C['accent'], 11, True)

def draw_boat_s1(p, w, h):
    cx, cy = w / 2, h / 2; rw, rh = w * 0.6, h * 0.4
    draw_paper(p, [(cx-rw/2, cy-rh/2), (cx+rw/2, cy-rh/2), (cx+rw/2, cy+rh/2), (cx-rw/2, cy+rh/2)])
    draw_fold(p, cx-rw/2, cy, cx+rw/2, cy, 'valley'); draw_arrow(p, cx + 30, cy - rh/4, cx + 30, cy - 5)
    draw_text_label(p, "Fold in half horizontally", cx - 65, cy + rh/2 + 25, C['text_sec'], 10)

def draw_boat_s2(p, w, h):
    cx, cy = w / 2, h / 2; rw, rh = w * 0.6, h * 0.2
    draw_paper(p, [(cx-rw/2, cy-rh/2), (cx+rw/2, cy-rh/2), (cx+rw/2, cy+rh/2), (cx-rw/2, cy+rh/2)])
    draw_fold(p, cx-rw/2, cy-rh/2, cx, cy+rh/2, 'valley'); draw_fold(p, cx+rw/2, cy-rh/2, cx, cy+rh/2, 'valley')
    draw_arrow(p, cx-rw/3, cy-rh/3, cx-5, cy+rh/4); draw_arrow(p, cx+rw/3, cy-rh/3, cx+5, cy+rh/4)
    draw_text_label(p, "Fold corners to center", cx - 60, cy + rh/2 + 25, C['text_sec'], 10)

def draw_boat_s3(p, w, h):
    cx, cy = w / 2, h / 2
    draw_paper(p, [(cx-w*0.15, cy-h*0.15), (cx, cy-h*0.25), (cx+w*0.15, cy-h*0.15), (cx+w*0.3, cy-h*0.15), (cx+w*0.3, cy+h*0.2), (cx-w*0.3, cy+h*0.2), (cx-w*0.3, cy-h*0.15)])
    draw_fold(p, cx-w*0.3, cy+h*0.05, cx+w*0.3, cy+h*0.05, 'valley'); draw_arrow(p, cx+w*0.1, cy+h*0.15, cx+w*0.1, cy-h*0.05)
    draw_text_label(p, "Fold bottom flaps up", cx - 55, cy + h*0.2 + 25, C['text_sec'], 10)

def draw_boat_s4(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.25
    draw_paper(p, [(cx-s, cy-s/2), (cx+s, cy-s/2), (cx+s, cy+s/2), (cx-s, cy+s/2)])
    draw_arrow(p, cx-s, cy+s/4, cx-s/2, cy+s/4); draw_arrow(p, cx+s, cy+s/4, cx+s/2, cy+s/4)
    draw_text_label(p, "Pull apart from bottom", cx - 65, cy + s/2 + 25, C['text_sec'], 10)

def draw_boat_s5(p, w, h):
    cx, cy = w / 2, h / 2
    pts = [(cx-w*0.3, cy-h*0.05), (cx-w*0.25, cy+h*0.2), (cx+w*0.25, cy+h*0.2), (cx+w*0.3, cy-h*0.05), (cx+w*0.15, cy-h*0.15), (cx-w*0.15, cy-h*0.15)]
    draw_paper(p, pts, '#FFEAA7', '#C8A84E'); draw_text_label(p, "⛵ Boat complete!", cx - 45, cy + h*0.2 + 25, C['accent'], 11, True)

def draw_crane_s1(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.35
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy-s, cx+s, cy+s, 'valley'); draw_fold(p, cx+s, cy-s, cx-s, cy+s, 'mountain')
    draw_arrow(p, cx+s-20, cy-s+20, cx-s+20, cy+s-20, C['arrow']); draw_arrow(p, cx-s+20, cy-s+20, cx+s-20, cy+s-20, C['fold_mountain'])
    draw_text_label(p, "Fold both diagonals", cx - 50, cy + s + 25, C['text_sec'], 10)

def draw_crane_s2(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.3
    draw_paper(p, [(cx, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy+s, cx+s, cy+s, 'valley'); draw_arrow(p, cx+s-20, cy+s-5, cx-s+20, cy+s-5)
    draw_text_label(p, "Fold triangle in half", cx - 55, cy + s + 25, C['text_sec'], 10)

def draw_crane_s3(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.2
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy+s, cx, cy-s, 'valley'); draw_fold(p, cx+s, cy+s, cx, cy-s, 'valley')
    draw_arrow(p, cx, cy-s+10, cx, cy, C['arrow']); draw_text_label(p, "Squash fold — press down", cx - 60, cy + s + 25, C['text_sec'], 10)

def draw_crane_s4(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.25
    draw_paper(p, [(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)])
    draw_text_label(p, "Flip over, repeat squash fold", cx - 85, cy + s + 25, C['text_sec'], 10); draw_arrow(p, cx+s+20, cy, cx+s+5, cy, C['fold_mountain'])

def draw_crane_s5(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.25
    draw_paper(p, [(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)])
    draw_fold(p, cx-s, cy, cx, cy-s, 'valley'); draw_fold(p, cx, cy-s, cx+s, cy, 'valley')
    draw_arrow(p, cx-s/2, cy-s/2, cx-s/4, cy-s/4); draw_text_label(p, "Fold edges to center (both sides)", cx - 95, cy + s + 25, C['text_sec'], 10)

def draw_crane_s6(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.2
    pts = [(cx, cy-s*1.5), (cx+s*0.5, cy-s*0.3), (cx+s, cy-s*0.3), (cx+s*0.3, cy+s*1.5), (cx-s*0.3, cy+s*1.5), (cx-s, cy-s*0.3), (cx-s*0.5, cy-s*0.3)]
    draw_paper(p, pts); draw_fold(p, cx-s*0.3, cy+s*1.5, cx, cy+s*0.5, 'valley'); draw_fold(p, cx+s*0.3, cy+s*1.5, cx, cy+s*0.5, 'valley')
    draw_text_label(p, "Petal fold front & back", cx - 65, cy + s*1.5 + 25, C['text_sec'], 10)

def draw_crane_s7(p, w, h):
    cx, cy = w / 2, h / 2
    pts = [(cx-w*0.3, cy-h*0.05), (cx-w*0.1, cy-h*0.1), (cx, cy-h*0.3), (cx+w*0.1, cy-h*0.1), (cx+w*0.3, cy-h*0.05), (cx+w*0.15, cy+h*0.05), (cx+w*0.05, cy+h*0.3), (cx-w*0.05, cy+h*0.3), (cx-w*0.15, cy+h*0.05)]
    draw_paper(p, pts, '#FFEAA7', '#C8A84E'); draw_text_label(p, "🦢 Reverse fold head, spread wings!", cx - 100, cy + h*0.3 + 25, C['accent'], 11, True)

def draw_frog_s1(p, w, h):
    cx, cy = w / 2, h / 2; rw, rh = w * 0.5, h * 0.6
    draw_paper(p, [(cx-rw/2, cy-rh/2), (cx+rw/2, cy-rh/2), (cx+rw/2, cy+rh/2), (cx-rw/2, cy+rh/2)])
    draw_fold(p, cx-rw/2, cy-rh/2, cx+rw/2, cy+rh/2, 'valley'); draw_fold(p, cx+rw/2, cy-rh/2, cx-rw/2, cy+rh/2, 'valley')
    draw_text_label(p, "Fold both diagonals", cx - 50, cy + rh/2 + 25, C['text_sec'], 10)

def draw_frog_s2(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.25
    draw_paper(p, [(cx, cy-s), (cx+s, cy+s), (cx-s, cy+s)]); draw_fold(p, cx, cy-s, cx-s/2, cy, 'valley'); draw_fold(p, cx, cy-s, cx+s/2, cy, 'valley')
    draw_text_label(p, "Fold top corners down", cx - 55, cy + s + 25, C['text_sec'], 10)

def draw_frog_s3(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.22
    draw_paper(p, [(cx-s, cy-s), (cx, cy-s/2), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_arrow(p, cx, cy-s, cx, cy, C['arrow']); draw_text_label(p, "Squash fold — press down", cx - 60, cy + s + 25, C['text_sec'], 10)

def draw_frog_s4(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.2
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s*1.5), (cx-s, cy+s*1.5)])
    draw_fold(p, cx-s, cy-s, cx-s/3, cy-s, 'valley'); draw_fold(p, cx+s/3, cy-s, cx+s, cy-s, 'valley')
    draw_text_label(p, "Fold sides to center", cx - 50, cy + s*1.5 + 25, C['text_sec'], 10)

def draw_frog_s5(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.2
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy), (cx+s*0.5, cy+s*1.5), (cx-s*0.5, cy+s*1.5), (cx-s, cy)])
    draw_fold(p, cx-s, cy+s*0.5, cx+s, cy+s*0.5, 'valley'); draw_text_label(p, "Fold bottom half up", cx - 50, cy + s*1.5 + 25, C['text_sec'], 10)

def draw_frog_s6(p, w, h):
    cx, cy = w / 2, h / 2
    pts = [(cx-w*0.15, cy-h*0.2), (cx, cy-h*0.3), (cx+w*0.15, cy-h*0.2), (cx+w*0.2, cy), (cx+w*0.25, cy+h*0.25), (cx+w*0.1, cy+h*0.3), (cx-w*0.1, cy+h*0.3), (cx-w*0.25, cy+h*0.25), (cx-w*0.2, cy)]
    draw_paper(p, pts, '#ABEBC6', '#7DCEA0'); draw_dot(p, cx-w*0.06, cy-h*0.2, '#2C3E50', 4); draw_dot(p, cx+w*0.06, cy-h*0.2, '#2C3E50', 4)
    draw_text_label(p, "🐸 Press back to make it jump!", cx - 80, cy + h*0.3 + 25, C['accent'], 11, True)

def draw_lotus_s1(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.3
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy-s, cx, cy-s/2, 'valley'); draw_fold(p, cx+s, cy-s, cx, cy-s/2, 'valley'); draw_fold(p, cx+s, cy+s, cx, cy+s/2, 'valley'); draw_fold(p, cx-s, cy+s, cx, cy+s/2, 'valley')
    draw_text_label(p, "Fold all corners to center", cx - 70, cy + s + 25, C['text_sec'], 10)

def draw_lotus_s2(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.22
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)], '#FFEAA7', '#C8A84E')
    draw_fold(p, cx-s, cy-s, cx, cy-s/2, 'valley'); draw_fold(p, cx+s, cy-s, cx, cy-s/2, 'valley'); draw_fold(p, cx+s, cy+s, cx, cy+s/2, 'valley'); draw_fold(p, cx-s, cy+s, cx, cy+s/2, 'valley')
    draw_text_label(p, "Fold corners to center again", cx - 75, cy + s + 25, C['text_sec'], 10)

def draw_lotus_s3(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.2
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)], '#FFECD2', '#D4A76A')
    draw_text_label(p, "Flip over, fold corners to center", cx - 95, cy + s + 25, C['text_sec'], 10)

def draw_lotus_s4(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.15
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    for a_deg in [0, 90, 180, 270]:
        rad = math.radians(a_deg); ex, ey = cx + s*1.5*math.cos(rad), cy + s*1.5*math.sin(rad)
        draw_arrow(p, cx + s*0.5*math.cos(rad), cy + s*0.5*math.sin(rad), ex, ey, '#FF85A2')
    draw_text_label(p, "Pull up petals from below", cx - 65, cy + s*2 + 20, C['text_sec'], 10)

def draw_lotus_s5(p, w, h):
    cx, cy = w / 2, h / 2
    for i in range(8):
        angle = math.radians(i * 45 - 90); px, py = cx + w*0.15 * math.cos(angle), cy + h*0.15 * math.sin(angle)
        draw_paper(p, [(cx, cy), (px-8, py+5), (px, py-10), (px+8, py+5)], '#FFB6C1', '#FF69B4')
    draw_paper(p, [(cx-8, cy-8), (cx+8, cy-8), (cx+8, cy+8), (cx-8, cy+8)], '#FFEAA7', '#C8A84E')
    draw_text_label(p, "🌺 Lotus complete!", cx - 50, cy + h*0.15 + 25, C['accent'], 11, True)

def draw_butterfly_s1(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.3
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy-s, cx+s, cy+s, 'valley'); draw_fold(p, cx+s, cy-s, cx-s, cy+s, 'mountain'); draw_fold(p, cx-s, cy, cx+s, cy, 'valley')
    draw_text_label(p, "Fold both diagonals & in half", cx - 85, cy + s + 25, C['text_sec'], 10)

def draw_butterfly_s2(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.25
    draw_paper(p, [(cx, cy-s), (cx+s, cy+s*0.5), (cx, cy+s), (cx-s, cy+s*0.5)])
    draw_text_label(p, "Collapse into waterbomb base", cx - 75, cy + s + 25, C['text_sec'], 10)

def draw_butterfly_s3(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.22
    draw_paper(p, [(cx-s, cy-s*0.5), (cx+s, cy-s*0.5), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy-s*0.5, cx, cy-s*0.5+5, 'valley'); draw_fold(p, cx+s, cy-s*0.5, cx, cy-s*0.5+5, 'valley')
    draw_text_label(p, "Fold top layer corners up", cx - 70, cy + s + 25, C['text_sec'], 10)

def draw_butterfly_s4(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.2
    draw_paper(p, [(cx-s, cy-s), (cx, cy), (cx+s, cy-s), (cx+s*0.3, cy+s), (cx-s*0.3, cy+s)])
    draw_fold(p, cx, cy-s, cx, cy+s*0.5, 'valley'); draw_text_label(p, "Fold in half vertically", cx - 60, cy + s + 25, C['text_sec'], 10)

def draw_butterfly_s5(p, w, h):
    cx, cy = w / 2, h / 2
    for side in [-1, 1]:
        pts = [(cx, cy-h*0.15), (cx+side*w*0.25, cy-h*0.15), (cx+side*w*0.3, cy+h*0.1), (cx+side*w*0.15, cy+h*0.2), (cx, cy+h*0.05)]
        draw_paper(p, pts, '#DDA0DD', '#BA55D3')
    draw_paper(p, [(cx-3, cy-h*0.15), (cx+3, cy-h*0.15), (cx+3, cy+h*0.1), (cx-3, cy+h*0.1)], '#2C3E50', '#1A252F')
    draw_text_label(p, "🦋 Butterfly complete!", cx - 60, cy + h*0.2 + 25, C['accent'], 11, True)

def draw_star_s1(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.3
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy-s, cx, cy+s, 'valley'); draw_fold(p, cx+s, cy-s, cx, cy+s, 'valley')
    draw_text_label(p, "Fold both diagonals", cx - 50, cy + s + 25, C['text_sec'], 10)

def draw_star_s2(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.3
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy, cx+s*0.2, cy-s, 'valley'); draw_fold(p, cx+s, cy, cx-s*0.2, cy-s, 'valley')
    draw_text_label(p, "Fold edges to create guide lines", cx - 90, cy + s + 25, C['text_sec'], 10)

def draw_star_s3(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.25
    pts = [(cx + s * math.cos(math.radians(i * 72 - 90)), cy + s * math.sin(math.radians(i * 72 - 90))) for i in range(5)]
    draw_paper(p, pts, '#FFEAA7', '#C8A84E'); draw_fold(p, pts[0][0], pts[0][1], pts[2][0], pts[2][1], 'valley')
    draw_text_label(p, "Fold into pentagon shape", cx - 60, cy + s + 30, C['text_sec'], 10)

def draw_star_s4(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.2
    pts = [(cx + s * math.cos(math.radians(i * 72 - 90)), cy + s * math.sin(math.radians(i * 72 - 90))) for i in range(5)]
    draw_paper(p, pts)
    for i in range(5):
        ma = math.radians(i * 72 - 90 + 36); draw_fold(p, pts[i][0], pts[i][1], cx + s * 0.4 * math.cos(ma), cy + s * 0.4 * math.sin(ma), 'valley')
    draw_text_label(p, "Fold edges to center", cx - 50, cy + s + 30, C['text_sec'], 10)

def draw_star_s5(p, w, h):
    cx, cy = w / 2, h / 2
    pts = []
    for i in range(10):
        a = math.radians(i * 36 - 90); r = min(w, h) * 0.25 if i % 2 == 0 else min(w, h) * 0.12
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw_paper(p, pts, '#FFEAA7', '#C8A84E'); draw_text_label(p, "⭐ Star complete!", cx - 50, cy + min(w, h)*0.25 + 30, C['accent'], 11, True)

def draw_heart_s1(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.3
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy, cx+s, cy, 'valley'); draw_arrow(p, cx+20, cy-s/2, cx+20, cy-5)
    draw_text_label(p, "Fold in half horizontally, unfold", cx - 85, cy + s + 25, C['text_sec'], 10)

def draw_heart_s2(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.3
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy-s, cx-s, cy, 'valley'); draw_fold(p, cx+s, cy-s, cx+s, cy, 'valley')
    draw_arrow(p, cx-s/2, cy-s/2, cx-s/2, cy-5); draw_arrow(p, cx+s/2, cy-s/2, cx+s/2, cy-5)
    draw_text_label(p, "Fold top edge to center crease", cx - 80, cy + s + 25, C['text_sec'], 10)

def draw_heart_s3(p, w, h):
    cx, cy = w / 2, h / 2; rw, rh = w * 0.5, h * 0.15
    draw_paper(p, [(cx-rw/2, cy-rh), (cx+rw/2, cy-rh), (cx+rw/2, cy+rh), (cx-rw/2, cy+rh)])
    draw_fold(p, cx-rw/2, cy-rh, cx-rw/4, cy+rh, 'valley'); draw_fold(p, cx+rw/2, cy-rh, cx+rw/4, cy+rh, 'valley')
    draw_arrow(p, cx-rw/3, cy, cx-rw/5, cy+rh/2); draw_arrow(p, cx+rw/3, cy, cx+rw/5, cy+rh/2)
    draw_text_label(p, "Fold side corners to center", cx - 70, cy + rh + 25, C['text_sec'], 10)

def draw_heart_s4(p, w, h):
    cx, cy = w / 2, h / 2; rw, rh = w * 0.4, h * 0.2
    draw_paper(p, [(cx-rw, cy-rh/2), (cx+rw, cy-rh/2), (cx+rw, cy+rh), (cx-rw, cy+rh)])
    draw_fold(p, cx-rw, cy-rh/2, cx-rw*0.5, cy+rh, 'valley'); draw_fold(p, cx+rw, cy-rh/2, cx+rw*0.5, cy+rh, 'valley')
    draw_text_label(p, "Fold bottom corners to center", cx - 75, cy + rh + 25, C['text_sec'], 10)

def draw_heart_s5(p, w, h):
    cx, cy = w / 2, h / 2
    pts = [(cx, cy-h*0.05), (cx-w*0.05, cy-h*0.15), (cx-w*0.2, cy-h*0.2), (cx-w*0.3, cy-h*0.1), (cx-w*0.3, cy+h*0.05), (cx, cy+h*0.3), (cx+w*0.3, cy+h*0.05), (cx+w*0.3, cy-h*0.1), (cx+w*0.2, cy-h*0.2), (cx+w*0.05, cy-h*0.15)]
    draw_paper(p, pts, '#FFB6C1', '#FF69B4'); draw_text_label(p, "❤️ Heart complete!", cx - 50, cy + h*0.3 + 25, C['accent'], 11, True)

def draw_box_s1(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.3
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy-s, cx, cy-s/2, 'valley'); draw_fold(p, cx+s, cy-s, cx, cy-s/2, 'valley'); draw_fold(p, cx+s, cy+s, cx, cy+s/2, 'valley'); draw_fold(p, cx-s, cy+s, cx, cy+s/2, 'valley')
    draw_text_label(p, "Fold all corners to center", cx - 70, cy + s + 25, C['text_sec'], 10)

def draw_box_s2(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.25
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy, cx+s, cy, 'valley'); draw_fold(p, cx, cy-s, cx, cy+s, 'valley')
    draw_text_label(p, "Fold edges to center (both ways), unfold", cx - 105, cy + s + 25, C['text_sec'], 10)

def draw_box_s3(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.22
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy-s, cx, cy-s, 'valley'); draw_fold(p, cx+s, cy-s, cx, cy-s, 'valley')
    draw_arrow(p, cx-s+10, cy-s/2, cx, cy-s/2); draw_text_label(p, "Fold top & bottom up partially", cx - 80, cy + s + 25, C['text_sec'], 10)

def draw_box_s4(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.18
    draw_paper(p, [(cx-s*1.5, cy-s), (cx+s*1.5, cy-s), (cx+s*1.5, cy+s), (cx-s*1.5, cy+s)])
    draw_fold(p, cx-s*1.5, cy-s, cx-s*0.5, cy+s*0.5, 'valley'); draw_fold(p, cx+s*1.5, cy-s, cx+s*0.5, cy+s*0.5, 'valley')
    draw_text_label(p, "Fold side flaps inward", cx - 55, cy + s + 25, C['text_sec'], 10)

def draw_box_s5(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.2
    draw_paper(p, [(cx-s*1.2, cy-s*0.6), (cx+s*1.2, cy-s*0.6), (cx+s*1.2, cy+s*0.6), (cx-s*1.2, cy+s*0.6)], '#FFEAA7', '#C8A84E')
    draw_paper(p, [(cx-s*0.8, cy-s*0.3), (cx+s*0.8, cy-s*0.3), (cx+s*0.8, cy+s*0.3), (cx-s*0.8, cy+s*0.3)], '#FFECD2', '#D4A76A')
    draw_text_label(p, "📦 Box complete! Make lid the same way", cx - 110, cy + s*0.6 + 25, C['accent'], 11, True)

def draw_flapping_s1(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.3
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy-s, cx+s, cy+s, 'valley'); draw_fold(p, cx+s, cy-s, cx-s, cy+s, 'valley')
    draw_text_label(p, "Fold both diagonals (same as crane)", cx - 95, cy + s + 25, C['text_sec'], 10)

def draw_flapping_s2(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.2
    draw_paper(p, [(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)])
    draw_fold(p, cx-s, cy, cx, cy-s, 'valley'); draw_fold(p, cx, cy-s, cx+s, cy, 'valley')
    draw_text_label(p, "Make preliminary base, fold edges to center", cx - 115, cy + s + 25, C['text_sec'], 10)

def draw_flapping_s3(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.2
    pts = [(cx, cy-s*1.5), (cx+s*0.5, cy-s*0.3), (cx+s, cy-s*0.3), (cx+s*0.3, cy+s*1.5), (cx-s*0.3, cy+s*1.5), (cx-s, cy-s*0.3), (cx-s*0.5, cy-s*0.3)]
    draw_paper(p, pts); draw_text_label(p, "Petal fold (same as crane step 6)", cx - 90, cy + s*1.5 + 25, C['text_sec'], 10)

def draw_flapping_s4(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.15
    pts = [(cx, cy-s*2), (cx+s*0.3, cy-s*0.5), (cx+s*0.3, cy+s*2), (cx-s*0.3, cy+s*2), (cx-s*0.3, cy-s*0.5)]
    draw_paper(p, pts); draw_fold(p, cx-s*0.3, cy+s*2, cx, cy, 'valley'); draw_fold(p, cx+s*0.3, cy+s*2, cx, cy, 'valley')
    draw_text_label(p, "Fold one layer up for neck & tail", cx - 90, cy + s*2 + 25, C['text_sec'], 10)

def draw_flapping_s5(p, w, h):
    cx, cy = w / 2, h / 2
    pts = [(cx-w*0.25, cy-h*0.05), (cx-w*0.1, cy-h*0.1), (cx, cy-h*0.25), (cx+w*0.1, cy-h*0.1), (cx+w*0.25, cy-h*0.05), (cx+w*0.1, cy+h*0.05), (cx+w*0.05, cy+h*0.25), (cx-w*0.05, cy+h*0.25), (cx-w*0.1, cy+h*0.05)]
    draw_paper(p, pts, '#87CEEB', '#5DADE2'); draw_arrow(p, cx, cy+h*0.05, cx, cy-h*0.15, C['arrow']); draw_arrow(p, cx, cy+h*0.05, cx, cy+h*0.2, C['arrow'])
    draw_text_label(p, "🐦 Pull tail to flap wings!", cx - 70, cy + h*0.25 + 25, C['accent'], 11, True)

def draw_tulip_s1(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.3
    draw_paper(p, [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s, cy-s, cx+s, cy+s, 'valley'); draw_text_label(p, "Fold one diagonal", cx - 40, cy + s + 25, C['text_sec'], 10)

def draw_tulip_s2(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.25
    draw_paper(p, [(cx, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    draw_fold(p, cx-s+5, cy+s, cx-s/3, cy-s/3, 'valley'); draw_fold(p, cx+s-5, cy+s, cx+s/3, cy-s/3, 'valley')
    draw_text_label(p, "Fold bottom corners up (not to tip)", cx - 90, cy + s + 25, C['text_sec'], 10)

def draw_tulip_s3(p, w, h):
    cx, cy = w / 2, h / 2; s = min(w, h) * 0.22
    draw_paper(p, [(cx-s, cy-s), (cx, cy-s*1.5), (cx+s, cy-s), (cx+s*0.8, cy+s), (cx-s*0.8, cy+s)])
    draw_fold(p, cx-s*0.8, cy+s, cx, cy, 'valley'); draw_fold(p, cx+s*0.8, cy+s, cx, cy, 'valley')
    draw_text_label(p, "Fold side corners to center", cx - 65, cy + s + 25, C['text_sec'], 10)

def draw_tulip_s4(p, w, h):
    cx, cy = w / 2, h / 2
    pts = [(cx-w*0.15, cy-h*0.2), (cx-w*0.2, cy-h*0.05), (cx-w*0.15, cy+h*0.25), (cx+w*0.15, cy+h*0.25), (cx+w*0.2, cy-h*0.05), (cx+w*0.15, cy-h*0.2), (cx, cy-h*0.35)]
    draw_paper(p, pts, '#FF6B6B', '#EE5A24'); draw_text_label(p, "🌷 Tulip complete! Add a stem!", cx - 80, cy + h*0.25 + 25, C['accent'], 11, True)


# ============================================================
# ORIGAMI DATA & FUN FACTS
# ============================================================
ORIGAMI_DATA = [
    {'id': 'airplane', 'name': 'Paper Airplane', 'category': 'Objects', 'difficulty': 'Easy', 'emoji': '✈️', 'time': '5 min', 'paper': 'A4 Rectangle', 'description': 'The classic paper airplane — quick to make and fun to fly! Perfect for beginners.', 'steps': [
        {'title': 'Start with a Rectangle', 'instruction': 'Begin with a rectangular piece of paper placed vertically. Colored side down.', 'tip': 'Standard A4 or letter paper works great!', 'draw': draw_airplane_s1},
        {'title': 'Fold in Half', 'instruction': 'Fold the paper in half vertically, then unfold to create a center crease.', 'tip': 'Align edges perfectly for a symmetrical airplane.', 'draw': draw_airplane_s2},
        {'title': 'Fold Edges to Center', 'instruction': 'Fold the top edges down to meet the center crease, forming a triangle.', 'tip': 'The sharper the fold, the better it flies.', 'draw': draw_airplane_s3},
        {'title': 'Final Folds & Wings', 'instruction': 'Fold edges to center again, fold plane in half, then fold down wings.', 'tip': 'Angle wings slightly upward for better gliding!', 'draw': draw_airplane_s4},
    ]},
    {'id': 'boat', 'name': 'Paper Boat', 'category': 'Objects', 'difficulty': 'Easy', 'emoji': '⛵', 'time': '8 min', 'paper': 'A4 Rectangle', 'description': 'A traditional paper boat that can actually float on water for a short time!', 'steps': [
        {'title': 'Start with Rectangle', 'instruction': 'Fold it in half from top to bottom.', 'tip': 'Wax paper works best for floating!', 'draw': draw_boat_s1},
        {'title': 'Fold Corners', 'instruction': 'Fold the top two corners down to meet at the center crease.', 'tip': 'Keep folds neat and even.', 'draw': draw_boat_s2},
        {'title': 'Fold Bottom Flaps', 'instruction': 'Fold the bottom front flap up. Flip over and repeat.', 'tip': 'Tuck corner triangles to hold in place.', 'draw': draw_boat_s3},
        {'title': 'Open & Reshape', 'instruction': 'Pull bottom edges apart and push sides in to form a diamond.', 'tip': 'Trickiest step — be patient!', 'draw': draw_boat_s4},
        {'title': 'Pull Apart', 'instruction': 'Gently pull top layers apart. Shape the bottom flat.', 'tip': 'Curl the ends for a realistic look.', 'draw': draw_boat_s5},
    ]},
    {'id': 'crane', 'name': 'Paper Crane', 'category': 'Birds', 'difficulty': 'Hard', 'emoji': '🦢', 'time': '15 min', 'paper': '15cm Square', 'description': 'The iconic origami crane — a symbol of peace and the most famous origami model.', 'steps': [
        {'title': 'Square Base — Diagonals', 'instruction': 'Start square, colored side up. Fold both diagonals, unfold.', 'tip': 'Use 15cm×15cm origami paper.', 'draw': draw_crane_s1},
        {'title': 'Fold Triangle', 'instruction': 'Fold in half to form a triangle.', 'tip': 'Crease well and keep aligned.', 'draw': draw_crane_s2},
        {'title': 'Squash Fold', 'instruction': 'Lift top layer, open and press down to form a square.', 'tip': 'Press firmly along the creases.', 'draw': draw_crane_s3},
        {'title': 'Flip & Repeat', 'instruction': 'Flip over, repeat squash fold on other side.', 'tip': 'You now have a diamond (preliminary base).', 'draw': draw_crane_s4},
        {'title': 'Fold to Center', 'instruction': 'Fold left and right edges to center on both sides.', 'tip': 'Fold precisely for best results.', 'draw': draw_crane_s5},
        {'title': 'Petal Fold', 'instruction': 'Unfold previous folds and petal fold front & back.', 'tip': 'Petal fold combines fold-up and fold-down.', 'draw': draw_crane_s6},
        {'title': 'Form the Crane', 'instruction': 'Fold narrow points up for neck/tail. Reverse fold head. Spread wings.', 'tip': 'Blow into the bottom hole to puff the body!', 'draw': draw_crane_s7},
    ]},
    {'id': 'frog', 'name': 'Jumping Frog', 'category': 'Animals', 'difficulty': 'Medium', 'emoji': '🐸', 'time': '10 min', 'paper': 'A4 Rectangle', 'description': 'A fun origami frog that actually jumps when you press its back!', 'steps': [
        {'title': 'Diagonal Folds', 'instruction': 'Start with rectangle. Fold both diagonals of the top square half.', 'tip': 'Slightly thicker paper jumps better.', 'draw': draw_frog_s1},
        {'title': 'Top Folds', 'instruction': 'Fold top corners down for waterbomb base creases.', 'tip': 'Crease firmly and unfold.', 'draw': draw_frog_s2},
        {'title': 'Waterbomb Base', 'instruction': 'Push sides in, press down to form triangle on top.', 'tip': 'Similar to crane base.', 'draw': draw_frog_s3},
        {'title': 'Fold Sides In', 'instruction': 'Fold outer triangle edges to center, then bottom sides to center.', 'tip': 'Keep folds symmetric for balanced jumping.', 'draw': draw_frog_s4},
        {'title': 'Fold Bottom Up', 'instruction': 'Fold the bottom portion up to meet the triangle.', 'tip': 'This creates the spring mechanism!', 'draw': draw_frog_s5},
        {'title': 'Final Jumps!', 'instruction': 'Fold bottom back down in Z-fold. Press the back to jump! Add eyes.', 'tip': 'Sharp Z-fold = higher jumps!', 'draw': draw_frog_s6},
    ]},
    {'id': 'lotus', 'name': 'Lotus Flower', 'category': 'Flowers', 'difficulty': 'Medium', 'emoji': '🌺', 'time': '12 min', 'paper': '20cm Square', 'description': 'A beautiful origami lotus flower — elegant and serene.', 'steps': [
        {'title': 'First Corner Fold', 'instruction': 'Fold all four corners to center.', 'tip': 'Use thin paper for multiple layers.', 'draw': draw_lotus_s1},
        {'title': 'Second Corner Fold', 'instruction': 'Fold all four corners to center again.', 'tip': 'Paper gets thicker — press firmly.', 'draw': draw_lotus_s2},
        {'title': 'Flip & Fold', 'instruction': 'Flip over, fold all corners to center once more.', 'tip': 'Last corner fold!', 'draw': draw_lotus_s3},
        {'title': 'Pull Up Petals', 'instruction': 'Gently pull each corner from underneath for outer petals.', 'tip': 'Be gentle — paper can tear!', 'draw': draw_lotus_s4},
        {'title': 'Shape the Lotus', 'instruction': 'Curl inner petals upward. Adjust all petals for natural look.', 'tip': 'Use a pen to curl petal tips!', 'draw': draw_lotus_s5},
    ]},
    {'id': 'butterfly', 'name': 'Butterfly', 'category': 'Animals', 'difficulty': 'Medium', 'emoji': '🦋', 'time': '10 min', 'paper': '15cm Square', 'description': 'A delicate origami butterfly that makes a lovely decoration.', 'steps': [
        {'title': 'Base Creases', 'instruction': 'Fold both diagonals and fold in half horizontally. Unfold all.', 'tip': 'Precise creases lead to better butterfly.', 'draw': draw_butterfly_s1},
        {'title': 'Waterbomb Base', 'instruction': 'Collapse into waterbomb base triangle.', 'tip': 'Push sides in while pressing top down.', 'draw': draw_butterfly_s2},
        {'title': 'Fold Top Layer', 'instruction': 'Fold top layer corners up to the top point.', 'tip': 'Only fold top layer, not both.', 'draw': draw_butterfly_s3},
        {'title': 'Fold & Shape', 'instruction': 'Fold top point down slightly, then fold in half.', 'tip': 'Small fold becomes the body.', 'draw': draw_butterfly_s4},
        {'title': 'Final Wings', 'instruction': 'Pull wings down and apart. Shape gently.', 'tip': 'Curve wings for a 3D effect!', 'draw': draw_butterfly_s5},
    ]},
    {'id': 'star', 'name': 'Ninja Star', 'category': 'Objects', 'difficulty': 'Hard', 'emoji': '⭐', 'time': '15 min', 'paper': 'Two 15cm Squares', 'description': 'A cool transforming ninja star (shuriken) made from two pieces of paper!', 'steps': [
        {'title': 'Diagonal Folds', 'instruction': 'Start with square. Fold both diagonals, unfold.', 'tip': 'You need TWO squares of different colors.', 'draw': draw_star_s1},
        {'title': 'Guide Folds', 'instruction': 'Fold edges to create guide creases for the star.', 'tip': 'Creases help form star points.', 'draw': draw_star_s2},
        {'title': 'Pentagon Shape', 'instruction': 'Using creases, fold into a pentagon shape.', 'tip': 'Most challenging step — take your time.', 'draw': draw_star_s3},
        {'title': 'Star Points', 'instruction': 'Fold each pentagon edge inward to create star points.', 'tip': 'Press firmly for clean points.', 'draw': draw_star_s4},
        {'title': 'Complete Star', 'instruction': 'Tuck loose edges, shape all five points.', 'tip': 'Balance on a pin to make it spin!', 'draw': draw_star_s5},
    ]},
    {'id': 'heart', 'name': 'Heart', 'category': 'Flowers', 'difficulty': 'Easy', 'emoji': '❤️', 'time': '5 min', 'paper': '15cm Square', 'description': 'A simple and sweet origami heart — perfect for love letters and cards!', 'steps': [
        {'title': 'Fold in Half', 'instruction': 'Fold square in half horizontally, then unfold to create a crease.', 'tip': 'Colored side up for this one!', 'draw': draw_heart_s1},
        {'title': 'Fold Top Edge', 'instruction': 'Fold the top edge down to the center crease.', 'tip': 'Keep it sharp and even.', 'draw': draw_heart_s2},
        {'title': 'Fold Corners In', 'instruction': 'Fold the top corners down to the center line, creating a point at the top.', 'tip': 'These will become the top bumps of the heart.', 'draw': draw_heart_s3},
        {'title': 'Fold Bottom', 'instruction': 'Fold the bottom corners to the center to create the heart point.', 'tip': 'Round the top with your fingers for a softer look.', 'draw': draw_heart_s4},
        {'title': 'Shape the Heart', 'instruction': 'Gently round the top bumps and shape the heart. Flip to show clean side.', 'tip': 'Write a message on it for someone special!', 'draw': draw_heart_s5},
    ]},
    {'id': 'box', 'name': 'Masu Box', 'category': 'Objects', 'difficulty': 'Medium', 'emoji': '📦', 'time': '10 min', 'paper': '20cm Square', 'description': 'A traditional Japanese masu box — great for holding small items or gifts!', 'steps': [
        {'title': 'Corner Folds', 'instruction': 'Fold all four corners to the center point.', 'tip': 'Make a pinch at center first to mark it.', 'draw': draw_box_s1},
        {'title': 'Edge Folds', 'instruction': 'Fold each edge to the center, unfold. Do this for all four edges.', 'tip': 'These creases define the box walls.', 'draw': draw_box_s2},
        {'title': 'Partial Fold Up', 'instruction': 'Fold top and bottom edges partially upward using existing creases.', 'tip': "Don't fold all the way — just to shape the walls.", 'draw': draw_box_s3},
        {'title': 'Side Flaps', 'instruction': 'Fold the side flaps inward to form the box corners.', 'tip': 'Tuck them behind the front wall for a clean look.', 'draw': draw_box_s4},
        {'title': 'Shape the Box', 'instruction': 'Open up and shape into a box. Make a second one slightly larger for a lid!', 'tip': 'Use larger paper for the lid (about 5% bigger).', 'draw': draw_box_s5},
    ]},
    {'id': 'flapping_bird', 'name': 'Flapping Bird', 'category': 'Birds', 'difficulty': 'Hard', 'emoji': '🐦', 'time': '12 min', 'paper': '15cm Square', 'description': 'Like the crane, but the wings actually flap when you pull the tail! A crowd favorite.', 'steps': [
        {'title': 'Diagonal Folds', 'instruction': 'Start with a square. Fold both diagonals, unfold.', 'tip': 'Same beginning as the crane.', 'draw': draw_flapping_s1},
        {'title': 'Preliminary Base', 'instruction': 'Make the preliminary base, then fold edges to center (both sides).', 'tip': 'You should have a bird base shape.', 'draw': draw_flapping_s2},
        {'title': 'Petal Fold', 'instruction': 'Petal fold on both front and back, just like the crane.', 'tip': 'This is the bird base — same as crane step 6.', 'draw': draw_flapping_s3},
        {'title': 'Fold Up Points', 'instruction': 'Fold one narrow point up for the neck, the other for the tail.', 'tip': 'Only fold one layer up, not both.', 'draw': draw_flapping_s4},
        {'title': 'Pull Tail to Flap!', 'instruction': 'Reverse fold the neck tip to make the head. Gently pull the tail — the wings flap!', 'tip': 'Pull gently and smoothly for best flapping action!', 'draw': draw_flapping_s5},
    ]},
    {'id': 'tulip', 'name': 'Tulip', 'category': 'Flowers', 'difficulty': 'Easy', 'emoji': '🌷', 'time': '6 min', 'paper': '15cm Square', 'description': 'A cheerful origami tulip — pair it with a paper stem for a complete flower!', 'steps': [
        {'title': 'Diagonal Fold', 'instruction': 'Fold the square in half diagonally to form a triangle.', 'tip': 'Colored side on the outside.', 'draw': draw_tulip_s1},
        {'title': 'Fold Corners Up', 'instruction': 'Fold the bottom corners upward, but not all the way to the top.', 'tip': "Leave a gap — they shouldn't meet at the peak.", 'draw': draw_tulip_s2},
        {'title': 'Fold Sides In', 'instruction': 'Fold the side corners inward slightly to shape the tulip.', 'tip': 'This gives the tulip its curved petal shape.', 'draw': draw_tulip_s3},
        {'title': 'Shape & Open', 'instruction': 'Gently open the tulip from the bottom and shape the petals. Insert a paper stem if desired.', 'tip': 'Roll a green square into a tube for a stem!', 'draw': draw_tulip_s4},
    ]},
]

CATEGORIES = ['All', 'Animals', 'Birds', 'Flowers', 'Objects']

FUN_FACTS = [
    "🇯🇵 Origami originated in Japan around the 6th century, brought by Buddhist monks who carried paper from China.",
    "🦢 The paper crane (orizuru) is the most iconic origami model and symbolizes peace, hope, and healing.",
    "📜 Ancient origami was used in religious ceremonies — folded paper offerings called 'oshi' were given at Shinto shrines.",
    "✂️ Traditional origami uses NO cuts or glue — only folding! This is called 'pureland' origami.",
    "🎀 The Japanese word 'origami' comes from 'oru' (to fold) and 'kami' (paper).",
    "💫 According to Japanese legend, folding 1,000 paper cranes (senbazuru) grants you a wish.",
    "🚀 NASA uses origami principles to design solar panels that fold compactly for space missions.",
    "📐 The mathematics of origami have led to breakthroughs in engineering, medicine, and space science.",
    "🔬 MIT offers courses on computational origami, combining art with advanced geometry.",
    "🏥 Origami is used in therapy to improve fine motor skills, concentration, and reduce stress.",
    "📏 The 'origami axiom' was proven mathematically in 1989 — it's as powerful as a compass and straightedge!",
    "🏗️ Architects use origami techniques to design foldable structures and emergency shelters.",
    "📱 The foldable screens in modern smartphones are based on origami mathematics.",
]


# ============================================================
# DATA MANAGER
# ============================================================
class DataManager:
    SAVE_PATH = Path.home() / '.origami_master' / 'progress.json'

    def __init__(self):
        self.progress = {}
        self.quiz_scores = []
        self.favorites = []
        self.notes = {}
        self.streak_dates = []
        self.speed_runs = []
        self.theme_dark = True
        self.load()

    def load(self):
        try:
            if self.SAVE_PATH.exists():
                data = json.loads(self.SAVE_PATH.read_text())
                self.progress = data.get('progress', {})
                self.quiz_scores = data.get('quiz_scores', [])
                self.favorites = data.get('favorites', [])
                self.notes = data.get('notes', {})
                self.streak_dates = data.get('streak_dates', [])
                self.speed_runs = data.get('speed_runs', [])
                self.theme_dark = data.get('theme_dark', True)
        except Exception:
            pass

    def save(self):
        try:
            self.SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'progress': self.progress, 'quiz_scores': self.quiz_scores,
                'favorites': self.favorites, 'notes': self.notes,
                'streak_dates': self.streak_dates, 'speed_runs': self.speed_runs,
                'theme_dark': self.theme_dark,
            }
            self.SAVE_PATH.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def get_progress(self, origami_id):
        return self.progress.get(origami_id, 0)

    def set_progress(self, origami_id, step):
        self.progress[origami_id] = max(self.progress.get(origami_id, 0), step)
        self.record_today()
        self.save()

    def is_completed(self, origami_id):
        orig = next((o for o in ORIGAMI_DATA if o['id'] == origami_id), None)
        if orig:
            return self.get_progress(origami_id) >= len(orig['steps'])
        return False

    def toggle_favorite(self, origami_id):
        if origami_id in self.favorites:
            self.favorites.remove(origami_id)
        else:
            self.favorites.append(origami_id)
        self.save()

    def is_favorite(self, origami_id):
        return origami_id in self.favorites

    def get_note(self, origami_id, step_idx):
        return self.notes.get(f"{origami_id}_{step_idx}", "")

    def set_note(self, origami_id, step_idx, text):
        self.notes[f"{origami_id}_{step_idx}"] = text
        self.save()

    def record_today(self):
        today = date.today().isoformat()
        if today not in self.streak_dates:
            self.streak_dates.append(today)
            self.save()

    def get_streak(self):
        if not self.streak_dates:
            return 0
        streak = 0
        today = date.today()
        sorted_dates = sorted([date.fromisoformat(d) for d in self.streak_dates], reverse=True)
        check = today
        for d in sorted_dates:
            if d == check:
                streak += 1
                check = date.fromordinal(check.toordinal() - 1)
            elif d < check:
                break
        return streak

    def add_speed_run(self, origami_id, seconds):
        self.speed_runs.append({'id': origami_id, 'time': seconds, 'date': date.today().isoformat()})
        self.save()

    def get_stats(self):
        total = len(ORIGAMI_DATA)
        completed = sum(1 for o in ORIGAMI_DATA if self.is_completed(o['id']))
        in_progress = sum(1 for o in ORIGAMI_DATA if 0 < self.get_progress(o['id']) < len(o['steps']))
        return {'total': total, 'completed': completed, 'in_progress': in_progress,
                'not_started': total - completed - in_progress}


# ============================================================
# CUSTOM WIDGETS
# ============================================================
class StepDiagram(QWidget):
    def __init__(self, draw_func=None, parent=None):
        super().__init__(parent)
        self.draw_func = draw_func
        self.old_draw_func = None
        self.anim_progress = 1.0
        self.anim_direction = 1 # 1 for next, -1 for prev
        self.offset = 0.0
        self.setMinimumSize(350, 300)
        
        # Animation Timer for Marching Ants
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._tick_anim)
        self.anim_timer.start(50) # 20 FPS for smooth dash movement

    def _tick_anim(self):
        self.offset -= 1.0 # Move dashes
        self.update()

    def set_draw_func(self, func, direction=1, animate=True):
        self.anim_direction = direction
        if animate and self.draw_func and self.draw_func != func:
            self.old_draw_func = self.draw_func
            self.draw_func = func
            self._animate_in()
        else:
            self.old_draw_func = None
            self.draw_func = func
            self.anim_progress = 1.0
            self.update()

    def _animate_in(self):
        self.anim_progress = 0.0
        self.anim = QPropertyAnimation(self, b"animProgress")
        self.anim.setDuration(600)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

    def get_animProgress(self): return self.anim_progress
    def set_animProgress(self, val):
        self.anim_progress = val
        self.update()
    animProgress = Property(float, get_animProgress, set_animProgress)

    def paintEvent(self, event):
        global _ANIM_OFFSET
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background & Grid
        painter.fillRect(self.rect(), QColor(C['bg_card']))
        painter.setPen(QPen(QColor(255, 255, 255, 6 if C['bg'] < '#4' else 40), 1))
        for x in range(0, self.width(), 30): painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 30): painter.drawLine(0, y, self.width(), y)

        # Set the global offset for marching ants
        _ANIM_OFFSET = self.offset

        # --- 3D Page Fold Effect ---
        if self.anim_progress < 1.0 and self.old_draw_func:
            # 1. Draw the NEW step flat underneath
            if self.draw_func:
                try: self.draw_func(painter, self.width(), self.height())
                except: pass

            # 2. Calculate the fold angle
            # scaleX goes from 1.0 to -1.0
            # At 0.0 -> 1.0 (old page fully visible)
            # At 0.5 -> 0.0 (old page edge-on)
            # At 1.0 -> -1.0 (old page folded behind)
            scale_x = math.cos(self.anim_progress * math.pi)

            if scale_x > 0.01: # Only draw the old page if its front face is visible
                painter.save()
                
                # Center fold transform
                painter.translate(self.width() / 2, 0)
                painter.scale(scale_x, 1.0)
                painter.translate(-self.width() / 2, 0)
                
                # Draw old step
                try: self.old_draw_func(painter, self.width(), self.height())
                except: pass

                # Add shadow to simulate 3D depth/lifting
                shadow_opacity = int((1.0 - scale_x) * 120)
                shadow_gradient = QLinearGradient(0, 0, self.width(), 0)
                shadow_gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
                shadow_gradient.setColorAt(0.45, QColor(0, 0, 0, shadow_opacity // 2))
                shadow_gradient.setColorAt(0.50, QColor(0, 0, 0, shadow_opacity))
                shadow_gradient.setColorAt(0.55, QColor(0, 0, 0, shadow_opacity // 2))
                shadow_gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.fillRect(self.rect(), QBrush(shadow_gradient))

                painter.restore()
        else:
            # Normal drawing (no animation)
            if self.draw_func:
                try: self.draw_func(painter, self.width(), self.height())
                except: pass

        # Border
        painter.setPen(QPen(QColor(C['border']), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
        painter.end()


class OrigamiCard(QFrame):
    clicked = Signal(str)
    favorite_toggled = Signal(str)

    def __init__(self, origami, data_manager, parent=None):
        super().__init__(parent)
        self.origami = origami
        self.data_manager = data_manager
        self.setFixedSize(240, 300)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty('hovered', False)
        self._build_ui()

    def _build_ui(self):
        if self.layout():
            old = self.layout()
            while old.count():
                item = old.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            QWidget().setLayout(old)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        top = QHBoxLayout()
        emoji_lbl = QLabel(self.origami['emoji'])
        emoji_lbl.setFont(QFont('Segoe UI Emoji', 28))
        emoji_lbl.setAlignment(Qt.AlignCenter)
        top.addWidget(emoji_lbl)
        top.addStretch()

        diff_color = C['easy'] if self.origami['difficulty'] == 'Easy' else C['medium'] if self.origami['difficulty'] == 'Medium' else C['hard']
        diff_lbl = QLabel(self.origami['difficulty'])
        diff_lbl.setFont(QFont('Segoe UI', 9, QFont.Bold))
        diff_lbl.setStyleSheet(f"color: {diff_color}; background: {diff_color}22; padding: 3px 8px; border-radius: 10px;")
        top.addWidget(diff_lbl)

        fav_btn = QPushButton('♥' if self.data_manager.is_favorite(self.origami['id']) else '♡')
        fav_btn.setFixedSize(28, 28)
        fav_btn.setFont(QFont('Segoe UI', 14))
        is_fav = self.data_manager.is_favorite(self.origami['id'])
        fav_btn.setStyleSheet(f"QPushButton {{ color: {'#FF6584' if is_fav else C['text_muted']}; background: transparent; border: none; }} QPushButton:hover {{ color: #FF6584; }}")
        fav_btn.clicked.connect(lambda: self.favorite_toggled.emit(self.origami['id']))
        top.addWidget(fav_btn)
        layout.addLayout(top)

        name = QLabel(self.origami['name'])
        name.setFont(QFont('Segoe UI', 13, QFont.Bold))
        name.setAlignment(Qt.AlignCenter)
        name.setWordWrap(True)
        layout.addWidget(name)

        meta = QLabel(f"{self.origami['category']} • {self.origami['time']} • {self.origami['paper']}")
        meta.setFont(QFont('Segoe UI', 8))
        meta.setStyleSheet(f"color: {C['text_sec']};")
        meta.setAlignment(Qt.AlignCenter)
        meta.setWordWrap(True)
        layout.addWidget(meta)

        progress = self.data_manager.get_progress(self.origami['id'])
        total_steps = len(self.origami['steps'])
        pct = int(progress / total_steps * 100) if total_steps > 0 else 0

        bar_frame = QFrame()
        bar_frame.setFixedHeight(6)
        bar_frame.setStyleSheet(f"background: {C['bg_hover']}; border-radius: 3px;")
        bar_layout = QHBoxLayout(bar_frame)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        fill = QFrame()
        fill.setFixedHeight(6)
        fill.setStyleSheet(f"background: {C['primary']}; border-radius: 3px;")
        bar_layout.addWidget(fill, max(pct, 1) if pct > 0 else 1)
        spacer = QFrame()
        spacer.setFixedHeight(6)
        bar_layout.addWidget(spacer, max(100 - pct, 1) if pct < 100 else 1)
        layout.addWidget(bar_frame)

        ptext = QLabel(f"{'✅ Complete!' if pct == 100 else f'Step {progress}/{total_steps}' if progress > 0 else 'Not started'}")
        ptext.setFont(QFont('Segoe UI', 8))
        ptext.setStyleSheet(f"color: {C['accent'] if pct == 100 else C['text_sec']};")
        ptext.setAlignment(Qt.AlignCenter)
        layout.addWidget(ptext)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg = QColor(C['bg_card']) if not self.property('hovered') else QColor(C['bg_surface'])
        painter.setBrush(bg)
        painter.setPen(QPen(QColor(C['border']), 1))
        painter.drawRoundedRect(self.rect(), 16, 16)
        painter.end()

    def enterEvent(self, event):
        self.setProperty('hovered', True)
        self.style().unpolish(self); self.style().polish(self)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty('hovered', False)
        self.style().unpolish(self); self.style().polish(self)
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit(self.origami['id'])
        super().mousePressEvent(event)

    def refresh(self):
        self._build_ui()
        self.update()


# ============================================================
# PAGES
# ============================================================
class DashboardPage(QWidget):
    start_lesson = Signal(str)

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 20)

    def refresh(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())
        self._build()

    def _build(self):
        layout = self.main_layout
        layout.setSpacing(20)

        banner = QFrame()
        banner.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {C['primary']}, stop:1 {C['secondary']});
                border-radius: 20px; padding: 30px;
            }}
        """)
        bl = QVBoxLayout(banner)
        bl.setSpacing(6)
        streak = self.data_manager.get_streak()
        streak_text = f" 🔥 {streak}-day streak!" if streak > 0 else ""
        title = QLabel(f"🪄 Welcome to Origami Master!{streak_text}")
        title.setFont(QFont('Segoe UI', 22, QFont.Bold))
        title.setStyleSheet("color: white;")
        title.setWordWrap(True)
        bl.addWidget(title)
        subtitle = QLabel("Learn the ancient art of paper folding, one crease at a time.")
        subtitle.setFont(QFont('Segoe UI', 11))
        subtitle.setStyleSheet("color: rgba(255,255,255,0.8);")
        bl.addWidget(subtitle)
        layout.addWidget(banner)

        stats = self.data_manager.get_stats()
        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)
        stat_items = [
            ("📚 Total", str(stats['total']), C['primary']),
            ("✅ Done", str(stats['completed']), C['accent']),
            ("🔄 Active", str(stats['in_progress']), C['medium']),
            ("🔥 Streak", str(self.data_manager.get_streak()), C['secondary']),
        ]
        for label, value, color in stat_items:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {C['bg_card']}; border: 1px solid {C['border']}; border-radius: 16px; }}")
            sl = QVBoxLayout(card)
            sl.setContentsMargins(15, 15, 15, 15)
            sl.setSpacing(4)
            v = QLabel(value)
            v.setFont(QFont('Segoe UI', 24, QFont.Bold))
            v.setStyleSheet(f"color: {color};")
            v.setAlignment(Qt.AlignCenter)
            sl.addWidget(v)
            l = QLabel(label)
            l.setFont(QFont('Segoe UI', 10))
            l.setStyleSheet(f"color: {C['text_sec']};")
            l.setAlignment(Qt.AlignCenter)
            sl.addWidget(l)
            stats_row.addWidget(card)
        layout.addLayout(stats_row)

        fact = random.choice(FUN_FACTS)
        fact_frame = QFrame()
        fact_frame.setStyleSheet(f"QFrame {{ background: {C['bg_surface']}; border: 1px solid {C['border']}; border-radius: 12px; }}")
        ff_layout = QHBoxLayout(fact_frame)
        ff_layout.setContentsMargins(15, 10, 15, 10)
        fi = QLabel("💡")
        fi.setFont(QFont('Segoe UI Emoji', 18))
        ff_layout.addWidget(fi)
        ft = QLabel(fact)
        ft.setFont(QFont('Segoe UI', 10))
        ft.setStyleSheet(f"color: {C['text_sec']};")
        ft.setWordWrap(True)
        ff_layout.addWidget(ft, 1)
        layout.addWidget(fact_frame)

        cl = QLabel("📖 Continue Learning")
        cl.setFont(QFont('Segoe UI', 16, QFont.Bold))
        layout.addWidget(cl)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; } QScrollBar { width: 6px; }")
        scroll_widget = QWidget()
        s_layout = QHBoxLayout(scroll_widget)
        s_layout.setSpacing(15)

        has_continue = False
        for orig in ORIGAMI_DATA:
            prog = self.data_manager.get_progress(orig['id'])
            if 0 < prog < len(orig['steps']):
                has_continue = True
                card = QFrame()
                card.setStyleSheet(f"QFrame {{ background: {C['bg_card']}; border: 1px solid {C['primary']}33; border-radius: 16px; padding: 12px; }} QFrame:hover {{ border-color: {C['primary']}; }}")
                card.setCursor(Qt.PointingHandCursor)
                ccl = QVBoxLayout(card)
                ccl.setSpacing(4)
                e = QLabel(orig['emoji'])
                e.setFont(QFont('Segoe UI Emoji', 28))
                e.setAlignment(Qt.AlignCenter)
                ccl.addWidget(e)
                n = QLabel(orig['name'])
                n.setFont(QFont('Segoe UI', 10, QFont.Bold))
                n.setAlignment(Qt.AlignCenter)
                ccl.addWidget(n)
                p = QLabel(f"Step {prog}/{len(orig['steps'])}")
                p.setFont(QFont('Segoe UI', 8))
                p.setStyleSheet(f"color: {C['text_sec']};")
                p.setAlignment(Qt.AlignCenter)
                ccl.addWidget(p)
                btn = QPushButton("Continue →")
                btn.setStyleSheet(f"QPushButton {{ background: {C['primary']}; color: white; border: none; border-radius: 8px; padding: 6px 12px; font-weight: bold; font-size: 10px; }} QPushButton:hover {{ background: {C['primary_light']}; }}")
                oid = orig['id']
                btn.clicked.connect(lambda checked, i=oid: self.start_lesson.emit(i))
                card.mousePressEvent = lambda e, i=oid: self.start_lesson.emit(i)
                ccl.addWidget(btn)
                s_layout.addWidget(card)

        if not has_continue:
            none_lbl = QLabel("No projects in progress — start one from the Catalog!")
            none_lbl.setFont(QFont('Segoe UI', 11))
            none_lbl.setStyleSheet(f"color: {C['text_sec']};")
            s_layout.addWidget(none_lbl)

        s_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setFixedHeight(180)
        layout.addWidget(scroll_area)
        layout.addStretch()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())


class CatalogPage(QWidget):
    start_lesson = Signal(str)

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_category = 'All'
        self.current_difficulty = 'All'
        self.search_text = ''
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 20)

    def refresh(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())
        self._build()

    def _build(self):
        layout = self.main_layout
        layout.setSpacing(15)

        header = QHBoxLayout()
        title = QLabel("📚 Origami Catalog")
        title.setFont(QFont('Segoe UI', 22, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        count = len(self._get_filtered())
        cl = QLabel(f"{count} project{'s' if count != 1 else ''}")
        cl.setFont(QFont('Segoe UI', 11))
        cl.setStyleSheet(f"color: {C['text_sec']};")
        header.addWidget(cl)
        layout.addLayout(header)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        search = QLineEdit()
        search.setPlaceholderText("🔍 Search origami...")
        search.setFixedWidth(220)
        search.setFixedHeight(36)
        search.setStyleSheet(f"""
            QLineEdit {{
                background: {C['bg_surface']}; border: 1px solid {C['border']};
                border-radius: 12px; padding: 8px 14px; color: {C['text']}; font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {C['primary']}; }}
        """)
        search.textChanged.connect(self._on_search)
        filter_row.addWidget(search)

        for cat in CATEGORIES:
            btn = QPushButton(cat)
            btn.setFixedHeight(32)
            is_active = self.current_category == cat
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {C['primary'] if is_active else C['bg_surface']};
                    color: {'white' if is_active else C['text_sec']};
                    border: 1px solid {C['primary'] if is_active else C['border']};
                    border-radius: 10px; padding: 5px 14px;
                    font-weight: {'bold' if is_active else 'normal'}; font-size: 11px;
                }}
                QPushButton:hover {{ background: {C['primary_dark'] if is_active else C['bg_hover']}; }}
            """)
            btn.clicked.connect(lambda checked, c=cat: self._set_category(c))
            filter_row.addWidget(btn)

        filter_row.addStretch()

        for diff in ['All', 'Easy', 'Medium', 'Hard']:
            btn = QPushButton(diff)
            btn.setFixedHeight(32)
            is_active = self.current_difficulty == diff
            dc = C['easy'] if diff == 'Easy' else C['medium'] if diff == 'Medium' else C['hard'] if diff == 'Hard' else C['primary']
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {dc if is_active else C['bg_surface']};
                    color: {'white' if is_active else C['text_sec']};
                    border: 1px solid {dc if is_active else C['border']};
                    border-radius: 10px; padding: 5px 12px;
                    font-weight: {'bold' if is_active else 'normal'}; font-size: 11px;
                }}
                QPushButton:hover {{ background: {C['bg_hover'] if not is_active else dc}; }}
            """)
            btn.clicked.connect(lambda checked, d=diff: self._set_difficulty(d))
            filter_row.addWidget(btn)

        layout.addLayout(filter_row)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(15)

        filtered = self._get_filtered()
        if not filtered:
            empty = QLabel("No origami found matching your filters.")
            empty.setFont(QFont('Segoe UI', 14))
            empty.setStyleSheet(f"color: {C['text_sec']};")
            empty.setAlignment(Qt.AlignCenter)
            grid.addWidget(empty, 0, 0)
        else:
            for i, orig in enumerate(filtered):
                card = OrigamiCard(orig, self.data_manager)
                card.clicked.connect(self.start_lesson.emit)
                card.favorite_toggled.connect(self._on_fav_toggle)
                grid.addWidget(card, i // 3, i % 3, Qt.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())

    def _get_filtered(self):
        result = ORIGAMI_DATA
        if self.current_category != 'All':
            result = [o for o in result if o['category'] == self.current_category]
        if self.current_difficulty != 'All':
            result = [o for o in result if o['difficulty'] == self.current_difficulty]
        if self.search_text:
            result = [o for o in result if self.search_text.lower() in o['name'].lower() or self.search_text.lower() in o['description'].lower()]
        return result

    def _set_category(self, cat):
        self.current_category = cat
        self.refresh()

    def _set_difficulty(self, diff):
        self.current_difficulty = diff
        self.refresh()

    def _on_search(self, text):
        self.search_text = text
        self.refresh()

    def _on_fav_toggle(self, origami_id):
        self.data_manager.toggle_favorite(origami_id)
        self.refresh()


class LessonPage(QWidget):
    back_requested = Signal()

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_origami = None
        self.current_step = 0
        self.timer_seconds = 0
        self.timer_running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick_timer)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 15, 30, 15)

    def load_origami(self, origami_id):
        self.current_origami = next((o for o in ORIGAMI_DATA if o['id'] == origami_id), None)
        if not self.current_origami: return

        self.current_step = min(self.data_manager.get_progress(origami_id), len(self.current_origami['steps']) - 1)
        self.timer_seconds = 0
        self.timer_running = True
        self.timer.start(1000)
        self._build()
        self._update_step(animate=False)

    def _tick_timer(self):
        if self.timer_running:
            self.timer_seconds += 1
            if hasattr(self, 'timer_label'):
                m, s = divmod(self.timer_seconds, 60)
                self.timer_label.setText(f"⏱ {m:02d}:{s:02d}")

    def _build(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())

        layout = self.main_layout
        layout.setSpacing(12)

        header = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(f"QPushButton {{ background: {C['bg_surface']}; color: {C['text']}; border: 1px solid {C['border']}; border-radius: 10px; padding: 7px 16px; font-weight: bold; font-size: 12px; }} QPushButton:hover {{ background: {C['bg_hover']}; }}")
        back_btn.clicked.connect(self._go_back)
        header.addWidget(back_btn)

        self.title_label = QLabel("")
        self.title_label.setFont(QFont('Segoe UI', 18, QFont.Bold))
        header.addWidget(self.title_label)
        header.addStretch()

        self.timer_label = QLabel("⏱ 00:00")
        self.timer_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.timer_label.setStyleSheet(f"color: {C['primary']}; background: {C['bg_surface']}; padding: 5px 12px; border-radius: 8px;")
        header.addWidget(self.timer_label)

        pause_btn = QPushButton("⏸")
        pause_btn.setFixedSize(32, 32)
        pause_btn.setStyleSheet(f"QPushButton {{ background: {C['bg_surface']}; color: {C['text']}; border: 1px solid {C['border']}; border-radius: 8px; font-size: 14px; }} QPushButton:hover {{ background: {C['bg_hover']}; }}")
        pause_btn.clicked.connect(self._toggle_timer)
        header.addWidget(pause_btn)

        self.diff_label = QLabel("")
        self.diff_label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        header.addWidget(self.diff_label)

        self.paper_label = QLabel("")
        self.paper_label.setFont(QFont('Segoe UI', 9))
        self.paper_label.setStyleSheet(f"color: {C['text_sec']}; background: {C['bg_surface']}; padding: 4px 10px; border-radius: 8px;")
        header.addWidget(self.paper_label)

        layout.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(20)

        self.diagram = StepDiagram()
        self.diagram.setMinimumSize(380, 320)
        content.addWidget(self.diagram, 1)

        instr_frame = QFrame()
        instr_frame.setStyleSheet(f"QFrame {{ background: {C['bg_card']}; border: 1px solid {C['border']}; border-radius: 20px; }}")
        il = QVBoxLayout(instr_frame)
        il.setContentsMargins(20, 20, 20, 20)
        il.setSpacing(10)

        self.step_title = QLabel("")
        self.step_title.setFont(QFont('Segoe UI', 16, QFont.Bold))
        self.step_title.setWordWrap(True)
        il.addWidget(self.step_title)

        self.step_indicator = QLabel("")
        self.step_indicator.setFont(QFont('Segoe UI', 10))
        self.step_indicator.setStyleSheet(f"color: {C['primary']};")
        il.addWidget(self.step_indicator)

        self.dots_widget = QWidget()
        self.dots_layout = QHBoxLayout(self.dots_widget)
        self.dots_layout.setSpacing(5)
        self.dots_layout.setContentsMargins(0, 0, 0, 0)
        il.addWidget(self.dots_widget)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {C['border']};")
        il.addWidget(sep)

        instr_icon = QLabel("📝 Instructions")
        instr_icon.setFont(QFont('Segoe UI', 11, QFont.Bold))
        instr_icon.setStyleSheet(f"color: {C['primary']};")
        il.addWidget(instr_icon)

        self.instr_text = QLabel("")
        self.instr_text.setFont(QFont('Segoe UI', 11))
        self.instr_text.setStyleSheet(f"color: {C['text_sec']};")
        self.instr_text.setWordWrap(True)
        self.instr_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        il.addWidget(self.instr_text)

        tip_frame = QFrame()
        tip_frame.setStyleSheet(f"QFrame {{ background: {C['primary']}15; border: 1px solid {C['primary']}33; border-radius: 12px; }}")
        tl = QVBoxLayout(tip_frame)
        tl.setSpacing(3)
        tip_title = QLabel("💡 Tip")
        tip_title.setFont(QFont('Segoe UI', 10, QFont.Bold))
        tip_title.setStyleSheet(f"color: {C['primary']};")
        tl.addWidget(tip_title)
        self.tip_text = QLabel("")
        self.tip_text.setFont(QFont('Segoe UI', 9))
        self.tip_text.setStyleSheet(f"color: {C['text_sec']};")
        self.tip_text.setWordWrap(True)
        tl.addWidget(self.tip_text)
        il.addWidget(tip_frame)

        notes_header = QHBoxLayout()
        notes_label = QLabel("📝 My Notes")
        notes_label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        notes_label.setStyleSheet(f"color: {C['secondary']};")
        notes_header.addWidget(notes_label)
        notes_header.addStretch()
        il.addLayout(notes_header)

        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(60)
        self.notes_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {C['bg_surface']}; color: {C['text']};
                border: 1px solid {C['border']}; border-radius: 8px;
                padding: 6px; font-size: 10px;
            }}
            QTextEdit:focus {{ border-color: {C['primary']}; }}
        """)
        self.notes_edit.textChanged.connect(self._save_note)
        self.notes_edit.setPlaceholderText("Add your notes for this step...")
        il.addWidget(self.notes_edit)

        legend_frame = QFrame()
        legend_frame.setStyleSheet(f"QFrame {{ background: {C['bg_surface']}; border-radius: 10px; }}")
        ll = QHBoxLayout(legend_frame)
        ll.setContentsMargins(10, 6, 10, 6)
        ll.setSpacing(12)
        for txt, clr in [("— — Valley", C['fold_valley']), ("—·— Mountain", C['fold_mountain']), ("→ Direction", C['arrow'])]:
            item = QLabel(txt)
            item.setFont(QFont('Segoe UI', 8))
            item.setStyleSheet(f"color: {clr};")
            ll.addWidget(item)
        il.addWidget(legend_frame)

        content.addWidget(instr_frame, 1)
        layout.addLayout(content)

        nav = QHBoxLayout()
        nav.setSpacing(12)

        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.setFixedHeight(42)
        self.prev_btn.setStyleSheet(f"QPushButton {{ background: {C['bg_surface']}; color: {C['text']}; border: 1px solid {C['border']}; border-radius: 12px; padding: 8px 20px; font-weight: bold; font-size: 12px; }} QPushButton:hover {{ background: {C['bg_hover']}; }} QPushButton:disabled {{ color: {C['text_muted']}; }}")
        self.prev_btn.clicked.connect(self._prev_step)
        nav.addWidget(self.prev_btn)

        self.step_slider = QSlider(Qt.Horizontal)
        self.step_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ background: {C['bg_surface']}; height: 6px; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: {C['primary']}; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }}
        """)
        self.step_slider.valueChanged.connect(self._slider_changed)
        nav.addWidget(self.step_slider, 1)

        self.next_btn = QPushButton("Next →")
        self.next_btn.setFixedHeight(42)
        self.next_btn.setStyleSheet(f"QPushButton {{ background: {C['primary']}; color: white; border: none; border-radius: 12px; padding: 8px 20px; font-weight: bold; font-size: 12px; }} QPushButton:hover {{ background: {C['primary_light']}; }}")
        self.next_btn.clicked.connect(self._next_step)
        nav.addWidget(self.next_btn)

        layout.addLayout(nav)

    def _update_step(self, animate=True, direction=1):
        if not self.current_origami: return

        steps = self.current_origami['steps']
        step = steps[self.current_step]

        self.title_label.setText(f"{self.current_origami['emoji']} {self.current_origami['name']}")
        diff = self.current_origami['difficulty']
        dc = C['easy'] if diff == 'Easy' else C['medium'] if diff == 'Medium' else C['hard']
        self.diff_label.setText(diff)
        self.diff_label.setStyleSheet(f"color: {dc}; background: {dc}22; padding: 3px 10px; border-radius: 8px; font-weight: bold;")
        self.paper_label.setText(f"📄 {self.current_origami['paper']}")

        self.diagram.set_draw_func(step['draw'], direction=direction, animate=animate)

        self.step_title.setText(f"Step {self.current_step + 1}: {step['title']}")
        self.step_indicator.setText(f"Step {self.current_step + 1} of {len(steps)}")
        self.instr_text.setText(step['instruction'])
        self.tip_text.setText(step['tip'])

        self.notes_edit.blockSignals(True)
        self.notes_edit.setText(self.data_manager.get_note(self.current_origami['id'], self.current_step))
        self.notes_edit.blockSignals(False)

        while self.dots_layout.count():
            item = self.dots_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for i in range(len(steps)):
            dot = QFrame()
            dot.setFixedSize(22, 7)
            if i < self.current_step: dot.setStyleSheet(f"background: {C['accent']}; border-radius: 3px;")
            elif i == self.current_step: dot.setStyleSheet(f"background: {C['primary']}; border-radius: 3px;")
            else: dot.setStyleSheet(f"background: {C['bg_hover']}; border-radius: 3px;")
            self.dots_layout.addWidget(dot)
        self.dots_layout.addStretch()

        self.prev_btn.setEnabled(self.current_step > 0)
        if self.current_step >= len(steps) - 1:
            self.next_btn.setText("✅ Complete!")
            self.next_btn.setStyleSheet(f"QPushButton {{ background: {C['accent']}; color: white; border: none; border-radius: 12px; padding: 8px 20px; font-weight: bold; font-size: 12px; }} QPushButton:hover {{ background: #3BD471; }}")
        else:
            self.next_btn.setText("Next →")
            self.next_btn.setStyleSheet(f"QPushButton {{ background: {C['primary']}; color: white; border: none; border-radius: 12px; padding: 8px 20px; font-weight: bold; font-size: 12px; }} QPushButton:hover {{ background: {C['primary_light']}; }}")

        self.step_slider.blockSignals(True)
        self.step_slider.setRange(0, len(steps) - 1)
        self.step_slider.setValue(self.current_step)
        self.step_slider.blockSignals(False)

        self.data_manager.set_progress(self.current_origami['id'], self.current_step + 1)

    def _save_note(self):
        if self.current_origami:
            self.data_manager.set_note(self.current_origami['id'], self.current_step, self.notes_edit.toPlainText())

    def _next_step(self):
        if not self.current_origami: return
        if self.current_step < len(self.current_origami['steps']) - 1:
            self.current_step += 1
            self._update_step(animate=True, direction=1)

    def _prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self._update_step(animate=True, direction=-1)

    def _slider_changed(self, value):
        if value != self.current_step:
            direction = 1 if value > self.current_step else -1
            self.current_step = value
            self._update_step(animate=True, direction=direction)

    def _toggle_timer(self):
        self.timer_running = not self.timer_running
        if self.timer_running: self.timer.start(1000)
        else: self.timer.stop()

    def _go_back(self):
        self.timer.stop()
        self.timer_running = False
        if self.current_origami and self.timer_seconds > 0:
            self.data_manager.add_speed_run(self.current_origami['id'], self.timer_seconds)
        self.back_requested.emit()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())


class QuizPage(QWidget):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.quiz_data = []
        self.current_q = 0
        self.score = 0
        self.answered = False
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 20)

    def refresh(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())
        self._show_start()

    def _show_start(self):
        layout = self.main_layout
        title = QLabel("🧪 Origami Quiz")
        title.setFont(QFont('Segoe UI', 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Test your origami knowledge!\nIdentify the correct instruction for each step shown.")
        desc.setFont(QFont('Segoe UI', 12))
        desc.setStyleSheet(f"color: {C['text_sec']};")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        if self.data_manager.quiz_scores:
            best = max(self.data_manager.quiz_scores)
            avg = sum(self.data_manager.quiz_scores) / len(self.data_manager.quiz_scores)
            sl = QLabel(f"🏆 Best: {best}%  •  📊 Average: {avg:.0f}%  •  📝 Quizzes taken: {len(self.data_manager.quiz_scores)}")
            sl.setFont(QFont('Segoe UI', 10))
            sl.setStyleSheet(f"color: {C['accent']};")
            sl.setAlignment(Qt.AlignCenter)
            layout.addWidget(sl)

        layout.addSpacing(20)
        start_btn = QPushButton("🎯 Start Quiz")
        start_btn.setFixedSize(200, 50)
        start_btn.setStyleSheet(f"QPushButton {{ background: {C['primary']}; color: white; border: none; border-radius: 14px; font-weight: bold; font-size: 15px; }} QPushButton:hover {{ background: {C['primary_light']}; }}")
        start_btn.clicked.connect(self._start_quiz)
        layout.addWidget(start_btn, alignment=Qt.AlignCenter)
        layout.addStretch()

    def _start_quiz(self):
        self.quiz_data = []
        self.current_q = 0
        self.score = 0
        for orig in ORIGAMI_DATA:
            for i, step in enumerate(orig['steps']):
                if i > 0:
                    all_instrs = list(set([s['instruction'][:55] for o in ORIGAMI_DATA for s in o['steps']]))
                    correct = step['instruction'][:55]
                    wrongs = [x for x in all_instrs if x != correct]
                    random.shuffle(wrongs)
                    options = [correct] + wrongs[:3]
                    random.shuffle(options)
                    self.quiz_data.append({
                        'question': f"In \"{orig['name']}\", what comes after this step?",
                        'draw_func': orig['steps'][i-1]['draw'],
                        'correct': correct,
                        'options': options,
                        'explanation': step['title'],
                    })
        random.shuffle(self.quiz_data)
        self.quiz_data = self.quiz_data[:10]
        self._show_question()

    def _show_question(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())
        self.answered = False
        layout = self.main_layout

        if self.current_q >= len(self.quiz_data):
            self._show_results()
            return

        q = self.quiz_data[self.current_q]
        prog = QLabel(f"Question {self.current_q + 1} / {len(self.quiz_data)}")
        prog.setFont(QFont('Segoe UI', 11))
        prog.setStyleSheet(f"color: {C['text_sec']};")
        prog.setAlignment(Qt.AlignCenter)
        layout.addWidget(prog)

        score_lbl = QLabel(f"Score: {self.score}/{self.current_q}")
        score_lbl.setFont(QFont('Segoe UI', 10))
        score_lbl.setStyleSheet(f"color: {C['primary']};")
        score_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(score_lbl)

        question = QLabel(q['question'])
        question.setFont(QFont('Segoe UI', 14, QFont.Bold))
        question.setAlignment(Qt.AlignCenter)
        question.setWordWrap(True)
        layout.addWidget(question)

        diagram = StepDiagram(q['draw_func'])
        diagram.setFixedSize(320, 260)
        layout.addWidget(diagram, alignment=Qt.AlignCenter)

        layout.addSpacing(8)
        for i, opt in enumerate(q['options']):
            btn = QPushButton(f"  {chr(65+i)}) {opt}")
            btn.setFixedHeight(46)
            btn.setStyleSheet(f"QPushButton {{ background: {C['bg_surface']}; color: {C['text']}; border: 1px solid {C['border']}; border-radius: 12px; padding: 8px 16px; font-size: 11px; text-align: left; }} QPushButton:hover {{ border-color: {C['primary']}; background: {C['bg_hover']}; }}")
            btn.clicked.connect(lambda checked, o=opt, b=btn: self._answer(o, b))
            layout.addWidget(btn)
        layout.addStretch()

    def _answer(self, selected, btn):
        if self.answered: return
        self.answered = True
        q = self.quiz_data[self.current_q]
        is_correct = selected == q['correct']

        if is_correct:
            self.score += 1
            btn.setStyleSheet(f"QPushButton {{ background: {C['accent']}33; color: {C['accent']}; border: 2px solid {C['accent']}; border-radius: 12px; padding: 8px 16px; font-size: 11px; text-align: left; }}")
        else:
            btn.setStyleSheet(f"QPushButton {{ background: {C['hard']}33; color: {C['hard']}; border: 2px solid {C['hard']}; border-radius: 12px; padding: 8px 16px; font-size: 11px; text-align: left; }}")

        expl = QLabel(f"{'✅ Correct!' if is_correct else '❌ Wrong.'} The next step is: {q['explanation']}")
        expl.setFont(QFont('Segoe UI', 10))
        expl.setStyleSheet(f"color: {C['accent'] if is_correct else C['hard']};")
        expl.setWordWrap(True)
        expl.setAlignment(Qt.AlignCenter)
        self.main_layout.insertWidget(self.main_layout.count() - 1, expl)

        next_btn = QPushButton("Next Question →" if self.current_q < len(self.quiz_data) - 1 else "See Results →")
        next_btn.setFixedHeight(42)
        next_btn.setStyleSheet(f"QPushButton {{ background: {C['primary']}; color: white; border: none; border-radius: 12px; padding: 8px 20px; font-weight: bold; font-size: 12px; }} QPushButton:hover {{ background: {C['primary_light']}; }}")
        next_btn.clicked.connect(self._next_question)
        self.main_layout.insertWidget(self.main_layout.count() - 1, next_btn, alignment=Qt.AlignCenter)

    def _next_question(self):
        self.current_q += 1
        self._show_question()

    def _show_results(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())
        layout = self.main_layout
        pct = int(self.score / len(self.quiz_data) * 100) if self.quiz_data else 0
        self.data_manager.quiz_scores.append(pct)
        self.data_manager.save()

        emoji = "🏆" if pct >= 80 else "👍" if pct >= 60 else "📚" if pct >= 40 else "💪"
        title = QLabel(f"{emoji} Quiz Complete!")
        title.setFont(QFont('Segoe UI', 26, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sc = C['accent'] if pct >= 80 else C['medium'] if pct >= 60 else C['hard']
        score_lbl = QLabel(f"{self.score} / {len(self.quiz_data)}")
        score_lbl.setFont(QFont('Segoe UI', 44, QFont.Bold))
        score_lbl.setStyleSheet(f"color: {sc};")
        score_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(score_lbl)

        pct_lbl = QLabel(f"{pct}% Correct")
        pct_lbl.setFont(QFont('Segoe UI', 14))
        pct_lbl.setStyleSheet(f"color: {C['text_sec']};")
        pct_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(pct_lbl)

        msg = "Outstanding! You're an origami master!" if pct >= 80 else "Great job! Keep practicing!" if pct >= 60 else "Good effort! Review the lessons." if pct >= 40 else "Keep learning! Practice makes perfect."
        msg_lbl = QLabel(msg)
        msg_lbl.setFont(QFont('Segoe UI', 11))
        msg_lbl.setStyleSheet(f"color: {C['text_sec']};")
        msg_lbl.setAlignment(Qt.AlignCenter)
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        layout.addSpacing(15)
        retry_btn = QPushButton("🔄 Try Again")
        retry_btn.setFixedSize(180, 44)
        retry_btn.setStyleSheet(f"QPushButton {{ background: {C['primary']}; color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 13px; }} QPushButton:hover {{ background: {C['primary_light']}; }}")
        retry_btn.clicked.connect(self.refresh)
        layout.addWidget(retry_btn, alignment=Qt.AlignCenter)
        layout.addStretch()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())


class ProgressPage(QWidget):
    start_lesson = Signal(str)

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 20)

    def refresh(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())
        self._build()

    def _build(self):
        layout = self.main_layout
        layout.setSpacing(12)

        title = QLabel("📊 My Progress")
        title.setFont(QFont('Segoe UI', 22, QFont.Bold))
        layout.addWidget(title)

        stats = self.data_manager.get_stats()
        sf = QFrame()
        sf.setStyleSheet(f"QFrame {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C['primary']}22, stop:1 {C['secondary']}22); border: 1px solid {C['border']}; border-radius: 16px; }}")
        sl = QHBoxLayout(sf)
        sl.setContentsMargins(20, 15, 20, 15)
        for label, value, color in [("Completed", str(stats['completed']), C['accent']),
                                     ("In Progress", str(stats['in_progress']), C['medium']),
                                     ("🔥 Streak", str(self.data_manager.get_streak()), C['secondary']),
                                     ("Total", str(stats['total']), C['primary'])]:
            col = QVBoxLayout()
            v = QLabel(value)
            v.setFont(QFont('Segoe UI', 22, QFont.Bold))
            v.setStyleSheet(f"color: {color};")
            v.setAlignment(Qt.AlignCenter)
            col.addWidget(v)
            l = QLabel(label)
            l.setFont(QFont('Segoe UI', 9))
            l.setStyleSheet(f"color: {C['text_sec']};")
            l.setAlignment(Qt.AlignCenter)
            col.addWidget(l)
            sl.addLayout(col)
        layout.addWidget(sf)

        for orig in ORIGAMI_DATA:
            progress = self.data_manager.get_progress(orig['id'])
            total = len(orig['steps'])
            pct = int(progress / total * 100) if total > 0 else 0
            is_completed = pct == 100

            card = QFrame()
            card.setCursor(Qt.PointingHandCursor)
            card.setStyleSheet(f"QFrame {{ background: {C['bg_card']}; border: 1px solid {C['border']}; border-radius: 14px; }} QFrame:hover {{ border-color: {C['primary']}; }}")
            cl = QHBoxLayout(card)
            cl.setContentsMargins(15, 12, 15, 12)
            cl.setSpacing(12)

            emoji = QLabel(orig['emoji'])
            emoji.setFont(QFont('Segoe UI Emoji', 22))
            cl.addWidget(emoji)

            info = QVBoxLayout()
            info.setSpacing(2)
            name = QLabel(orig['name'])
            name.setFont(QFont('Segoe UI', 11, QFont.Bold))
            info.addWidget(name)
            status = QLabel("✅ Completed!" if is_completed else f"Step {progress}/{total}" if progress > 0 else "Not started")
            status.setFont(QFont('Segoe UI', 9))
            status.setStyleSheet(f"color: {C['accent'] if is_completed else C['text_sec']};")
            info.addWidget(status)
            cl.addLayout(info, 1)

            bar_w = 150
            bar = QFrame()
            bar.setFixedSize(bar_w, 8)
            bar.setStyleSheet(f"background: {C['bg_hover']}; border-radius: 4px;")
            bar_l = QHBoxLayout(bar)
            bar_l.setContentsMargins(0, 0, 0, 0)
            bar_l.setSpacing(0)
            fill = QFrame()
            fill.setFixedHeight(8)
            fill.setStyleSheet(f"background: {C['accent'] if is_completed else C['primary']}; border-radius: 4px;")
            bar_l.addWidget(fill, max(pct, 1))
            spacer = QFrame()
            spacer.setFixedHeight(8)
            bar_l.addWidget(spacer, max(100 - pct, 1))
            cl.addWidget(bar)

            pct_lbl = QLabel(f"{pct}%")
            pct_lbl.setFont(QFont('Segoe UI', 10, QFont.Bold))
            pct_lbl.setStyleSheet(f"color: {C['accent'] if is_completed else C['primary']};")
            pct_lbl.setFixedWidth(40)
            cl.addWidget(pct_lbl)

            orig_id = orig['id']
            card.mousePressEvent = lambda e, oid=orig_id: self.start_lesson.emit(oid)
            layout.addWidget(card)

        layout.addSpacing(10)
        reset_btn = QPushButton("🗑️ Reset All Progress")
        reset_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {C['hard']}; border: 1px solid {C['hard']}44; border-radius: 10px; padding: 8px 18px; font-size: 11px; }} QPushButton:hover {{ background: {C['hard']}22; }}")
        reset_btn.clicked.connect(self._reset_progress)
        layout.addWidget(reset_btn, alignment=Qt.AlignRight)
        layout.addStretch()

    def _reset_progress(self):
        reply = QMessageBox.question(self, "Reset Progress", "Are you sure you want to reset all progress?\nThis cannot be undone.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.data_manager.progress = {}
            self.data_manager.quiz_scores = []
            self.data_manager.favorites = []
            self.data_manager.notes = {}
            self.data_manager.streak_dates = []
            self.data_manager.speed_runs = []
            self.data_manager.save()
            self.refresh()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())


# ============================================================
# MAIN WINDOW
# ============================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Origami Master - Learn Paper Folding")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 800)

        self.data_manager = DataManager()
        set_theme(self.data_manager.theme_dark)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(70)
        sidebar.setStyleSheet(f"QFrame {{ background: {C['bg_card']}; border-right: 1px solid {C['border']}; }}")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(5, 15, 5, 15)
        side_layout.setSpacing(8)

        logo = QLabel("🦢")
        logo.setFont(QFont('Segoe UI Emoji', 24))
        logo.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(logo)
        side_layout.addSpacing(5)

        self.nav_buttons = []
        nav_items = [("🏠", "Home", 0), ("📚", "Catalog", 1), ("📊", "Progress", 2), ("🧪", "Quiz", 3)]
        for icon, label, idx in nav_items:
            btn = QPushButton(icon)
            btn.setFixedSize(56, 56)
            btn.setToolTip(label)
            btn.setProperty('nav_idx', idx)
            btn.setStyleSheet(self._nav_btn_style(idx == 0))
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            side_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        side_layout.addStretch()

        # Theme Toggle Button
        self.theme_btn = QPushButton("🌙" if self.data_manager.theme_dark else "☀️")
        self.theme_btn.setFixedSize(56, 56)
        self.theme_btn.setToolTip("Toggle Theme")
        self.theme_btn.setStyleSheet(self._nav_btn_style(False))
        self.theme_btn.clicked.connect(self._toggle_theme)
        side_layout.addWidget(self.theme_btn)

        # Stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {C['bg']};")

        self.dashboard = DashboardPage(self.data_manager)
        self.catalog = CatalogPage(self.data_manager)
        self.lesson = LessonPage(self.data_manager)
        self.progress_page = ProgressPage(self.data_manager)
        self.quiz = QuizPage(self.data_manager)

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.catalog)
        self.stack.addWidget(self.progress_page)
        self.stack.addWidget(self.quiz)

        self.dashboard.start_lesson.connect(self._open_lesson)
        self.catalog.start_lesson.connect(self._open_lesson)
        self.progress_page.start_lesson.connect(self._open_lesson)
        self.lesson.back_requested.connect(self._back_from_lesson)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack, 1)

        self._switch_page(0)
        apply_stylesheet(self)

    def _nav_btn_style(self, active):
        if active:
            return f"QPushButton {{ background: {C['primary']}22; color: {C['primary']}; border: none; border-radius: 14px; font-size: 22px; }}"
        return f"QPushButton {{ background: transparent; color: {C['text_sec']}; border: none; border-radius: 14px; font-size: 22px; }} QPushButton:hover {{ background: {C['bg_hover']}; color: {C['text']}; }}"

    def _switch_page(self, idx):
        if idx == 0: self.dashboard.refresh()
        elif idx == 1: self.catalog.refresh()
        elif idx == 2: self.progress_page.refresh()
        self.stack.setCurrentIndex(idx)

        for i, btn in enumerate(self.nav_buttons):
            btn.setStyleSheet(self._nav_btn_style(i == idx))

    def _open_lesson(self, origami_id):
        if self.stack.indexOf(self.lesson) == -1:
            self.stack.addWidget(self.lesson)
        self.lesson.load_origami(origami_id)
        self.stack.setCurrentWidget(self.lesson)
        for btn in self.nav_buttons:
            btn.setStyleSheet(self._nav_btn_style(False))

    def _back_from_lesson(self):
        self.stack.setCurrentIndex(0)
        self._switch_page(0)

    def _toggle_theme(self):
        self.data_manager.theme_dark = not self.data_manager.theme_dark
        self.data_manager.save()
        set_theme(self.data_manager.theme_dark)
        self.theme_btn.setText("🌙" if self.data_manager.theme_dark else "☀️")
        
        # Update main app stylesheet and force refresh
        apply_stylesheet(self)
        
        # Update sidebar style
        self.findChild(QFrame).setStyleSheet(f"QFrame {{ background: {C['bg_card']}; border-right: 1px solid {C['border']}; }}")
        for i, btn in enumerate(self.nav_buttons):
            btn.setStyleSheet(self._nav_btn_style(self.stack.currentIndex() == i))
        self.theme_btn.setStyleSheet(self._nav_btn_style(False))
        
        # Refresh current page to apply new colors
        current_idx = self.stack.currentIndex()
        if current_idx < 4:
            self._switch_page(current_idx)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(C['bg']))
    palette.setColor(QPalette.WindowText, QColor(C['text']))
    palette.setColor(QPalette.Base, QColor(C['bg_card']))
    palette.setColor(QPalette.AlternateBase, QColor(C['bg_surface']))
    palette.setColor(QPalette.Text, QColor(C['text']))
    palette.setColor(QPalette.Button, QColor(C['bg_surface']))
    palette.setColor(QPalette.ButtonText, QColor(C['text']))
    palette.setColor(QPalette.Highlight, QColor(C['primary']))
    palette.setColor(QPalette.HighlightedText, QColor(C['text']))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
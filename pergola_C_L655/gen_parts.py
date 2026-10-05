# -*- coding: utf-8 -*-
"""
조형파고라C(회랑형) 부품도 생성기
원도면: L-655 조형파고라C (DXF) 에서 추출한 좌표/치수를 기반으로 부품별 제작도(DXF, PDF)를 생성한다.

좌표계(전체 배치 기준)
  X : 정면도 기준 좌→우 (지붕 좌측 끝 = 0, 우측 끝 = 12000)
  Y : 평면도 기준 앞→뒤 (지붕 앞면 = 0, 뒷면 = 4000)
  Z : F.L(마감면) = 0, 지붕 하단 = 2700, 지붕 상단 = 3000
"""
import ezdxf
from ezdxf.enums import TextEntityAlignment
import math, csv, os

OUT = os.path.dirname(os.path.abspath(__file__))
doc = ezdxf.new("R2018", setup=True)
doc.units = ezdxf.units.MM
msp = doc.modelspace()

doc.styles.add("KOR", font="NanumGothic.ttf")
for name, col, lt in [("OUTLINE", 7, "Continuous"), ("THIN", 8, "Continuous"), ("HIDDEN", 8, "DASHED"),
                      ("CENTER", 1, "CENTER"), ("DIM", 3, "Continuous"), ("TEXT", 7, "Continuous"),
                      ("HATCH", 8, "Continuous"), ("FRAME", 7, "Continuous"), ("NOTE", 1, "Continuous")]:
    doc.layers.add(name, color=col, linetype=lt)
ds = doc.dimstyles.duplicate_entry("EZDXF", "PART")
ds.dxf.dimtxsty = "KOR"
ds.dxf.dimtxt = 2.2
ds.dxf.dimasz = 2.0
ds.dxf.dimexe = 1.2
ds.dxf.dimexo = 1.0
ds.dxf.dimgap = 0.8
ds.dxf.dimdec = 1
ds.dxf.dimzin = 8
ds.dxf.dimclrd = 3
ds.dxf.dimclre = 3
ds.dxf.dimclrt = 3

BOM = []           # 부품 일람표
SHEETS = []        # (번호, 제목, xmin, ymin, xmax, ymax)


class Sheet:
    """A3(420x297) 도곽을 척도 N 으로 확대해 모델공간에 배치"""
    W, H = 420.0, 297.0
    count = 0

    def __init__(self, no, title, N, part=None):
        self.no, self.title, self.N = no, title, N
        idx = Sheet.count
        Sheet.count += 1
        # 시트끼리 겹치지 않도록 가로로 배치 (최대 척도 100 기준 간격)
        self.ox = idx * 50000.0
        self.oy = 0.0
        self.draw_frame(part)
        SHEETS.append((no, title, self.ox, self.oy, self.ox + self.W * N, self.oy + self.H * N))

    # 용지좌표(mm) -> 모델좌표
    def P(self, px, py):
        return (self.ox + px * self.N, self.oy + py * self.N)

    def view(self, pleft, ptop, n=None, label=None, sub=None, xmin=0.0, ymin=0.0, ymax=0.0, top=22.0):
        """pleft/ptop: 용지상 뷰 영역의 좌측·상단 (치수 여백 top 포함). 형상 실좌표 범위로 원점 자동 계산"""
        n = n or self.N
        return View(self, pleft - xmin / n, ptop - top - ymax / n, n, label, sub, pleft, ptop - top - (ymax - ymin) / n)

    def ptext(self, px, py, s, h=3.0, layer="TEXT", align="LEFT", color=None):
        t = msp.add_text(s, height=h * self.N, dxfattribs={"layer": layer, "style": "KOR"})
        if color:
            t.dxf.color = color
        al = {"LEFT": TextEntityAlignment.BOTTOM_LEFT, "CENTER": TextEntityAlignment.BOTTOM_CENTER,
              "RIGHT": TextEntityAlignment.BOTTOM_RIGHT, "MC": TextEntityAlignment.MIDDLE_CENTER,
              "ML": TextEntityAlignment.MIDDLE_LEFT}[align]
        t.set_placement(self.P(px, py), align=al)
        return t

    def pline(self, pts, layer="FRAME", close=False, lw=None):
        e = msp.add_lwpolyline([self.P(*p) for p in pts], close=close, dxfattribs={"layer": layer})
        if lw:
            e.dxf.const_width = lw * self.N
        return e

    def notes(self, px, py, lines, h=2.6, gap=4.4, title="※ 비 고"):
        self.ptext(px, py, title, h=h + 0.4)
        for i, s in enumerate(lines):
            self.ptext(px, py - gap * (i + 1), s, h=h)

    def table(self, px, py, cols, rows, rh=6.0, h=2.4):
        """cols=[(제목,폭)], 좌상단(px,py)"""
        tw = sum(w for _, w in cols)
        n = len(rows) + 1
        self.pline([(px, py), (px + tw, py), (px + tw, py - rh * n), (px, py - rh * n)], close=True)
        for i in range(1, n):
            self.pline([(px, py - rh * i), (px + tw, py - rh * i)], layer="THIN")
        x = px
        for j, (c, w) in enumerate(cols):
            if j:
                self.pline([(x, py), (x, py - rh * n)], layer="THIN")
            self.ptext(x + w / 2, py - rh * 0.5, c, h=h, align="MC")
            for i, r in enumerate(rows):
                self.ptext(x + w / 2, py - rh * (i + 1.5), str(r[j]), h=h * 0.95, align="MC")
            x += w

    def draw_frame(self, part):
        W, H = self.W, self.H
        self.pline([(0, 0), (W, 0), (W, H), (0, H)], close=True, layer="FRAME")
        self.pline([(10, 10), (W - 10, 10), (W - 10, H - 10), (10, H - 10)], close=True, lw=0.5)
        # 표제란
        x0, y0, w = W - 10 - 150, 10, 150
        rows = [("공 사 명", "조형파고라C(회랑형) 제작"),
                ("도 면 명", self.title),
                ("부품번호", part["no"] if part else "-"),
                ("재    질", part["mat"] if part else "-"),
                ("수    량", part["qty"] if part else "-"),
                ("척    도", f"1/{self.N:g} (A3)"),
                ("도면번호", f"PC-{self.no}"),
                ("원 도 면", "L-655 조형파고라C")]
        rh = 6.0
        self.pline([(x0, y0), (x0 + w, y0), (x0 + w, y0 + rh * len(rows)), (x0, y0 + rh * len(rows))], close=True)
        self.pline([(x0 + 28, y0), (x0 + 28, y0 + rh * len(rows))], layer="THIN")
        for i, (k, v) in enumerate(reversed(rows)):
            y = y0 + rh * i
            if i:
                self.pline([(x0, y), (x0 + w, y)], layer="THIN")
            self.ptext(x0 + 14, y + rh / 2, k, h=2.5, align="MC")
            self.ptext(x0 + 31, y + rh / 2, v, h=2.6 if len(v) < 40 else 2.2, align="ML")


class View:
    """뷰: 용지좌표(px,py)에 실척 형상을 1/n 으로 배치. 치수는 실치수로 표기."""

    def __init__(self, sh, px, py, n, label, sub, lx, lby):
        self.sh, self.px, self.py, self.n = sh, px, py, n
        self.m = sh.N / n                      # 모델 확대계수
        if label:
            ly = lby - 23
            sh.ptext(lx, ly, label, h=3.4)
            sh.pline([(lx, ly - 1), (lx + 3.4 * len(label) * 0.95, ly - 1)], layer="TEXT")
            sh.ptext(lx, ly - 5.5, sub or f"S = 1/{n:g}", h=2.4)

    def P(self, x, y):
        bx, by = self.sh.P(self.px, self.py)
        return (bx + x * self.m, by + y * self.m)

    def line(self, a, b, layer="OUTLINE"):
        msp.add_line(self.P(*a), self.P(*b), dxfattribs={"layer": layer})

    def poly(self, pts, layer="OUTLINE", close=True):
        msp.add_lwpolyline([self.P(*p) for p in pts], close=close, dxfattribs={"layer": layer})

    def rect(self, x0, y0, x1, y1, layer="OUTLINE", cross=False):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer)
        if cross:
            self.line((x0, y0), (x1, y1), "THIN")
            self.line((x0, y1), (x1, y0), "THIN")

    def circle(self, c, r, layer="OUTLINE"):
        msp.add_circle(self.P(*c), r * self.m, dxfattribs={"layer": layer})

    def hatch(self, pts, pattern="ANSI31", scale=1.0, layer="HATCH"):
        h = msp.add_hatch(dxfattribs={"layer": layer})
        h.set_pattern_fill(pattern, scale=scale * self.sh.N * 0.5)
        h.paths.add_polyline_path([self.P(*p) for p in pts], is_closed=True)

    def text(self, x, y, s, h=2.4, align="LEFT", layer="TEXT"):
        bx, by = self.P(x, y)
        t = msp.add_text(s, height=h * self.sh.N, dxfattribs={"layer": layer, "style": "KOR"})
        al = {"LEFT": TextEntityAlignment.BOTTOM_LEFT, "CENTER": TextEntityAlignment.BOTTOM_CENTER,
              "MC": TextEntityAlignment.MIDDLE_CENTER, "RIGHT": TextEntityAlignment.BOTTOM_RIGHT}[align]
        t.set_placement((bx, by), align=al)

    def leader(self, p, dx, dy, s, h=2.3):
        """p(실좌표)에서 용지 mm 기준 (dx,dy) 만큼 인출"""
        a = self.P(*p)
        N = self.sh.N
        b = (a[0] + dx * N, a[1] + dy * N)
        c = (b[0] + (8 if dx >= 0 else -8) * N, b[1])
        msp.add_lwpolyline([a, b, c], dxfattribs={"layer": "DIM"})
        msp.add_circle(a, 0.5 * N, dxfattribs={"layer": "DIM"})
        lines = s.split("\n")
        for i, ln in enumerate(lines):
            t = msp.add_text(ln, height=h * N, dxfattribs={"layer": "TEXT", "style": "KOR"})
            al = TextEntityAlignment.BOTTOM_LEFT if dx >= 0 else TextEntityAlignment.BOTTOM_RIGHT
            t.set_placement((c[0] + (1 if dx >= 0 else -1) * N, c[1] + 0.6 * N - i * (h + 1.2) * N), align=al)

    def _ov(self):
        return {"dimscale": self.sh.N, "dimlfac": 1.0 / self.m}

    def dh(self, x0, x1, y, off, text=None):
        """수평치수: y(실좌표) 기준으로 off(용지mm) 만큼 띄움"""
        base_y = self.P(0, y)[1] + off * self.sh.N
        d = msp.add_linear_dim(base=(self.P(x0, y)[0], base_y), p1=self.P(x0, y), p2=self.P(x1, y),
                               dimstyle="PART", override=self._ov(), dxfattribs={"layer": "DIM"},
                               text=text if text else "<>")
        d.render()

    def dv(self, y0, y1, x, off, text=None):
        base_x = self.P(x, 0)[0] + off * self.sh.N
        d = msp.add_linear_dim(base=(base_x, self.P(x, y0)[1]), p1=self.P(x, y0), p2=self.P(x, y1), angle=90,
                               dimstyle="PART", override=self._ov(), dxfattribs={"layer": "DIM"},
                               text=text if text else "<>")
        d.render()

    def chain_h(self, xs, y, off):
        for a, b in zip(xs, xs[1:]):
            self.dh(a, b, y, off)

    def chain_v(self, ys, x, off):
        for a, b in zip(ys, ys[1:]):
            self.dv(a, b, x, off)

    def cl(self, a, b):
        self.line(a, b, "CENTER")


def part(no, name, spec, mat, qty, unit_len, remark=""):
    BOM.append({"no": no, "name": name, "spec": spec, "mat": mat, "qty": qty, "len": unit_len, "remark": remark})
    return {"no": no, "mat": mat, "qty": f"{qty} EA"}


# ---------------------------------------------------------------------------
# 원도면에서 추출한 배치 데이터 (기초평면도 앵커위치 + 평면/정면/측면도 교차검증)
# ---------------------------------------------------------------------------
H_ROOF_BOT, H_ROOF_TOP = 2700.0, 3000.0
BP_TOP = -81.0                     # 베이스플레이트 상면 (F.L -81, L-655 기초상세도)
COL_L = H_ROOF_BOT - BP_TOP        # 기둥 길이 2781
FIN_L = 2698.0 - BP_TOP            # 루버 핀 길이 2779 (지붕하부 2mm 이격)

C200 = [("C1", 100, 3600), ("C2", 11700, 3600)]                       # □200x200 (좌하단 X,Y)
C300 = [("C3", 11700, 0)]                                             # □300x200
C100 = [("C4-1", 3006.3, 300), ("C4-2", 3900, 300),                    # 전면 루버열
        ("C4-3", 400, 500), ("C4-4", 400, 1393.8),                     # 좌측 벽 루버열
        ("C4-5", 3900, 3700), ("C4-6", 8000, 3700), ("C4-7", 8893.8, 3700),  # 후면
        ("C4-8", 8000, 675),                                           # 벤치 좌측
        ("C4-9", 11700, 291.7), ("C4-10", 11700, 483.3), ("C4-11", 11700, 675)]  # 우측 벽
# 50x100 루버 핀 : (X, Y, 방향)  방향 'x' = X방향 50 / Y방향 100
FINS = [(x, 300, "x") for x in (3225.0, 3393.8, 3562.5, 3731.3)] + \
       [(400, y, "y") for y in (718.8, 887.5, 1056.3, 1225.0)] + \
       [(x, 3700, "x") for x in (8218.8, 8387.5, 8556.3, 8725.0)]
GLASS_W = [(350.0, 1526.7), (1536.7, 2713.4), (2723.4, 3900.0)]   # 벽체유리 X구간 (Y 3700~3800 라인)
ROOF_GLASS_X = [(500, 1275), (1325, 2100), (2200, 2975), (3025, 3800)]
ROOF_GLASS_Y = [(500, 1466.7), (1516.7, 2483.4), (2533.4, 3500)]
PLATE_X = [4000.0, 4958.8, 4963.8, 5922.5, 5927.5, 6886.3, 6891.3, 7850.0, 7855.0, 8813.8,
           8818.8, 9777.5, 9782.5, 10741.3, 10746.3, 11700.0]
PLATE_Y = [300.0, 1429.3, 1434.3, 2563.6, 2568.6, 3697.9]
LED = [(x, y) for x in (4905, 6720, 8535, 10350) for y in (1205, 3020)]
BENCH = (8000, 225, 11700, 675)
TRENCH_Y = (3790.7, 3909.3)
SLOPE = 2.0  # 지붕 상부 배수구배 (deg)


# ===========================================================================
# PC-00  부품 배치도 (Key plan)
# ===========================================================================
def sheet_keyplan():
    sh = Sheet("00", "부품 배치도 (KEY PLAN)", 50)
    v = sh.view(42, 272, 50, "기둥·핀·벽체 배치도 (F.L 상부 수평단면)", ymax=4000, top=28)
    v.rect(0, 0, 12000, 4000, "HIDDEN")
    v.text(6000, 4080, "지붕 외곽선 (점선) 12000 x 4000", h=2.2, align="CENTER")
    for nm, x, y in C200:
        v.rect(x, y, x + 200, y + 200, cross=True)
        v.text(x + 100, y + 260, nm, h=2.4, align="CENTER")
    for nm, x, y in C300:
        v.rect(x, y, x + 300, y + 200, cross=True)
        v.text(x - 60, y + 40, nm, h=2.4, align="RIGHT")
    for nm, x, y in C100:
        v.rect(x, y, x + 100, y + 100, cross=True)
        if nm in ("C4-9", "C4-10", "C4-11"):
            v.text(x - 60, y + 20, nm, h=1.9, align="RIGHT")
        elif nm in ("C4-3", "C4-4"):
            v.text(x + 160, y + 20, nm, h=1.9)
        else:
            v.text(x + 50, y + (150 if y > 2000 else -230), nm, h=1.9, align="CENTER")
    for i, (x, y, d) in enumerate(FINS):
        w, h = (50, 100) if d == "x" else (100, 50)
        v.rect(x, y, x + w, y + h, "OUTLINE")
    v.text(3500, 50, "F1 x4", h=1.9, align="CENTER")
    v.text(560, 950, "F1 x4", h=1.9)
    v.text(8500, 3560, "F1 x4", h=1.9, align="CENTER")
    for i, (a, b) in enumerate(GLASS_W):
        v.rect(a, 3746, b, 3754, "OUTLINE")
        v.text((a + b) / 2, 3560, f"G2-{i + 1}", h=1.9, align="CENTER")
    v.rect(*BENCH)
    v.text(9850, 400, "B1 연식벤치", h=2.2, align="CENTER")
    v.rect(7992, 320, 8089, 580, cross=True)
    v.leader((8040, 450), -14, 14, "E1 분전함")
    v.chain_h([0, 400, 3006.3, 4000, 8000, 8993.8, 11700, 12000], 4000, 14)
    v.dh(0, 12000, 4000, 22)
    v.chain_v([0, 500, 1493.8, 3600, 4000], 0, -14)
    v.dv(0, 4000, 0, -22)
    sh.notes(25, 52, [
        "1. 본 배치도는 원도면 '기초평면도'의 앵커(X표기) 위치를 정면도·측면도와 교차 검증하여 작성함.",
        "2. 좌표 원점: 지붕 좌측·전면 모서리 (X=0, Y=0), 높이 기준 F.L ±0.",
        "3. 원도면 기초평면 표기는 지붕 기준 X +50, Y +150 이동 배치되어 있음 (본 도면은 보정치 적용).",
        "4. 각 부품 상세는 PC-01 ~ PC-12 참조. 부품 일람표는 PC-13 참조.",
    ])


# ===========================================================================
# PC-01  지붕 프레임 (외곽 박스)
# ===========================================================================
def sheet_roof():
    p = part("R1", "지붕 프레임(외곽 박스)", "12000 x 4000 x H300", "STL 각관 하지 + T1.6 STL PLATE 마감 / 지정색 도장",
             1, "-", "내부 하지 구조 원도면 미표기")
    sh = Sheet("01", "지붕 프레임 (R1)", 50, p)
    v = sh.view(35, 272, 50, "지붕 평면도 (상부)", ymax=4000)
    v.rect(0, 0, 12000, 4000)
    v.rect(300, 300, 11700, 3700, "THIN")
    v.rect(300, TRENCH_Y[0], 11700, TRENCH_Y[1])
    v.hatch([(300, TRENCH_Y[0]), (11700, TRENCH_Y[0]), (11700, TRENCH_Y[1]), (300, TRENCH_Y[1])], "ANSI37", 0.3)
    v.rect(300, 300, 4000, 3700, "THIN")
    v.rect(500, 500, 3800, 3500, "THIN")
    v.text(2150, 2000, "지붕유리 개구부 (R3 참조)", h=2.0, align="CENTER")
    v.text(9500, 2000, "STL PLATE 구간 (R2 참조)", h=2.0, align="CENTER")
    v.line((7300, 1300), (7300, 2600), "NOTE")
    v.poly([(7240, 2480), (7300, 2650), (7360, 2480)], "NOTE")
    v.text(7400, 1900, "SLOPE 2°", h=2.0)
    v.text(6000, 3350, "↑ 후면 트렌치(물받이) W118.6 → 배수 인출 (PC-12, 현장협의)", h=2.0, align="CENTER")
    v.chain_h([0, 300, 4000, 11700, 12000], 4000, 10)
    v.dh(0, 12000, 4000, 17)
    v.chain_v([0, 300, 3700, 4000], 12000, 12)
    v.dv(0, 4000, 12000, 22)

    v2 = sh.view(35, 150, 50, "정면도", ymax=300, top=14)
    v2.rect(0, 0, 12000, 300)
    v2.dh(0, 12000, 0, -8)
    v2.dv(0, 300, 0, -8)
    v2.text(6000, 330, "F.L +2700 ~ +3000 (지붕 두께 300)", h=2.0, align="CENTER")

    v3 = sh.view(35, 102, 25, "측면 단면도 (배수구배)", ymax=300, top=14)
    v3.rect(0, 0, 4000, 300)
    drop = (3700 - 300) * math.tan(math.radians(SLOPE))
    v3.line((300, 300), (3700, 300 - drop), "THIN")
    v3.rect(TRENCH_Y[0], 300 - drop - 80, TRENCH_Y[1], 300 - drop, "THIN")
    v3.text(1800, 330, f"상부 마감판 구배 2° (낙차 약 {drop:.0f})", h=2.0, align="CENTER")
    v3.dh(0, 4000, 0, -8)
    v3.chain_h([0, 300, 3700, 4000], 0, -14)
    v3.dv(0, 300, 4000, 8)
    sh.notes(220, 100, [
        "1. 외곽 치수 12000 x 4000, 두께 300 (지붕하부 F.L+2700).",
        "2. 외곽 띠(폭 300) : T1.6 STL PLATE 지정색 도장 (색상 원도면 미표기).",
        "3. 상부 마감면은 후면 방향 2° 구배, 후면 트렌치(W118.6)로 집수.",
        "4. 내부 하지(각관 규격·간격)는 원도면 미표기 → 구조계산 후 확정할 것.",
        "5. 하부: 좌측(X300~4000) 지붕유리 R3, 우측(X4000~11700) 천장판 R2.",
        "6. LED 매입등 8EA 개구부 위치는 PC-02 참조.",
    ], h=2.4, gap=4.2)


# ===========================================================================
# PC-02  천장 STL PLATE 패널 (24EA) + LED 개구부
# ===========================================================================
def sheet_plate():
    p = part("R2", "천장 STL PLATE 패널", "958.8 x 1129.3 (21EA) / 953.7 x 1129.3 (3EA)", "T1.6 STL PLATE / 지정색 도장",
             24, "-", "줄눈 5mm, LED 개구부 포함 8EA")
    sh = Sheet("02", "천장 STL PLATE 패널 (R2)", 40, p)
    v = sh.view(35, 272, 40, "패널 배치도 (지붕 하부에서 올려본 평면)", xmin=4000, ymin=300, ymax=3700)
    xs, ys = PLATE_X, PLATE_Y
    k = 0
    for j in range(0, len(ys), 2):
        for i in range(0, len(xs), 2):
            v.rect(xs[i], ys[j], xs[i + 1], ys[j + 1])
            k += 1
            v.text((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2 + 150, f"R2-{k:02d}", h=1.8, align="CENTER")
    for (x, y) in LED:
        v.rect(x - 60, y - 60, x + 60, y + 60, cross=True)
    v.chain_h([4000, 4958.8, 4963.8, 5922.5], ys[-1], 8)
    v.dh(xs[-2], xs[-1], ys[-1], 8)
    v.dh(4000, 11700, ys[-1], 15)
    v.chain_v([ys[0], ys[1], ys[2]], 11700, 8)
    v.dv(300, 3697.9, 11700, 16)
    v.chain_h([4000, 4905, 6720, 8535, 10350], 300, -9)
    v.chain_v([300, 1205, 3020], 4000, -9)

    v2 = sh.view(62, 122, 20, "단위 패널 상세 (R2 표준)", ymax=1129.3, top=14)
    v2.rect(0, 0, 958.8, 1129.3)
    v2.rect(905 - 60, 905 - 60, 905 + 60, 905 + 60, cross=True)
    v2.dh(0, 958.8, 0, -8)
    v2.dv(0, 1129.3, 0, -8)
    v2.chain_h([0, 845, 958.8], 1129.3, 6)
    v2.chain_v([0, 845, 965, 1129.3], 958.8, 7)
    v2.leader((845, 905), -12, -26, "LED 매입등 개구부 □120\n(R2-01 기준, LED 위치 패널만)")
    sh.table(140, 122, [("구분", 20), ("규격(W x L)", 40), ("수량", 14), ("비고", 50)],
             [("R2-A", "958.8 x 1129.3", "21", "표준 (LED 개구부 6EA 포함)"),
              ("R2-B", "953.7 x 1129.3", "3", "우측 끝열 (X10746.3~11700)"),
              ("LED", "□120 개구", "8", "4열 x 2행, 피치 1815 / 1815")])
    sh.notes(140, 92, [
        "1. T1.6 STL PLATE, 지정색 도장 (색상 원도면 미표기).",
        "2. 패널 줄눈 5mm (X·Y 공통), 지붕 하부 F.L+2700 면에 부착.",
        "3. 우측 끝열 3EA는 폭 953.7 로 현장 맞춤 재단.",
        "4. 4변 절곡(플랜지) 및 고정 방법은 원도면 미표기 → 제작사 표준 적용.",
        "5. LED 매입등 : 총 8EA, 128W (원도면 기준).",
        "6. LED 개구부 위치는 패널마다 상이 → 배치도 좌표로 타공.",
    ], h=2.4, gap=4.2)


# ===========================================================================
# PC-03  지붕 접합유리 (12EA)
# ===========================================================================
def sheet_roof_glass():
    p = part("R3", "지붕 접합유리", "775 x 966.7", "T10.76 접합유리 (보호필름 부착)", 12, "-", "유리 줄눈 50/100")
    sh = Sheet("03", "지붕 접합유리 (R3)", 25, p)
    v = sh.view(25, 272, 25, "지붕유리 배치도 (평면)", xmin=300, ymin=300, ymax=3700)
    v.rect(300, 300, 4000, 3700, "THIN")
    k = 0
    for (y0, y1) in reversed(ROOF_GLASS_Y):
        for (x0, x1) in ROOF_GLASS_X:
            k += 1
            v.rect(x0, y0, x1, y1)
            v.text((x0 + x1) / 2, (y0 + y1) / 2, f"R3-{k:02d}", h=2.0, align="MC")
    v.chain_h([300, 500, 1275, 1325, 2100, 2200, 2975, 3025, 3800, 4000], 3700, 8)
    v.dh(300, 4000, 3700, 15)
    v.chain_v([300, 500, 1466.7, 1516.7, 2483.4, 2533.4, 3500, 3700], 4000, 8)
    v.dv(300, 3700, 4000, 18)

    v2 = sh.view(215, 272, 10, "단위 유리 상세", ymax=966.7)
    v2.rect(0, 0, 775, 966.7)
    v2.line((0, 0), (200, 200), "THIN")
    v2.dh(0, 775, 0, -8)
    v2.dv(0, 966.7, 775, 8)
    v3 = sh.view(215, 128, 2, "유리 단면 (T10.76)", ymax=10.76, top=18)
    v3.rect(0, 0, 100, 5)
    v3.rect(0, 5, 100, 5.76)
    v3.rect(0, 5.76, 100, 10.76)
    v3.dv(0, 10.76, 100, 6)
    v3.leader((60, 5.4), 8, 8, "PVB 필름 0.76")
    v3.leader((30, 2.5), -6, -8, "강화유리 5 + 5")
    sh.notes(25, 82, [
        "1. T10.76 접합유리 (5 + PVB0.76 + 5), 보호필름 부착.",
        "2. 투과율·KS인증 여부: 원도면 미표기 → 발주처 확인.",
        "3. 크기 775 x 966.7, 12EA (4열 x 3행).",
        "4. 줄눈: X방향 50 / 100(중앙) / 50, Y방향 50.",
        "5. 지지 프레임(유리 받침) 상세는 원도면 미표기",
        "   → 실링·세팅블록 포함 제작사 표준 적용.",
        "6. 유리 구성(5+0.76+5)은 T10.76 표준 구성 기준 추정.",
    ], h=2.4, gap=4.2)


# ===========================================================================
# 기둥/핀 공통 : 정면 입면 + 단면 + 베이스플레이트
# ===========================================================================
def column_sheet(no, pid, name, w, d, t_hint, qty, locs, mat, remark, extra=None, plate=(200, 200)):
    p = part(pid, name, f"□{w:g}x{d:g} L={COL_L if 'F' not in pid else FIN_L:g}", mat, qty,
             COL_L if 'F' not in pid else FIN_L, remark)
    L = COL_L if 'F' not in pid else FIN_L
    pt = 12 if max(plate) >= 300 else 9
    sh = Sheet(no, f"{name} ({pid})", 20, p)
    v = sh.view(40, 275, 20, "입면도", ymin=-9, ymax=L)
    v.rect(0, 0, w, L)
    v.cl((w / 2, -150), (w / 2, L + 100))
    pw, pd = plate
    v.rect(w / 2 - pw / 2, -9, w / 2 + pw / 2, 0)
    v.line((-400, -BP_TOP), (w + 400, -BP_TOP), "NOTE")
    v.text(w + 420, -BP_TOP, "F.L ±0", h=2.0)
    v.text(w + 420, L, "지붕 하부 (F.L+2700)" if 'F' not in pid else "F.L+2698 (지붕하부 2mm 이격)", h=2.0)
    v.dv(0, L, 0, -12)
    v.dv(0, -BP_TOP, w, 10)
    v.dv(-BP_TOP, L, w, 10)
    v.dh(0, w, L, 6)
    v.leader((w / 2 + pw / 2, -4), 12, -6, f"BASE PL {pw:g}x{pd:g}x{pt:g} (PC-09)")
    if extra:
        extra(v)

    v2 = sh.view(110, 272, 5, "단면도 A-A", ymax=d, top=16)
    v2.rect(0, 0, w, d)
    tt = t_hint
    v2.rect(tt, tt, w - tt, d - tt, "THIN")
    v2.hatch([(0, 0), (w, 0), (w, d), (0, d)], "ANSI31", 1.5)
    v2.dh(0, w, 0, -8)
    v2.dv(0, d, w, 8)
    v2.leader((w, d * 0.8), 8, 6, f"t={tt:g} (원도면 미표기, 권장)")

    v3 = sh.view(110, 178, 5, "베이스플레이트 평면", ymax=pd, top=16)
    v3.rect(0, 0, pw, pd)
    v3.rect(pw / 2 - w / 2, pd / 2 - d / 2, pw / 2 + w / 2, pd / 2 + d / 2, "THIN")
    for (ax, ay) in anchors(pw, pd):
        v3.circle((ax, ay), 6)
        v3.cl((ax - 12, ay), (ax + 12, ay))
    v3.dh(0, pw, 0, -8)
    v3.dv(0, pd, pw, 8)
    a = anchors(pw, pd)
    v3.chain_h([0, a[0][0], a[1][0], pw], pd, 6)
    sh.ptext(110, 62, "앵커: M10 x L100 셋트앙카 (구멍 Φ12)", h=2.2)

    rows = [(nm, f"{x:g}", f"{y:g}", f"{w:g}x{d:g}") for (nm, x, y) in locs]
    if len(rows) > 14:
        half = (len(rows) + 1) // 2
        sh.table(230, 268, [("부호", 16), ("X", 20), ("Y", 18), ("단면", 18)], rows[:half], rh=5.2, h=2.1)
        sh.table(287, 270, [("부호", 16), ("X", 20), ("Y", 18), ("단면", 18)], rows[half:], rh=5.2, h=2.1)
    else:
        sh.table(230, 268, [("부호", 22), ("X(좌하단)", 30), ("Y(좌하단)", 30), ("단면", 24)], rows, rh=5.5, h=2.2)
    sh.ptext(230, 272, "설치 위치 (PC-00 좌표, 단위 mm)", h=2.4)
    lines = [
        f"1. 재질: {mat}.",
        f"2. 길이 L = {L:g} (F.L 상부 {L + BP_TOP:g} + 포장 하부 {-BP_TOP:g}).",
        "3. 하단 BASE PLATE 전둘레 용접 후 M10xL100 셋트앙카 고정 (PC-09).",
        "4. 상단은 지붕 하지(R1)에 용접 또는 브라켓 볼트 고정.",
        f"5. 수량 {qty} EA, 표면처리: 지정색 도장 (색상 원도면 미표기).",
    ] + (remark_lines(remark))
    sh.notes(230, 268 - 5.5 * (len(rows) + 1) - 12, lines, h=2.3, gap=4.0)


def remark_lines(r):
    return [f"6. {r}"] if r else []


def anchors(pw, pd):
    e = 25 if min(pw, pd) <= 100 else 27
    if min(pw, pd) <= 100:
        return [(pw / 2 - (pw / 2 - e), pd / 2), (pw - e, pd / 2)]
    return [(e, e), (pw - e, e), (pw - e, pd - e), (e, pd - e)]


def sheets_columns():
    def drain(v):
        v.line((100 - 25, 0), (100 - 25, COL_L), "HIDDEN")
        v.line((100 + 25, 0), (100 + 25, COL_L), "HIDDEN")
        v.leader((100, 1900), 24, 4, "배수 인출 기둥 지정 시: 하단 측면 인출구 타공\n(배수 상세 PC-12, 현장협의)")
    column_sheet("04", "C1/C2", "□200x200 기둥", 200, 200, 6, 2, C200, "STL 각관 □200x200 (SS275)",
                 "배수 인출 기둥 위치 현장협의 (PC-12)", extra=drain, plate=(300, 300))
    column_sheet("05", "C3", "□300x200 기둥", 300, 200, 6, 1, C300, "STL 각관 □300x200 (SS275)",
                 "원도면 기초평면 4모서리 앵커 표기 기준", plate=(300, 200))
    column_sheet("06", "C4", "□100x100 기둥", 100, 100, 3.2, len(C100), C100, "100x100 STL PIPE (각관) 지정색 도장",
                 "", plate=(200, 200))
    fins = []
    for i, (x, y, dd) in enumerate(FINS):
        fins.append((f"F1-{i + 1}", x, y))
    column_sheet("07", "F1", "50x100 루버 핀", 50, 100, 2.3, len(FINS), fins, "50x100 STL 각관 지정색 도장",
                 "핀 피치 168.75 C/C, 지붕하부 2mm 이격", plate=(100, 150))


# ===========================================================================
# PC-08  벽체 접합유리 (3EA)
# ===========================================================================
def sheet_wall_glass():
    p = part("G2", "벽체 접합유리", "1176.7 x 1050", "T10.76 접합유리 (보호필름 부착)", 3, "-", "후면 좌측 벽")
    sh = Sheet("08", "벽체 접합유리 (G2)", 20, p)
    v = sh.view(30, 272, 20, "입면도 (후면 좌측 X350~3900)", ymax=1100)
    for i, (a, b) in enumerate(GLASS_W):
        v.rect(a - 350, 50, b - 350, 1100)
        v.text((a + b) / 2 - 350, 575, f"G2-{i + 1}", h=2.6, align="MC")
    v.line((-300, 0), (3800, 0), "NOTE")
    v.text(3600, 20, "F.L", h=2.0)
    v.chain_h([0, 1176.7, 1186.7, 2363.4, 2373.4, 3550], 1100, 8)
    v.dh(0, 3550, 1100, 15)
    v.chain_v([0, 50, 1100], 3550, 8)
    v.dv(0, 1100, 3550, 16)

    v2 = sh.view(40, 150, 5, "설치 단면 (Y방향)", xmin=-200, ymax=400, top=14)
    v2.rect(0, 50, 10.76, 400)
    v2.rect(-30, 0, 40.76, 50, "THIN")
    v2.line((-200, 0), (250, 0), "NOTE")
    v2.text(-180, 10, "F.L", h=2.0)
    v2.dv(0, 50, -30, -8)
    v2.dh(0, 10.76, 400, 6)
    v2.leader((5, 300), 10, 4, "T10.76 접합유리")
    v2.leader((40, 25), 10, -6, "하부 고정 채널 (추정)")
    sh.notes(200, 140, [
        "1. T10.76 접합유리, 보호필름 부착 (투과율 원도면 미표기).",
        "2. 크기 1176.7(W) x 1050(H) x 3EA, 유리간 줄눈 10.",
        "3. 설치높이 F.L+50 ~ +1100 (정면도 기준).",
        "4. 설치 위치: 후면 Y3700~3800 라인 (C1 기둥 ~ C4-5 기둥 사이).",
        "5. 고정 방식(채널/클램프)은 원도면 미표기 → 제작사 표준 적용.",
    ], h=2.4, gap=4.2)


# ===========================================================================
# PC-09  기초 / 베이스플레이트 / 앵커
# ===========================================================================
def sheet_footing():
    p = part("FD", "기둥 기초 + BASE PLATE", "기초 400x400x400 / BASE PL 200x200x9", "콘크리트 25-18-80 / SS275",
             26, "-", "기둥·핀 1개소당 1EA")
    sh = Sheet("09", "기초 및 BASE PLATE 상세 (FD)", 10, p)
    v = sh.view(25, 272, 10, "기초 단면 상세", xmin=-600, ymin=-500, ymax=500, top=10)
    # 포장층 (L-655: 보도블럭 60 / 모래 30 / 기층 150)
    v.rect(-600, -60, 600, 0, "THIN")
    v.rect(-600, -90, 600, -60, "THIN")
    v.rect(-600, -240, 600, -90, "THIN")
    v.hatch([(-600, -240), (-200, -240), (-200, -90), (-600, -90)], "AR-CONC", 0.05)
    v.hatch([(200, -240), (600, -240), (600, -90), (200, -90)], "AR-CONC", 0.05)
    # 기초 (상단 F.L-90)
    v.rect(-200, -490, 200, -90)
    v.hatch([(-200, -490), (200, -490), (200, -90), (-200, -90)], "AR-CONC", 0.05)
    # 베이스 플레이트 + 기둥
    v.rect(-100, -90, 100, -81)
    v.rect(-60, -81, 60, 500)
    for ax in (-73, 73):
        v.rect(ax - 5, -90 - 90, ax + 5, -81 + 10, "THIN")
    v.dh(-200, 200, -490, -10)
    v.dv(-490, -90, -200, -14)
    v.chain_v([-240, -90, -60, 0], 600, 8)
    v.dv(-240, 0, 600, 18)
    v.chain_h([-100, -73, 73, 100], -81, 12)
    v.leader((0, 300), 18, 4, "STL PIPE (기둥)")
    v.leader((80, -85), 70, 46, "BASE PLATE 200x200x9")
    v.leader((73, -150), 70, -2, "M10 x L100 셋트앙카")
    v.leader((150, -350), 60, -6, "기초콘크리트 400x400x400\n(25-18-80)")
    v.leader((450, -30), 28, 24, "보도블럭 T60")
    v.leader((500, -75), 30, 16, "모래 T30")
    v.leader((550, -170), 34, 8, "기층 T150")
    v.text(-560, 20, "F.L ±0", h=2.2)

    v2 = sh.view(300, 272, 5, "BASE PLATE 평면 (C4 / □100 기준)", ymax=200, top=16)
    v2.rect(0, 0, 200, 200)
    v2.rect(50, 50, 150, 150, "THIN")
    for a in anchors(200, 200):
        v2.circle(a, 6)
    v2.dh(0, 200, 0, -8)
    v2.dv(0, 200, 200, 8)
    v2.chain_h([0, 27, 173, 200], 200, 6)
    sh.table(255, 150, [("적용 부재", 30), ("BASE PL", 32), ("앵커", 24), ("수량", 14)], [
        ("C1/C2 □200", "300x300x12", "M10 4EA", "2"),
        ("C3 □300x200", "300x200x12", "M10 4EA", "1"),
        ("C4 □100", "200x200x9", "M10 4EA", str(len(C100))),
        ("F1 50x100", "100x150x9", "M10 2EA", str(len(FINS))),
    ], rh=5.5, h=2.2)
    sh.notes(255, 110, [
        "1. 원도면 상세: BASE PL 200(W) x 9(t) 실측, 앵커 C/C 146,",
        "   M10xL100 셋트앙카, 기초 400x400x400 (25-18-80).",
        "2. 상기 표 중 □200/□300/핀 BASE PL 규격은 원도면 미표기",
        "   → 기둥 단면에 맞춘 제안치 (구조검토 필요).",
        "3. BASE PL 상면 F.L-81, 기초 상단 F.L-90 (L-655 기초상세도).",
        "   포장: 보도블럭 60 / 모래 30 / 기층 150 (계 240).",
        "4. 기초 총 26개소 (기둥 14 + 핀 12).",
    ], h=2.3, gap=4.0)


# ===========================================================================
# PC-10  연식벤치
# ===========================================================================
def sheet_bench():
    p = part("B1", "연식벤치", "3700 x 450 x H450", "STL 프레임 + (상부) 포세린타일", 1, 3700, "타일 600x430 x6 + 50x430 x1")
    sh = Sheet("10", "연식벤치 (B1)", 20, p)
    v = sh.view(60, 272, 20, "평면도", ymax=450)
    x0, y0, x1, y1 = 0, 0, 3700, 450
    v.rect(x0, y0, x1, y1)
    v.rect(10, 10, 3690, 440, "THIN")
    xs = [10]
    for i in range(6):
        xs.append(xs[-1] + 600)
        v.rect(xs[-2], 10, xs[-1], 440, "THIN")
        xs[-1] += 5
    v.rect(xs[-1], 10, 3690, 440, "THIN")
    v.chain_h([0, 10, 610, 615, 1215], 450, 7)
    v.dh(3640, 3690, 450, 7)
    v.dh(0, 3700, 450, 14)
    v.chain_v([0, 10, 440, 450], 3700, 7)
    v.rect(-8, 95, 89 - 8, 355, cross=True)
    v.leader((40, 250), -6, -14, "E1 분전함 (PC-11)")

    v2 = sh.view(60, 210, 20, "정면도", ymax=450, top=16)
    v2.rect(0, 0, 3700, 450)
    v2.rect(0, 430, 3700, 450, "THIN")
    v2.dh(0, 3700, 0, -8)
    v2.dv(0, 450, 3700, 8)
    v2.leader((1800, 445), 8, 10, "포세린타일 (상부 마감)")
    v3 = sh.view(60, 140, 10, "측면도", ymax=450, top=10)
    v3.rect(0, 0, 450, 450)
    v3.rect(0, 430, 450, 450, "THIN")
    v3.dh(0, 450, 0, -8)
    v3.dv(0, 450, 450, 8)
    sh.notes(150, 125, [
        "1. 설치 위치: X8000~11700, Y225~675 (PC-00).",
        "2. 상판 포세린타일 600 x 430, 줄눈 5, 6EA + 끝단 50 x 430 1EA.",
        "3. 테두리 프레임 폭 10 (평면 기준).",
        "4. 좌측 측면에 분전함(E1) 설치, 하부 배선 F-CV 2.5SQ 이상.",
        "5. 내부 하지 및 타일 접착 방식은 원도면 미표기 → 제작사 표준.",
        "6. 타일 두께는 원도면 미표기 (단면 20 가정).",
    ], h=2.4, gap=4.2)


# ===========================================================================
# PC-11  전기·배수 부속
# ===========================================================================
def sheet_misc():
    p = part("E1", "분전함", "260 x 300 x 97 (도면 실측)", "기성품", 1, "-", "0.5kW 이상, 220V 단상")
    BOM.append({"no": "L1", "name": "LED 매입등", "spec": "□120, 16W급 x 8EA = 128W", "mat": "기성품", "qty": 8, "len": "-",
                "remark": "지붕 하부 R2 패널 개구부"})
    sh = Sheet("11", "분전함·조명 (E1/L1)", 20, p)
    v = sh.view(25, 272, 10, "분전함 E1 (정면 / 측면)", ymax=330)
    v.rect(0, 0, 260, 300)
    v.rect(15, 15, 245, 285, "THIN")
    v.dh(0, 260, 0, -8)
    v.dv(0, 300, 0, -8)
    v.rect(400, 0, 497, 300)
    v.dh(400, 497, 0, -8)
    v.text(130, 330, "설치높이 F.L+75 ~ +375", h=2.0, align="CENTER")
    sh.notes(25, 176, [
        "· 0.5kW 이상 (220V, 단상)",
        "· 제품 내 모든 전선 2.5SQ 이상 F-CV선",
        "· 누전차단기, 접지 부스바, 타이머 적용",
        "· 전기인입 구분: 평면 '1차 전기공사분' / 정면 '조경공사분' (확인)",
        "· 크기는 원도면 축척 실측치 (기성품 선정 시 조정)",
    ], h=2.3, gap=4.0, title="※ 분전함 사양")
    sh.notes(25, 140, [
        "· 등기구류: 128W (8EA, 실사용전력은 기구에 따라 다름)",
        "· 총 전기용량: 128 x 1.3(여유율) = 0.5kW",
        "· 배치: X 4905/6720/8535/10350, Y 1205/3020",
    ], h=2.3, gap=4.0, title="※ LED 매입등 L1")

    sh.notes(25, 110, [
        "1. 배수 상세는 PC-12 참조 (원도면 L-655 '배수 상세도').",
    ], h=2.3, gap=4.0)


# ===========================================================================
# PC-12  배수 상세 (L-655 신규)
# ===========================================================================
def sheet_drain():
    p = part("D0", "배수 인출구 (기둥 하부)", "인출관 약 Φ32 (도면 실측)", "STL (기둥 일체, 시설물 공사분)", 1, "-",
             "배수 인출 기둥 1개소, 위치 현장협의")
    sh = Sheet("12", "배수 상세 (D0/D1/D2)", 10, p)
    v = sh.view(30, 272, 6, "배수 상세도 (원도면 L-655 기준)", xmin=-900, ymin=-650, ymax=320, top=16)
    # 포장 단면 (상부층 100 / 콘크리트 100 + 와이어메쉬 / 기층 150)
    X0, X1 = -259.3, 535.2
    v.line((X0, 0), (-50.2, 0))
    v.line((49.8, 0), (X1, 0))
    v.line((X0, -100.2), (X1, -100.2), "THIN")
    v.line((-133.4, -200.2), (X1, -200.2), "THIN")
    v.line((-133.4, -350.2), (X1, -350.2), "THIN")
    v.line((X0, 0), (X0, -350.2), "THIN")
    v.hatch([(-133.4, -200.2), (X1, -200.2), (X1, -100.2), (-133.4, -100.2)], "AR-CONC", 0.03)
    v.hatch([(-133.4, -350.2), (X1, -350.2), (X1, -200.2), (-133.4, -200.2)], "ANSI37", 0.4)
    for x in range(-110, 520, 110):
        v.line((x, -150.2), (x + 90, -150.2), "HIDDEN")
    # 기둥 + BASE PL + 앵커
    v.rect(-50.2, -91.2, 49.8, 300)
    v.rect(-167.5, -100.2, 124.8, -91.2)
    for ax in (-79.4, 79.6):
        v.rect(ax - 6, -178, ax + 6, -63, "THIN")
    # 인출관 (기둥 측면 → 하향)
    v.poly([(-50.2, -59.2), (-174.5, -59.2), (-199.5, -84.2), (-199.5, -154.6), (-167.5, -154.6),
            (-167.5, -91.2), (-50.2, -91.2)], close=False)
    v.cl((-183.5, 9), (-183.5, -182))
    # 배수관 (Φ100, 우배수 공사분)
    v.poly([(-233.4, -100.2), (-233.4, -380.2), (-253.4, -400.2), (-370.1, -400.2)], close=False)
    v.poly([(-133.4, -100.2), (-133.4, -450.2), (-183.4, -500.2), (-370.1, -500.2)], close=False)
    # 조경 빗물받이
    v.rect(-870.1, -600.2, -370.1, -0.2)
    v.line((-900, 0), (X0, 0), "NOTE")
    v.text(-880, 15, "F.L", h=2.0)
    # 치수
    v.dh(-870.1, -370.1, -600.2, -8)
    v.dv(-600.2, -0.2, -870.1, -8)
    v.chain_h([-370.1, -233.4, -133.4, -50.2, 49.8], 0, 12)
    v.chain_v([-350.2, -200.2, -100.2, 0], X1, 8)
    v.dv(-500.2, -400.2, -370.1, 6)
    v.dh(-79.4, 79.6, -178, -8)
    # 인출
    v.leader((0, 200), 14, 4, "STL PIPE (기둥)")
    v.leader((-120, -75), 8, 30, "시설물 공사분 (기둥·BASE PL·인출관)")
    v.leader((-183, -300), 14, -38, "배수관 Φ100 (도면 실측) = 우배수 공사분")
    v.text(-620, -280, "조경 빗물받이", h=2.4, align="CENTER")
    v.text(-620, -340, "500 x 600", h=2.2, align="CENTER")
    v.leader((300, -150.2), 10, -30, "와이어메쉬 (콘크리트 슬래브 T100)")
    v.leader((450, -280), 6, -18, "기층 T150")
    sh.notes(268, 268, [
        "1. 원도면 L-655 '배수 상세도'를 축척 실측하여 작성.",
        "2. 지붕 트렌치 → 배수 기둥 내부 → 하부 측면 인출관",
        "   → 배수관 Φ100 → 조경 빗물받이(500x600).",
        "3. 공사 구분: 기둥·인출관 = 시설물 공사분,",
        "   배수관·빗물받이 = 우배수 공사분.",
        "4. ※ 배수 관련 현장협의 후 진행 (원도면 명기).",
        "5. 배수 인출 기둥 위치는 원도면 미표기",
        "   (L-654 에서는 C2 우측 후면 기둥 내장).",
        "6. 본 상세의 포장은 슬래브형(상부 100 / 콘크리트",
        "   100+메쉬 / 기층 150)으로 PC-09 기초상세와 상이",
        "   → 배수 기둥 위치의 포장구성 현장 확인.",
        "7. BASE PL 은 인출구 측으로 비대칭 연장(실측 292),",
        "   앵커 C/C 159, 관경(Φ32/Φ100)은 실측치 → 규격 확인.",
    ], h=2.3, gap=4.0)
    BOM.append({"no": "D1", "name": "배수관", "spec": "Φ100 (도면 실측)", "mat": "현장협의", "qty": 1, "len": "-",
                "remark": "우배수 공사분, 인출구 → 빗물받이"})
    BOM.append({"no": "D2", "name": "조경 빗물받이", "spec": "500 x 600", "mat": "기성품", "qty": 1, "len": "-",
                "remark": "우배수 공사분, 현장협의"})


# ===========================================================================
# PC-13  부품 일람표
# ===========================================================================
def sheet_bom():
    sh = Sheet("13", "부품 일람표 (BOM)", 1)
    rows = [(b["no"], b["name"], b["spec"], b["mat"], b["qty"], b["len"], b["remark"]) for b in BOM]
    sh.table(18, 270, [("부호", 16), ("품명", 42), ("규격", 74), ("재질", 90), ("수량", 13), ("단위길이", 18), ("비고", 120)],
             rows, rh=8, h=2.3)
    sh.notes(20, 270 - 8 * (len(rows) + 1) - 12, [
        "1. 원도면에 명시된 값: 외곽 치수, 기둥·핀 위치, 유리 규격(T10.76), 강판(T1.6), 기초(400x400x400), 앵커(M10xL100), 도장(지정색).",
        "2. 원도면 미표기 → 제안치/추정치(각 도면에 '미표기' 표시): 각관 두께, □200·□300·핀용 BASE PL, 지붕 내부 하지, 유리 지지 프레임.",
        "3. 제작 전 구조계산 및 감리 승인 후 확정할 것.",
    ], h=2.5, gap=4.6)


sheet_keyplan()
sheet_roof()
sheet_plate()
sheet_roof_glass()
sheets_columns()
sheet_wall_glass()
sheet_footing()
sheet_bench()
sheet_misc()
sheet_drain()
sheet_bom()

doc.saveas(os.path.join(OUT, "조형파고라C_L655_부품도.dxf"))
with open(os.path.join(OUT, "조형파고라C_L655_부품일람표.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["부호", "품명", "규격", "재질", "수량", "단위길이(mm)", "비고"])
    for b in BOM:
        w.writerow([b["no"], b["name"], b["spec"], b["mat"], b["qty"], b["len"], b["remark"]])

# ---- PDF (시트별 A3 1페이지) ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, ColorPolicy, BackgroundPolicy, LineweightPolicy

from ezdxf import bbox as _bb


def _inside(e, x0, x1):
    b = _bb.extents([e], fast=True)
    return b.has_data and b.extmin.x >= x0 - 1 and b.extmax.x <= x1 + 1


cfg = Configuration(color_policy=ColorPolicy.BLACK, background_policy=BackgroundPolicy.WHITE,
                    lineweight_policy=LineweightPolicy.RELATIVE, min_lineweight=0.12)
os.makedirs(os.path.join(OUT, "png"), exist_ok=True)
with PdfPages(os.path.join(OUT, "조형파고라C_L655_부품도.pdf")) as pdf:
    for (no, title, x0, y0, x1, y1) in SHEETS:
        fig = plt.figure(figsize=(16.54, 11.69))
        ax = fig.add_axes([0, 0, 1, 1])
        ents = [e for e in msp if _inside(e, x0, x1)]
        Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_entities(ents)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect("equal")
        ax.axis("off")
        pdf.savefig(fig)
        fig.savefig(os.path.join(OUT, "png", f"PC-{no}.png"), dpi=110)
        plt.close(fig)
print("sheets:", len(SHEETS), "bom:", len(BOM))

import numpy as np
from nicegui import ui
import transforms as T
from geometry import Part

part = Part()
M0 = T.shift(60, 45)  # початкове положення деталі в першій чверті
M = M0           # матриця деталі
G = np.eye(3)    # матриця сітки й осей: змінюється лише афінними/проективними
view = {'half': 120}
fields = []  # (поле, значення за замовчуванням) — для кнопки «По замовчуванню»
resetting = False


def path(pts, close=False):
    return 'M' + ' L'.join(f'{x:.3f} {y:.3f}' for x, y in pts) + (' Z' if close else '')


def render(*_):
    h = view['half']
    grid, axes = [], []
    r = np.arange(-h, h + 1, 10)
    for v in r:  # лінії сітки — це відрізки, тож перетворюємо лише кінці
        for seg in ([[v, -h], [v, h]], [[-h, v], [h, v]]):
            grid.append(path(T.apply(seg, G)))
    for seg in ([[-h, 0], [h, 0]], [[0, -h], [0, h]]):
        axes.append(path(T.apply(seg, G)))
    shape = ' '.join(path(T.apply(c, M), True) for c in part.contours())
    (xl_x, xl_y), (yl_x, yl_y) = T.apply([[h * .93, -h * .05], [h * .03, h * .93]], G)  # підписи осей X, Y
    ctr = (cx.value or 0, cy.value or 0)  # центр обертання (екранні координати) — червона точка
    svg = (f'<svg viewBox="{-h} {-h} {2*h} {2*h}" style="width:100%;height:100vh;background:#fff">'
           f'<g transform="scale(1,-1)" fill="none">'
           f'<path d="{" ".join(grid)}" stroke="#ccc" stroke-width="1" vector-effect="non-scaling-stroke"/>'
           f'<path d="{" ".join(axes)}" stroke="#333" stroke-width="2" vector-effect="non-scaling-stroke"/>'
           f'<path d="{shape}" stroke="#000" stroke-width="2" fill-rule="evenodd" vector-effect="non-scaling-stroke"/>'
           f'<circle cx="{ctr[0]}" cy="{ctr[1]}" r="{h/80}" fill="#f00"/>'
           f'</g>'
           f'<g font-size="{h/18}" font-family="Arial" fill="#333">'
           f'<text x="{xl_x}" y="{-xl_y}">X</text><text x="{yl_x}" y="{-yl_y}">Y</text></g></svg>')
    canvas.set_content(svg)


def apply_m(m, coords=False):
    global M, G
    M = M @ m
    if coords:
        G = G @ m
    render()


def reset():
    global M, G, resetting
    M, G, resetting = M0, np.eye(3), True
    for f, v in fields:
        f.value = v
    resetting = False
    render()


def num(label, value, **kw):
    f = ui.number(label, value=value, **kw).props('dense outlined hide-bottom-space').classes('w-full')
    fields.append((f, value))
    return f


def on_size(*_):
    if resetting:
        return
    for k, f in size.items():
        setattr(part, k, f.value)
    try:
        render()
    except AssertionError as e:
        ui.notify(str(e), type='warning')


def group(title):
    c = ui.card().props('flat bordered').classes('w-full gap-2')
    with c:
        ui.label(title).classes('font-bold')
    return c


def fgrid(cols, *specs):
    with ui.grid(columns=cols).classes('w-full gap-2'):
        return [num(*s) for s in specs]


ui.query('.nicegui-content').classes('p-0 gap-0')
with ui.row().classes('w-full no-wrap gap-0'):
    canvas = ui.html('', sanitize=False).classes('flex-grow min-w-0')
    with ui.column().classes('w-[350px] shrink-0 h-screen overflow-auto p-3 gap-2 bg-grey-2'):
        with group('Параметри деталі (мм)'):
            specs = [('W', 'Ширина', 90), ('H', 'Висота', 60), ('R', 'Радіус дуги', 40),
                     ('hole_d', 'Діаметр отвору', 14), ('hole_x', 'Отвір x', 30), ('hole_y', 'Отвір y', 15),
                     ('sq', 'Квадратний виріз', 30)]
            size = {}
            with ui.grid(columns=2).classes('w-full gap-x-2 items-center'):
                for k, lbl, v in specs:
                    ui.label(lbl)
                    size[k] = num('', v, min=1, step=1)
                    size[k].on_value_change(on_size)
        ui.button('По замовчуванню', on_click=reset).classes('w-full')

        with ui.tabs().props('dense').classes('w-full') as tabs:
            t_euc, t_aff, t_proj = ui.tab('Евклідові'), ui.tab('Афінні'), ui.tab('Проективні')
        with ui.tab_panels(tabs, value=t_euc).classes('w-full bg-transparent'):
            with ui.tab_panel(t_euc).classes('p-0 gap-2'):
                with group('Зсув та Обертання'):
                    ui.label('Зсув').classes('font-bold')
                    dx, dy = fgrid(2, ('dx', 0), ('dy', 0))
                    ui.button('Застосувати зсув', on_click=lambda: apply_m(T.shift(dx.value, dy.value))).classes('w-full')
                    ui.label('Обертання').classes('font-bold')
                    ang, cx, cy = fgrid(3, ('Кут (°)', 45), ('Центр X', 70), ('Центр Y', 70))
                    cx.on_value_change(render), cy.on_value_change(render)
                    ui.button('Застосувати обертання', on_click=lambda: apply_m(T.rotate(cx.value, cy.value, ang.value))).classes('w-full')
                with group('Масштабування та Симетрія'):
                    sx_, sy_, scx, scy = fgrid(4, ('Sx', 1), ('Sy', 1), ('cx', 0), ('cy', 0))
                    ui.button('Масштабувати', on_click=lambda: apply_m(T.scale(scx.value, scy.value, sx_.value, sy_.value))).classes('w-full')
                    ui.button('Симетрія відносно (cx, cy)', on_click=lambda: apply_m(T.point_symmetry(scx.value, scy.value))).classes('w-full')
            with ui.tab_panel(t_aff).classes('p-0'):
                with group('Афінне перетворення'):
                    a = fgrid(2, ('Xx', 1), ('Xy', 0), ('Yx', 0), ('Yy', 1), ('0x', 0), ('0y', 0))
                    ui.button('Перетворити сцену', on_click=lambda: apply_m(T.affine(*[f.value for f in a]), True)).classes('w-full')
            with ui.tab_panel(t_proj).classes('p-0'):
                with group('Проективне перетворення'):
                    p = fgrid(3, ('Xx', 1), ('Xy', 0), ('wX', 0), ('Yx', 0), ('Yy', 1), ('wY', 0), ('0x', 0), ('0y', 0), ('w0', 1))
                    ui.button('Перетворити сцену', on_click=lambda: apply_m(T.projective(*[f.value for f in p]), True)).classes('w-full')
        half = num('Вид ±', 120, min=20, step=10)
        half.on_value_change(lambda e: (view.update(half=e.value), render()))

render()
ui.run(host='127.0.0.1', port=8080, show=False, reload=False, title='Lab1')

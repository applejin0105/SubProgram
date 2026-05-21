"""
Cultist Card Effects Editor (v2)
================================
새 스키마(cardsEffects.json: { "<cardId>": { "<trigger>": [<commands>] } })에 맞춰
재작성한 에디터.

설계 원칙
- 좌측: 카드 목록 (cardDB.json에서 이름/ID 로드 + 효과 보유 여부 표시)
- 우측: 선택된 카드의 트리거별 명령 트리. 더블 클릭으로 편집.
- 명령 편집은 schema-driven. 알려진 필드는 전용 위젯, 모르는 필드는 Raw JSON 박스로 폴백.
- 다형 값(amount/owner/from)은 모드 전환 콤보로 표현.
- If.then/else, Sacrifice.then 등 중첩 명령은 같은 CommandListDialog로 재귀 편집.

파일 경로
- 기본은 스크립트와 같은 폴더의 cardsEffects.json / cardDB.json.
- 메뉴에서 다른 경로로 열기/저장 가능.
"""

import copy
import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

# =====================================================================
# 스키마 정의 — 명령/조건 추가 시 이 섹션만 손대면 된다.
# =====================================================================

TRIGGERS = [
    "OnHand", "OnReveal", "OnRevealCost",
    "OnClick", "OnDestroyed", "RevealCondition", "Passive",
]

RESOURCES = ["influence", "unity", "monotheism", "polytheism", "strength", "pantheon", "cultist"]
SYMBOLS   = ["Influence", "Unity", "Monotheism", "Polytheism", "Strength", "Pantheon"]
STAT_KEYS = ["influence", "unity", "monotheism", "polytheism", "strength", "pantheon", "cultist"]
ZONES     = ["Field", "Hand", "Deck"]
COMPARE_OPS = [">", ">=", "<", "<=", "==", "!="]

# Phase target 문자열 (Phase 명령에서 사용)
PHASE_TARGETS = [
    "Phase.StandBy",
    "Phase.Draw.StandBy", "Phase.Draw.Draw", "Phase.Draw.Trade",
    "Phase.Play.Play",
]

# 히스토리 카운트에서 쓰는 액션 종류 (필요 시 자유롭게 추가)
HISTORY_ACTIONS = ["Trade", "Destroy", "Reveal", "Play", "Use", "Exile", "Sacrifice", "Draw"]

# 필드 타입 키워드 — 폼 빌더가 보고 위젯을 고른다.
#   int, str, bool, select, dynamicInt, amount, owner, from, filter,
#   condition, commands(=명령 배열), raw
COMMAND_SCHEMAS = {
    "Log": [
        ("msg", "str", "(no msg)"),
    ],
    "Get": [
        ("res", ("select", RESOURCES), "unity"),
        ("amount", "dynamicInt", 1),
    ],
    "Draw": [
        ("amount", "dynamicInt", 1),
        ("where", "filter", None),  # optional
    ],
    "Trade": [
        ("target", "owner", "Self"),
        ("amount", "dynamicInt", 1),
        ("starveIfFailed", "bool", False),
    ],
    "Starve": [
        ("target", "owner", "Self"),
        ("amount", "dynamicInt", 1),
    ],
    "Destroy": [
        ("from", "from", None),
        ("amount", "amount", 1),
        ("selectionType", ("select", ["Auto", "Manual"]), "Auto"),
        ("singleOwner", "bool", False),
        ("bind", "str", ""),
    ],
    "Exile": [
        ("from", "from", None),
        ("amount", "amount", 1),
        ("selectionType", ("select", ["Auto", "Manual"]), "Auto"),
        ("selectionController", ("select", ["Actor", "TargetPlayer"]), "Actor"),
        ("singleOwner", "bool", False),
        ("bind", "str", ""),
    ],
    "Sacrifice": [
        ("from", "from", None),
        ("amount", "dynamicInt", 1),
        ("selectionType", ("select", ["Auto", "Manual"]), "Manual"),
        ("bind", "str", ""),
        ("then", "commands", []),
    ],
    "Reveal": [
        ("from", "from", None),
        ("amount", "amount", 1),
        ("selectionType", ("select", ["Auto", "Manual"]), "Auto"),
    ],
    "Phase": [
        ("target", ("select", PHASE_TARGETS), "Phase.Draw.StandBy"),
        ("type", ("select", ["skip"]), "skip"),
    ],
    "SetNextDraw": [
        ("amount", "dynamicInt", 1),
        ("skipSelection", "bool", False),
        ("where", "filter", None),
    ],
    "AddTurnCycle": [
        ("amount", "int", 1),
    ],
    "If": [
        ("condition", "condition", None),
        ("then", "commands", []),
        ("else", "commands", []),
    ],
    "SetVar": [
        ("name", "str", "n"),
        ("value", "dynamicInt", 0),
    ],
    "Cancel": [],
}

CONDITION_SCHEMAS = {
    "HasSymbol": [
        ("symbol", ("select", SYMBOLS), "Strength"),
        ("amount", "int", 1),
        ("target", "owner", "Self"),
    ],
    "HasCultist": [
        ("amount", "int", 1),
        ("op", ("select", COMPARE_OPS), ">="),
        ("target", "owner", "Self"),
    ],
    "HasCard": [
        ("cardId", "int", 0),
        ("zone", ("select", ["Field", "Hand"]), "Field"),
        ("target", "owner", "Self"),
    ],
    "Compare": [
        ("lhs", "dynamicInt", 0),
        ("op", ("select", COMPARE_OPS), ">="),
        ("rhs", "dynamicInt", 0),
    ],
}

OWNER_TYPES = ["PlayerLowestStat", "PlayerHighestStat", "OpponentLowerStat", "OpponentHigherStat"]
OWNER_SIMPLE = ["Self", "All", "Opponent"]

DYNAMIC_INT_KINDS = ["int", "var", "cardCount", "playerStat", "historyCount"]
AMOUNT_KINDS      = ["int", "All", "range", "var", "cardCount", "playerStat", "historyCount"]


# =====================================================================
# 파일 IO
# =====================================================================

class Paths:
    """기본 파일 경로. 메뉴에서 갈아끼울 수 있다."""
    def __init__(self):
        base = os.path.dirname(os.path.abspath(__file__))
        self.effects = os.path.join(base, "cardsEffects.json")
        self.cardDB  = os.path.join(base, "cardDB.json")


def load_json(path, default):
    if not os.path.exists(path):
        return copy.deepcopy(default)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Load Error", f"{path}\n{e}")
        return copy.deepcopy(default)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =====================================================================
# 다형 값 위젯 — 모든 위젯이 동일하게 .get() / .set(value) 지원
# =====================================================================

class DynamicIntWidget:
    """정수 또는 { var | cardCount | playerStat | historyCount } 객체."""
    def __init__(self, parent, value=0):
        self.frame = ttk.Frame(parent)
        self.kind = tk.StringVar()
        self.cb_kind = ttk.Combobox(self.frame, textvariable=self.kind,
                                    values=DYNAMIC_INT_KINDS, width=11, state="readonly")
        self.cb_kind.pack(side="left")
        self.kind.trace_add("write", lambda *a: self._render())
        self.body = ttk.Frame(self.frame); self.body.pack(side="left", fill="x", expand=True)
        self.body_widgets = {}
        self.set(value)

    def pack(self, **kw): self.frame.pack(**kw)
    def grid(self, **kw): self.frame.grid(**kw)

    def _render(self):
        for w in self.body.winfo_children(): w.destroy()
        self.body_widgets = {}
        k = self.kind.get()
        if k == "int":
            v = tk.StringVar(value=str(self.body_widgets.get("_cached_int", 0)))
            e = ttk.Entry(self.body, textvariable=v, width=8); e.pack(side="left")
            self.body_widgets["int"] = v
        elif k == "var":
            v = tk.StringVar(value="n")
            ttk.Label(self.body, text="var=").pack(side="left")
            ttk.Entry(self.body, textvariable=v, width=10).pack(side="left")
            self.body_widgets["var"] = v
        elif k == "cardCount":
            ttk.Label(self.body, text="(from: ...)").pack(side="left")
            self.body_widgets["from"] = FromWidget(self.body, value=None)
            self.body_widgets["from"].pack(side="left", fill="x", expand=True)
        elif k == "playerStat":
            stat = tk.StringVar(value="strength")
            ttk.Label(self.body, text="stat=").pack(side="left")
            ttk.Combobox(self.body, textvariable=stat, values=STAT_KEYS, width=10).pack(side="left")
            self.body_widgets["stat"] = stat
        elif k == "historyCount":
            action = tk.StringVar(value="Trade")
            scope  = tk.StringVar(value="Turn")
            ttk.Label(self.body, text="action=").pack(side="left")
            ttk.Combobox(self.body, textvariable=action, values=HISTORY_ACTIONS, width=10).pack(side="left")
            ttk.Label(self.body, text="scope=").pack(side="left")
            ttk.Combobox(self.body, textvariable=scope, values=["Turn", "Round", "Game"], width=8).pack(side="left")
            self.body_widgets["action"] = action
            self.body_widgets["scope"]  = scope

    def get(self):
        k = self.kind.get()
        if k == "int":
            try: return int(self.body_widgets["int"].get())
            except ValueError: return 0
        if k == "var":
            return {"var": self.body_widgets["var"].get()}
        if k == "cardCount":
            return {"type": "cardCount", "from": self.body_widgets["from"].get()}
        if k == "playerStat":
            return {"type": "playerStat", "stat": self.body_widgets["stat"].get()}
        if k == "historyCount":
            return {"type": "historyCount",
                    "action": self.body_widgets["action"].get(),
                    "scope":  self.body_widgets["scope"].get()}
        return 0

    def set(self, value):
        if isinstance(value, bool) or isinstance(value, int):
            self.kind.set("int")
            self.body_widgets.setdefault("_cached_int", int(value))
            self._render()
            self.body_widgets["int"].set(str(int(value)))
            return
        if isinstance(value, dict):
            if "var" in value:
                self.kind.set("var"); self._render()
                self.body_widgets["var"].set(str(value["var"])); return
            t = value.get("type")
            if t == "cardCount":
                self.kind.set("cardCount"); self._render()
                self.body_widgets["from"].set(value.get("from")); return
            if t == "playerStat":
                self.kind.set("playerStat"); self._render()
                self.body_widgets["stat"].set(value.get("stat", "strength")); return
            if t == "historyCount":
                self.kind.set("historyCount"); self._render()
                self.body_widgets["action"].set(value.get("action", "Trade"))
                self.body_widgets["scope"].set(value.get("scope", "Turn")); return
        # fallback
        self.kind.set("int"); self._render()
        self.body_widgets["int"].set("0")


class AmountWidget:
    """amount 전용: int / "All" / {min,max} / dynamicInt 변형들."""
    def __init__(self, parent, value=1):
        self.frame = ttk.Frame(parent)
        self.kind = tk.StringVar()
        self.cb_kind = ttk.Combobox(self.frame, textvariable=self.kind,
                                    values=AMOUNT_KINDS, width=9, state="readonly")
        self.cb_kind.pack(side="left")
        self.kind.trace_add("write", lambda *a: self._render())
        self.body = ttk.Frame(self.frame); self.body.pack(side="left", fill="x", expand=True)
        self.body_widgets = {}
        self.set(value)

    def pack(self, **kw): self.frame.pack(**kw)
    def grid(self, **kw): self.frame.grid(**kw)

    def _render(self):
        for w in self.body.winfo_children(): w.destroy()
        self.body_widgets = {}
        k = self.kind.get()
        if k == "int":
            v = tk.StringVar(value="1")
            ttk.Entry(self.body, textvariable=v, width=6).pack(side="left")
            self.body_widgets["int"] = v
        elif k == "All":
            ttk.Label(self.body, text='(literal "All")').pack(side="left")
        elif k == "range":
            mn = tk.StringVar(value="0"); mx = tk.StringVar(value="1")
            ttk.Label(self.body, text="min=").pack(side="left")
            ttk.Entry(self.body, textvariable=mn, width=4).pack(side="left")
            ttk.Label(self.body, text="max=").pack(side="left")
            ttk.Entry(self.body, textvariable=mx, width=4).pack(side="left")
            self.body_widgets["min"] = mn
            self.body_widgets["max"] = mx
        else:
            # 나머지(var/cardCount/playerStat/historyCount)는 DynamicIntWidget 재활용
            dw = DynamicIntWidget(self.body, value=0)
            dw.kind.set(k); dw._render()
            dw.pack(side="left", fill="x", expand=True)
            self.body_widgets["dyn"] = dw

    def get(self):
        k = self.kind.get()
        if k == "int":
            try: return int(self.body_widgets["int"].get())
            except ValueError: return 0
        if k == "All":
            return "All"
        if k == "range":
            try: mn = int(self.body_widgets["min"].get())
            except ValueError: mn = 0
            try: mx = int(self.body_widgets["max"].get())
            except ValueError: mx = mn
            return {"min": mn, "max": mx}
        return self.body_widgets["dyn"].get()

    def set(self, value):
        if isinstance(value, str) and value.lower() == "all":
            self.kind.set("All"); self._render(); return
        if isinstance(value, dict) and ("min" in value or "max" in value):
            self.kind.set("range"); self._render()
            self.body_widgets["min"].set(str(value.get("min", 0)))
            self.body_widgets["max"].set(str(value.get("max", 1)))
            return
        if isinstance(value, dict):
            # dynamicInt 변형으로 위임
            if "var" in value: self.kind.set("var")
            elif value.get("type") == "cardCount":    self.kind.set("cardCount")
            elif value.get("type") == "playerStat":   self.kind.set("playerStat")
            elif value.get("type") == "historyCount": self.kind.set("historyCount")
            else: self.kind.set("int")
            self._render()
            if "dyn" in self.body_widgets:
                self.body_widgets["dyn"].set(value)
            return
        # int
        self.kind.set("int"); self._render()
        try: self.body_widgets["int"].set(str(int(value)))
        except Exception: self.body_widgets["int"].set("0")


class OwnerWidget:
    """Self / All / Opponent / 통계 기반 객체 / { var }."""
    def __init__(self, parent, value="Self"):
        self.frame = ttk.Frame(parent)
        self.kind = tk.StringVar()
        kinds = OWNER_SIMPLE + OWNER_TYPES + ["var"]
        self.cb = ttk.Combobox(self.frame, textvariable=self.kind, values=kinds, width=18, state="readonly")
        self.cb.pack(side="left")
        self.kind.trace_add("write", lambda *a: self._render())
        self.body = ttk.Frame(self.frame); self.body.pack(side="left", fill="x", expand=True)
        self.body_widgets = {}
        self.set(value)

    def pack(self, **kw): self.frame.pack(**kw)
    def grid(self, **kw): self.frame.grid(**kw)

    def _render(self):
        for w in self.body.winfo_children(): w.destroy()
        self.body_widgets = {}
        k = self.kind.get()
        if k in OWNER_TYPES:
            stat = tk.StringVar(value="strength")
            ttk.Label(self.body, text="stat=").pack(side="left")
            ttk.Combobox(self.body, textvariable=stat, values=STAT_KEYS, width=10).pack(side="left")
            self.body_widgets["stat"] = stat
        elif k == "var":
            v = tk.StringVar(value="targetP")
            ttk.Label(self.body, text="var=").pack(side="left")
            ttk.Entry(self.body, textvariable=v, width=10).pack(side="left")
            self.body_widgets["var"] = v

    def get(self):
        k = self.kind.get()
        if k in OWNER_SIMPLE: return k
        if k in OWNER_TYPES:  return {"type": k, "stat": self.body_widgets["stat"].get()}
        if k == "var":        return {"var": self.body_widgets["var"].get()}
        return "Self"

    def set(self, value):
        if value is None:
            self.kind.set("Self"); self._render(); return
        if isinstance(value, str):
            self.kind.set(value if value in OWNER_SIMPLE else "Self")
            self._render(); return
        if isinstance(value, dict):
            if "var" in value:
                self.kind.set("var"); self._render()
                self.body_widgets["var"].set(str(value["var"])); return
            t = value.get("type")
            if t in OWNER_TYPES:
                self.kind.set(t); self._render()
                self.body_widgets["stat"].set(value.get("stat", "strength")); return
        self.kind.set("Self"); self._render()


class FilterWidget:
    """필터 객체. 잘 알려진 필드 + Raw JSON 폴백."""
    KNOWN_BOOLS = ["isCultistCard", "isRevealed", "inSect", "inSectOfCause"]

    def __init__(self, parent, value=None):
        self.frame = ttk.LabelFrame(parent, text="filter")
        self.bool_vars = {k: tk.BooleanVar(value=False) for k in self.KNOWN_BOOLS}
        for k, var in self.bool_vars.items():
            ttk.Checkbutton(self.frame, text=k, variable=var).pack(anchor="w")

        row = ttk.Frame(self.frame); row.pack(fill="x", pady=2)
        ttk.Label(row, text="cardIds (쉼표):").pack(side="left")
        self.var_cardIds = tk.StringVar(value="")
        ttk.Entry(row, textvariable=self.var_cardIds, width=20).pack(side="left")

        row2 = ttk.Frame(self.frame); row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="cultist op/val:").pack(side="left")
        self.var_cult_op = tk.StringVar(value="")
        ttk.Combobox(row2, textvariable=self.var_cult_op,
                     values=[""] + COMPARE_OPS, width=4).pack(side="left")
        self.var_cult_val = tk.StringVar(value="")
        ttk.Entry(row2, textvariable=self.var_cult_val, width=6).pack(side="left")

        ttk.Label(self.frame, text="extra (raw JSON, 옵션):").pack(anchor="w")
        self.txt_extra = tk.Text(self.frame, height=3, width=30)
        self.txt_extra.pack(fill="x")
        self.set(value)

    def pack(self, **kw): self.frame.pack(**kw)
    def grid(self, **kw): self.frame.grid(**kw)

    def get(self):
        out = {}
        for k, var in self.bool_vars.items():
            if var.get(): out[k] = True
        ids_str = self.var_cardIds.get().strip()
        if ids_str:
            try:
                out["cardIds"] = [int(x) for x in ids_str.split(",") if x.strip()]
            except ValueError:
                pass
        op = self.var_cult_op.get().strip()
        val = self.var_cult_val.get().strip()
        if op and val:
            try: out["cultist"] = {"op": op, "value": int(val)}
            except ValueError: pass
        elif val:
            try: out["cultist"] = int(val)
            except ValueError: pass
        extra = self.txt_extra.get("1.0", tk.END).strip()
        if extra:
            try:
                merged = json.loads(extra)
                if isinstance(merged, dict):
                    for k, v in merged.items():
                        out.setdefault(k, v)
            except Exception:
                pass
        return out or None

    def set(self, value):
        for var in self.bool_vars.values(): var.set(False)
        self.var_cardIds.set("")
        self.var_cult_op.set("")
        self.var_cult_val.set("")
        self.txt_extra.delete("1.0", tk.END)
        if not isinstance(value, dict): return
        leftover = {}
        for k, v in value.items():
            if k in self.bool_vars:
                self.bool_vars[k].set(bool(v))
            elif k == "cardIds" and isinstance(v, list):
                self.var_cardIds.set(",".join(str(x) for x in v))
            elif k == "cultist":
                if isinstance(v, dict):
                    self.var_cult_op.set(v.get("op", ""))
                    self.var_cult_val.set(str(v.get("value", "")))
                else:
                    self.var_cult_val.set(str(v))
            else:
                leftover[k] = v
        if leftover:
            self.txt_extra.insert("1.0", json.dumps(leftover, ensure_ascii=False, indent=2))


class FromWidget:
    """{ owner, zone, filter } 복합 위젯."""
    def __init__(self, parent, value=None):
        self.frame = ttk.LabelFrame(parent, text="from")

        row1 = ttk.Frame(self.frame); row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="owner:").pack(side="left")
        self.owner = OwnerWidget(row1, value="Self")
        self.owner.pack(side="left", fill="x", expand=True)

        row2 = ttk.Frame(self.frame); row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="zone:").pack(side="left")
        self.var_zone = tk.StringVar(value="Field")
        ttk.Combobox(row2, textvariable=self.var_zone, values=ZONES, width=8, state="readonly").pack(side="left")

        self.filter = FilterWidget(self.frame, value=None)
        self.filter.pack(fill="x")

        self.set(value)

    def pack(self, **kw): self.frame.pack(**kw)
    def grid(self, **kw): self.frame.grid(**kw)

    def get(self):
        out = {"owner": self.owner.get(), "zone": self.var_zone.get()}
        f = self.filter.get()
        if f: out["filter"] = f
        return out

    def set(self, value):
        if not isinstance(value, dict):
            self.owner.set("Self"); self.var_zone.set("Field"); self.filter.set(None); return
        self.owner.set(value.get("owner", "Self"))
        self.var_zone.set(value.get("zone", "Field"))
        self.filter.set(value.get("filter"))


# =====================================================================
# 조건 / 명령 편집 다이얼로그
# =====================================================================

class ConditionWidget:
    """If.condition 객체. 타입 콤보 + 타입별 폼."""
    def __init__(self, parent, value=None):
        self.frame = ttk.LabelFrame(parent, text="condition")
        head = ttk.Frame(self.frame); head.pack(fill="x")
        ttk.Label(head, text="type:").pack(side="left")
        self.var_type = tk.StringVar()
        self.cb_type = ttk.Combobox(head, textvariable=self.var_type,
                                    values=list(CONDITION_SCHEMAS.keys()), state="readonly", width=14)
        self.cb_type.pack(side="left")
        self.body = ttk.Frame(self.frame); self.body.pack(fill="x")
        self.var_type.trace_add("write", lambda *a: self._render())
        self.fields = {}
        self.set(value)

    def pack(self, **kw): self.frame.pack(**kw)
    def grid(self, **kw): self.frame.grid(**kw)

    def _render(self):
        for w in self.body.winfo_children(): w.destroy()
        self.fields = {}
        schema = CONDITION_SCHEMAS.get(self.var_type.get(), [])
        for name, ftype, default in schema:
            row = ttk.Frame(self.body); row.pack(fill="x", pady=1)
            ttk.Label(row, text=f"{name}:", width=10).pack(side="left")
            w = _build_field_widget(row, ftype, default)
            w.pack(side="left", fill="x", expand=True)
            self.fields[name] = (w, ftype)

    def get(self):
        out = {"type": self.var_type.get()}
        for name, (w, ftype) in self.fields.items():
            out[name] = _read_field(w, ftype)
        return out

    def set(self, value):
        if isinstance(value, dict) and "type" in value and value["type"] in CONDITION_SCHEMAS:
            self.var_type.set(value["type"])
            self._render()
            for name, (w, ftype) in self.fields.items():
                if name in value:
                    _write_field(w, ftype, value[name])
        else:
            self.var_type.set("Compare")


# ---- 폼 빌더 헬퍼 ----

def _build_field_widget(parent, ftype, default):
    if ftype == "int":
        v = tk.StringVar(value=str(default if default is not None else 0))
        e = ttk.Entry(parent, textvariable=v, width=10); e._var = v; e._kind = "int"
        return e
    if ftype == "str":
        v = tk.StringVar(value=str(default or ""))
        e = ttk.Entry(parent, textvariable=v); e._var = v; e._kind = "str"
        return e
    if ftype == "bool":
        v = tk.BooleanVar(value=bool(default))
        c = ttk.Checkbutton(parent, variable=v); c._var = v; c._kind = "bool"
        return c
    if isinstance(ftype, tuple) and ftype[0] == "select":
        v = tk.StringVar(value=str(default or (ftype[1][0] if ftype[1] else "")))
        cb = ttk.Combobox(parent, textvariable=v, values=ftype[1], state="readonly", width=14)
        cb._var = v; cb._kind = "select"; return cb
    if ftype == "dynamicInt":
        return DynamicIntWidget(parent, value=default if default is not None else 0)
    if ftype == "amount":
        return AmountWidget(parent, value=default if default is not None else 1)
    if ftype == "owner":
        return OwnerWidget(parent, value=default or "Self")
    if ftype == "from":
        return FromWidget(parent, value=default)
    if ftype == "filter":
        return FilterWidget(parent, value=default)
    if ftype == "condition":
        return ConditionWidget(parent, value=default)
    if ftype == "commands":
        return CommandListField(parent, value=default or [])
    # fallback: Raw JSON entry
    v = tk.StringVar(value=json.dumps(default) if default is not None else "")
    e = ttk.Entry(parent, textvariable=v); e._var = v; e._kind = "raw"
    return e


def _read_field(widget, ftype):
    if hasattr(widget, "_kind"):
        if widget._kind == "int":
            try: return int(widget._var.get())
            except ValueError: return 0
        if widget._kind == "str":   return widget._var.get()
        if widget._kind == "bool":  return bool(widget._var.get())
        if widget._kind == "select":return widget._var.get()
        if widget._kind == "raw":
            s = widget._var.get().strip()
            if not s: return None
            try: return json.loads(s)
            except Exception: return s
    return widget.get()


def _write_field(widget, ftype, value):
    if hasattr(widget, "_kind"):
        if widget._kind in ("int", "str", "select"):
            widget._var.set("" if value is None else str(value)); return
        if widget._kind == "bool":
            widget._var.set(bool(value)); return
        if widget._kind == "raw":
            widget._var.set("" if value is None else json.dumps(value, ensure_ascii=False)); return
    widget.set(value)


class CommandListField:
    """명령 배열을 다루는 필드. 버튼을 누르면 CommandListDialog가 뜬다."""
    def __init__(self, parent, value=None):
        self.frame = ttk.Frame(parent)
        self.data = list(value or [])
        self.lbl = ttk.Label(self.frame, text=self._summary())
        self.lbl.pack(side="left", padx=5)
        ttk.Button(self.frame, text="Edit...", command=self._open).pack(side="left")

    def pack(self, **kw): self.frame.pack(**kw)
    def grid(self, **kw): self.frame.grid(**kw)

    def _summary(self):
        n = len(self.data)
        if n == 0: return "(empty)"
        names = ", ".join(c.get("cmd", "?") for c in self.data[:3])
        more = f" +{n-3}" if n > 3 else ""
        return f"{n}개: {names}{more}"

    def _open(self):
        CommandListDialog(self.frame, self.data, self._on_save)

    def _on_save(self, new_list):
        self.data = new_list
        self.lbl.config(text=self._summary())

    def get(self):  return list(self.data)
    def set(self, value):
        self.data = list(value or [])
        self.lbl.config(text=self._summary())


# =====================================================================
# 명령 편집 다이얼로그 (단일 명령 하나)
# =====================================================================

class CommandDialog:
    def __init__(self, parent, data, on_save):
        self.on_save = on_save
        self.win = tk.Toplevel(parent)
        self.win.title("Command")
        self.win.geometry("640x600")
        self.original = copy.deepcopy(data) if data else {}

        head = ttk.Frame(self.win); head.pack(fill="x", padx=8, pady=5)
        ttk.Label(head, text="cmd:").pack(side="left")
        self.var_cmd = tk.StringVar(value=self.original.get("cmd", "Log"))
        self.cb = ttk.Combobox(head, textvariable=self.var_cmd,
                               values=list(COMMAND_SCHEMAS.keys()), state="readonly", width=18)
        self.cb.pack(side="left")
        self.var_cmd.trace_add("write", lambda *a: self._render())

        self.body = ttk.Frame(self.win); self.body.pack(fill="both", expand=True, padx=8, pady=5)
        self.fields = {}

        # 알려지지 않은 필드는 Raw JSON 탭으로
        ttk.Label(self.win, text="Unknown fields (raw JSON):").pack(anchor="w", padx=8)
        self.txt_extra = tk.Text(self.win, height=4)
        self.txt_extra.pack(fill="x", padx=8)

        btns = ttk.Frame(self.win); btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Save", command=self._save).pack(side="right", padx=8)
        ttk.Button(btns, text="Cancel", command=self.win.destroy).pack(side="right")

        self._render()

    def _render(self):
        for w in self.body.winfo_children(): w.destroy()
        self.fields = {}
        cmd = self.var_cmd.get()
        schema = COMMAND_SCHEMAS.get(cmd, [])

        # 알려진 필드명 집합으로 leftover 분리
        known = {n for n, _, _ in schema}

        for name, ftype, default in schema:
            row = ttk.Frame(self.body); row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"{name}:", width=14).pack(side="left", anchor="n")
            val = self.original.get(name, default)
            w = _build_field_widget(row, ftype, val)
            w.pack(side="left", fill="x", expand=True)
            # 기존 값 주입 (build_field_widget이 default로 받았으므로 set 한 번 더)
            if name in self.original:
                _write_field(w, ftype, self.original[name])
            self.fields[name] = (w, ftype)

        # leftover → 텍스트 박스
        leftover = {k: v for k, v in self.original.items()
                    if k != "cmd" and k not in known}
        self.txt_extra.delete("1.0", tk.END)
        if leftover:
            self.txt_extra.insert("1.0", json.dumps(leftover, ensure_ascii=False, indent=2))

    def _save(self):
        out = {"cmd": self.var_cmd.get()}
        for name, (w, ftype) in self.fields.items():
            val = _read_field(w, ftype)
            # 빈 문자열/None/빈 컬렉션은 옵션으로 보고 누락
            if val is None: continue
            if isinstance(val, str) and val == "": continue
            if isinstance(val, list) and len(val) == 0: continue
            if isinstance(val, dict) and len(val) == 0: continue
            out[name] = val

        extra_txt = self.txt_extra.get("1.0", tk.END).strip()
        if extra_txt:
            try:
                extra = json.loads(extra_txt)
                if isinstance(extra, dict):
                    for k, v in extra.items():
                        out.setdefault(k, v)
            except Exception as e:
                messagebox.showerror("Raw JSON error", str(e)); return

        self.on_save(out)
        self.win.destroy()


# =====================================================================
# 명령 리스트 다이얼로그 (트리거 안의 명령 배열)
# =====================================================================

class CommandListDialog:
    def __init__(self, parent, data_list, on_save, title="Commands"):
        self.on_save = on_save
        self.data = copy.deepcopy(data_list)
        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.geometry("500x400")

        self.lst = tk.Listbox(self.win)
        self.lst.pack(fill="both", expand=True, padx=6, pady=6)
        self.lst.bind("<Double-1>", lambda e: self._edit())

        bf = ttk.Frame(self.win); bf.pack(fill="x", padx=6)
        ttk.Button(bf, text="Add",    command=self._add).pack(side="left")
        ttk.Button(bf, text="Edit",   command=self._edit).pack(side="left")
        ttk.Button(bf, text="Up",     command=lambda: self._move(-1)).pack(side="left")
        ttk.Button(bf, text="Down",   command=lambda: self._move(+1)).pack(side="left")
        ttk.Button(bf, text="Remove", command=self._remove).pack(side="left")

        ok = ttk.Frame(self.win); ok.pack(fill="x", pady=6)
        ttk.Button(ok, text="OK",     command=self._ok).pack(side="right", padx=6)
        ttk.Button(ok, text="Cancel", command=self.win.destroy).pack(side="right")
        self._refresh()

    def _refresh(self):
        self.lst.delete(0, tk.END)
        for c in self.data:
            label = c.get("cmd", "?")
            short = ""
            if "amount" in c: short += f" amount={_short(c['amount'])}"
            if "res"    in c: short += f" res={c['res']}"
            if "from"   in c and isinstance(c["from"], dict):
                short += f" owner={_short(c['from'].get('owner'))}"
                short += f" zone={c['from'].get('zone')}"
            self.lst.insert(tk.END, f"{label}{short}")

    def _selected(self):
        sel = self.lst.curselection()
        return sel[0] if sel else None

    def _add(self):
        CommandDialog(self.win, {}, lambda d: (self.data.append(d), self._refresh()))

    def _edit(self):
        idx = self._selected()
        if idx is None: return
        CommandDialog(self.win, self.data[idx], lambda d: (self.data.__setitem__(idx, d), self._refresh()))

    def _remove(self):
        idx = self._selected()
        if idx is None: return
        del self.data[idx]; self._refresh()

    def _move(self, dx):
        idx = self._selected()
        if idx is None: return
        j = idx + dx
        if 0 <= j < len(self.data):
            self.data[idx], self.data[j] = self.data[j], self.data[idx]
            self._refresh()
            self.lst.selection_set(j)

    def _ok(self):
        self.on_save(self.data); self.win.destroy()


def _short(v, n=14):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    return s if len(s) <= n else s[:n] + "…"


# =====================================================================
# 메인 앱
# =====================================================================

class EffectsEditorApp:
    def __init__(self, root):
        self.root = root
        self.paths = Paths()
        self.effects = {}    # { "cardId": { "trigger": [commands] } }
        self.cards = {}      # { int_id: name }
        self.selected_id = None

        root.title("Cultist Effects Editor v2")
        root.geometry("1280x760")

        self._build_menu()
        self._build_ui()
        self._load_files()

    # ---- 메뉴 ----
    def _build_menu(self):
        m = tk.Menu(self.root); self.root.config(menu=m)
        fm = tk.Menu(m, tearoff=0); m.add_cascade(label="File", menu=fm)
        fm.add_command(label="Reload",         command=self._load_files)
        fm.add_command(label="Save effects",   command=self._save_effects)
        fm.add_separator()
        fm.add_command(label="Open effects.json...", command=self._pick_effects)
        fm.add_command(label="Open cardDB.json...",  command=self._pick_carddb)

    def _pick_effects(self):
        p = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if p: self.paths.effects = p; self._load_files()

    def _pick_carddb(self):
        p = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if p: self.paths.cardDB = p; self._load_files()

    # ---- UI ----
    def _build_ui(self):
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        # 왼쪽: 카드 목록
        left = ttk.Frame(paned); paned.add(left, width=320)
        ttk.Label(left, text="Cards (★=효과 있음)").pack(anchor="w", padx=4)

        self.var_search = tk.StringVar()
        sf = ttk.Frame(left); sf.pack(fill="x", padx=4)
        ttk.Label(sf, text="🔍").pack(side="left")
        ttk.Entry(sf, textvariable=self.var_search).pack(side="left", fill="x", expand=True)
        self.var_search.trace_add("write", lambda *a: self._refresh_card_list())

        self.tv = ttk.Treeview(left, columns=("id", "name", "has"), show="headings")
        for col, t, w in [("id", "ID", 60), ("name", "Name", 180), ("has", "FX", 40)]:
            self.tv.heading(col, text=t); self.tv.column(col, width=w, anchor="w")
        self.tv.pack(fill="both", expand=True)
        self.tv.bind("<<TreeviewSelect>>", self._on_card_selected)

        # 오른쪽: 트리거 + 명령
        right = ttk.Frame(paned); paned.add(right)
        self.lbl_card = ttk.Label(right, text="(카드를 선택하세요)", font=("Arial", 12, "bold"))
        self.lbl_card.pack(anchor="w", padx=8, pady=4)

        self.notebook = ttk.Notebook(right); self.notebook.pack(fill="both", expand=True, padx=6)
        self.trigger_pages = {}      # trigger -> {frame, listbox}

        for trig in TRIGGERS:
            page = ttk.Frame(self.notebook)
            self.notebook.add(page, text=trig)

            lst = tk.Listbox(page); lst.pack(fill="both", expand=True, padx=4, pady=4)
            lst.bind("<Double-1>", lambda e, t=trig: self._edit_command(t))

            bf = ttk.Frame(page); bf.pack(fill="x", padx=4)
            ttk.Button(bf, text="Add",    command=lambda t=trig: self._add_command(t)).pack(side="left")
            ttk.Button(bf, text="Edit",   command=lambda t=trig: self._edit_command(t)).pack(side="left")
            ttk.Button(bf, text="Up",     command=lambda t=trig: self._move_command(t, -1)).pack(side="left")
            ttk.Button(bf, text="Down",   command=lambda t=trig: self._move_command(t, +1)).pack(side="left")
            ttk.Button(bf, text="Remove", command=lambda t=trig: self._remove_command(t)).pack(side="left")
            ttk.Button(bf, text="Clear trigger", command=lambda t=trig: self._clear_trigger(t)).pack(side="right")

            self.trigger_pages[trig] = {"lst": lst}

        save_bar = ttk.Frame(right); save_bar.pack(fill="x", pady=6)
        ttk.Button(save_bar, text="SAVE EFFECTS",
                   command=self._save_effects).pack(side="right", padx=8)

    # ---- 파일 로딩 ----
    def _load_files(self):
        self.cards   = {}
        card_data = load_json(self.paths.cardDB, {"cards": []})
        for c in card_data.get("cards", []):
            try: self.cards[int(c["id"])] = c.get("name", f"Card {c['id']}")
            except Exception: pass

        self.effects = load_json(self.paths.effects, {})
        # cardId 키는 문자열로 유지 (JSON 표준)
        # 카드 목록에 없는 cardId가 있다면 함께 보이도록 함
        self._refresh_card_list()

    def _save_effects(self):
        try:
            save_json(self.paths.effects, self.effects)
            messagebox.showinfo("Saved", f"{self.paths.effects}\n저장 완료")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    # ---- 카드 리스트 ----
    def _refresh_card_list(self):
        for it in self.tv.get_children(): self.tv.delete(it)
        q = self.var_search.get().strip().lower()
        # 카드DB + 효과에만 존재하는 cardId 합집합
        ids = set(self.cards.keys())
        for k in self.effects.keys():
            try: ids.add(int(k))
            except ValueError: pass
        for cid in sorted(ids):
            name = self.cards.get(cid, "(unknown)")
            has = "★" if str(cid) in self.effects else ""
            if q and q not in str(cid) and q not in name.lower():
                continue
            self.tv.insert("", "end", iid=str(cid), values=(cid, name, has))

    def _on_card_selected(self, _e=None):
        sel = self.tv.selection()
        if not sel: return
        cid = sel[0]
        self.selected_id = cid
        name = self.cards.get(int(cid), "(unknown)")
        self.lbl_card.config(text=f"[{cid}] {name}")
        self._refresh_all_triggers()

    # ---- 트리거 편집 ----
    def _refresh_all_triggers(self):
        if self.selected_id is None: return
        card_fx = self.effects.get(self.selected_id, {})
        for trig, page in self.trigger_pages.items():
            page["lst"].delete(0, tk.END)
            for cmd in card_fx.get(trig, []):
                page["lst"].insert(tk.END, self._summarize_cmd(cmd))

    def _summarize_cmd(self, cmd):
        if not isinstance(cmd, dict): return str(cmd)
        # RevealCondition은 condition 객체가 직접 들어감 (cmd가 없음)
        if "cmd" not in cmd and "type" in cmd:
            return f"Cond:{cmd['type']} {_short(cmd, 60)}"
        s = cmd.get("cmd", "?")
        extras = []
        for k in ("res", "amount", "target", "selectionType"):
            if k in cmd: extras.append(f"{k}={_short(cmd[k])}")
        return s + (" | " + ", ".join(extras) if extras else "")

    def _get_trigger_list(self, trig):
        if self.selected_id is None: return None
        card_fx = self.effects.setdefault(self.selected_id, {})
        return card_fx.setdefault(trig, [])

    def _add_command(self, trig):
        lst = self._get_trigger_list(trig)
        if lst is None: return
        # RevealCondition은 condition 객체 직접 추가
        if trig == "RevealCondition":
            def _save(d): lst.append(d); self._refresh_all_triggers(); self._refresh_card_list()
            ConditionDialog(self.root, {}, _save); return
        CommandDialog(self.root, {}, lambda d: (lst.append(d),
                                                self._refresh_all_triggers(),
                                                self._refresh_card_list()))

    def _edit_command(self, trig):
        lst = self._get_trigger_list(trig)
        if lst is None: return
        sel = self.trigger_pages[trig]["lst"].curselection()
        if not sel: return
        idx = sel[0]
        if trig == "RevealCondition":
            def _save(d): lst[idx] = d; self._refresh_all_triggers()
            ConditionDialog(self.root, lst[idx], _save); return
        CommandDialog(self.root, lst[idx],
                      lambda d: (lst.__setitem__(idx, d), self._refresh_all_triggers()))

    def _remove_command(self, trig):
        lst = self._get_trigger_list(trig)
        if lst is None: return
        sel = self.trigger_pages[trig]["lst"].curselection()
        if not sel: return
        del lst[sel[0]]
        if not lst:
            self.effects[self.selected_id].pop(trig, None)
            if not self.effects[self.selected_id]:
                self.effects.pop(self.selected_id, None)
        self._refresh_all_triggers()
        self._refresh_card_list()

    def _move_command(self, trig, dx):
        lst = self._get_trigger_list(trig)
        if lst is None: return
        sel = self.trigger_pages[trig]["lst"].curselection()
        if not sel: return
        i = sel[0]; j = i + dx
        if 0 <= j < len(lst):
            lst[i], lst[j] = lst[j], lst[i]
            self._refresh_all_triggers()
            self.trigger_pages[trig]["lst"].selection_set(j)

    def _clear_trigger(self, trig):
        if self.selected_id is None: return
        if self.selected_id not in self.effects: return
        if trig not in self.effects[self.selected_id]: return
        if not messagebox.askyesno("Clear", f"{trig} 전체를 비울까요?"): return
        self.effects[self.selected_id].pop(trig, None)
        if not self.effects[self.selected_id]:
            self.effects.pop(self.selected_id, None)
        self._refresh_all_triggers()
        self._refresh_card_list()


class ConditionDialog:
    """RevealCondition 트리거가 condition 객체를 직접 담기에 별도 다이얼로그."""
    def __init__(self, parent, data, on_save):
        self.on_save = on_save
        self.win = tk.Toplevel(parent)
        self.win.title("Condition")
        self.win.geometry("520x420")

        self.cond = ConditionWidget(self.win, value=data); self.cond.pack(fill="both", expand=True, padx=8, pady=8)

        bf = ttk.Frame(self.win); bf.pack(fill="x", pady=6)
        ttk.Button(bf, text="Save", command=self._save).pack(side="right", padx=6)
        ttk.Button(bf, text="Cancel", command=self.win.destroy).pack(side="right")

    def _save(self):
        self.on_save(self.cond.get()); self.win.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    EffectsEditorApp(root)
    root.mainloop()

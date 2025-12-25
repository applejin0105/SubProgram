import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import copy

# === 파일 설정 ===
EFFECTS_FILE = "effects.json"
DB_FILE = "cardDatabase.json"
CONFIG_FILE = "schema_config_v8.json"

# === 데이터 정의 ===
RESOURCE_LIST = ["Influence", "Unity", "Monotheism", "Polytheism", "Strength", "Pantheon", "Cultist", "MessiahIdeology"]
PHASE_ENUMS = [
    "GameStart", "Draft.Draw", "Main.StandBy", "Main.Draw", "Main.Play", "Main.Reveal", 
    "Flip", "EnterPlay", "Destroyed", "DestroyAttempt", "AnyTime"
]

# === 기본 스키마 ===
DEFAULT_CONFIG = {
    "Kinds": ["trigger", "replacement", "constraint", "continuous", "activated", "requirement"],
    "Timings": ["OnGameStart", "OnFlip", "OnPlay", "OnPreDestroy", "OnRevealInHand", "OnActivate", "OnTryFlip", "OnTurnEnd", "AnyTime"],
    
    "ConditionTypes": {
        "CompareValue": {"fields": ["valueSource", "operator", "threshold"]},
        "CheckHistory": {"fields": ["historyTarget", "period", "minCount"]},
        "SourceIsEnemy": {"fields": []},
        "Limit_FaceUpCount": {"fields": ["limit", "scope"]}
    },

    "ActionTypes": {
        "Debug_CrashGame": {"fields": ["message"]},
        "Phase_Skip": {"fields": ["phaseName"]},
        "Phase_Add": {"fields": ["phaseName", "amount"]},
        "Card_SearchAndAdd": {"fields": ["searchSource", "searchFilter", "amount", "selectionType"]},
        "Force_Select": {"fields": ["target_fixed"]},
        "Card_Exile": {"fields": ["exileTarget", "targetCardType", "amount"]},
        "Card_Destroy": {"fields": ["targetPlayer", "targetCardType", "amount", "selectionType"]},
        "Resource_Gain": {"fields": ["resourceType", "amount"]},
        "Resource_Gain_Dynamic": {"fields": ["resourceType", "perCount"]},
        "Action_Trade": {"fields": ["amount"]},
        "Card_Flip": {"fields": ["target_fixed"]},
        "Cancel_Event": {"fields": []},
        "Condition_Fail_Check": {"fields": ["nested_actions"]},
        "Conditional": {"fields": ["condition_custom", "nested_actions"]},
        "Add_Starve": {"fields": ["starveTarget", "amount"]},
        "Allow_Flip": {"fields": []},
        "Card_Draw": {"fields": ["drawSource", "amount"]}
    },

    "FieldDefinitions": {
        # --- 기본 타입 ---
        "amount": {"type": "int", "default": 1},
        "threshold": {"type": "int", "default": 0},
        "minCount": {"type": "int", "default": 1},
        "limit": {"type": "int", "default": 1},
        "message": {"type": "string", "default": "Error"},
        "perCount": {"type": "string", "default": "MessiahIdeology"},
        
        # --- 선택형 ---
        "phaseName": {"type": "selection_custom", "values": PHASE_ENUMS, "default": "Draft.Draw"},
        "resourceType": {"type": "selection_custom", "values": RESOURCE_LIST, "default": "Influence"},
        "searchSource": {"type": "selection_custom", "values": ["Deck", "Trade"], "default": "Deck"},
        "searchFilter": {"type": "selection_custom", "values": RESOURCE_LIST, "default": "Cultist"},
        "selectionType": {"type": "selection_custom", "values": ["Essential", "Optional"], "default": "Essential"},
        "targetCardType": {"type": "selection_custom", "values": ["Cultist", "TargetCard"], "default": "Cultist"},
        "drawSource": {"type": "selection_custom", "values": ["Deck", "Trade"], "default": "Deck"},
        "starveTarget": {"type": "selection_custom", "values": ["Self", "Other"], "default": "Self"},
        "valueSource": {"type": "selection_custom", "values": RESOURCE_LIST, "default": "MessiahIdeology"},
        "operator": {"type": "selection", "values": [">", ">=", "<", "<=", "==", "!="], "default": ">="},
        "period": {"type": "selection", "values": ["ThisTurn", "LastTurn"], "default": "ThisTurn"},
        "historyTarget": {"type": "selection_custom", "values": ["Trade", "DestroyEnemyCard"], "default": "Trade"},

        "target_fixed": {"type": "fixed", "value": "Self", "save_key": "target"},
        
        "targetPlayer": {
            "type": "stat_comparison", 
            "parts": [["Lower", "Higher", "Equal", "Sacrifice"], RESOURCE_LIST + ["Strength"]],
            "default": "LowerStrength"
        },
        
        # [요청 1] AllPlayers 추가 및 로직 확장
        "exileTarget": {
            "type": "exile_mode_selector",
            "modes": ["CanSelectTarget", "CantSelectTarget", "AllPlayers"],
            "comparators": ["Lowest", "Highest", "Lower", "Higher", "Equal"],
            "stats": RESOURCE_LIST + ["Strength"],
            "default": "CanSelectTarget"
        },
        
        "nested_actions": {"type": "action_list", "save_key": "nested_actions"},
        "condition_custom": {"type": "condition_object", "save_key": "condition"}
    }
}

class CardEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Final Card Editor v8 (Double Click & AllPlayers)")
        self.root.geometry("1300x850")

        self.schema_config = self.load_json(CONFIG_FILE, DEFAULT_CONFIG)
        self.effects_data = self.load_effects()
        self.card_db = self.load_card_db()
        
        self.setup_ui()

    def load_json(self, path, default):
        if not os.path.exists(path): return default
        try:
            with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return default

    def load_effects(self):
        data = self.load_json(EFFECTS_FILE, {"schema": "v6", "effects": [], "cardBindings": []})
        if "effects" not in data: data["effects"] = []
        if "cardBindings" not in data: data["cardBindings"] = []
        return data

    def load_card_db(self):
        data = self.load_json(DB_FILE, {"cards": []})
        return {c.get("id"): c.get("name", "Unknown") for c in data.get("cards", [])}

    def save_all(self):
        try:
            self.effects_data["effects"].sort(key=lambda x: x.get("id", ""))
            self.effects_data["cardBindings"].sort(key=lambda x: int(x.get("cardId", 0)))
            
            with open(EFFECTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.effects_data, f, indent=2, ensure_ascii=False)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.schema_config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("저장 완료", "effects.json 및 스키마 설정이 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"저장 중 오류 발생: {e}")

    # === UI Setup ===
    def setup_ui(self):
        tab_control = ttk.Notebook(self.root)
        self.tab_effects = ttk.Frame(tab_control)
        self.tab_bindings = ttk.Frame(tab_control)
        tab_control.add(self.tab_effects, text="Effect Manager")
        tab_control.add(self.tab_bindings, text="Card Bindings")
        tab_control.pack(expand=1, fill="both")
        self.setup_effects_tab()
        self.setup_bindings_tab()
        ttk.Button(self.root, text="SAVE ALL", command=self.save_all).pack(fill="x", pady=5)

    def setup_effects_tab(self):
        paned = tk.PanedWindow(self.tab_effects, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        left_frame = ttk.LabelFrame(paned, text="Effects List")
        paned.add(left_frame, width=300)
        self.eff_listbox = tk.Listbox(left_frame)
        self.eff_listbox.pack(fill="both", expand=True)
        self.eff_listbox.bind("<<ListboxSelect>>", self.on_effect_select)
        
        bf = ttk.Frame(left_frame)
        bf.pack(fill="x")
        ttk.Button(bf, text="New", command=self.add_new_effect).pack(side="left", expand=True)
        ttk.Button(bf, text="Del", command=self.delete_effect).pack(side="left", expand=True)

        right_frame = ttk.Frame(paned)
        paned.add(right_frame)

        info_frame = ttk.LabelFrame(right_frame, text="Info")
        info_frame.pack(fill="x", pady=5)
        ttk.Label(info_frame, text="ID:").pack(side=tk.LEFT)
        self.var_eff_id = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.var_eff_id, width=10).pack(side=tk.LEFT)
        ttk.Label(info_frame, text="Raw:").pack(side=tk.LEFT)
        self.var_eff_raw = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.var_eff_raw).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(info_frame, text="Update", command=self.update_effect_info).pack(side=tk.LEFT)

        comp_frame = ttk.LabelFrame(right_frame, text="Components")
        comp_frame.pack(fill="both", expand=True, pady=5)
        self.comp_tree = ttk.Treeview(comp_frame, columns=("Kind", "Timing", "Actions"), show="headings")
        self.comp_tree.heading("Kind", text="Kind"); self.comp_tree.heading("Timing", text="Timing"); self.comp_tree.heading("Actions", text="Actions")
        self.comp_tree.pack(fill="both", expand=True)
        
        # [요청 2] 더블 클릭 시 편집
        self.comp_tree.bind("<Double-1>", lambda e: self.edit_component())
        
        cbf = ttk.Frame(comp_frame)
        cbf.pack(fill="x")
        ttk.Button(cbf, text="Add Component", command=self.add_component).pack(side="left")
        ttk.Button(cbf, text="Edit", command=self.edit_component).pack(side="left")
        ttk.Button(cbf, text="Remove", command=self.remove_component).pack(side="left")

        self.current_eff_index = -1
        self.refresh_effect_list()

    def refresh_effect_list(self):
        self.eff_listbox.delete(0, tk.END)
        for eff in self.effects_data["effects"]:
            self.eff_listbox.insert(tk.END, f"[{eff.get('id')}] {eff.get('raw', '')[:30]}")

    def on_effect_select(self, event):
        sel = self.eff_listbox.curselection()
        if not sel: return
        self.current_eff_index = sel[0]
        eff = self.effects_data["effects"][self.current_eff_index]
        self.var_eff_id.set(eff.get("id", ""))
        self.var_eff_raw.set(eff.get("raw", ""))
        self.refresh_comp_tree(eff.get("components", []))

    def refresh_comp_tree(self, components):
        for item in self.comp_tree.get_children(): self.comp_tree.delete(item)
        for i, comp in enumerate(components):
            actions = comp.get("actions", [])
            if not actions and "replaceWith" in comp: actions = comp.get("replaceWith", [])
            summary = ", ".join([a.get("action", "?") for a in actions])
            self.comp_tree.insert("", "end", iid=i, values=(comp.get("kind"), comp.get("timing"), summary))

    def add_new_effect(self):
        new_id = f"E{len(self.effects_data['effects']):02d}"
        self.effects_data["effects"].append({"id": new_id, "raw": "New", "components": []})
        self.refresh_effect_list()

    def delete_effect(self):
        if self.current_eff_index == -1: return
        del self.effects_data["effects"][self.current_eff_index]
        self.current_eff_index = -1
        self.refresh_effect_list()
        self.refresh_comp_tree([])

    def update_effect_info(self):
        if self.current_eff_index != -1:
            self.effects_data["effects"][self.current_eff_index].update({"id": self.var_eff_id.get(), "raw": self.var_eff_raw.get()})
            self.refresh_effect_list()

    def add_component(self):
        if self.current_eff_index == -1: return
        ComponentEditor(self.root, self.schema_config, {}, lambda d: self.save_comp(d, -1))
    def edit_component(self):
        sel = self.comp_tree.selection()
        if sel:
            idx = int(sel[0])
            data = self.effects_data["effects"][self.current_eff_index]["components"][idx]
            ComponentEditor(self.root, self.schema_config, data, lambda d: self.save_comp(d, idx))
    def remove_component(self):
        sel = self.comp_tree.selection()
        if sel:
            del self.effects_data["effects"][self.current_eff_index]["components"][int(sel[0])]
            self.on_effect_select(None)
    def save_comp(self, data, idx):
        comps = self.effects_data["effects"][self.current_eff_index]["components"]
        if idx == -1: comps.append(data)
        else: comps[idx] = data
        self.on_effect_select(None)

    def setup_bindings_tab(self):
        frame = ttk.Frame(self.tab_bindings)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.bind_tree = ttk.Treeview(frame, columns=("CardID", "CardName", "BoundEffectID"), show="headings")
        self.bind_tree.heading("CardID", text="ID"); self.bind_tree.heading("CardName", text="Name"); self.bind_tree.heading("BoundEffectID", text="Bound Effect")
        self.bind_tree.pack(fill="both", expand=True)
        self.bind_tree.bind("<<TreeviewSelect>>", self.on_binding_select)

        edit_frame = ttk.Frame(frame)
        edit_frame.pack(fill="x", pady=5)
        ttk.Label(edit_frame, text="Bind Effect: ").pack(side="left")
        self.var_bind_eff = tk.StringVar()
        self.combo_bind_eff = ttk.Combobox(edit_frame, textvariable=self.var_bind_eff, state="readonly")
        self.combo_bind_eff.pack(side="left")
        ttk.Button(edit_frame, text="Bind", command=self.apply_binding).pack(side="left")
        ttk.Button(edit_frame, text="Unbind", command=self.remove_binding).pack(side="left")
        self.refresh_bindings()

    def refresh_bindings(self):
        self.combo_bind_eff["values"] = [e["id"] for e in self.effects_data["effects"]]
        for item in self.bind_tree.get_children(): self.bind_tree.delete(item)
        bind_map = {b["cardId"]: b["effectId"] for b in self.effects_data["cardBindings"]}
        for cid in sorted(list(set(self.card_db.keys()) | set(bind_map.keys()))):
            self.bind_tree.insert("", "end", values=(cid, self.card_db.get(cid, "Unknown"), bind_map.get(cid, "-")))
    def on_binding_select(self, e):
        sel = self.bind_tree.selection()
        if sel: self.var_bind_eff.set(self.bind_tree.item(sel[0])["values"][2] if self.bind_tree.item(sel[0])["values"][2] != "-" else "")
    def apply_binding(self):
        sel = self.bind_tree.selection()
        if sel:
            cid = int(self.bind_tree.item(sel[0])["values"][0])
            self.effects_data["cardBindings"] = [b for b in self.effects_data["cardBindings"] if b["cardId"] != cid]
            if self.var_bind_eff.get(): self.effects_data["cardBindings"].append({"cardId": cid, "effectId": self.var_bind_eff.get()})
            self.refresh_bindings()
    def remove_binding(self):
        sel = self.bind_tree.selection()
        if sel:
            cid = int(self.bind_tree.item(sel[0])["values"][0])
            self.effects_data["cardBindings"] = [b for b in self.effects_data["cardBindings"] if b["cardId"] != cid]
            self.refresh_bindings()

class ComponentEditor:
    def __init__(self, parent, schema, data, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Component Editor")
        self.schema = schema; self.data = copy.deepcopy(data); self.callback = callback
        
        kf = ttk.Frame(self.window); kf.pack(fill="x", padx=5)
        ttk.Label(kf, text="Kind:").pack(side="left")
        self.var_kind = tk.StringVar(value=self.data.get("kind", "trigger"))
        self.cb_kind = ttk.Combobox(kf, textvariable=self.var_kind, values=schema["Kinds"])
        self.cb_kind.pack(side="left", fill="x", expand=True)
        self.create_mod_buttons(kf, "Kinds", self.cb_kind, self.var_kind)

        tf = ttk.Frame(self.window); tf.pack(fill="x", padx=5)
        ttk.Label(tf, text="Timing:").pack(side="left")
        self.var_timing = tk.StringVar(value=self.data.get("timing", "OnGameStart"))
        self.cb_timing = ttk.Combobox(tf, textvariable=self.var_timing, values=schema["Timings"])
        self.cb_timing.pack(side="left", fill="x", expand=True)
        self.create_mod_buttons(tf, "Timings", self.cb_timing, self.var_timing)

        af = ttk.LabelFrame(self.window, text="Actions"); af.pack(fill="both", expand=True, padx=5)
        self.lst_act = tk.Listbox(af); self.lst_act.pack(fill="both", expand=True)
        
        # [요청 2] 더블 클릭 시 편집
        self.lst_act.bind("<Double-1>", lambda e: self.edit_act())
        
        bf = ttk.Frame(af); bf.pack(fill="x")
        ttk.Button(bf, text="Add Action", command=self.add_act).pack(side="left")
        ttk.Button(bf, text="Edit", command=self.edit_act).pack(side="left")
        ttk.Button(bf, text="Del", command=self.del_act).pack(side="left")
        
        ttk.Button(self.window, text="Save", command=self.save).pack(pady=5)
        self.refresh()

    def create_mod_buttons(self, parent, schema_key, combo, var):
        def add_item():
            val = simpledialog.askstring("Add", f"New {schema_key} item:")
            if val and val not in self.schema[schema_key]:
                self.schema[schema_key].append(val)
                combo["values"] = self.schema[schema_key]
                var.set(val)
        def del_item():
            val = var.get()
            if val in self.schema[schema_key]:
                self.schema[schema_key].remove(val)
                combo["values"] = self.schema[schema_key]
                var.set("")
        ttk.Button(parent, text="[+]", width=3, command=add_item).pack(side="left")
        ttk.Button(parent, text="[-]", width=3, command=del_item).pack(side="left")

    def refresh(self):
        self.lst_act.delete(0, tk.END)
        acts = self.data.get("actions", [])
        if not acts and "replaceWith" in self.data: acts = self.data["replaceWith"]
        for a in acts: self.lst_act.insert(tk.END, a.get("action"))
    def add_act(self):
        GenericDetailEditor(self.window, self.schema, "ActionTypes", {}, lambda d: self.upd_act(d, -1))
    def edit_act(self):
        sel = self.lst_act.curselection()
        if sel:
            acts = self.data.get("actions", [])
            if not acts and "replaceWith" in self.data: acts = self.data["replaceWith"]
            GenericDetailEditor(self.window, self.schema, "ActionTypes", acts[sel[0]], lambda d: self.upd_act(d, sel[0]))
    def del_act(self):
        sel = self.lst_act.curselection()
        if sel:
            k = "replaceWith" if self.var_kind.get() == "replacement" else "actions"
            if k in self.data: del self.data[k][sel[0]]; self.refresh()
    def upd_act(self, item, idx):
        k = "replaceWith" if self.var_kind.get() == "replacement" else "actions"
        if k not in self.data: self.data[k] = []
        if idx == -1: self.data[k].append(item)
        else: self.data[k][idx] = item
        self.refresh()
    def save(self):
        self.data["kind"] = self.var_kind.get()
        self.data["timing"] = self.var_timing.get()
        self.callback(self.data)
        self.window.destroy()

class GenericDetailEditor:
    def __init__(self, parent, schema, schema_key, data, callback):
        self.window = tk.Toplevel(parent); self.window.title("Detail Editor")
        self.schema = schema; self.schema_key = schema_key
        self.data = copy.deepcopy(data); self.callback = callback
        self.widgets = {}

        keys = list(schema[schema_key].keys())
        type_key = "type" if schema_key == "ConditionTypes" else "action"
        
        tf = ttk.Frame(self.window); tf.pack(fill="x", padx=5, pady=5)
        ttk.Label(tf, text="Type:").pack(side="left")
        self.var_type = tk.StringVar(value=self.data.get(type_key, keys[0]))
        self.cb_type = ttk.Combobox(tf, textvariable=self.var_type, values=keys, state="readonly")
        self.cb_type.pack(side="left", fill="x", expand=True)
        self.cb_type.bind("<<ComboboxSelected>>", self.on_type_change)
        self.create_mod_buttons(tf, schema_key, self.cb_type, self.var_type)

        self.p_frame = ttk.LabelFrame(self.window, text="Parameters"); self.p_frame.pack(fill="both", expand=True, padx=5)
        ttk.Button(self.window, text="Save", command=self.save).pack(pady=5)
        self.on_type_change(None)

    def create_mod_buttons(self, parent, schema_key, combo, var):
        def add_item():
            val = simpledialog.askstring("Add", f"New Type Name:")
            if val and val not in self.schema[schema_key]:
                self.schema[schema_key][val] = {"fields": []}
                combo["values"] = list(self.schema[schema_key].keys())
                var.set(val)
                self.on_type_change(None)
        def del_item():
            val = var.get()
            if val in self.schema[schema_key]:
                del self.schema[schema_key][val]
                combo["values"] = list(self.schema[schema_key].keys())
                var.set("")
                self.on_type_change(None)
        ttk.Button(parent, text="[+]", width=3, command=add_item).pack(side="left")
        ttk.Button(parent, text="[-]", width=3, command=del_item).pack(side="left")

    def on_type_change(self, event):
        for w in self.p_frame.winfo_children(): w.destroy()
        self.widgets = {}
        t = self.var_type.get()
        if not t: return
        fields = self.schema[self.schema_key].get(t, {}).get("fields", [])

        for f in fields:
            fdef = self.schema["FieldDefinitions"].get(f, {"type": "string"})
            row = ttk.Frame(self.p_frame); row.pack(fill="x", pady=2)
            ttk.Label(row, text=f+":", width=15).pack(side="left")
            
            ftype = fdef.get("type", "string")
            val = self.data.get(f, fdef.get("default"))

            if ftype in ["selection", "selection_custom"]:
                var = tk.StringVar(value=str(val))
                cb = ttk.Combobox(row, textvariable=var, values=fdef.get("values", []))
                cb.pack(side="left", fill="x", expand=True)
                self.widgets[f] = (var, ftype)
            elif ftype == "condition_object":
                lbl = ttk.Label(row, text=val.get("type", "None") if val else "None")
                lbl.pack(side="left", padx=5)
                self.widgets[f] = (val if val else {}, ftype, fdef.get("save_key"), lbl)
                def open_sub_cond(target, label):
                    GenericDetailEditor(self.window, self.schema, "ConditionTypes", target,
                                        lambda d: self.upd_nested_dict(target, d, label))
                ttk.Button(row, text="Edit", command=lambda v=self.widgets[f][0], l=lbl: open_sub_cond(v, l)).pack(side="left")
            elif ftype == "action_list":
                lbl = ttk.Label(row, text=f"{len(val)} actions" if val else "0 actions")
                lbl.pack(side="left", padx=5)
                self.widgets[f] = (val if val else [], ftype, fdef.get("save_key"), lbl)
                def open_sub_list(target, label):
                    NestedListEditor(self.window, self.schema, "ActionTypes", target,
                                     lambda l: self.upd_nested_list(target, l, label))
                ttk.Button(row, text="Edit", command=lambda v=self.widgets[f][0], l=lbl: open_sub_list(v, l)).pack(side="left")
            elif ftype == "fixed":
                v = fdef["value"]; ttk.Label(row, text=v, font="bold").pack(side="left")
                self.widgets[f] = (v, ftype, fdef.get("save_key"))
            elif ftype == "stat_comparison":
                parts = fdef["parts"]; sval = str(val); v1, v2 = parts[0][0], parts[1][0]
                for p in parts[0]:
                    if sval.startswith(p): v1 = p; v2 = sval[len(p):]; break
                var1, var2 = tk.StringVar(value=v1), tk.StringVar(value=v2)
                ttk.Combobox(row, textvariable=var1, values=parts[0], width=10).pack(side="left")
                ttk.Combobox(row, textvariable=var2, values=parts[1], width=10).pack(side="left")
                self.widgets[f] = ([var1, var2], ftype)
            elif ftype == "exile_mode_selector":
                # [요청 1] 3가지 모드 지원 (CanSelect, CantSelect, AllPlayers)
                modes = fdef["modes"]
                current_mode = modes[0] # Default
                if val in modes: current_mode = val
                else: current_mode = modes[1] # CantSelectTarget (Auto)

                c, s = fdef["comparators"][0], fdef["stats"][0]
                if current_mode == modes[1]: # Auto (CantSelect)
                    for cmp in fdef["comparators"]:
                        if str(val).startswith(cmp): c = cmp; s = str(val)[len(cmp):]; break
                
                vm, vc, vs = tk.StringVar(value=current_mode), tk.StringVar(value=c), tk.StringVar(value=s)
                ttk.Combobox(row, textvariable=vm, values=modes, width=15).pack(side="left")
                c1 = ttk.Combobox(row, textvariable=vc, values=fdef["comparators"], width=8)
                c1.pack(side="left")
                c2 = ttk.Combobox(row, textvariable=vs, values=fdef["stats"], width=8)
                c2.pack(side="left")
                
                def toggle(*a): 
                    # CantSelectTarget일 때만 비교/스탯 활성화
                    is_auto = (vm.get() == modes[1]) 
                    st = "!disabled" if is_auto else "disabled"
                    c1.state([st]); c2.state([st])
                
                vm.trace_add("write", toggle); toggle()
                self.widgets[f] = ([vm, vc, vs], ftype, modes)
            else:
                var = tk.StringVar(value=str(val))
                ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
                self.widgets[f] = (var, ftype)

    def upd_nested_dict(self, target, new_dict, label):
        target.clear(); target.update(new_dict)
        label.config(text=new_dict.get("type", "Set"))
    def upd_nested_list(self, target, new_list, label):
        target[:] = new_list
        label.config(text=f"{len(target)} actions")

    def save(self):
        type_key = "type" if self.schema_key == "ConditionTypes" else "action"
        res = {type_key: self.var_type.get()}
        for f, val_data in self.widgets.items():
            holder, ftype, *ex = val_data
            if ftype == "fixed": res[ex[0]] = holder
            elif ftype == "stat_comparison": res[f] = f"{holder[0].get()}{holder[1].get()}"
            elif ftype == "exile_mode_selector":
                # [요청 1] 저장 로직: Auto가 아니면 모드명 그대로 저장
                mode_val = holder[0].get()
                modes = ex[0]
                if mode_val == modes[1]: # CantSelectTarget (Auto)
                    res[f] = f"{holder[1].get()}{holder[2].get()}"
                else: # CanSelectTarget or AllPlayers
                    res[f] = mode_val
            elif ftype == "action_list": res[ex[0]] = holder
            elif ftype == "condition_object": res[ex[0]] = holder
            else:
                v = holder.get()
                if ftype == "int": 
                    try: res[f] = int(v)
                    except: res[f] = 0
                else: res[f] = v
        self.callback(res)
        self.window.destroy()

class NestedListEditor:
    def __init__(self, parent, schema, schema_key, data_list, callback):
        self.window = tk.Toplevel(parent); self.window.geometry("400x400")
        self.schema = schema; self.schema_key = schema_key
        self.data_list = copy.deepcopy(data_list); self.callback = callback
        
        self.lst = tk.Listbox(self.window); self.lst.pack(fill="both", expand=True)
        
        # [요청 2] 더블 클릭 시 편집
        self.lst.bind("<Double-1>", lambda e: self.edit())
        
        bf = ttk.Frame(self.window); bf.pack(fill="x")
        ttk.Button(bf, text="+", command=self.add).pack(side="left")
        ttk.Button(bf, text="Edit", command=self.edit).pack(side="left")
        ttk.Button(bf, text="-", command=self.dele).pack(side="left")
        ttk.Button(self.window, text="OK", command=self.ok).pack()
        self.refresh()

    def refresh(self):
        self.lst.delete(0, tk.END)
        k = "type" if self.schema_key == "ConditionTypes" else "action"
        for i in self.data_list: self.lst.insert(tk.END, i.get(k, "?"))
    def add(self):
        GenericDetailEditor(self.window, self.schema, self.schema_key, {}, lambda d: self.upd(d, -1))
    def edit(self):
        sel = self.lst.curselection()
        if sel: GenericDetailEditor(self.window, self.schema, self.schema_key, self.data_list[sel[0]], lambda d: self.upd(d, sel[0]))
    def dele(self):
        sel = self.lst.curselection()
        if sel: del self.data_list[sel[0]]; self.refresh()
    def upd(self, d, i):
        if i == -1: self.data_list.append(d)
        else: self.data_list[i] = d
        self.refresh()
    def ok(self):
        self.callback(self.data_list); self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CardEditorApp(root)
    root.mainloop()
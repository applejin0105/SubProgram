import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, UnidentifiedImageError
import shutil
import json
import os
import zipfile, tempfile

import pygame

pygame.init()
try:
    pygame.mixer.init()
except Exception as e:
    print(f"[오류] 사운드 초기화 실패: {e}")

class CardCreatorApp:
    def __init__(self, root):
        
        self.language_var = tk.StringVar(value="ko")
        self.language_labels = {"ko": "한국어", "en": "English", "ja": "日本語", "zh": "简体中文"}
        self.language_codes = {v: k for k, v in self.language_labels.items()}
        
        self.languages = {
            "ko": {
                "number": "번호", "name": "이름", "description": "설명", "effect": "효과",
                "auto_analyze": "자동 분석", "species": "종족", "require_symbol": "요구심볼",
                "gift_symbol": "증여심볼", "cultist": "신도수", "junction": "갈림길",
                "image_path": "이미지 경로", "sound_path": "사운드 경로",
                "search": "찾기", "preview": "미리보기", "play": "재생", "stop": "정지",
                "save": "저장", "reset": "초기화", "merge": "파일 합치기",
                "load": "JSON 불러오기", "modify": "수정 저장", "detail_effect": "세부효과",
                "json_preview": "JSON"
            },
            "en": {
                "number": "Number", "name": "Name", "description": "Description", "effect": "Effect",
                "auto_analyze": "Auto Analyze", "species": "Species", "require_symbol": "Required Symbol",
                "gift_symbol": "Gifted Symbol", "cultist": "Cultists", "junction": "Junction",
                "image_path": "Image Path", "sound_path": "Sound Path",
                "search": "Browse", "preview": "Preview", "play": "Play", "stop": "Stop",
                "save": "Save", "reset": "Reset", "merge": "Merge Files",
                "load": "Load JSON", "modify": "Modify Save", "detail_effect": "Detail Effect",
                "json_preview": "JSON"
            },
            "ja": {
                "number": "番号", "name": "名前", "description": "説明", "effect": "効果",
                "auto_analyze": "自動分析", "species": "種族", "require_symbol": "必要なシンボル",
                "gift_symbol": "与えるシンボル", "cultist": "信者数", "junction": "分岐",
                "image_path": "画像パス", "sound_path": "サウンドパス",
                "search": "参照", "preview": "プレビュー", "play": "再生", "stop": "停止",
                "save": "保存", "reset": "リセット", "merge": "ファイル統合",
                "load": "JSON読み込み", "modify": "修正保存", "detail_effect": "詳細効果",
                "json_preview": "JSON"
            },
            "zh": {
                "number": "编号", "name": "名称", "description": "说明", "effect": "效果",
                "auto_analyze": "自动分析", "species": "种族", "require_symbol": "所需符号",
                "gift_symbol": "赠送符号", "cultist": "信徒数", "junction": "分支",
                "image_path": "图片路径", "sound_path": "音效路径",
                "search": "浏览", "preview": "预览", "play": "播放", "stop": "停止",
                "save": "保存", "reset": "重置", "merge": "合并文件",
                "load": "载入JSON", "modify": "保存修改", "detail_effect": "详细效果",
                "json_preview": "JSON"
            }
        }

        self.effect_descriptions = {
            "DrawFromDeck": {
                "ko": "덱에서 카드를 추가로 뽑습니다.",
                "en": "Draw extra card(s) from the deck.",
                "ja": "デッキからカードを追加で引きます。",
                "zh": "从牌堆中额外抽取卡牌。"
            },
            "SkipDraw": {
                "ko": "카드 뽑기 단계를 건너뜁니다.",
                "en": "Skip the draw phase.",
                "ja": "ドローフェイズをスキップします。",
                "zh": "跳过抽牌阶段。"
            },
            "ForcedSelect": {
                "ko": "선택 없이 이 카드가 강제 선택됩니다.",
                "en": "This card is forcibly selected.",
                "ja": "このカードが強制的に選ばれます。",
                "zh": "该卡牌被强制选择。"
            },
            "DestroyEnemyCultist": {
                "ko": "상대 신도의 카드를 파괴합니다.",
                "en": "Destroy a cultist card of the opponent.",
                "ja": "相手の信者カードを破壊します。",
                "zh": "摧毁对方的信徒卡牌。"
            },
            "Exile": {
                "ko": "카드를 추방합니다.",
                "en": "Exile a card.",
                "ja": "カードを追放します。",
                "zh": "放逐卡牌。"
            },
            "GainPantheon": {
                "ko": "만신전을 획득합니다.",
                "en": "Gain the Pantheon.",
                "ja": "万神殿を獲得します。",
                "zh": "获得万神殿。"
            },
            "SacrificeOther": {
                "ko": "신도 카드를 희생합니다.",
                "en": "Sacrifice a cultist.",
                "ja": "信者カードを犠牲にします。",
                "zh": "牺牲信徒卡牌。"
            },
            "TradeExtra": {
                "ko": "추가 교역을 수행합니다.",
                "en": "Perform an extra trade.",
                "ja": "追加の交易を行います。",
                "zh": "进行额外的贸易。"
            },
            "TradeRequiredToFlip": {
                "ko": "교역 조건이 있어야 앞면으로 뒤집을 수 있습니다.",
                "en": "Trade is required to flip this card.",
                "ja": "表にするには交易が必要です。",
                "zh": "翻面此卡需要贸易条件。"
            },
            "GainFamine": {
                "ko": "기아 상태를 얻습니다.",
                "en": "Gain famine condition.",
                "ja": "飢餓状態になります。",
                "zh": "获得饥荒状态。"
            },
            "FlipInsteadDestroy": {
                "ko": "파괴 대신 이 카드를 뒤집습니다.",
                "en": "Flip this card instead of destroying.",
                "ja": "破壊の代わりにこのカードを裏返します。",
                "zh": "将此卡翻面代替摧毁。"
            },
            "OneFaceUpOnly": {
                "ko": "이 카드의 앞면은 하나만 존재할 수 있습니다.",
                "en": "Only one copy of this card can be face-up.",
                "ja": "このカードは1枚だけ表向きにできます。",
                "zh": "此卡只能有一张正面朝上。"
            },
            "ConditionalEffect": {
                "ko": "특정 조건 하에 발동됩니다.",
                "en": "Triggers under certain conditions.",
                "ja": "特定の条件下で発動します。",
                "zh": "在特定条件下触发。"
            },
            "Unknown": {
                "ko": "정의되지 않은 효과입니다.",
                "en": "Undefined effect.",
                "ja": "未定義の効果です。",
                "zh": "未定义的效果。"
            }
        }

        self.root = root
        self.root.title("카드 생성기")

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        # GUI 요소들
        self.label_number = tk.Label(root, text=self.languages["ko"]["number"])
        self.label_number.grid(row=0, column=0, sticky="w")
        self.number_spinbox = tk.Spinbox(root, from_=0, to=1000000)
        self.number_spinbox.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        self.label_name = tk.Label(root, text=self.languages["ko"]["name"])
        self.label_name.grid(row=1, column=0, sticky="w")
        self.name_entry = tk.Entry(root)
        self.name_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        self.label_description = tk.Label(root, text=self.languages["ko"]["description"])
        self.label_description.grid(row=2, column=0, sticky="nw", padx=5, pady=5)
        self.description_text = tk.Text(root, height=5, wrap="word")
        self.description_text.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

        self.label_effect = tk.Label(root, text=self.languages["ko"]["effect"])
        self.label_effect.grid(row=3, column=0, sticky="nw", padx=5, pady=5)
        self.effect_text = tk.Text(root, height=5, wrap="word")
        self.effect_text.grid(row=3, column=1, sticky="nsew", padx=5, pady=5)
        self.button_analyze = tk.Button(root, text=self.languages["ko"]["auto_analyze"], command=self.fill_detail_from_effect)
        self.button_analyze.grid(row=3, column=2, padx=5, pady=5)

        self.trigger_options = ["OnStart", "OnFlip", "OnDraw", "OnDestroy", "OnPreFlip", "Passive"]
        self.target_options = ["Self", "OtherPlayer", "AllPlayers", "OwnCultist", "EnemyCultist", "None"]

        self.label_detail_effect = tk.Label(root, text=self.languages["ko"]["detail_effect"])
        self.label_detail_effect.grid(row=4, column=0, sticky="nw")
        self.detail_effect_frame = tk.Frame(root)
        self.detail_effect_frame.grid(row=4, column=1, sticky="nsew", padx=5, pady=5)
        self.detail_effects = []
        self.used_effects = set()
        self.create_detail_effect_row()
        self.button_add_effect = tk.Button(root, text="+", command=self.create_detail_effect_row)
        self.button_add_effect.grid(row=4, column=2, sticky="w", padx=5)

        self.label_species = tk.Label(root, text=self.languages["ko"]["species"])
        self.label_species.grid(row=5, column=0, sticky="w")
        self.species_var = tk.StringVar(value="일반")
        self.species_dropdown = ttk.Combobox(
            root, textvariable=self.species_var, values=["일반", "여신", "인신공양", "사기사"], state="readonly"
        )
        self.species_dropdown.grid(row=5, column=1, sticky="ew", padx=5, pady=5)

        self.label_require_symbol = tk.Label(root, text=self.languages["ko"]["require_symbol"])
        self.label_require_symbol.grid(row=6, column=0, sticky="w")
        self.requirement_spinboxes = {}
        self.create_symbol_inputs("요구심볼", self.requirement_spinboxes, row=6)

        self.label_gift_symbol = tk.Label(root, text=self.languages["ko"]["gift_symbol"])
        self.label_gift_symbol.grid(row=7, column=0, sticky="w")
        self.gift_spinboxes = {}
        self.create_symbol_inputs("증여심볼", self.gift_spinboxes, row=7)

        self.label_cultist = tk.Label(root, text=self.languages["ko"]["cultist"])
        self.label_cultist.grid(row=8, column=0, sticky="w")
        self.follower_spinbox = tk.Spinbox(root, from_=0, to=1000000)
        self.follower_spinbox.grid(row=8, column=1, sticky="ew", padx=5, pady=5)

        self.label_junction = tk.Label(root, text=self.languages["ko"]["junction"])
        self.label_junction.grid(row=9, column=0, sticky="w")
        self.path_spinbox = tk.Spinbox(root, from_=0, to=1000000)
        self.path_spinbox.grid(row=9, column=1, sticky="ew", padx=5, pady=5)

        self.label_image_path = tk.Label(root, text=self.languages["ko"]["image_path"])
        self.label_image_path.grid(row=10, column=0, sticky="w", padx=5)
        self.image_entry = tk.Entry(root, width=40)
        self.image_entry.grid(row=10, column=1, columnspan=2, padx=5, pady=2)

        self.button_image_browse = tk.Button(root, text=self.languages["ko"]["search"], command=self.select_image_file)
        self.button_image_browse.grid(row=11, column=1, sticky="w", padx=5)
        self.button_image_preview = tk.Button(root, text=self.languages["ko"]["preview"], command=self.show_image_preview)
        self.button_image_preview.grid(row=11, column=1, sticky="e", padx=5)

        self.image_preview_label = tk.Label(root)
        self.image_preview_label.grid(row=12, column=1, columnspan=2, pady=5)

        self.label_sound_path = tk.Label(root, text=self.languages["ko"]["sound_path"])
        self.label_sound_path.grid(row=13, column=0, sticky="w", padx=5)
        self.sound_entry = tk.Entry(root, width=40)
        self.sound_entry.grid(row=13, column=1, columnspan=2, padx=5, pady=2)

        sound_button_frame = tk.Frame(root)
        sound_button_frame.grid(row=14, column=1, columnspan=2, sticky="w", padx=5)
        self.button_sound_browse = tk.Button(sound_button_frame, text=self.languages["ko"]["search"], command=self.select_sound_file)
        self.button_sound_browse.pack(side="left", padx=2)
        self.button_sound_play = tk.Button(sound_button_frame, text=self.languages["ko"]["play"], command=self.play_sound)
        self.button_sound_play.pack(side="left", padx=2)
        self.button_sound_stop = tk.Button(sound_button_frame, text=self.languages["ko"]["stop"], command=self.stop_sound)
        self.button_sound_stop.pack(side="left", padx=2)

        self.button_save = tk.Button(root, text=self.languages["ko"]["save"], command=self.save_card)
        self.button_save.grid(row=15, column=0, pady=5)
        self.button_reset = tk.Button(root, text=self.languages["ko"]["reset"], command=self.reset_all)
        self.button_reset.grid(row=15, column=1, pady=5)
        
        self.button_load = tk.Button(root, text=self.languages["ko"]["load"], command=self.load_card)
        self.button_load.grid(row=16, column=0, pady=5)
        self.button_modify = tk.Button(root, text=self.languages["ko"]["modify"], command=self.save_modified_card)
        self.button_modify.grid(row=16, column=1, pady=5)
        
        # 언어 선택 콤보박스
        self.language_var = tk.StringVar(value="ko")
        language_labels = {"ko": "한국어", "en": "English", "ja": "日本語", "zh": "简体中文"}
        self.language_selector = ttk.Combobox(
            root,
            textvariable=self.language_var,
            values=[language_labels[code] for code in ["ko", "en", "ja", "zh"]],
            state="readonly",
            width=10
        )
        self.language_selector.grid(row=0, column=3, padx=5, pady=5)
        self.language_selector.bind("<<ComboboxSelected>>", self.switch_language)
        self.language_labels = language_labels
        self.language_codes = {v: k for k, v in language_labels.items()}
        
        # 추가된 이미지와 소리 파일 경로
        self.image_path = None
        # 추가된 소리 파일 경로
        self.sfx_path = None
        self.is_paused = False  # 소리 일시정지 상태

        # 창 크기 조정을 위한 설정
        root.rowconfigure(2, weight=1)  # 설명 텍스트 창
        root.rowconfigure(3, weight=1)  # 효과 텍스트 창
        root.rowconfigure(4, weight=1)  # 세부효과 프레임               
        root.columnconfigure(1, weight=1)
        
        # 실시간 JSON 미리보기 창
        tk.Label(root, text="JSON:").grid(row=0, column=3, sticky="nw", padx=5)
        self.preview_text = tk.Text(root, height=40, width=50, wrap="none", bg="#f7f7f7")
        self.preview_text.grid(row=1, column=3, rowspan=12, sticky="nsew", padx=5, pady=5)
        
        # 주요 입력 필드에 이벤트 연결
        for widget in [
            self.number_spinbox, self.name_entry, self.description_text, self.effect_text,
            self.follower_spinbox, self.path_spinbox
        ]:
            widget.bind("<KeyRelease>", lambda e: self.update_preview())

        self.species_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_preview())

    def create_detail_effect_row(self, effect=None, count=1, trigger="OnFlip", target="None"):
        row_frame = tk.Frame(self.detail_effect_frame)
        row_frame.pack(fill="x", pady=2)

        all_options = sorted([
            "DrawFromDeck", "SkipDraw", "ForcedSelect", "DestroyEnemyCultist",
            "Exile", "GainPantheon", "SacrificeOther", "TradeExtra",
            "TradeRequiredToFlip", "GainFamine", "FlipInsteadDestroy",
            "OneFaceUpOnly", "ConditionalEffect", "Unknown"
        ])
        available_options = [opt for opt in all_options if opt not in self.used_effects]

        if not available_options:
            messagebox.showwarning("경고", "더 이상 추가할 수 있는 효과가 없습니다.")
            return

        effect_var = tk.StringVar(value=effect or "선택")
        effect_dropdown = ttk.Combobox(row_frame, textvariable=effect_var, values=available_options, state="readonly")
        effect_dropdown.pack(side="left", padx=5)

        trigger_var = tk.StringVar(value=trigger)
        trigger_dropdown = ttk.Combobox(row_frame, textvariable=trigger_var, values=self.trigger_options, state="readonly")
        trigger_dropdown.pack(side="left", padx=5)

        target_var = tk.StringVar(value=target)
        target_dropdown = ttk.Combobox(row_frame, textvariable=target_var, values=self.target_options, state="readonly")
        target_dropdown.pack(side="left", padx=5)

        value_spinbox = tk.Spinbox(row_frame, from_=0, to=100)
        value_spinbox.delete(0, tk.END)
        value_spinbox.insert(0, count)
        value_spinbox.pack(side="left", padx=5)

        # 설명 버튼
        description_button = tk.Button(row_frame, text="설명", command=lambda: self.show_effect_description(effect_var))
        description_button.pack(side="left", padx=5)

        delete_button = tk.Button(row_frame, text="삭제", command=lambda: self.delete_detail_effect_row(row_frame, effect_var))
        delete_button.pack(side="left", padx=5)

        def on_effect_selected(event=None):
            self.update_preview()

        effect_dropdown.bind("<<ComboboxSelected>>", on_effect_selected)
        value_spinbox.bind("<KeyRelease>", lambda e: self.update_preview())

        self.detail_effects.append({
            "effect_var": effect_var,
            "value_entry": value_spinbox,
            "trigger_var": trigger_var,
            "target_var": target_var
        })

    def delete_detail_effect_row(self, row_frame, effect_var):
        for detail in self.detail_effects:
            if detail[0] == effect_var:
                selected_effect = effect_var.get()
                if selected_effect in self.used_effects:
                    self.used_effects.remove(selected_effect)
                self.detail_effects.remove(detail)
                break
        row_frame.destroy()

        
    def create_symbol_inputs(self, label, spinboxes, row):
        """요구 심볼과 증여 심볼 입력을 생성."""
        frame = tk.Frame(self.root)
        frame.grid(row=row, column=1, sticky="nsew", padx=5, pady=5)
        symbols = ["Influence", "Unity", "Monotheism", "Polytheism", "Strength", "Pantheon"]
        for symbol in symbols:
            tk.Label(frame, text=symbol).pack(side="left", padx=2)
            spinbox = tk.Spinbox(frame, from_=0, to=100)
            spinbox.pack(side="left", padx=2)
            spinboxes[symbol] = spinbox

    def get_detail_effects(self):
        effects = []
        for detail in self.detail_effects:
            effect_var = detail["effect_var"]
            spinbox = detail["value_entry"]
            trigger_var = detail["trigger_var"]
            target_var = detail["target_var"]
            effect_name = effect_var.get()
            if effect_name != "선택":
                effects.append({
                    "Effect": effect_name,
                    "Count": int(spinbox.get()),
                    "Trigger": trigger_var.get(),
                    "Target": target_var.get(),
                    "Priority": 1
                })
        return effects


    def get_symbols(self, spinboxes):
        """심볼 데이터 가져오기."""
        return {k: int(v.get()) for k, v in spinboxes.items()}

    def save_card(self):
        card_name = self.name_entry.get().strip() or "card"
        card_data = {
            "Number": int(self.number_spinbox.get()),
            "Name": card_name,
            "Description": self.description_text.get("1.0", tk.END).strip(),
            "Effect": self.effect_text.get("1.0", tk.END).strip(),
            "Detail": self.get_detail_effects(),
            "Kind": self.species_var.get(),
            "Symbol_R": self.get_symbols(self.requirement_spinboxes),
            "Symbol_G": self.get_symbols(self.gift_spinboxes),
            "Cultist": int(self.follower_spinbox.get()),
            "Junction": int(self.path_spinbox.get()),
            "ImagePath": self.image_entry.get().strip(),
            "SoundPath": self.sound_entry.get().strip()
        }

        temp_dir = tempfile.mkdtemp()
        json_path = os.path.join(temp_dir, "card.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(card_data, f, ensure_ascii=False, indent=2)

        # 이미지 복사
        image_src = self.get_absolute_path(card_data["ImagePath"])
        if os.path.isfile(image_src):
            shutil.copy(image_src, os.path.join(temp_dir, "image.png"))

        # 사운드 복사
        sound_src = self.get_absolute_path(card_data["SoundPath"])
        if os.path.isfile(sound_src):
            shutil.copy(sound_src, os.path.join(temp_dir, "sound.mp3"))

        # 압축 저장
        save_path = filedialog.asksaveasfilename(
            defaultextension=".cardpkg",
            filetypes=[("Card Package", "*.cardpkg")],
            initialfile=f"{card_name}.cardpkg"
        )
        if save_path:
            with zipfile.ZipFile(save_path, "w") as zipf:
                for fname in os.listdir(temp_dir):
                    zipf.write(os.path.join(temp_dir, fname), arcname=fname)
            shutil.rmtree(temp_dir)
            messagebox.showinfo("저장 완료", f"{save_path} 로 카드가 저장되었습니다.")

    def reset_all(self):
        """모든 필드를 초기화."""
        self.number_spinbox.delete(0, tk.END)
        self.number_spinbox.insert(0, "0")
        self.name_entry.delete(0, tk.END)
        self.description_text.delete("1.0", tk.END)
        self.effect_text.delete("1.0", tk.END)
        self.follower_spinbox.delete(0, tk.END)
        self.follower_spinbox.insert(0, "0")
        self.path_spinbox.delete(0, tk.END)
        self.path_spinbox.insert(0, "0")
        self.species_var.set("일반")

        # 이미지 경로 초기화
        self.image_entry.delete(0, tk.END)
        self.image_preview_label.config(image=None)
        self.image_preview_label.image = None

        # 사운드 경로 초기화 및 정지
        self.sound_entry.delete(0, tk.END)
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception as e:
            print(f"[사운드 정지 실패] {e}")

        # 세부 효과 초기화
        for widget in self.detail_effect_frame.winfo_children():
            widget.destroy()
        self.detail_effects.clear()
        self.used_effects.clear()
        self.create_detail_effect_row()

        # 요구 및 증여 심볼 초기화
        for spinbox in self.requirement_spinboxes.values():
            spinbox.delete(0, tk.END)
            spinbox.insert(0, 0)
        for spinbox in self.gift_spinboxes.values():
            spinbox.delete(0, tk.END)
            spinbox.insert(0, 0)

        # 미리보기 JSON 초기화
        self.update_preview()

        messagebox.showinfo("초기화 완료", "모든 필드가 초기화되었습니다.")

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        cards_folder = os.path.join(desktop_path, "Cards")
        os.makedirs(cards_folder, exist_ok=True)

        cards_file = os.path.join(cards_folder, "Card_Data.json")
        all_cards = []

        # 기존 cards.json 읽기
        if os.path.exists(cards_file):
            with open(cards_file, "r", encoding="utf-8") as file:
                try:
                    existing_data = json.load(file)
                    all_cards = existing_data.get("cards", [])
                except json.JSONDecodeError:
                    messagebox.showwarning("경고", "기존 cards.json 파일이 손상되었습니다. 새로 생성합니다.")

        # 새 JSON 파일 데이터 추가
        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    card_data = json.load(file)
                    if isinstance(card_data, dict):
                        all_cards.append(card_data)
                    elif isinstance(card_data, list):
                        all_cards.extend(card_data)
                    else:
                        messagebox.showwarning("경고", f"{file_path}의 형식이 잘못되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"{file_path} 파일을 읽는 중 오류 발생: {e}")

        # Number 기준으로 정렬
        all_cards = sorted(all_cards, key=lambda card: card.get("Number", 0))

        # 중복 제거
        seen_numbers = set()
        unique_cards = []
        for card in all_cards:
            card_number = card.get("Number")
            if card_number not in seen_numbers:
                seen_numbers.add(card_number)
                unique_cards.append(card)

        # cards.json에 저장
        with open(cards_file, "w", encoding="utf-8") as file:
            json.dump({"cards": unique_cards}, file, ensure_ascii=False, indent=4)

        messagebox.showinfo("완료", "JSON 파일이 성공적으로 추가되고 정렬되었습니다.")

        
    def load_card(self):
        """JSON 파일을 불러와 데이터를 GUI에 로드."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                card_data = json.load(file)

            # 기본 필드 로드
            self.number_spinbox.delete(0, tk.END)
            self.number_spinbox.insert(0, card_data.get("Number", 0))
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, card_data.get("Name", ""))
            self.description_text.delete("1.0", tk.END)
            self.description_text.insert("1.0", card_data.get("Description", ""))
            self.effect_text.delete("1.0", tk.END)
            self.effect_text.insert("1.0", card_data.get("Effect", ""))
            
            self.image_entry.delete(0, tk.END)
            self.image_entry.insert(0, card_data.get("ImagePath", ""))
            self.show_image_preview()

            self.sound_entry.delete(0, tk.END)
            self.sound_entry.insert(0, card_data.get("SoundPath", ""))

            
            # 세부효과 로드
            for widget in self.detail_effect_frame.winfo_children():
                widget.destroy()
            self.detail_effects.clear()
            self.used_effects.clear()
            for effect_name, value in card_data.get("Detail", {}).items():
                effect_var = tk.StringVar(value=effect_name)
                value_spinbox = tk.Spinbox(self.detail_effect_frame, from_=0, to=100, value=value)
                self.create_detail_effect_row()
                self.detail_effects[-1] = (effect_var, value_spinbox)

            # 종족 및 심볼 로드
            self.species_var.set(card_data.get("Kind", "일반"))
            for symbol, spinbox in self.requirement_spinboxes.items():
                spinbox.delete(0, tk.END)
                spinbox.insert(0, card_data.get("Symbol_R", {}).get(symbol, 0))
            for symbol, spinbox in self.gift_spinboxes.items():
                spinbox.delete(0, tk.END)
                spinbox.insert(0, card_data.get("Symbol_G", {}).get(symbol, 0))
            self.follower_spinbox.delete(0, tk.END)
            self.follower_spinbox.insert(0, card_data.get("Cultist", 0))
            self.path_spinbox.delete(0, tk.END)
            self.path_spinbox.insert(0, card_data.get("Junction", 0))

            messagebox.showinfo("완료", "카드 데이터가 성공적으로 로드되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"JSON 파일을 불러오는 중 오류 발생: {e}")

    def save_modified_card(self):
        """수정된 데이터를 JSON 파일로 저장."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")]
        )
        if not file_path:
            return

        try:
            # 현재 GUI 데이터를 JSON 형태로 변환
            card_data = {
                "Number": int(self.number_spinbox.get()),
                "Name": self.name_entry.get(),
                "Description": self.description_text.get("1.0", tk.END).strip(),
                "Effect": self.effect_text.get("1.0", tk.END).strip(),
                "Detail": self.get_detail_effects(),
                "Kind": self.species_var.get(),
                "Symbol_R": self.get_symbols(self.requirement_spinboxes),
                "Symbol_G": self.get_symbols(self.gift_spinboxes),
                "Cultist": int(self.follower_spinbox.get()),
                "Junction": int(self.path_spinbox.get()),
            }

            # JSON 파일에 저장
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(card_data, file, ensure_ascii=False, indent=4)

            messagebox.showinfo("완료", "카드 데이터가 성공적으로 저장되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"JSON 파일을 저장하는 중 오류 발생: {e}")

    def update_preview(self):
        """현재 카드 정보를 실시간으로 JSON 텍스트로 미리보기."""
        try:
            card_data = {
                "Number": int(self.number_spinbox.get()),
                "Name": self.name_entry.get(),
                "Description": self.description_text.get("1.0", tk.END).strip(),
                "Effect": self.effect_text.get("1.0", tk.END).strip(),
                "Detail": self.get_detail_effects(),
                "Kind": self.species_var.get(),
                "Symbol_R": self.get_symbols(self.requirement_spinboxes),
                "Symbol_G": self.get_symbols(self.gift_spinboxes),
                "Cultist": int(self.follower_spinbox.get()),
                "Junction": int(self.path_spinbox.get()),
            }
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", json.dumps(card_data, ensure_ascii=False, indent=2))
        except Exception as e:
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", f"오류: {e}")
            
            
    def analyze_effect_text(self, text):
        """Effect 자연어 설명을 기반으로 Detail 자동 분석"""
        effects = []
        clean = text.replace(" ", "").replace("\n", "")

        def contains_any(keywords):
            return any(keyword in clean for keyword in keywords)

        def add_effect(effect_name, count, trigger, target):
            effects.append({
                "Effect": effect_name,
                "Count": count,
                "Trigger": trigger,
                "Target": target,
                "Priority": len(effects) + 1  # 이 시점의 길이에 따라 우선순위 설정
            })

        # 개별 효과 추출
        if contains_any(["만신전", "신을얻", "만신전을얻", "만신전을획득"]):
            trigger = "OnStart" if contains_any(["게임시작", "시작할때", "처음에"]) else "OnFlip"
            add_effect("GainPantheon", 1, trigger, "Self")

        if contains_any(["상대신도", "적신도", "상대의신도", "상대방의신도", "적의신도", "카드를파괴", "상대파괴"]):
            add_effect("DestroyEnemyCultist", 1, "OnFlip", "OtherPlayer")

        if contains_any(["카드를얻", "덱에서", "1장얻", "카드한장", "추가로얻"]):
            add_effect("DrawFromDeck", 1, "OnFlip", "None")

        if contains_any(["기아를받", "기아상태", "기아에빠짐"]):
            add_effect("GainFamine", 1, "OnFlip", "Self")

        if contains_any(["희생", "신도를희생", "카드를희생", "제물로바침"]):
            add_effect("SacrificeOther", 1, "OnFlip", "OwnCultist")

        if not effects:
            add_effect("Unknown", 1, "OnFlip", "None")

        return effects

    def fill_detail_from_effect(self):
        """Effect 텍스트를 기반으로 Detail 자동 채우기"""
        text = self.effect_text.get("1.0", tk.END).strip()
        details = self.analyze_effect_text(text)

        # 기존 Detail 행 초기화
        for widget in self.detail_effect_frame.winfo_children():
            widget.destroy()
        self.detail_effects.clear()
        self.used_effects.clear()

        # 분석된 Detail 내용 채워넣기
        for item in details:
            self.create_detail_effect_row(
                effect=item["Effect"],
                count=item["Count"],
                trigger=item.get("Trigger", "OnFlip"),
                target=item.get("Target", "None")
            )

        self.update_preview()

    def show_image_preview(self):
        relative_path = self.image_entry.get()
        try:
            abs_path = self.get_absolute_path(relative_path)
            img = Image.open(abs_path)
            img = img.resize((150, 200))
            photo = ImageTk.PhotoImage(img)
            self.image_preview_label.config(image=photo)
            self.image_preview_label.image = photo  # 참조 유지
        except Exception as e:
            messagebox.showerror("이미지 오류", f"이미지를 불러올 수 없습니다: {e}")

    def select_image_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")],
            title="카드 이미지 선택"
        )
        if filepath:
            cards_root = os.path.join(os.path.expanduser("~"), "Desktop", "Cards")
            try:
                if os.path.splitdrive(filepath)[0] != os.path.splitdrive(cards_root)[0]:
                    raise ValueError("다른 드라이브")
                relative_path = os.path.relpath(filepath, cards_root)
            except ValueError:
                relative_path = filepath  # 절대 경로 유지

            self.image_entry.delete(0, tk.END)
            self.image_entry.insert(0, relative_path)
            self.show_image_preview()

    def select_sound_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Sound Files", "*.mp3 *.wav")],
            title="사운드 파일 선택"
        )
        if filepath:
            cards_root = os.path.join(os.path.expanduser("~"), "Desktop", "Cards")
            try:
                if os.path.splitdrive(filepath)[0] != os.path.splitdrive(cards_root)[0]:
                    raise ValueError("다른 드라이브")
                relative_path = os.path.relpath(filepath, cards_root)
            except ValueError:
                relative_path = filepath

            self.sound_entry.delete(0, tk.END)
            self.sound_entry.insert(0, relative_path)

    def get_absolute_path(self, path):
        if os.path.isabs(path):
            return path
        cards_path = os.path.join(os.path.expanduser("~"), "Desktop", "Cards")
        return os.path.join(cards_path, path)


    def play_sound(self):
        relative_path = self.sound_entry.get()
        try:
            abs_path = self.get_absolute_path(relative_path)
            pygame.mixer.music.load(abs_path)
            pygame.mixer.music.play()
        except Exception as e:
            messagebox.showerror("사운드 오류", f"사운드를 재생할 수 없습니다: {e}")
            
    def stop_sound(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception as e:
            print(f"[사운드 정지 실패] {e}")

    def switch_language(self, event=None):
        selected_label = self.language_var.get()
        lang = self.language_codes.get(selected_label, "ko")
        self.language_var.set(selected_label)
        L = self.languages.get(lang, self.languages["ko"])

        self.label_number.config(text=L["number"])
        self.label_name.config(text=L["name"])
        self.label_description.config(text=L["description"])
        self.label_effect.config(text=L["effect"])
        self.button_analyze.config(text=L["auto_analyze"])
        self.label_detail_effect.config(text=L["detail_effect"])
        self.label_species.config(text=L["species"])
        self.label_require_symbol.config(text=L["require_symbol"])
        self.label_gift_symbol.config(text=L["gift_symbol"])
        self.label_cultist.config(text=L["cultist"])
        self.label_junction.config(text=L["junction"])
        self.label_image_path.config(text=L["image_path"])
        self.button_image_browse.config(text=L["search"])
        self.button_image_preview.config(text=L["preview"])
        self.label_sound_path.config(text=L["sound_path"])
        self.button_sound_browse.config(text=L["search"])
        self.button_sound_play.config(text=L["play"])
        self.button_sound_stop.config(text=L["stop"])
        self.button_save.config(text=L["save"])
        self.button_reset.config(text=L["reset"])
        self.button_merge.config(text=L["merge"])
        self.button_load.config(text=L["load"])
        self.button_modify.config(text=L["modify"])

        # 효과 설명 라벨 갱신
        for detail in self.detail_effects:
            effect_key = detail["effect_var"].get()
            label = detail.get("description_label")
            if label and effect_key in self.effect_descriptions:
                desc = self.effect_descriptions[effect_key].get(lang, "")
                label.config(text=desc)

    def show_effect_description(self, effect_var):
        effect_key = effect_var.get()
        lang_code = self.language_codes.get(self.language_selector.get(), "ko")
        desc_dict = self.effect_descriptions.get(effect_key, {})
        desc = desc_dict.get(lang_code, "설명이 없습니다.")
        messagebox.showinfo("효과 설명", desc)

if __name__ == "__main__":
    root = tk.Tk()
    app = CardCreatorApp(root)
    root.mainloop()
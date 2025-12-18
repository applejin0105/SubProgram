import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import shutil
import json
import os
import zipfile
import tempfile
import pygame

# --- 설정 및 데이터 ---
class Config:
    SYMBOLS = ["Influence", "Unity", "Monotheism", "Polytheism", "Strength", "Pantheon"]
    
    LANGUAGES = {
        "ko": {
            "id": "번호 (ID)", "name": "이름", "description": "설명", "effect": "효과 텍스트",
            "auto_analyze": "자동 분석", "species": "종족", "require_symbol": "요구 심볼",
            "gift_symbol": "제공 심볼", "cultist": "신도 수", "junction": "갈림길",
            "image_path": "이미지 경로", "sound_path": "사운드 경로",
            "search": "찾기", "preview": "미리보기", "play": "재생", "stop": "정지",
            "save": "저장 (.cardpkg)", "json_save": "JSON 저장", "load": "불러오기", 
            "reset": "초기화", "detail_effect": "세부 효과(로직용)",
            "is_root": "루트 카드 여부 (IsRoot)", "religion": "종교 태그 (쉼표로 구분)",
            "header_info": "기본 정보", "header_stats": "스탯 설정", "header_media": "미디어"
        },
        "en": {
            "id": "ID", "name": "Name", "description": "Description", "effect": "Effect Text",
            "auto_analyze": "Auto Analyze", "species": "Species", "require_symbol": "Required Symbols",
            "gift_symbol": "Gifted Symbols", "cultist": "Cultists", "junction": "Junction",
            "image_path": "Image Path", "sound_path": "Sound Path",
            "search": "Browse", "preview": "Preview", "play": "Play", "stop": "Stop",
            "save": "Save Package", "json_save": "Save JSON", "load": "Load JSON", 
            "reset": "Reset", "detail_effect": "Detail Effects",
            "is_root": "Is Root Card", "religion": "Religion Tags (comma separated)",
            "header_info": "Basic Info", "header_stats": "Stats", "header_media": "Media"
        },
        "ja": {
            "id": "番号 (ID)",
            "name": "名前",
            "description": "説明",
            "effect": "効果テキスト",
            "auto_analyze": "自動分析",
            "species": "種族",
            "require_symbol": "要求シンボル",
            "gift_symbol": "提供シンボル",
            "cultist": "信者数",
            "junction": "分岐点",
            "image_path": "画像パス",
            "sound_path": "音声パス",
            "search": "参照",
            "preview": "プレビュー",
            "play": "再生",
            "stop": "停止",
            "save": "パッケージ保存",
            "json_save": "JSON保存",
            "load": "読み込み",
            "reset": "初期化",
            "detail_effect": "詳細効果",
            "is_root": "ルートカード (IsRoot)",
            "religion": "宗教タグ (カンマ区切り)",
            "header_info": "基本情報",
            "header_stats": "ステータス設定",
            "header_media": "メディア"
        },
        "zh": {
            "id": "编号 (ID)",
            "name": "名称",
            "description": "描述",
            "effect": "效果文本",
            "auto_analyze": "自动分析",
            "species": "种族",
            "require_symbol": "需求符号",
            "gift_symbol": "提供符号",
            "cultist": "信徒数",
            "junction": "交叉点",
            "image_path": "图片路径",
            "sound_path": "音频路径",
            "search": "浏览",
            "preview": "预览",
            "play": "播放",
            "stop": "停止",
            "save": "保存包",
            "json_save": "保存 JSON",
            "load": "加载",
            "reset": "重置",
            "detail_effect": "详细效果",
            "is_root": "根卡 (IsRoot)",
            "religion": "宗教标签（逗号分隔）",
            "header_info": "基本信息",
            "header_stats": "属性设置",
            "header_media": "媒体"
        }
    }

class CardCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cultist Simulator Card Creator")
        self.root.geometry("530x1060")

        # 상태 변수 초기화
        self.current_lang = "ko"
        self.image_ref = None # 이미지 가비지 컬렉션 방지
        
        # Pygame 사운드 초기화
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"[Warning] Sound init failed: {e}")

        # UI 구성요소 저장소
        self.widgets = {}
        self.symbol_vars_r = [] # 요구 심볼 변수 리스트
        self.symbol_vars_g = [] # 제공 심볼 변수 리스트
        self.detail_effects = [] # 세부 효과 리스트

        # UI 생성
        self._init_variables()
        self._create_menu()
        self._create_main_layout()
        
        # 초기 갱신
        self.update_preview()

    def _init_variables(self):
        """Tkinter 변수 초기화"""
        self.var_id = tk.IntVar(value=0)
        self.var_name = tk.StringVar()
        self.var_species = tk.StringVar(value="일반")
        self.var_cultist = tk.IntVar(value=0)
        self.var_junction = tk.IntVar(value=0)
        self.var_is_root = tk.BooleanVar(value=False)
        self.var_religion = tk.StringVar() # "Gre, Pho" 형태의 문자열
        self.var_image_path = tk.StringVar()
        self.var_sound_path = tk.StringVar()
        
        # 심볼 변수 (순서대로 6개)
        self.symbol_vars_r = [tk.IntVar(value=0) for _ in range(6)]
        self.symbol_vars_g = [tk.IntVar(value=0) for _ in range(6)]

    def _create_menu(self):
        """상단 언어 선택 메뉴"""
        top_frame = tk.Frame(self.root, bg="#ddd", pady=5)
        top_frame.pack(fill="x")
        
        tk.Label(top_frame, text="Language: ", bg="#ddd").pack(side="left", padx=10)
        self.lang_combo = ttk.Combobox(top_frame, values=["한국어", "English", "日本語", "中文"], state="readonly", width=10)
        self.lang_combo.current(0)
        self.lang_combo.pack(side="left")
        self.lang_combo.bind("<<ComboboxSelected>>", self.switch_language)

    def _create_main_layout(self):
        """메인 스크롤 가능한 영역 생성"""
        # 전체 캔버스 설정
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 내부 컨텐츠 생성
        self._create_header_section(self.scrollable_frame)
        ttk.Separator(self.scrollable_frame, orient='horizontal').pack(fill='x', pady=10)
        self._create_stats_section(self.scrollable_frame)
        ttk.Separator(self.scrollable_frame, orient='horizontal').pack(fill='x', pady=10)
        self._create_media_section(self.scrollable_frame)
        ttk.Separator(self.scrollable_frame, orient='horizontal').pack(fill='x', pady=10)
        self._create_json_preview(self.scrollable_frame)
        
        # 하단 버튼
        self._create_footer_buttons(self.scrollable_frame)

    def _create_header_section(self, parent):
        """기본 정보 입력 (ID, 이름, 설명, 효과 등)"""
        frame = tk.LabelFrame(parent, text="기본 정보", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)
        self.widgets['group_info'] = frame

        # Grid Layout
        grid_opts = {'padx': 5, 'pady': 5, 'sticky': 'w'}
        
        # 1. ID & 이름
        self.widgets['lbl_id'] = tk.Label(frame, text="ID")
        self.widgets['lbl_id'].grid(row=0, column=0, **grid_opts)
        tk.Spinbox(frame, from_=0, to=99999, textvariable=self.var_id, width=10).grid(row=0, column=1, **grid_opts)

        self.widgets['lbl_name'] = tk.Label(frame, text="이름")
        self.widgets['lbl_name'].grid(row=0, column=2, **grid_opts)
        entry_name = tk.Entry(frame, textvariable=self.var_name)
        entry_name.grid(row=0, column=3, sticky="ew", padx=5)
        entry_name.bind("<KeyRelease>", self.update_preview)

        # 2. IsRoot & Religion
        self.widgets['chk_root'] = tk.Checkbutton(frame, text="IsRoot (루트 카드)", variable=self.var_is_root, command=self.update_preview)
        self.widgets['chk_root'].grid(row=1, column=0, columnspan=2, **grid_opts)

		# Religion 레이블 및 체크박스 프레임 생성
        self.widgets['lbl_religion'] = tk.Label(frame, text="Religion")
        self.widgets['lbl_religion'].grid(row=1, column=2, **grid_opts)

        rel_frame = tk.Frame(frame)
        rel_frame.grid(row=1, column=3, sticky="w", padx=5)

		# 종교 목록 정의 및 변수 생성 (클래스 __init__ 혹은 적절한 위치에 미리 정의되어 있어야 함)
        self.rel_vars = {rel: tk.BooleanVar(value=False) for rel in ["None", "Isl", "Cri", "Gre", "Pho"]}
        self.rel_vars["None"].set(True) 

        self.rel_chk_btns = {}
        for rel in ["None", "Isl", "Cri", "Gre", "Pho"]:
            btn = tk.Checkbutton(rel_frame, text=rel, 
								 variable=self.rel_vars[rel], 
								 command=lambda r=rel: self._on_religion_change(r))
            btn.pack(side="left", padx=2)
            self.rel_chk_btns[rel] = btn

        # 3. 설명 & 효과
        self.widgets['lbl_desc'] = tk.Label(frame, text="설명")
        self.widgets['lbl_desc'].grid(row=2, column=0, **grid_opts)
        self.txt_desc = tk.Text(frame, height=3, width=40)
        self.txt_desc.grid(row=2, column=1, columnspan=3, padx=5, pady=5)
        self.txt_desc.bind("<KeyRelease>", self.update_preview)

        self.widgets['lbl_effect'] = tk.Label(frame, text="효과 텍스트")
        self.widgets['lbl_effect'].grid(row=3, column=0, **grid_opts)
        self.txt_effect = tk.Text(frame, height=3, width=40)
        self.txt_effect.grid(row=3, column=1, columnspan=3, padx=5, pady=5)
        self.txt_effect.bind("<KeyRelease>", self.update_preview)

    def _create_stats_section(self, parent):
        """스탯 관련 (심볼, 신도수, 갈림길)"""
        frame = tk.LabelFrame(parent, text="스탯 설정", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)
        self.widgets['group_stats'] = frame

        # 심볼 입력 함수
        def create_symbol_row(row_idx, label_key, var_list):
            lbl = tk.Label(frame, text=label_key)
            lbl.grid(row=row_idx, column=0, sticky="w")
            self.widgets[f'lbl_{label_key}'] = lbl
            
            sub_frame = tk.Frame(frame)
            sub_frame.grid(row=row_idx, column=1, columnspan=3, sticky="w")
            
            for i, sym_name in enumerate(Config.SYMBOLS):
                tk.Label(sub_frame, text=sym_name[0:3], font=("Arial", 8)).pack(side="left", padx=2)
                sp = tk.Spinbox(sub_frame, from_=0, to=10, textvariable=var_list[i], width=3, command=self.update_preview)
                sp.pack(side="left")
                sp.bind("<KeyRelease>", self.update_preview)

        create_symbol_row(0, "require_symbol", self.symbol_vars_r)
        create_symbol_row(1, "gift_symbol", self.symbol_vars_g)

        # 기타 수치
        f_etc = tk.Frame(frame)
        f_etc.grid(row=2, column=0, columnspan=4, sticky="w", pady=10)
        
        self.widgets['lbl_cultist'] = tk.Label(f_etc, text="신도수")
        self.widgets['lbl_cultist'].pack(side="left", padx=5)
        tk.Spinbox(f_etc, from_=0, to=99, textvariable=self.var_cultist, width=5, command=self.update_preview).pack(side="left")
        
        self.widgets['lbl_junction'] = tk.Label(f_etc, text="갈림길")
        self.widgets['lbl_junction'].pack(side="left", padx=5)
        tk.Spinbox(f_etc, from_=0, to=99, textvariable=self.var_junction, width=5, command=self.update_preview).pack(side="left")

    def _create_media_section(self, parent):
        """이미지 및 사운드 경로"""
        frame = tk.LabelFrame(parent, text="미디어", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)
        self.widgets['group_media'] = frame

        # Image
        self.widgets['lbl_img'] = tk.Label(frame, text="이미지")
        self.widgets['lbl_img'].grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.var_image_path, width=40).grid(row=0, column=1, padx=5)
        self.widgets['btn_img_search'] = tk.Button(frame, text="찾기", command=self.select_image)
        self.widgets['btn_img_search'].grid(row=0, column=2)
        
        # Image Preview Area
        self.lbl_preview_img = tk.Label(frame, text="No Image", bg="#eee", width=20, height=10)
        self.lbl_preview_img.grid(row=1, column=1, pady=5)

        # Sound
        self.widgets['lbl_snd'] = tk.Label(frame, text="사운드")
        self.widgets['lbl_snd'].grid(row=2, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.var_sound_path, width=40).grid(row=2, column=1, padx=5)
        
        snd_btn_frame = tk.Frame(frame)
        snd_btn_frame.grid(row=2, column=2)
        self.widgets['btn_snd_search'] = tk.Button(snd_btn_frame, text="찾기", command=self.select_sound)
        self.widgets['btn_snd_search'].pack(side="left")
        self.widgets['btn_snd_play'] = tk.Button(snd_btn_frame, text="▶", command=self.play_sound)
        self.widgets['btn_snd_play'].pack(side="left")

    def _create_json_preview(self, parent):
        """JSON 미리보기 창"""
        frame = tk.LabelFrame(parent, text="JSON Preview", padx=5, pady=5)
        frame.pack(fill="both", padx=10, pady=5)
        
        self.txt_preview = tk.Text(frame, height=15, bg="#f0f0f0", font=("Consolas", 9))
        self.txt_preview.pack(fill="both", expand=True)

    def _create_footer_buttons(self, parent):
        frame = tk.Frame(parent, pady=20)
        frame.pack(fill="x")

        self.widgets['btn_reset'] = tk.Button(frame, text="초기화", command=self.reset_all, bg="#ffcccc")
        self.widgets['btn_reset'].pack(side="left", padx=10)

        self.widgets['btn_load'] = tk.Button(frame, text="불러오기", command=self.load_json)
        self.widgets['btn_load'].pack(side="right", padx=10)

        self.widgets['btn_save_json'] = tk.Button(frame, text="JSON 저장", command=self.save_json_file, bg="#ccffcc")
        self.widgets['btn_save_json'].pack(side="right", padx=10)

        self.widgets['btn_save_pkg'] = tk.Button(frame, text="패키지 저장", command=self.save_package)
        self.widgets['btn_save_pkg'].pack(side="right", padx=10)

    # --- 로직 함수들 ---

    def get_current_data(self):
        religion_list = [r for r, v in self.rel_vars.items() if v.get() and r != "None"]

        data = {
            "id": self.var_id.get(),
            "name": self.var_name.get(),
            "symbol_R": [v.get() for v in self.symbol_vars_r],
            "symbol_G": [v.get() for v in self.symbol_vars_g],
            "cultist": self.var_cultist.get(),
            "junction": self.var_junction.get(),
            "effect": self.txt_effect.get("1.0", tk.END).strip(),
            "description": self.txt_desc.get("1.0", tk.END).strip(),
            "IsRoot": 1 if self.var_is_root.get() else 0,
            "Religion": religion_list
        }
        return data


    def update_preview(self, event=None):
        """JSON 미리보기 갱신"""
        data = self.get_current_data()
        self.txt_preview.delete("1.0", tk.END)
        self.txt_preview.insert("1.0", json.dumps(data, ensure_ascii=False, indent=4))

    def switch_language(self, event=None):
        """언어 변경 로직 (버그 수정됨)"""
        selection = self.lang_combo.get()
        lang_map = {
            "한국어": "ko",
            "English": "en",
            "日本語": "ja",
            "中文": "zh",
        }
        lang_code = lang_map.get(selection, "ko")
        L = Config.LANGUAGES[lang_code]
        
        # 라벨 텍스트 업데이트
        self.widgets['group_info'].config(text=L['header_info'])
        self.widgets['lbl_id'].config(text=L['id'])
        self.widgets['lbl_name'].config(text=L['name'])
        self.widgets['chk_root'].config(text=L['is_root'])
        self.widgets['lbl_religion'].config(text=L['religion'])
        self.widgets['lbl_desc'].config(text=L['description'])
        self.widgets['lbl_effect'].config(text=L['effect'])
        
        self.widgets['group_stats'].config(text=L['header_stats'])
        self.widgets['lbl_require_symbol'].config(text=L['require_symbol'])
        self.widgets['lbl_gift_symbol'].config(text=L['gift_symbol'])
        self.widgets['lbl_cultist'].config(text=L['cultist'])
        self.widgets['lbl_junction'].config(text=L['junction'])
        
        self.widgets['group_media'].config(text=L['header_media'])
        self.widgets['lbl_img'].config(text=L['image_path'])
        self.widgets['btn_img_search'].config(text=L['search'])
        self.widgets['lbl_snd'].config(text=L['sound_path'])
        self.widgets['btn_snd_search'].config(text=L['search'])
        
        self.widgets['btn_reset'].config(text=L['reset'])
        self.widgets['btn_load'].config(text=L['load'])
        self.widgets['btn_save_json'].config(text=L['json_save'])
        self.widgets['btn_save_pkg'].config(text=L['save'])

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if path:
            self.var_image_path.set(path)
            self._load_preview_image(path)

    def _load_preview_image(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((150, 150))
            self.image_ref = ImageTk.PhotoImage(img)
            self.lbl_preview_img.config(image=self.image_ref, text="")
        except Exception:
            self.lbl_preview_img.config(image=None, text="Load Error")

    def select_sound(self):
        path = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.ogg")])
        if path:
            self.var_sound_path.set(path)

    def play_sound(self):
        path = self.var_sound_path.get()
        if path and os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
            except Exception as e:
                print(e)

    def reset_all(self):
        self._init_variables()
        self.txt_desc.delete("1.0", tk.END)
        self.txt_effect.delete("1.0", tk.END)
        self.lbl_preview_img.config(image=None, text="No Image")
        self.update_preview()

    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path: return
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 데이터 매핑
            self.var_id.set(data.get("id", 0))
            self.var_name.set(data.get("name", ""))
            self.var_cultist.set(data.get("cultist", 0))
            self.var_junction.set(data.get("junction", 0))
            self.var_is_root.set(bool(data.get("IsRoot", 0)))
            
            # Religion 리스트 -> 문자열
            rel = data.get("Religion", [])
            self.var_religion.set(", ".join(rel) if isinstance(rel, list) else str(rel))
            
            # Symbol 배열 매핑
            sym_r = data.get("symbol_R", [0]*6)
            sym_g = data.get("symbol_G", [0]*6)
            for i in range(6):
                if i < len(sym_r): self.symbol_vars_r[i].set(sym_r[i])
                if i < len(sym_g): self.symbol_vars_g[i].set(sym_g[i])

            self.txt_desc.delete("1.0", tk.END)
            self.txt_desc.insert("1.0", data.get("description", ""))
            self.txt_effect.delete("1.0", tk.END)
            self.txt_effect.insert("1.0", data.get("effect", ""))
            
            self.update_preview()
            messagebox.showinfo("로드 성공", "데이터를 불러왔습니다.")
            
        except Exception as e:
            messagebox.showerror("오류", f"파일 로드 중 오류: {e}")

    def save_json_file(self):
        data = self.get_current_data()
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("저장", "JSON 저장 완료")

    def save_package(self):
        """여러 JSON을 선택하여 하나의 JSON으로 합쳐 저장"""
        json_paths = filedialog.askopenfilenames(
            title="합칠 JSON 파일을 선택하세요",
            filetypes=[("JSON", "*.json")]
        )
        if not json_paths:
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if not save_path:
            return

        try:
            merged = []
            for p in json_paths:
                with open(p, "r", encoding="utf-8") as f:
                    merged.append(json.load(f))

            # 원하는 포맷으로 저장 (리스트 그대로 또는 dict로 래핑)
            out = {"cards": merged}

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=4)

            messagebox.showinfo("완료", "패키지(JSON 합치기)가 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"저장 중 오류 발생: {e}")
            
    def _on_religion_change(self, changed_rel: str):
    # None은 단독 선택(다른 것과 공존 불가) 규칙 예시
        if changed_rel == "None" and self.rel_vars["None"].get():
            for rel in self.rel_vars:
                if rel != "None":
                    self.rel_vars[rel].set(False)
        else:
            # 다른 종교가 하나라도 체크되면 None 해제
            if changed_rel != "None" and self.rel_vars[changed_rel].get():
                self.rel_vars["None"].set(False)

            # 모두 해제된 상태가 되면 None을 다시 켬(선택 정책)
            if not any(self.rel_vars[r].get() for r in self.rel_vars if r != "None"):
                self.rel_vars["None"].set(True)
                
        self.update_preview()


if __name__ == "__main__":
    root = tk.Tk()
    app = CardCreatorApp(root)
    root.mainloop()

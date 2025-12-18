import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageOps
import shutil
import json
import os
import pygame

# --- 설정 및 데이터 ---
class Config:
    SYMBOLS = ["Influence", "Unity", "Monotheism", "Polytheism", "Strength", "Pantheon"]
    
    LANGUAGES = {
        "ko": {
            "id": "번호 (ID)", "name": "이름", "description": "설명", "effect": "효과",
            "auto_analyze": "자동 분석", "species": "종족", "require_symbol": "요구 심볼",
            "gift_symbol": "제공 심볼", "cultist": "신도 수", "junction": "갈림길",
            "image_path": "이미지 경로", "sound_path": "사운드 경로",
            "search": "찾기", "preview": "미리보기", "play": "재생", "stop": "정지",
            "save": "저장 (.cardpkg)", "json_save": "JSON 저장", "load": "불러오기", 
            "reset": "초기화", "detail_effect": "세부 효과(로직용)",
            "is_root": "루트 카드 여부 (IsRoot)", "religion": "종교 태그 (쉼표로 구분)",
            "header_info": "기본 정보", "header_stats": "스탯 설정", "header_media": "미디어",
            "msg_title_error": "오류",
            "msg_title_saved": "저장",
            "msg_title_done": "완료",
            "msg_title_load_ok": "로드 성공",
            "msg_load_ok": "데이터를 불러왔습니다.",
            "msg_load_fail": "파일 로드 중 오류: {err}",
            "msg_id_not_int": "ID는 정수여야 합니다.",
            "msg_id_negative": "ID는 음수가 될 수 없습니다.",
            "msg_save_ok": "저장 완료:\n{path}",
            "msg_pkg_saved": "패키지(JSON 합치기)가 저장되었습니다.",
            "msg_pkg_fail": "저장 중 오류 발생: {err}",
            "msg_sound_no_file": "사운드 경로가 비어있습니다.",
            "msg_sound_missing": "사운드 파일을 찾을 수 없습니다:\n{path}",
            "msg_sound_play_fail": "사운드 재생 중 오류: {err}",
            "msg_sound_stop_fail": "사운드 중지 중 오류: {err}",
            "dlg_merge_select_title": "합칠 JSON 파일을 선택하세요",
            "msg_pkg_saved_auto": "cardDB.json 저장 완료:\n{path}",
            "msg_pkg_saved_with_overwrites": "cardDB.json 저장 완료:\n{path}\n\n중복 ID {count}건이 덮어쓰기 되었습니다.\n{detail}",
            "msg_pkg_overwrite_more": "... 외 {n}건 더 있습니다.",
            "msg_pkg_src_unknown": "(알 수 없음)"
        },
        "en": {
            "id": "ID", "name": "Name", "description": "Description", "effect": "Effect",
            "auto_analyze": "Auto Analyze", "species": "Species", "require_symbol": "Required Symbols",
            "gift_symbol": "Gifted Symbols", "cultist": "Cultists", "junction": "Junction",
            "image_path": "Image Path", "sound_path": "Sound Path",
            "search": "Browse", "preview": "Preview", "play": "Play", "stop": "Stop",
            "save": "Save Package", "json_save": "Save JSON", "load": "Load JSON", 
            "reset": "Reset", "detail_effect": "Detail Effects",
            "is_root": "Is Root Card", "religion": "Religion Tags (comma separated)",
            "header_info": "Basic Info", "header_stats": "Stats", "header_media": "Media",
            "msg_title_error": "Error",
            "msg_title_saved": "Saved",
            "msg_title_done": "Done",
            "msg_title_load_ok": "Load OK",
            "msg_load_ok": "Data loaded.",
            "msg_load_fail": "Error while loading file: {err}",
            "msg_id_not_int": "ID must be an integer.",
            "msg_id_negative": "ID cannot be negative.",
            "msg_save_ok": "Saved:\n{path}",
            "msg_pkg_saved": "Package (merged JSON) saved.",
            "msg_pkg_fail": "Error while saving: {err}",
            "msg_sound_no_file": "Sound path is empty.",
            "msg_sound_missing": "Sound file not found:\n{path}",
            "msg_sound_play_fail": "Error while playing sound: {err}",
            "msg_sound_stop_fail": "Error while stopping sound: {err}",
            "dlg_merge_select_title": "Select JSON files to merge",
            "msg_pkg_saved_auto": "Saved cardDB.json:\n{path}",
            "msg_pkg_saved_with_overwrites": "Saved cardDB.json:\n{path}\n\nOverwrote {count} duplicate ID(s).\n{detail}",
            "msg_pkg_overwrite_more": "... and {n} more.",
            "msg_pkg_src_unknown": "(unknown)"
        },
        "ja": {
            "id": "番号 (ID)",
            "name": "名前",
            "description": "説明",
            "effect": "効果",
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
            "header_media": "メディア",
            "msg_title_error": "エラー",
            "msg_title_saved": "保存",
            "msg_title_done": "完了",
            "msg_title_load_ok": "読み込み成功",
            "msg_load_ok": "データを読み込みました。",
            "msg_load_fail": "読み込み中にエラー: {err}",
            "msg_id_not_int": "IDは整数である必要があります。",
            "msg_id_negative": "IDは負の値にできません。",
            "msg_save_ok": "保存完了:\n{path}",
            "msg_pkg_saved": "パッケージ(JSON結合)を保存しました。",
            "msg_pkg_fail": "保存中にエラー: {err}",
            "msg_sound_no_file": "サウンドパスが空です。",
            "msg_sound_missing": "サウンドファイルが見つかりません:\n{path}",
            "msg_sound_play_fail": "サウンド再生中にエラー: {err}",
            "msg_sound_stop_fail": "サウンド停止中にエラー: {err}",
            "dlg_merge_select_title": "結合するJSONファイルを選択してください",
            "msg_pkg_saved_auto": "cardDB.json を保存しました:\n{path}",
            "msg_pkg_saved_with_overwrites": "cardDB.json を保存しました:\n{path}\n\n重複ID {count}件を上書きしました。\n{detail}",
            "msg_pkg_overwrite_more": "... 他 {n}件",
            "msg_pkg_src_unknown": "(不明)"
        },
        "zh": {
            "id": "编号 (ID)",
            "name": "名称",
            "description": "描述",
            "effect": "效果",
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
            "header_media": "媒体",
            "msg_title_error": "错误",
            "msg_title_saved": "已保存",
            "msg_title_done": "完成",
            "msg_title_load_ok": "加载成功",
            "msg_load_ok": "已加载数据。",
            "msg_load_fail": "加载文件时出错: {err}",
            "msg_id_not_int": "ID 必须是整数。",
            "msg_id_negative": "ID 不能为负数。",
            "msg_save_ok": "保存完成:\n{path}",
            "msg_pkg_saved": "已保存包（合并 JSON）。",
            "msg_pkg_fail": "保存时出错: {err}",
            "msg_sound_no_file": "音频路径为空。",
            "msg_sound_missing": "找不到音频文件:\n{path}",
            "msg_sound_play_fail": "播放音频时出错: {err}",
            "msg_sound_stop_fail": "停止音频时出错: {err}",
            "dlg_merge_select_title": "选择要合并的 JSON 文件",
            "msg_pkg_saved_auto": "已保存 cardDB.json:\n{path}",
            "msg_pkg_saved_with_overwrites": "已保存 cardDB.json:\n{path}\n\n已覆盖 {count} 个重复ID。\n{detail}",
            "msg_pkg_overwrite_more": "... 还有 {n} 条",
            "msg_pkg_src_unknown": "(未知)"
        }
    }

class CardCreatorApp:
    def __init__(self, root):
        self.root = root
        self.save_mode = "single"  # "single" 또는 "db"
        self.loaded_card_id = None  # 불러온 카드의 원래 id (id 변경 감지용)
        self.root.title("Cultist Simulator Card Creator")
        self.root.geometry("620x900")

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
        self.loaded_db_path = None  # 불러온 DB/패키지 json 경로(저장 시 이 파일에 덮어쓰기)

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
        
        # Religion 체크박스 변수 (UI 생성 전에 준비)
        self.rel_vars = {rel: tk.BooleanVar(value=False) for rel in ["None", "Isl", "Cri", "Gre", "Pho"]}
        self.rel_vars["None"].set(True)

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
        self.canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)


        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
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
        self._bind_mousewheel(self.canvas, self.scrollable_frame)

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

        self.rel_chk_btns = {}
        for rel in ["None", "Isl", "Cri", "Gre", "Pho"]:
            btn = tk.Checkbutton(rel_frame, text=rel, 
								 variable=self.rel_vars[rel], 
								 command=lambda r=rel: self._on_religion_change(r))
            btn.pack(side="left", padx=2)
            self.rel_chk_btns[rel] = btn

        # 3. 설명 & 효과
        self.widgets['lbl_effect'] = tk.Label(frame, text=self._t("effect"))
        self.widgets['lbl_effect'].grid(row=2, column=0, **grid_opts)
        self.txt_effect = tk.Text(frame, height=3, width=40)
        self.txt_effect.grid(row=2, column=1, columnspan=3, padx=5, pady=5)
        self.txt_effect.bind("<KeyRelease>", self.update_preview)

        self.widgets['lbl_desc'] = tk.Label(frame, text=self._t("description"))
        self.widgets['lbl_desc'].grid(row=3, column=0, **grid_opts)
        self.txt_desc = tk.Text(frame, height=3, width=40)
        self.txt_desc.grid(row=3, column=1, columnspan=3, padx=5, pady=5)
        self.txt_desc.bind("<KeyRelease>", self.update_preview)

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
        self.lbl_preview_img = tk.Label(frame, text="No Image", bg="#eee")
        self.lbl_preview_img.grid(row=1, column=1, pady=5, sticky="n")

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
        # Religion 저장 규칙:
        # - 다른 종교가 하나라도 있으면 그것만 저장
        # - 아무 것도 없으면 ["None"] 저장
        selected = [r for r, v in self.rel_vars.items() if v.get() and r != "None"]

        if selected:
            religion_list = selected
        else:
            religion_list = ["None"]

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
        self.current_lang = lang_code
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
            box = (256, 256)  # 원하는 미리보기 최대 크기
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)  # 회전 정보 보정(스마트폰 사진 등)
            img = ImageOps.contain(img, box)    # 비율 유지하며 box 안에 들어가게
            self.image_ref = ImageTk.PhotoImage(img)
            self.lbl_preview_img.config(image=self.image_ref, text="")
        except Exception:
            self.image_ref = None
            self.lbl_preview_img.config(image=None, text="Load Error")


    def select_sound(self):
        path = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.ogg")])
        if path:
            self.var_sound_path.set(path)

    def play_sound(self):
        path = self.var_sound_path.get().strip()
        if not path:
            messagebox.showerror(self._t("msg_title_error"), self._t("msg_sound_no_file"))
            return
        if not os.path.exists(path):
            messagebox.showerror(self._t("msg_title_error"), self._t("msg_sound_missing", path=path))
            return

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as e:
            messagebox.showerror(self._t("msg_title_error"), self._t("msg_sound_play_fail", err=e))

    def reset_all(self):
        # 변수 객체는 재생성하지 말고 값만 초기화
        self.loaded_card_id = None
        self.save_mode = "single"
        self.var_id.set(0)
        self.var_name.set("")
        self.var_species.set("일반")
        self.var_cultist.set(0)
        self.var_junction.set(0)
        self.var_is_root.set(False)
        self.var_religion.set("")
        self.var_image_path.set("")
        self.var_sound_path.set("")
        
        for v in self.symbol_vars_r:
            v.set(0)
        for v in self.symbol_vars_g:
            v.set(0)

        # Religion 체크박스 초기화
        for k in self.rel_vars:
            self.rel_vars[k].set(False)
        self.rel_vars["None"].set(True)
        
        # 텍스트/이미지 UI 초기화
        self.txt_desc.delete("1.0", tk.END)
        self.txt_effect.delete("1.0", tk.END)
        self.lbl_preview_img.config(image=None, text="No Image")
        self.image_ref = None

        self.update_preview()
        self.loaded_db_path = None

    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path:
            return

        fname = os.path.basename(file_path).lower()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                obj = json.load(f)

            # 단일/패키지/배열 모두 카드 리스트로 추출
            cards = self._extract_cards(obj)

            # 저장 모드 결정
            # - cardDB.json을 열면 DB 모드
            # - 그 외는 single 모드(0.json 등 단일 카드 파일 포함)
            if fname == "carddb.json":
                self.save_mode = "db"
                self.loaded_db_path = file_path
            else:
                self.save_mode = "single"
                self.loaded_db_path = file_path

            # 어떤 카드 1장을 UI에 반영할지 선택
            def _pick_card():
                if not cards:
                    return obj if isinstance(obj, dict) else {}
                if len(cards) == 1:
                    return cards[0]

                # 여러 장이면: 파일명이 숫자면 그 id 우선, 아니면 현재 UI id 우선, 아니면 첫 번째
                target_id = None
                base = os.path.splitext(os.path.basename(file_path))[0]
                if base.isdigit():
                    target_id = int(base)
                else:
                    try:
                        target_id = int(self.var_id.get())
                    except Exception:
                        target_id = None

                if target_id is not None:
                    for c in cards:
                        try:
                            if int(c.get("id")) == target_id:
                                return c
                        except Exception:
                            pass
                return cards[0]

            data = _pick_card()

            # 불러온 카드의 원래 id 저장(이후 id 변경 감지용)
            try:
                self.loaded_card_id = int(data.get("id", 0))
            except Exception:
                self.loaded_card_id = None

            # 기본 데이터 매핑
            self.var_id.set(int(data.get("id", 0)))
            self.var_name.set(data.get("name", ""))
            self.var_cultist.set(int(data.get("cultist", 0)))
            self.var_junction.set(int(data.get("junction", 0)))
            self.var_is_root.set(bool(data.get("IsRoot", 0)))

            # Religion 체크박스 동기화 (None 규칙 포함)
            rel = data.get("Religion", [])
            if isinstance(rel, list):
                rel_list = [str(x).strip() for x in rel if str(x).strip()]
            elif isinstance(rel, str):
                rel_list = [x.strip() for x in rel.split(",") if x.strip()]
            else:
                rel_list = []

            for k in self.rel_vars:
                self.rel_vars[k].set(False)

            if rel_list == ["None"] or not rel_list:
                self.rel_vars["None"].set(True)
            else:
                for r in rel_list:
                    if r in self.rel_vars:
                        self.rel_vars[r].set(True)
                self.rel_vars["None"].set(False)

            # Symbol
            sym_r = data.get("symbol_R", [0] * 6)
            sym_g = data.get("symbol_G", [0] * 6)
            for i in range(6):
                self.symbol_vars_r[i].set(int(sym_r[i]) if i < len(sym_r) else 0)
                self.symbol_vars_g[i].set(int(sym_g[i]) if i < len(sym_g) else 0)

            # 텍스트
            self.txt_desc.delete("1.0", tk.END)
            self.txt_desc.insert("1.0", data.get("description", ""))

            self.txt_effect.delete("1.0", tk.END)
            self.txt_effect.insert("1.0", data.get("effect", ""))

            # 이미지/사운드: JSON에 경로가 없으므로 id 기반으로 탐색
            dirs = self._ensure_cards_dirs()
            card_id = int(data.get("id", 0))

            img_path = ""
            for ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
                cand = os.path.join(dirs["images"], f"{card_id}{ext}")
                if os.path.exists(cand):
                    img_path = cand
                    break

            snd_path = ""
            for ext in (".wav", ".mp3", ".ogg"):
                cand = os.path.join(dirs["sounds"], f"{card_id}{ext}")
                if os.path.exists(cand):
                    snd_path = cand
                    break

            self.var_image_path.set(img_path)
            if img_path:
                self._load_preview_image(img_path)
            else:
                self.image_ref = None
                self.lbl_preview_img.config(image=None, text="No Image")

            self.var_sound_path.set(snd_path)

            self.update_preview()
            messagebox.showinfo(self._t("msg_title_load_ok"), self._t("msg_load_ok"))

        except Exception as e:
            messagebox.showerror(self._t("msg_title_error"), self._t("msg_load_fail", err=e))

    def save_json_file(self):
        try:
            data = self.get_current_data()

            raw_id = str(self.var_id.get()).strip()
            try:
                card_id = int(raw_id)
            except ValueError:
                messagebox.showerror(self._t("msg_title_error"), self._t("msg_id_not_int"))
                return

            if card_id < 0:
                messagebox.showerror(self._t("msg_title_error"), self._t("msg_id_negative"))
                return

            dirs = self._ensure_cards_dirs()

            # 기본 저장 경로
            json_dir = os.path.join(dirs["root"], "JSON")
            os.makedirs(json_dir, exist_ok=True)
            default_single_path = os.path.join(json_dir, f"{card_id}.json")

            db_dir = os.path.join(dirs["root"], "DB")
            os.makedirs(db_dir, exist_ok=True)
            default_db_path = os.path.join(db_dir, "cardDB.json")

            # 저장 모드에 따라 target_path 결정
            if getattr(self, "save_mode", "single") == "db":
                # DB 모드: 불러온 DB가 있으면 그 파일, 없으면 기본 cardDB.json
                target_path = self.loaded_db_path if self.loaded_db_path else default_db_path
            else:
                # 단일 모드: 불러온 단일 json이 있으면 그 파일에 저장,
                # 단, id가 바뀌면 JSON 폴더에 새 이름으로 저장
                old_id = self.loaded_card_id
                if self.loaded_db_path and old_id is not None and card_id == old_id:
                    target_path = self.loaded_db_path
                else:
                    target_path = default_single_path

            # 2) 단일 카드 파일(예: 0.json)을 불러온 상태에서 id가 바뀌면 -> 새 id 이름으로 저장
            if self.loaded_db_path:
                base = os.path.splitext(os.path.basename(self.loaded_db_path))[0]
                is_single_card_file = base.isdigit()  # 0.json, 12.json 같은 케이스
                if is_single_card_file and old_id is not None and card_id != old_id:
                    target_path = os.path.join(os.path.dirname(self.loaded_db_path), f"{card_id}.json")

            # JSON에는 image_path/sound_path를 넣지 않음 (혹시 포함돼도 제거)
            data.pop("image_path", None)
            data.pop("sound_path", None)

            # ---------- 리소스 저장(권장: ID 변경 시 old id 리소스 정리) ----------
            # 이미지
            img_src = self.var_image_path.get().strip()
            img_ext = None
            img_dst = None
            if img_src and os.path.exists(img_src):
                img_ext = os.path.splitext(img_src)[1] or ".png"
                img_dst = os.path.join(dirs["images"], f"{card_id}{img_ext}")

                if os.path.abspath(img_src) != os.path.abspath(img_dst):
                    shutil.copy2(img_src, img_dst)

                self.var_image_path.set(img_dst)

            # 사운드
            snd_src = self.var_sound_path.get().strip()
            snd_ext = None
            snd_dst = None
            if snd_src and os.path.exists(snd_src):
                snd_ext = os.path.splitext(snd_src)[1] or ".mp3"
                snd_dst = os.path.join(dirs["sounds"], f"{card_id}{snd_ext}")

                if os.path.abspath(snd_src) != os.path.abspath(snd_dst):
                    shutil.copy2(snd_src, snd_dst)

                self.var_sound_path.set(snd_dst)

            # ID 변경 시: old id 리소스 파일 제거(동일 확장자만)
            if old_id is not None and old_id != card_id:
                if img_ext:
                    old_img = os.path.join(dirs["images"], f"{old_id}{img_ext}")
                    if img_dst and os.path.exists(old_img) and os.path.abspath(old_img) != os.path.abspath(img_dst):
                        try:
                            os.remove(old_img)
                        except Exception:
                            pass

                if snd_ext:
                    old_snd = os.path.join(dirs["sounds"], f"{old_id}{snd_ext}")
                    if snd_dst and os.path.exists(old_snd) and os.path.abspath(old_snd) != os.path.abspath(snd_dst):
                        try:
                            os.remove(old_snd)
                        except Exception:
                            pass
            # ---------------------------------------------------------------

            # 기존 카드 로드(없으면 빈 리스트)
            existing_cards = []
            if os.path.exists(target_path):
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        existing_obj = json.load(f)
                    existing_cards = self._extract_cards(existing_obj)
                except Exception:
                    existing_cards = []

            # DB/패키지 파일에 저장하는 경우: id가 변경되었으면 "이전 id 항목" 제거 후 병합
            if old_id is not None and card_id != old_id:
                filtered = []
                for c in existing_cards:
                    try:
                        if int(c.get("id")) == int(old_id):
                            continue
                    except Exception:
                        pass
                    filtered.append(c)
                existing_cards = filtered

            # 현재 카드 1장(data)을 id 기준으로 덮어쓰기 병합 + id 정렬
            merged_cards = self._merge_cards_by_id(existing_cards, [data])
            out = {"cards": merged_cards}

            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=4)
                
            self.loaded_card_id = card_id
            self.loaded_db_path = target_path
            # 단일 저장이면 single 유지, DB 저장이면 db 유지(이미 save_mode로 관리)

            messagebox.showinfo(self._t("msg_title_saved"), self._t("msg_save_ok", path=target_path))
        except Exception as e:
            messagebox.showerror(self._t("msg_title_error"), self._t("msg_pkg_fail", err=e))


    def save_package(self):
        """여러 JSON(단일 카드 / cards 패키지 / 카드 배열)을 하나의 패키지로 병합하여 자동 저장
        - 저장 위치: Desktop/Cards/DB/cardDB.json
        - 결과는 {"cards": [...]} 고정
        - id 기준 정렬
        - 동일 id가 있으면 덮어쓰기(마지막에 읽힌 파일 우선)
        - 중복 id 덮어쓰기 발생 시, 어떤 파일이 기준(최종 반영)인지 메시지로 알림
        """
        json_paths = filedialog.askopenfilenames(
            title=self._t("dlg_merge_select_title"),
            filetypes=[("JSON", "*.json")]
        )
        if not json_paths:
            return

        # 자동 저장 경로: Desktop/Cards/DB/cardDB.json
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        db_dir = os.path.join(desktop_dir, "Cards", "DB")
        os.makedirs(db_dir, exist_ok=True)
        save_path = os.path.join(db_dir, "cardDB.json")

        def _extract_cards(obj):
            """obj가 (1) 단일 카드 dict (2) {'cards': [...]} (3) [...] 인 경우를 모두 카드 리스트로 변환"""
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict):
                if "cards" in obj and isinstance(obj["cards"], list):
                    return obj["cards"]
                if "cards: " in obj and isinstance(obj["cards: "], list):  # 과거 오타 키 방어
                    return obj["cards: "]
                if "id" in obj:
                    return [obj]
            return []

        def _safe_int_id(card):
            try:
                return int(card.get("id"))
            except Exception:
                return None

        try:
            by_id = {}
            src_by_id = {}      # 현재 by_id[id]가 어디에서 왔는지 기록
            overwrites = []     # (id, prev_src, new_src)

            # 1) 기존 cardDB.json이 있으면 먼저 로드
            if os.path.exists(save_path):
                try:
                    with open(save_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    for c in _extract_cards(existing):
                        cid = _safe_int_id(c)
                        if cid is None or cid < 0:
                            continue
                        c["id"] = cid
                        by_id[cid] = c
                        src_by_id[cid] = os.path.basename(save_path)  # "cardDB.json"
                except Exception:
                    pass

            # 2) 선택한 파일들을 순서대로 병합 (같은 id면 덮어쓰기 + 출처 기록)
            for p in json_paths:
                with open(p, "r", encoding="utf-8") as f:
                    obj = json.load(f)

                incoming_src = os.path.basename(p)
                for c in _extract_cards(obj):
                    cid = _safe_int_id(c)
                    if cid is None or cid < 0:
                        continue

                    c["id"] = cid
                    if cid in by_id:
                        prev_src = src_by_id.get(cid, self._t("msg_pkg_src_unknown"))
                        overwrites.append((cid, prev_src, incoming_src))

                    by_id[cid] = c
                    src_by_id[cid] = incoming_src

            # 3) id 기준 정렬 후 저장
            cards_sorted = [by_id[k] for k in sorted(by_id.keys())]
            out = {"cards": cards_sorted}
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=4)

            # 4) 중복 id 덮어쓰기 리포트 메시지
            if overwrites:
                # 너무 길어지면 UI가 불편하므로 상한
                max_lines = 25
                lines = []
                for i, (cid, prev_src, new_src) in enumerate(overwrites[:max_lines]):
                    lines.append(f"- ID {cid}: {prev_src} -> {new_src}")
                if len(overwrites) > max_lines:
                    lines.append(self._t("msg_pkg_overwrite_more", n=len(overwrites) - max_lines))

                msg = self._t(
                    "msg_pkg_saved_with_overwrites",
                    path=save_path,
                    count=len(overwrites),
                    detail="\n".join(lines),
                )
            else:
                msg = self._t("msg_pkg_saved_auto", path=save_path)

            messagebox.showinfo(self._t("msg_title_done"), msg)

        except Exception as e:
            messagebox.showerror(self._t("msg_title_error"), self._t("msg_pkg_fail", err=e))


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
        
    def _cards_root_dir(self) -> str:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        return os.path.join(desktop, "Cards")
    
    def _ensure_cards_dirs(self) -> dict:
        root = self._cards_root_dir()
        paths={
            "root": root,
            "json": os.path.join(root, "JSON"),
            "images": os.path.join(root,"Images"),
            "sounds": os.path.join(root,"Sounds"),
        }
        for p in paths.values():
            os.makedirs(p, exist_ok=True)
        return paths
    
    def _L(self) -> dict:
        return Config.LANGUAGES.get(self.current_lang, Config.LANGUAGES["ko"])
    
    def _t(self, key: str, **kwargs) -> str:
        s = self._L().get(key, key)
        return s.format(**kwargs) if kwargs else s

    def stop_sound(self):
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            messagebox.showerror(self._t("msg_title_error"), self._t("msg_sound_stop_fail", err=e))

    def _extract_cards(self, obj):
        """obj를 카드 리스트로 표준화:
        - 단일 카드 dict -> [dict]
        - {'cards': [...]} -> [...]
        - [...] -> [...]
        """
        if isinstance(obj, list):
            return obj

        if isinstance(obj, dict):
            if "cards" in obj and isinstance(obj["cards"], list):
                return obj["cards"]
            # 과거 잘못 저장된 키 방어 (원하면 제거 가능)
            if "cards: " in obj and isinstance(obj["cards: "], list):
                return obj["cards: "]
            if "id" in obj:
                return [obj]

        return []

    def _merge_cards_by_id(self, base_cards, incoming_cards):
        """id 기준 병합: 동일 id면 incoming이 덮어쓰기, 결과는 id 정렬된 리스트"""
        by_id = {}

        def put(card):
            try:
                cid = int(card.get("id"))
            except Exception:
                return
            if cid < 0:
                return
            card["id"] = cid
            by_id[cid] = card

        for c in base_cards:
            put(c)
        for c in incoming_cards:
            put(c)

        return [by_id[k] for k in sorted(by_id.keys())]
    
    def _bind_mousewheel(self, canvas: tk.Canvas, target_widget: tk.Widget):
        def _on_enter(_):
            self.root.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas))   # Windows/macOS
            self.root.bind_all("<Button-4>", lambda e: self._on_mousewheel(e, canvas))    # Linux up
            self.root.bind_all("<Button-5>", lambda e: self._on_mousewheel(e, canvas))    # Linux down

        def _on_leave(_):
            self.root.unbind_all("<MouseWheel>")
            self.root.unbind_all("<Button-4>")
            self.root.unbind_all("<Button-5>")

        target_widget.bind("<Enter>", _on_enter)
        target_widget.bind("<Leave>", _on_leave)

    def _on_mousewheel(self, event, canvas: tk.Canvas):
        # Windows/macOS: event.delta 사용, Linux: Button-4/5 사용
        if hasattr(event, "delta") and event.delta:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")


if __name__ == "__main__":
    root = tk.Tk()
    app = CardCreatorApp(root)
    root.mainloop()

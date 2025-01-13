import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, UnidentifiedImageError
import json
import os


class CardCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("카드 생성기")

        # 창 크기 조정 가능 설정
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        # GUI 요소들
        tk.Label(root, text="번호:").grid(row=0, column=0, sticky="w")
        self.number_spinbox = tk.Spinbox(root, from_=0, to=1000000)
        self.number_spinbox.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(root, text="이름:").grid(row=1, column=0, sticky="w")
        self.name_entry = tk.Entry(root)
        self.name_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(root, text="설명:").grid(row=2, column=0, sticky="nw", padx=5, pady=5)
        self.description_text = tk.Text(root, height=5, wrap="word")
        self.description_text.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

        tk.Label(root, text="효과:").grid(row=3, column=0, sticky="nw", padx=5, pady=5)
        self.effect_text = tk.Text(root, height=5, wrap="word")
        self.effect_text.grid(row=3, column=1, sticky="nsew", padx=5, pady=5)

        # 세부효과 영역
        tk.Label(root, text="세부효과:").grid(row=4, column=0, sticky="nw")
        self.detail_effect_frame = tk.Frame(root)
        self.detail_effect_frame.grid(row=4, column=1, sticky="nsew", padx=5, pady=5)
        self.detail_effects = []
        self.used_effects = set()  # 이미 선택된 효과를 추적
        self.create_detail_effect_row()

        tk.Button(root, text="+", command=self.create_detail_effect_row).grid(row=4, column=2, sticky="w", padx=5)

        # 종족 영역
        tk.Label(root, text="종족:").grid(row=5, column=0, sticky="w")
        self.species_var = tk.StringVar(value="일반")
        self.species_dropdown = ttk.Combobox(
            root, textvariable=self.species_var, values=["일반", "여신", "인신공양", "사기사"], state="readonly"
        )
        self.species_dropdown.grid(row=5, column=1, sticky="ew", padx=5, pady=5)

        # 요구심볼
        tk.Label(root, text="요구심볼:").grid(row=6, column=0, sticky="w")
        self.requirement_spinboxes = {}
        self.create_symbol_inputs("요구심볼", self.requirement_spinboxes, row=6)

        # 증여심볼
        tk.Label(root, text="증여심볼:").grid(row=7, column=0, sticky="w")
        self.gift_spinboxes = {}
        self.create_symbol_inputs("증여심볼", self.gift_spinboxes, row=7)

        # 신도수
        tk.Label(root, text="신도수:").grid(row=8, column=0, sticky="w")
        self.follower_spinbox = tk.Spinbox(root, from_=0, to=1000000)
        self.follower_spinbox.grid(row=8, column=1, sticky="ew", padx=5, pady=5)

        # 갈림길
        tk.Label(root, text="갈림길:").grid(row=9, column=0, sticky="w")
        self.path_spinbox = tk.Spinbox(root, from_=0, to=1000000)
        self.path_spinbox.grid(row=9, column=1, sticky="ew", padx=5, pady=5)

        # 저장 및 초기화 버튼
        tk.Button(root, text="저장", command=self.save_card).grid(row=12, column=0, pady=5)
        tk.Button(root, text="초기화", command=self.reset_all).grid(row=12, column=1, pady=5)

        # 파일 추가 버튼
        tk.Button(root, text="파일 합치기", command=self.load_json_files).grid(row=13, column=0, pady=5)
        
        # JSON 불러오기 버튼
        tk.Button(root, text="JSON 불러오기", command=self.load_card).grid(row=13, column=1, pady=5)

        # JSON 저장 버튼
        tk.Button(root, text="수정 저장", command=self.save_modified_card).grid(row=13, column=2, pady=5)

        
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
        
    def create_detail_effect_row(self):
        """세부효과 입력 필드 추가."""
        row_frame = tk.Frame(self.detail_effect_frame)
        row_frame.pack(fill="x", pady=2)

        all_options = sorted([
            "AddDraw", "AddKia", "AddSim", "Discard", "DrawSkip", "ForceSelect", "InPanth",
            "IsFliped", "IsInflu", "IsMono", "IsPoly", "IsStrong", "IsTrade", "IsUni",
            "OnlyOne", "Proph", "Remove", "Sacri", "SearchField", "Select", "Start"
        ])
        available_options = [opt for opt in all_options if opt not in self.used_effects]

        if not available_options:
            messagebox.showwarning("경고", "더 이상 추가할 수 있는 효과가 없습니다.")
            return

        # 드롭다운 메뉴
        effect_var = tk.StringVar(value="선택")
        effect_dropdown = ttk.Combobox(row_frame, textvariable=effect_var, values=available_options, state="readonly")
        effect_dropdown.pack(side="left", padx=5)

        # 숫자 입력 필드
        value_spinbox = tk.Spinbox(row_frame, from_=0, to=100)
        value_spinbox.pack(side="left", padx=5)

        # 삭제 버튼
        delete_button = tk.Button(row_frame, text="삭제", command=lambda: self.delete_detail_effect_row(row_frame, effect_var))
        delete_button.pack(side="left", padx=5)

        def on_effect_selected(event):
            selected_effect = effect_var.get()
            if selected_effect != "선택" and selected_effect not in self.used_effects:
                self.used_effects.add(selected_effect)

        effect_dropdown.bind("<<ComboboxSelected>>", on_effect_selected)
        self.detail_effects.append((effect_var, value_spinbox))

    def delete_detail_effect_row(self, row_frame, effect_var):
        """세부효과 행 삭제."""
        for effect, spinbox in self.detail_effects:
            if effect == effect_var:
                selected_effect = effect.get()
                if selected_effect in self.used_effects:
                    self.used_effects.remove(selected_effect)
                self.detail_effects.remove((effect, spinbox))
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
        """세부효과 리스트 반환."""
        effects = {}
        for effect_var, spinbox in self.detail_effects:
            effect_name = effect_var.get()
            if effect_name != "선택":
                effects[effect_name] = int(spinbox.get())
        return effects

    def get_symbols(self, spinboxes):
        """심볼 데이터 가져오기."""
        return {k: int(v.get()) for k, v in spinboxes.items()}

    def save_card(self):
        """카드 데이터를 저장."""
        card_number = int(self.number_spinbox.get())
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        cards_folder = os.path.join(desktop_path, "Cards")
        json_folder = os.path.join(cards_folder, "Json")

        os.makedirs(json_folder, exist_ok=True)

        # 저장 데이터 구성
        card_data = {
            "Number": card_number,
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

        # 카드 데이터 JSON으로 저장
        json_path = os.path.join(json_folder, f"{card_number}.json")
        try:
            with open(json_path, "w", encoding="utf-8") as json_file:
                json.dump(card_data, json_file, ensure_ascii=False, indent=4)
            messagebox.showinfo("저장 완료", "카드가 성공적으로 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"JSON 저장 중 오류 발생: {e}")


    def reset_all(self):
        """모든 필드를 초기화."""
        self.number_spinbox.delete(0, tk.END)
        self.number_spinbox.insert(0, 0)
        self.name_entry.delete(0, tk.END)
        self.description_text.delete("1.0", tk.END)
        self.effect_text.delete("1.0", tk.END)
        for widget in self.detail_effect_frame.winfo_children():
            widget.destroy()
        self.detail_effects.clear()
        self.used_effects.clear()
        self.create_detail_effect_row()
        self.species_var.set("일반")
        for spinbox in self.requirement_spinboxes.values():
            spinbox.delete(0, tk.END)
            spinbox.insert(0, 0)
        for spinbox in self.gift_spinboxes.values():
            spinbox.delete(0, tk.END)
            spinbox.insert(0, 0)
        self.follower_spinbox.delete(0, tk.END)
        self.follower_spinbox.insert(0, 0)
        self.path_spinbox.delete(0, tk.END)
        self.path_spinbox.insert(0, 0)
        messagebox.showinfo("초기화 완료", "모든 필드가 초기화되었습니다.")
        
    def load_json_files(self):
        """여러 JSON 파일을 추가하고 cards.json 파일에 저장."""
        file_paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")])
        if not file_paths:
            return

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

        
if __name__ == "__main__":
    root = tk.Tk()
    app = CardCreatorApp(root)
    root.mainloop()

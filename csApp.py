import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from PIL import Image, ImageTk, UnidentifiedImageError
import shutil
import json

class CharacterSheetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("캐릭터 시트")
        self.root.geometry("600x800")

        # 창 크기 조정 비율 유지
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(8, weight=1)

        # GUI 요소들
        tk.Label(root, text="이름:").grid(row=0, column=0, sticky="w")
        self.name_entry = tk.Entry(root)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(root, text="나이:").grid(row=1, column=0, sticky="w")
        self.age_entry = tk.Entry(root)
        self.age_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(root, text="성별:").grid(row=2, column=0, sticky="w")
        self.gender_var = tk.StringVar()
        self.gender_dropdown = ttk.Combobox(root, textvariable=self.gender_var, values=["남", "여", "공격 헬리콥터"], state="readonly")
        self.gender_dropdown.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.gender_dropdown.set("공격 헬리콥터")

        # 소속 드롭다운 메뉴
        tk.Label(root, text="소속:").grid(row=3, column=0, sticky="w")
        self.affiliation_var = tk.StringVar(value="혁명세력")
        self.affiliation_dropdown = ttk.Combobox(root, textvariable=self.affiliation_var, values=["혁명세력", "기업국가", "신정통치", ""], state="readonly")
        self.affiliation_dropdown.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        self.affiliation_dropdown.bind("<<ComboboxSelected>>", self.update_faction_dropdown)

        # 급진파/온건파 서브 드롭다운
        self.faction_var = tk.StringVar(value="")
        self.faction_dropdown = ttk.Combobox(root, textvariable=self.faction_var, values=[], state="readonly")
        self.faction_dropdown.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        self.faction_dropdown.grid_remove()  # 초기에는 숨김

        tk.Label(root, text="직업:").grid(row=5, column=0, sticky="w")
        self.job_entry = tk.Entry(root)
        self.job_entry.grid(row=5, column=1, sticky="ew", padx=5, pady=5)

        # 세부 설정 텍스트 박스
        tk.Label(root, text="세부 설정:").grid(row=6, column=0, sticky="nw", padx=5, pady=5)
        self.details_text = tk.Text(root, height=10, wrap="word")
        self.details_text.grid(row=6, column=1, sticky="nsew", padx=5, pady=5)

        # 이미지 영역
        self.image_frame = tk.Frame(root, height=256, width=256, relief="solid", bd=1)
        self.image_frame.grid(row=7, column=1, pady=10)
        self.image_canvas = tk.Canvas(self.image_frame, width=256, height=256, bg="white")
        self.image_canvas.pack()

        tk.Button(root, text="이미지 추가", command=self.add_image).grid(row=7, column=0, padx=5, pady=5)

        # 저장, 불러오기 및 초기화 버튼
        tk.Button(root, text="캐릭터 저장", command=self.save_character).grid(row=8, column=0, pady=5)
        tk.Button(root, text="캐릭터 불러오기", command=self.load_character).grid(row=8, column=1, pady=5)
        tk.Button(root, text="초기화", command=self.reset_all).grid(row=8, column=2, pady=5)

        # 이미지 파일 경로 저장
        self.character_image_path = None

    def update_faction_dropdown(self, event):
        """신정통치 선택 시 급진파/온건파 드롭다운 표시."""
        selected_affiliation = self.affiliation_var.get()

        if selected_affiliation == "신정통치":
            # 급진파/온건파 드롭다운 표시
            self.faction_dropdown["values"] = ["급진파", "온건파"]
            self.faction_dropdown.grid()
            self.faction_var.set("급진파")  # 기본값 설정
        else:
            # 다른 소속 선택 시 서브 드롭다운 숨김
            self.faction_dropdown.grid_remove()
            self.faction_var.set("")  # 서브 드롭다운 초기화

    def add_image(self):
        """사용자의 파일에서 이미지를 불러옴."""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if file_path:
            self.character_image_path = file_path
            self.update_image_display(file_path)

    def update_image_display(self, file_path):
        """이미지 박스에 이미지를 표시."""
        try:
            img = Image.open(file_path)
            img.thumbnail((256, 256))  # 이미지 크기 조정
            self.image_tk = ImageTk.PhotoImage(img)
            self.image_canvas.create_image(128, 128, image=self.image_tk, anchor="center")
        except UnidentifiedImageError:
            messagebox.showerror("Error", "이미지 파일을 불러올 수 없습니다.")
        except Exception as e:
            messagebox.showerror("Error", f"이미지 표시 중 오류 발생: {e}")

    def save_character(self):
        """캐릭터 데이터를 저장."""
        name = self.name_entry.get()
        affiliation = self.affiliation_var.get()
        faction = self.faction_var.get()
        job = self.job_entry.get()

        if not name or not affiliation or not job:
            messagebox.showerror("Error", "이름, 소속, 직업을 입력해야 합니다.")
            return

        # 바탕화면 경로 설정
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        characters_folder = os.path.join(desktop_path, "Characters")
        os.makedirs(characters_folder, exist_ok=True)

        # 이미지 폴더 생성
        image_folder = os.path.join(characters_folder, "image")
        os.makedirs(image_folder, exist_ok=True)

        # 캐릭터 저장 경로 생성
        base_filename = f"{affiliation}_{faction}_{job}_{name}".replace("__", "_").strip("_")
        json_path = os.path.join(characters_folder, f"{base_filename}.json")
        image_save_path = os.path.join(image_folder, f"{base_filename}.png")

        character_data = {
            "name": name,
            "age": self.age_entry.get(),
            "gender": self.gender_var.get(),
            "affiliation": affiliation,
            "faction": faction,
            "job": job,
            "details": self.details_text.get("1.0", tk.END).strip(),
            "image_path": os.path.relpath(image_save_path, desktop_path) if self.character_image_path else None
        }

        # JSON 저장
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(character_data, file, ensure_ascii=False, indent=4)

        # 이미지 저장
        if self.character_image_path:
            try:
                shutil.copy(self.character_image_path, image_save_path)
            except Exception as e:
                messagebox.showerror("Error", f"이미지 저장 중 오류 발생: {e}")

        messagebox.showinfo("Success", f"캐릭터가 저장되었습니다:\n{json_path}")

    def load_character(self):
        """캐릭터 데이터를 불러옴."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                character_data = json.load(file)

            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, character_data.get("name", ""))
            self.age_entry.delete(0, tk.END)
            self.age_entry.insert(0, character_data.get("age", ""))
            self.gender_var.set(character_data.get("gender", "공격 헬리콥터"))
            self.affiliation_var.set(character_data.get("affiliation", ""))
            self.faction_var.set(character_data.get("faction", ""))
            self.update_faction_dropdown(None)  # 서브 드롭다운 갱신
            self.job_entry.delete(0, tk.END)
            self.job_entry.insert(0, character_data.get("job", ""))
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert("1.0", character_data.get("details", ""))

            self.character_image_path = os.path.join(os.path.expanduser("~"), "Desktop", character_data.get("image_path", ""))
            if self.character_image_path and os.path.exists(self.character_image_path):
                self.update_image_display(self.character_image_path)
            else:
                self.image_canvas.delete("all")

            messagebox.showinfo("Success", "캐릭터가 불러와졌습니다.")
        except Exception as e:
            messagebox.showerror("Error", f"캐릭터 불러오기에 실패했습니다: {e}")

    def reset_all(self):
        """모든 설정을 초기화."""
        self.name_entry.delete(0, tk.END)
        self.age_entry.delete(0, tk.END)
        self.gender_var.set("공격 헬리콥터")
        self.affiliation_var.set("혁명세력")
        self.faction_var.set("")
        self.faction_dropdown.grid_remove()  # 서브 드롭다운 숨김
        self.job_entry.delete(0, tk.END)
        self.details_text.delete("1.0", tk.END)
        self.image_canvas.delete("all")
        self.character_image_path = None
        messagebox.showinfo("Reset", "모든 설정이 초기화되었습니다.")


# 프로그램 실행
if __name__ == "__main__":
    root = tk.Tk()
    app = CharacterSheetApp(root)
    root.mainloop()

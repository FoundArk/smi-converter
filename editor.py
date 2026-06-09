import os, re, tkinter as tk
from tkinter import ttk, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SMI Editor - 안전 변환 모드")
        self.root.geometry("600x650")
        
        # 1. 트리뷰 생성
        self.tree = ttk.Treeview(root, columns=("File Name", "Status", "Review"), show="headings", height=15)
        self.tree.heading("File Name", text="File Name")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Review", text="Review")
        self.tree.column("File Name", width=300, minwidth=150, stretch=True)
        self.tree.column("Status", width=100, minwidth=80, stretch=False)
        self.tree.column("Review", width=200, minwidth=100, stretch=True)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 2. 바인딩
        self.tree.bind('<Double-1>', self.on_header_double_click)
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop_files)
        self.tree.bind('<F5>', self.clear_list)

        # 3. UI 및 버튼
        self.status_label = tk.Label(root, text="파일을 드래그하고 [전체 변환]을 누르세요.", fg="blue", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="전체 변환 실행", command=self.run_all_process, bg="skyblue").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="검수", command=self.review_files, bg="khaki").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="덮어쓰기 저장", command=lambda: self.save_files(overwrite=True), bg="lightgreen").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="다른 이름으로 저장", command=lambda: self.save_files(overwrite=False), bg="orange").pack(side=tk.LEFT, padx=5)

        self.file_data = {}
        self.temp_contents = {}

    # --- 여기서부터 아래로 모든 기능 함수들을 넣습니다 ---

    def on_header_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            column = self.tree.identify_column(event.x)
            column_id = self.tree.column(column, "id")
            max_width = len(self.tree.heading(column_id, "text")) * 10
            for child in self.tree.get_children():
                val = str(self.tree.set(child, column_id))
                max_width = max(max_width, len(val) * 8)
            self.tree.column(column_id, width=max_width + 20)

    def clear_list(self, event=None):
        for item in self.tree.get_children(): self.tree.delete(item)
        self.file_data.clear()
        self.temp_contents.clear()
        self.status_label.config(text="초기화됨")

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.endswith('.smi'):
                item = self.tree.insert("","end",values=(os.path.basename(f),"준비됨","-"))
                self.file_data[item] = f
        self.status_label.config(text=f"{len(self.file_data)}개 파일 준비 완료")

    def review_files(self):
        for item, path in self.file_data.items():
            try:
                with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    content = f.read()
                issues = []
                if r'{\an8}' in content: issues.append(r'{\an8}')
                if r'KOKRCC' in content: issues.append(r'KOKRCC')
                if r'KOKR' in content: issues.append(r'KOKR')
                result = ", ".join(issues) + " 발견" if issues else "이상 없음"
                self.tree.set(item, "Review", result)
            except Exception as e:
                self.tree.set(item, "Review", f"검수 실패: {e}")
        self.status_label.config(text="검수 완료")

    def run_all_process(self):
        for item, path in self.file_data.items():
            try:
                with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    content = f.read()
                # 1. KRCC로 변환
                content = re.sub(r'KOKRCC', 'KRCC', content, flags=re.IGNORECASE)
                content = re.sub(r'KOKR', 'KRCC', content, flags=re.IGNORECASE)
                # 2. 줄바꿈 최적화
                content = re.sub(r'(<P Class=KRCC>)(?!\s*&nbsp;)([^ \s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
                content = re.sub(r'(&nbsp;)([^ \s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
                content = re.sub(r'(<br>)\s*([^\r\n<>])', r'\1\n\2', content, flags=re.IGNORECASE)
                # 3. \an8 삭제
                content = re.sub(r'{\an8}', '', content)
                # 4. 헤더 교체
                lines = ["<SAMI>", "<HEAD>", "<TITLE>Subtitle Validation Tool x64 1.2.4 - (C) SPTek, Inc.</TITLE>",
                         '<STYLE TYPE="text/css">', "", "</STYLE>", 
                         "</HEAD>", "<BODY>", "<SYNC Start=0><P Class=KRCC>&nbsp;"]
                idx = content.find('<SYNC')
                if idx != -1: content = "\n".join(lines) + "\n" + content[idx:]
                self.temp_contents[item] = content
                self.tree.set(item, "Status", "변환 완료(저장 대기)")
            except Exception as e:
                self.tree.set(item, "Status", f"오류: {e}")
        self.status_label.config(text="모든 파일 변환 완료. 저장 방식을 선택하세요.")

    def save_files(self, overwrite):
        saved_count = 0
        for item, path in self.file_data.items():
            if item not in self.temp_contents: continue
            save_path = path if overwrite else os.path.join(os.path.dirname(path), f"{os.path.splitext(os.path.basename(path))[0]}_변환완료.smi")
            try:
                with open(save_path, 'w', encoding='utf-8-sig') as f:
                    f.write(self.temp_contents[item])
                self.tree.set(item, "Status", "저장 완료")
                saved_count += 1
            except Exception as e:
                self.tree.set(item, "Status", f"저장 실패: {e}")
        self.status_label.config(text=f"총 {saved_count}개 파일 저장 완료")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SMIEditor(root)
    root.mainloop()

import os, re, tkinter as tk
from tkinter import ttk, font
from tkinterdnd2 import DND_FILES, TkinterDnD

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SMI Editor - 안전 변환 모드")
        self.root.geometry("800x650")

        # [스타일 설정]
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", borderwidth=2, relief="solid")
        style.configure("Treeview.Heading", relief="raised")

        # [메인 구성]
        self.tree = ttk.Treeview(root, columns=("File Name", "Status", "Encode", "Review"), show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree.heading("File Name", text="File Name")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Encode", text="Encode")
        self.tree.heading("Review", text="Review")
        self.tree.column("File Name", width=250); self.tree.column("Status", width=100)
        self.tree.column("Encode", width=80); self.tree.column("Review", width=150)
        
        self.root.bind('<F5>', self.clear_list)

        self.status_label = tk.Label(root, text="파일을 드래그하세요. (F5: 초기화)", fg="black", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10)

        btn_frame = tk.Frame(root, pady=10)
        btn_frame.pack()

        tk.Button(btn_frame, text="전체 변환 실행", command=self.run_all_process, bg="skyblue", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="덮어쓰기 저장", command=lambda: self.save_files(True), bg="lightgreen", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="다른 이름으로 저장", command=lambda: self.save_files(False), bg="orange", width=15).pack(side=tk.LEFT, padx=5)

        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop_files)

        self.file_data = {}; self.temp_contents = {}

    def get_info(self, content, path):
        # 인코딩 및 이슈 분석
        enc = "UTF-8" if "utf" in content.lower() else "ANSI"
        issues = [r'{\an'+str(i)+r'}' for i in range(1, 10) if r'{\an'+str(i)+r'}' in content]
        if 'KOKRCC' in content.upper(): issues.append('KOKRCC')
        elif 'KOKR' in content.upper(): issues.append('KOKR')
        return enc, (", ".join(issues) + " 발견" if issues else "이상 없음")

    def read_file(self, path):
        for enc in ['cp949', 'utf-8', 'utf-8-sig']:
            try:
                with open(path, 'r', encoding=enc) as f: return f.read()
            except: continue
        return ""

    def clear_list(self, event=None):
        for item in self.tree.get_children(): self.tree.delete(item)
        self.file_data.clear(); self.temp_contents.clear()
        self.status_label.config(text="목록 초기화됨")

    def run_all_process(self):
        for item, path in self.file_data.items():
            content = self.read_file(path)
            
            
            # 주석 및 표준 헤더 구성
            lines = ["<SAMI>", "<HEAD>", "<TITLE>Subtitle Validation Tool x64 1.2.4 - (C) SPTek, Inc.</TITLE>",
                         '<STYLE TYPE="text/css">', "<!--", "P {margin-left:4pt; margin-right:4pt; margin-bottom:2pt; margin-top:2pt;",
                         "   text-align:Center; font-size:18pt; font-family: 맑은 고딕, 굴림, Arial;", "   font-weight:Bold; color:white;}",
                         ".KRCC {Name:한국어; Lang:ko-KR; SAMIType:CC;}", "-->", "</STYLE>", 
                         "</HEAD>", "<BODY>", "<SYNC Start=0><P Class=KRCC>&nbsp;"
            ]
            
            # 본문 추출 (BODY 이후 내용 보존)
            body = re.sub(r'.*?<BODY[^>]*>', '', content, flags=re.IGNORECASE | re.DOTALL)
            
            # 변환 (Class 교체 및 위치 태그 삭제)
            body = re.sub(r'Class=[^> ]+', 'Class=KRCC', body, flags=re.IGNORECASE)
            body = re.sub(r'{\\an[1-9]}', '', body, flags=re.IGNORECASE)
            
            new_content = "\n".join(lines) + "\n" + body
            self.temp_contents[item] = new_content
            
            # 변환 후 정보 갱신
            enc, info = self.get_info(new_content, path)
            self.tree.set(item, "Status", "변환 완료")
            self.tree.set(item, "Encode", enc)
            self.tree.set(item, "Review", info)
        self.status_label.config(text="전체 변환 완료.")

    def save_files(self, overwrite):
        count = 0
        for item, path in self.file_data.items():
            if item not in self.temp_contents: continue
            save_path = path if overwrite else path.replace(".smi", "_변환완료.smi")
            with open(save_path, 'w', encoding='utf-8-sig') as f:
                f.write(self.temp_contents[item])
            self.tree.set(item, "Status", "저장 완료")
            count += 1
        self.status_label.config(text=f"총 {count}개 파일 저장 완료")

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.endswith('.smi'):
                content = self.read_file(f)
                enc, info = self.get_info(content, f)
                item = self.tree.insert("", "end", values=(os.path.basename(f), "준비됨", enc, info))
                self.file_data[item] = f

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SMIEditor(root)
    root.mainloop()

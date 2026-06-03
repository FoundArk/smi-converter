import os, re, tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional SMI Editor")
        self.root.geometry("600x600")
        
        # 저장 방식 (True: 덮어쓰기, False: 별도 저장)
        self.overwrite_var = tk.BooleanVar(value=True)

        # 1. 트리뷰 (파일명과 상태 표시)
        self.tree = ttk.Treeview(root, columns=("File Name", "Status"), show="headings", height=15)
        self.tree.heading("File Name", text="File Name")
        self.tree.heading("Status", text="Status")
        self.tree.column("File Name", width=400)
        self.tree.column("Status", width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- 드래그 앤 드롭 핵심 수정 부분 ---
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop_files)
        # -----------------------------------
        
        self.tree.bind('<F5>', self.clear_list) # F5로 초기화

        # 2. 상태 메시지 라벨 (좌측 정렬)
        self.status_label = tk.Label(root, text="준비됨", fg="blue", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10)

        # 3. 버튼 영역
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        
        tk.Checkbutton(btn_frame, text="원본 덮어쓰기", variable=self.overwrite_var).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="KRCC 변환", command=lambda: self.process("krcc")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="줄바꿈 최적화", command=lambda: self.process("newline")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="헤더 일괄 교체", command=lambda: self.process("header"), bg="yellow").pack(side=tk.LEFT, padx=5)

        self.file_data = {} 

    def clear_list(self, event=None):
        for item in self.tree.get_children(): self.tree.delete(item)
        self.file_data.clear()
        self.status_label.config(text="리스트 초기화됨")

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.endswith('.smi'):
                item = self.tree.insert("", "end", values=(os.path.basename(f), "변환 전"))
                self.file_data[item] = f
        self.status_label.config(text=f"{len(self.file_data)}개 대기 중")

    def process(self, mode):
        for item, path in self.file_data.items():
            self.tree.set(item, "Status", "변환 중")
            self.root.update()
            
            try:
                with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f: content = f.read()
                
                if mode == "krcc":
                    content = re.sub(r'KOKRCC|KOKR', 'KRCC', content, flags=re.IGNORECASE)
                elif mode == "newline":
                    content = re.sub(r'(<P Class=KRCC>)(?!\s*&nbsp;)([^ \s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
                    content = re.sub(r'(&nbsp;)([^ \s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
                    content = re.sub(r'(<br>)\s*([^\r\n<>])', r'\1\n\2', content, flags=re.IGNORECASE)
                elif mode == "header":
                    lines = [
                        "<SAMI>", "<HEAD>", "<TITLE>Subtitle Validation Tool x64 1.2.4 - (C) SPTek, Inc.</TITLE>",
                        '<STYLE TYPE="text/css">', "", "</STYLE>", 
                        "</HEAD>", "<BODY>", "<SYNC Start=0><P Class=KRCC>&nbsp;"
                    ]
                    idx = content.find('<SYNC')
                    content = "\n".join(lines) + "\n" + (content[idx:] if idx != -1 else "")

                save_path = path if self.overwrite_var.get() else path.replace(".smi", "_converted.smi")
                with open(save_path, 'w', encoding='utf-8-sig') as f: f.write(content)
                self.tree.set(item, "Status", "변환 완료")
            except Exception as e:
                self.tree.set(item, "Status", "오류")
                self.status_label.config(text=f"오류: {e}")
        self.status_label.config(text="작업 완료")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    editor = SMIEditor(root)
    root.dnd_bind('<<Drop>>', editor.drop_files)
    root.mainloop()

    def fix_header(self):
        lines = [
            "<SAMI>",
            "<HEAD>",
            "<TITLE>Subtitle Validation Tool x64 1.2.4 - (C) SPTek, Inc.</TITLE>",
            '<STYLE TYPE="text/css">',
            "<!--",
            "P {margin-left:4pt; margin-right:4pt; margin-bottom:2pt; margin-top:2pt;",
            "   text-align:Center; font-size:18pt; font-family: 맑은 고딕, 굴림, Arial;",
            "   font-weight:Bold; color:white;}",
            ".KRCC {Name:한국어; Lang:ko-KR; SAMIType:CC;}",
            "-->",
            "</STYLE>",
            "</HEAD>",
            "<BODY>",
            "<SYNC Start=0><P Class=KRCC>&nbsp;"
        ]
        final_header = "\n".join(lines)
        
        for path in self.file_list:
            try:
                with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f: content = f.read()
                idx = content.find('<SYNC')
                if idx != -1:
                    final_content = final_header + "\n" + content[idx:]
                    with open(path, 'w', encoding='utf-8-sig') as f: f.write(final_content)
            except Exception as e:
                self.status_label.config(text=f"오류 발생: {e}")
                return
        self.status_label.config(text="헤더 교체 완료")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SMIEditor(root)
    root.mainloop()

import os, re, tkinter as tk
from tkinter import ttk, font
from tkinterdnd2 import DND_FILES, TkinterDnD

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SMI Editor")
        self.root.geometry("800x650")

        # [UI 영역]
        tree_frame = tk.Frame(root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(tree_frame, columns=("Name", "Status", "Encode", "Info"), show="headings")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for col in ["Name", "Status", "Encode", "Info"]:
            self.tree.heading(col, text=col)
        
        self.tree.column("Name", width=200); self.tree.column("Status", width=100)
        self.tree.column("Encode", width=80); self.tree.column("Info", width=200)
        
        self.status_label = tk.Label(root, text="파일을 드래그하세요.", fg="black", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10)

        btn_frame = tk.Frame(root, pady=10)
        btn_frame.pack()

        tk.Button(btn_frame, text="전체 변환 실행", command=self.run_all_process, bg="skyblue", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="덮어쓰기 저장", command=lambda: self.save_files(True), bg="lightgreen", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="다른 이름으로 저장", command=lambda: self.save_files(False), bg="orange", width=15).pack(side=tk.LEFT, padx=5)

        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop_files)
        
        self.file_data = {}; self.temp_contents = {}

    def get_info_data(self, content, path):
        enc = self.get_encoding(path)
        issues = [r'{\an'+str(i)+r'}' for i in range(1, 10) if r'{\an'+str(i)+r'}' in content]
        if 'KOKRCC' in content.upper(): issues.append('KOKRCC')
        elif 'KOKR' in content.upper(): issues.append('KOKR')
        info = ", ".join(issues) + " 발견" if issues else "이상 없음"
        return enc, info

    def get_encoding(self, path):
        with open(path, 'rb') as f:
            raw = f.read(3)
            if raw == b'\xef\xbb\xbf': return "UTF-8(BOM)"
        try:
            with open(path, 'r', encoding='utf-8') as f: f.read()
            return "UTF-8"
        except: return "ANSI"

    def read_file(self, path):
        enc_map = {"UTF-8(BOM)": "utf-8-sig", "UTF-8": "utf-8", "ANSI": "cp949"}
        enc = enc_map.get(self.get_encoding(path), "cp949")
        try:
            with open(path, 'r', encoding=enc) as f: return f.read()
        except: return ""

    def run_all_process(self):
        for item, path in self.file_data.items():
            content = self.read_file(path)
            sync_blocks = re.findall(r'(<SYNC\s+Start=\d+>.*?(?:<P[^>]*>|&nbsp;).*?(?:<br>.*?)*)', content, re.DOTALL | re.IGNORECASE)
            
            # 주석 및 표준 헤더 구성
            lines = ["<SAMI>", "<HEAD>", "<TITLE>Subtitle Validation Tool x64 1.2.4 - (C) SPTek, Inc.</TITLE>",
                         '<STYLE TYPE="text/css">', "<!--", "P {margin-left:4pt; margin-right:4pt; margin-bottom:2pt; margin-top:2pt;",
                         "   text-align:Center; font-size:18pt; font-family: 맑은 고딕, 굴림, Arial;", "   font-weight:Bold; color:white;}",
                         ".KRCC {Name:한국어; Lang:ko-KR; SAMIType:CC;}", "-->", "</STYLE>", 
                         "</HEAD>", "<BODY>", "<SYNC Start=0><P Class=KRCC>&nbsp;"
            ]
            
            new_content = "\n".join(lines) + "\n"
            for block in sync_blocks:
                clean_block = re.sub(r'Class=[^> ]+', 'Class=KRCC', block, flags=re.IGNORECASE)
                clean_block = re.sub(r'{\\an[1-9]}', '', clean_block, flags=re.IGNORECASE)
                new_content += clean_block + "\n"
            
            new_content += "</BODY>\n</SAMI>"
            self.temp_contents[item] = new_content
            
            # 변환 후 정보 자동 업데이트
            enc, info = self.get_info_data(new_content, path)
            self.tree.set(item, "Status", "변환 완료")
            self.tree.set(item, "Encode", enc)
            self.tree.set(item, "Info", info)
        self.status_label.config(text="전체 변환 및 정보 업데이트 완료.")

    def save_files(self, overwrite):
        count = 0
        for item, path in self.file_data.items():
            if item not in self.temp_contents: continue
            save_path = path if overwrite else path.replace(".smi", "_변환완료.smi")
            with open(save_path, 'w', encoding='utf-8-sig') as f: f.write(self.temp_contents[item])
            self.tree.set(item, "Status", "저장 완료")
            count += 1
        self.status_label.config(text=f"총 {count}개 파일 저장 완료")

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.endswith('.smi'):
                content = self.read_file(f)
                enc, info = self.get_info_data(content, f)
                item = self.tree.insert("","end",values=(os.path.basename(f), "준비됨", enc, info))
                self.file_data[item] = f

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SMIEditor(root)
    root.mainloop()

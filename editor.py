import os, re, tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional SMI Batch Editor")
        self.root.geometry("600x500")
        self.file_list = []

        tk.Label(root, text="SMI 파일을 이곳에 드래그하세요").pack(pady=5)
        self.listbox = tk.Listbox(root, selectmode=tk.MULTIPLE, width=80, height=15)
        self.listbox.pack(pady=5)
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self.drop_files)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="1. KRCC 변환", command=self.fix_krcc).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="2. 줄바꿈 최적화", command=self.fix_newline).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="3. 헤더 일괄 교체", command=self.fix_header, bg="yellow").pack(side=tk.LEFT, padx=5)

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.endswith('.smi'): self.file_list.append(f); self.listbox.insert(tk.END, os.path.basename(f))

    def fix_krcc(self):
        for path in self.file_list:
            with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f: content = f.read()
            content = re.sub(r'KOKRCC|KOKR', 'KRCC', content, flags=re.IGNORECASE)
            with open(path, 'w', encoding='utf-8-sig') as f: f.write(content)
        messagebox.showinfo("완료", "KRCC 변환 완료")

    def fix_newline(self):
        for path in self.file_list:
            with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f: content = f.read()
            content = re.sub(r'(<P Class=KRCC>)(?!\s*&nbsp;)([^ \s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
            content = re.sub(r'(&nbsp;)([^ \s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
            content = re.sub(r'(<br>)\s*([^\r\n<>])', r'\1\n\2', content, flags=re.IGNORECASE)
            with open(path, 'w', encoding='utf-8-sig') as f: f.write(content)
        messagebox.showinfo("완료", "줄바꿈 최적화 완료")

    def fix_header(self):
        new_header = r"""<SAMI>
<HEAD>
<TITLE>Subtitle Validation Tool x64 1.2.4 - (C) SPTek, Inc.</TITLE>
<STYLE TYPE="text/css">
</STYLE>
</HEAD>
<BODY>
<SYNC Start=0><P Class=KRCC>&nbsp;"""
        for path in self.file_list:
            try:
                with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f: content = f.read()
                # 헤더 삭제 후 삽입 방식
                content = re.sub(r'(?is)<SAMI>.*?(?=<BODY>)', '', content, count=1)
                content = re.sub(r'(?is)<BODY>.*?(<--.*?-->\s*<--.*?-->)?', new_header, content, count=1)
                with open(path, 'w', encoding='utf-8-sig') as f: f.write(content)
            except Exception as e: print(f"Error: {e}")
        messagebox.showinfo("완료", "헤더 교체 완료")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SMIEditor(root)
    root.mainloop()

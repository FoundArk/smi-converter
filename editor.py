import os, re, tkinter as tk
from tkinter import messagebox, scrolledtext
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
        # 1. 삽입할 헤더 (Raw String으로 기호 유지)
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
                with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f: 
                    content = f.read()
                
                # 2. 헤더 작업: <SAMI>부터 원본 주석 2줄까지를 정확하게 매칭해서 제거
                # 정규식 설명: <SAMI>부터 시작해서 <BODY>를 지나고 주석 2줄이 끝나는 지점까지 찾음
                pattern = r'(?is)<SAMI>.*?(?:<--\s*Open\s+tools\s+menu.*?-->\s*|(?=<BODY>))'
                
                # 먼저 기존 헤더를 싹 지우고, <BODY> 뒤의 쓸데없는 주석 2줄도 찾아 제거
                content = re.sub(pattern, "", content, count=1)
                content = re.sub(r'(?is)<--\s*Open\s+play\s+menu.*?-->\s*<--\s*Open\s+tools\s+menu.*?-->', "", content)
                
                # 3. 새로운 헤더와 결합
                # <BODY> 태그가 날아갔을 수 있으니 보장하고 헤더 삽입
                if "<BODY>" not in content.upper():
                    content = "<BODY>\n" + content
                
                final_content = new_header + "\n" + content
                
                with open(path, 'w', encoding='utf-8-sig') as f: 
                    f.write(final_content)
            except Exception as e:
                print(f"Error: {e}")
        messagebox.showinfo("완료", "헤더 교체 완료")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SMIEditor(root)
    root.mainloop()

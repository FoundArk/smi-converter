import os, re, tkinter as tk
from tkinter import filedialog, messagebox

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SMI Batch Processor")
        self.root.geometry("350x200")
        tk.Label(root, text="SMI 파일 일괄 변환기 (최대 200개)").pack(pady=10)
        tk.Button(root, text="파일 선택 및 변환 시작", command=self.process_files, bg="#e0e0e0").pack(pady=20)

    def process_files(self):
        files = filedialog.askopenfilenames(filetypes=[("SMI files", "*.smi")])
        if not files: return

        # 5. 헤더 교체용 타겟 문자열
        target_header = """<SAMI>
<HEAD>
<TITLE>Subtitle Validation Tool x64 1.2.4 - (C) SPTek, Inc.</TITLE>
<STYLE TYPE="text/css">
</STYLE>
</HEAD>
<BODY>
<SYNC Start=0><P Class=KRCC>&nbsp;"""

        for path in files:
            try:
                with open(path, 'r', encoding='cp949', errors='ignore') as f: content = f.read()
                
                # 3. KOKRCC/KOKR -> KRCC 변환
                content = re.sub(r'KOKRCC|KOKR', 'KRCC', content, flags=re.IGNORECASE)
                
                # 4. 줄바꿈 로직
                # 4-1, 4-2: <P Class=KRCC> 뒤 문자 줄바꿈 (&nbsp; 제외)
                content = re.sub(r'(<P Class=KRCC>)(?!\s*&nbsp;)([^ \s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
                # 4-3: &nbsp; 뒤 문자 줄바꿈
                content = re.sub(r'(&nbsp;)([^ \s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
                # 4-4: <br> 뒤 문자 줄바꿈
                content = re.sub(r'(<br>)\s*([^\r\n<>])', r'\1\n\2', content, flags=re.IGNORECASE)
                
                # 5. 헤더 교체
                content = re.sub(r'(?is)<SAMI>.*?(<--.*?-->\s*<--.*?-->|<BODY>)', target_header, content, count=1)
                
                with open(path, 'w', encoding='cp949') as f: f.write(content)
            except Exception as e: continue
        
        messagebox.showinfo("완료", f"{len(files)}개의 파일이 변환되었습니다.")

if __name__ == "__main__":
    root = tk.Tk()
    SMIEditor(root)
    root.mainloop()

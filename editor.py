import os, re, tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SMI Editor")
        self.root.geometry("600x550")
        self.file_list = []

        # 1. 상태 메시지 라벨 (팝업 대신 사용)
        self.status_label = tk.Label(root, text="SMI 파일을 드래그하세요.", fg="blue", font=("Arial", 10))
        self.status_label.pack(pady=5)

        # 2. 리스트박스
        self.listbox = tk.Listbox(root, selectmode=tk.MULTIPLE, width=80, height=15)
        self.listbox.pack(pady=5)
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self.drop_files)

        # 3. 버튼 영역
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="KRCC 변환", command=self.fix_krcc).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="줄바꿈 최적화", command=self.fix_newline).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="헤더 일괄 교체", command=self.fix_header, bg="yellow").pack(side=tk.LEFT, padx=5)

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.endswith('.smi'):
                self.file_list.append(f)
                self.listbox.insert(tk.END, os.path.basename(f))
        self.status_label.config(text=f"{len(self.file_list)}개의 파일이 추가되었습니다.")

    def fix_krcc(self):
        for path in self.file_list:
            with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f: content = f.read()
            content = re.sub(r'KOKRCC|KOKR', 'KRCC', content, flags=re.IGNORECASE)
            with open(path, 'w', encoding='utf-8-sig') as f: f.write(content)
        self.status_label.config(text="KRCC 변환 완료")

    def fix_newline(self):
        for path in self.file_list:
            with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f: content = f.read()
            content = re.sub(r'(<P Class=KRCC>)(?!\s*&nbsp;)([^ \s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
            content = re.sub(r'(&nbsp;)([^ \s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
            content = re.sub(r'(<br>)\s*([^\r\n<>])', r'\1\n\2', content, flags=re.IGNORECASE)
            with open(path, 'w', encoding='utf-8-sig') as f: f.write(content)
        self.status_label.config(text="줄바꿈 최적화 완료")

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

import os, re, tkinter as tk
from tkinter import ttk, filedialog
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
        # 상단 트리뷰 영역
        self.tree = ttk.Treeview(root, columns=("File Name", "Status", "Review"), show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree.heading("File Name", text="File Name")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Review", text="Review")
        self.tree.column("File Name", width=300)
        self.tree.column("Status", width=120)
        self.tree.column("Review", width=180)

        # 하단 상태 라벨 및 버튼 영역
        self.status_label = tk.Label(root, text="검수 완료", fg="black", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10)

        btn_frame = tk.Frame(root, pady=10)
        btn_frame.pack()

        # 버튼 4개 배치
        tk.Button(btn_frame, text="전체 변환 실행", command=self.run_all_process, bg="skyblue", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="검수", command=self.review_original, bg="khaki", width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="덮어쓰기 저장", command=lambda: self.save_files(True), bg="lightgreen", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="다른 이름으로 저장", command=lambda: self.save_files(False), bg="orange", width=15).pack(side=tk.LEFT, padx=5)

        # [이벤트 바인딩]
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop_files)

        self.file_data = {}
        self.temp_contents = {}

    # --- 기능함수 모음 ---
    def convert_content(self, content):
        # 1. KRCC 변환
        # 1-1. 기존코드: KOKRCC와 KOKR만 KRCC로 변경 (안정성 높음)
        # 1-2. 변경코드: <P Class=****>의 ****에 해당하는 모든 문자를 KRCC로 변경 (범용성 높음)
        content = re.sub(r'(<P\s+Class=)(KOKR|KRCC)[^>]*>', r'\1KRCC>', content, flags=re.IGNORECASE)
        
        # 2. 줄바꿈 최적화 (<br> 포함 필수 줄바꿈)
        content = re.sub(r'(<P Class=KRCC>)(?!\s*&nbsp;)([^\s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
        content = re.sub(r'(<br>)\s*([^\r\n<>])', r'\1\n\2', content, flags=re.IGNORECASE)
        
        # 3. \an8 삭제 (현재로서는 {\an8}만 발견되어 사용했으나, 1-9 범위 내 다른 숫자 발견 시 적용)
        content = re.sub(r'{\\an[1-9]}', '', content, flags=re.IGNORECASE)
        
        return content

    def run_all_process(self):
        for item, path in self.file_data.items():
            try:
                # 1. 인코딩 문제 해결: ANSI(cp949) 파일도 utf-8로 저장 가능!
                try:
                    with open(path, 'r', encoding='cp949') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                content = self.convert_content(content)
                                
                # 1. 태그 변환 및 줄바꿈 최적화
                content = self.convert_content(content)

                # 4. 헤더 교체 (<!--부터 -->까지의 내용을 AI는 인식하지 못하는 경우가 많아서 앞쪽 헤더 강제화가 필수, 사라지는 것에 주의)
                lines = ["<SAMI>", "<HEAD>", "<TITLE>Subtitle Validation Tool x64 1.2.4 - (C) SPTek, Inc.</TITLE>",
                         '<STYLE TYPE="text/css">', "<!--", "P {margin-left:4pt; margin-right:4pt; margin-bottom:2pt; margin-top:2pt;",
                         "   text-align:Center; font-size:18pt; font-family: 맑은 고딕, 굴림, Arial;", "   font-weight:Bold; color:white;}",
                         ".KRCC {Name:한국어; Lang:ko-KR; SAMIType:CC;}", "-->", "</STYLE>", 
                         "</HEAD>", "<BODY>", "<SYNC Start=0><P Class=KRCC>&nbsp;"]
                
                idx = content.find('<SYNC')
                if idx != -1: content = "\n".join(lines) + "\n" + content[idx:]
                
                self.temp_contents[item] = content
                self.tree.set(item, "Status", "변환 완료")
            except Exception as e:
                self.tree.set(item, "Status", f"오류: {e}")
        self.status_label.config(text="전체 변환 완료.")

    def review_original(self):
        for item, path in self.file_data.items():
            try:
                with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    content = f.read()
                issues = []
                for i in range(1, 10):
                    tag = r'{\an' + str(i) + r'}'
                    if tag in content: issues.append(tag)
                if 'KOKRCC' in content.upper(): issues.append('KOKRCC')
                elif 'KOKR' in content.upper(): issues.append('KOKR')
                self.tree.set(item, "Review", ", ".join(issues) + " 발견" if issues else "이상 없음")
            except Exception as e:
                self.tree.set(item, "Review", f"검수 실패: {e}")
        self.status_label.config(text="검수 완료")

    def save_files(self, overwrite):
        count = 0
        for item, path in self.file_data.items():
            if item not in self.temp_contents: continue
            save_path = path if overwrite else os.path.join(os.path.dirname(path), f"{os.path.splitext(os.path.basename(path))[0]}_변환완료.smi")
            try:
                with open(save_path, 'w', encoding='utf-8-sig') as f:
                    f.write(self.temp_contents[item])
                self.tree.set(item, "Status", "저장 완료")
                count += 1
            except Exception as e:
                self.tree.set(item, "Status", f"저장 실패: {e}")
        self.status_label.config(text=f"총 {count}개 파일 저장 완료")

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.endswith('.smi'):
                item = self.tree.insert("","end",values=(os.path.basename(f),"준비됨","-"))
                self.file_data[item] = f

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SMIEditor(root)
    root.mainloop()

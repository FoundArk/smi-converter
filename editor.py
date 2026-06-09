import os, re, tkinter as tk
from tkinter import ttk, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SMI Editor - 안전 변환 모드")
        self.root.geometry("610x650")

        # [스타일 설정]
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", borderwidth=2, relief="solid")
        style.configure("Treeview.Heading", relief="raised")

        # [컨테이너 생성]
        container = tk.Frame(root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # [스크롤바 생성] - container 안에!
        scrollbar = ttk.Scrollbar(container, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # [트리뷰 생성] - container 안에! (yscrollcommand 연결)
        self.tree = ttk.Treeview(container, columns=("File Name", "Status", "Review"), 
                                 show="headings", height=15, 
                                 yscrollcommand=scrollbar.set)
        
        # [스크롤바와 트리뷰 연결]
        scrollbar.config(command=self.tree.yview)

        # [트리뷰 배치] - container 안에서 왼쪽
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # [컬럼 설정]
        self.tree.heading("File Name", text="File Name")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Review", text="Review")
        self.tree.column("File Name", width=250)
        self.tree.column("Status", width=100)
        self.tree.column("Review", width=150)

        # 2. 바인딩
        self.tree.bind('<Double-1>', self.on_header_double_click)
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop_files)
        self.tree.bind('<F5>', self.clear_list)

        # 3. UI 및 버튼
        self.status_label = tk.Label(root, text="파일을 드래그하고 [전체 변환]을 누르세요.", fg="black", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="전체 변환 실행", command=self.run_all_process, bg="skyblue").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="검수", command=self.review_files, bg="khaki").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="덮어쓰기 저장", command=lambda: self.save_files(overwrite=True), bg="lightgreen").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="다른 이름으로 저장", command=lambda: self.save_files(overwrite=False), bg="orange").pack(side=tk.LEFT, padx=5)

        self.file_data = {}
        self.temp_contents = {}

    # --- 기능함수 모음 ---
    def convert_content(self, content):
        # 1. KRCC 변환
        # 1-1. 기존코드: KOKRCC와 KOKR만 KRCC로 변경 (안정성 높음)
        # content = re.sub(r'KOKRCC', 'KRCC', content, flags=re.IGNORECASE)
        # content = re.sub(r'KOKR', 'KRCC', content, flags=re.IGNORECASE)
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
                with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    content = f.read()
                
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
                self.tree.set(item, "Status", "변환 완료(저장 대기)")
            except Exception as e:
                self.tree.set(item, "Status", f"오류: {e}")
        self.status_label.config(text="모든 파일 변환 완료. 저장 방식을 선택하세요.")

    def on_header_double_click(self, event):
        from tkinter import font
        region = self.tree.identify_region(event.x, event.y)
        if region in ("separator", "heading"):
            column = self.tree.identify_column(event.x)
            col_id = self.tree.column(column, "id")
            f = font.nametofont("TkHeadingFont")
            header_text = self.tree.heading(col_id, "text")
            max_width = f.measure(header_text)
            for child in self.tree.get_children():
                val = str(self.tree.set(child, col_id))
                max_width = max(max_width, f.measure(val))
            new_width = max_width + 20
            self.tree.column(col_id, width=new_width, minwidth=new_width)

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
                if any(x in content for x in [r'{\an1}', r'{\an2}', r'{\an3}', r'{\an4}', r'{\an5}', r'{\an6}', r'{\an7}', r'{\an8}', r'{\an9}']): issues.append(r'{\an*}')
                if any(x in content.upper() for x in ['KOKRCC', 'KOKR']): issues.append(r'KOKR계열')
                result = ", ".join(issues) + " 발견" if issues else "이상 없음"
                self.tree.set(item, "Review", result)
            except Exception as e:
                self.tree.set(item, "Review", f"검수 실패: {e}")
        self.status_label.config(text="검수 완료")

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

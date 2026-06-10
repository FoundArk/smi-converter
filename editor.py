import os, re, tkinter as tk
from tkinter import ttk, font
from tkinterdnd2 import DND_FILES, TkinterDnD

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SMI Editor")  # 실행 파일 이름 연동 제거
        self.root.geometry("600x650")

        # [스타일 설정]
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", borderwidth=2, relief="solid")
        style.configure("Treeview.Heading", relief="raised")

        # [메인 구성]
        self.tree = ttk.Treeview(root, columns=("Name", "Status", "Encode", "Info"), show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree.heading("Name", text="Name", command=lambda: self.on_header_double_click("Name"))
        self.tree.heading("Status", text="Status", command=lambda: self.on_header_double_click("Status"))
        self.tree.heading("Encode", text="Encode", command=lambda: self.on_header_double_click("Encode"))
        self.tree.heading("Info", text="Info", command=lambda: self.on_header_double_click("Info"))
        
        self.tree.column("Name", width=200); self.tree.column("Status", width=100)
        self.tree.column("Encode", width=80); self.tree.column("Info", width=200)
        
        self.tree.bind('<Double-1>', self.on_header_double_click)
        self.root.bind('<F5>', self.clear_list)

        # 하단 상태 라벨 및 버튼 영역
        self.status_label = tk.Label(root, text="검수 완료", fg="black", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10)

        btn_frame = tk.Frame(root, pady=10)
        btn_frame.pack()

        # 버튼 4개 배치
        tk.Button(btn_frame, text="자막 변환 실행", command=self.run_all_process, bg="skyblue", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="변환 자막 검수", command=self.review_original, bg="khaki", width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="덮어쓰기 저장", command=lambda: self.save_files(True), bg="lightgreen", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="다른 이름으로 저장", command=lambda: self.save_files(False), bg="orange", width=15).pack(side=tk.LEFT, padx=5)

        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop_files)

        self.file_data = {}; self.temp_contents = {}

    # --- 기능함수 모음 ---
    def read_file(self, path):
        # 인코딩 자동 보정: ANSI(cp949) 우선 시도 후 실패 시 utf-8
        for enc in ['cp949', 'utf-8', 'utf-8-sig']:
            try:
                with open(path, 'r', encoding=enc) as f: return f.read()
            except: continue
        return ""

    def clear_list(self, event=None):
        for item in self.tree.get_children(): self.tree.delete(item)
        self.file_data.clear(); self.temp_contents.clear()

    def on_header_double_click(self, event):
        if self.tree.identify_region(event.x, event.y) == 'heading':
            col = self.tree.identify_column(event.x)
            col_id = self.tree.column(col, "id")
            f = font.nametofont("TkHeadingFont")
            max_width = f.measure(self.tree.heading(col_id, "text"))
            for child in self.tree.get_children(): max_width = max(max_width, f.measure(self.tree.set(child, col_id)))
            self.tree.column(col_id, width=max_width + 20)

    def convert_content(self, content):
        # 1. KRCC 변환
        # 1-1. 기존코드: KOKRCC와 KOKR만 KRCC로 변경 (안정성 높음)
        # 1-2. 변경코드: <P Class=****>의 ****에 해당하는 모든 문자를 KRCC로 변경 (범용성 높음)
        content = re.sub(r'(<P\s+Class=)[^>]+>', r'\1KRCC>', content, flags=re.IGNORECASE)
        
        # 2. 줄바꿈 최적화 (<br> 포함 필수 줄바꿈)
        content = re.sub(r'(<P Class=KRCC>)(?!\s*&nbsp;)([^\s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
        content = re.sub(r'(<br>)\s*([^\r\n<>])', r'\1\n\2', content, flags=re.IGNORECASE)
        
        # 3. \an8 삭제 (현재로서는 {\an8}만 발견되어 사용했으나, 1-9 범위 내 다른 숫자 발견 시 적용)
        content = re.sub(r'{\\an[1-9]}', '', content, flags=re.IGNORECASE)
        
        return content

    def run_all_process(self):
        for item, path in self.file_data.items():
            try:
                content = self.convert_content(self.read_file(path))
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
                # 파일 인코딩 체크
                is_ansi = False
                try:
                    with open(path, 'r', encoding='cp949'): is_ansi = True
                except: is_ansi = False
                
                content = self.read_file(path)
                issues = []
                for i in range(1, 10):
                    tag = r'{\an' + str(i) + r'}'
                    if tag in content: issues.append(tag)
                if 'KOKRCC' in content.upper(): issues.append('KOKRCC')
                elif 'KOKR' in content.upper(): issues.append('KOKR')
                
                self.tree.set(item, "Encode", "ANSI" if is_ansi else "UTF-8")
                self.tree.set(item, "Info", ", ".join(issues) + " 발견" if issues else "이상 없음")
            except Exception as e:
                self.tree.set(item, "Info", f"검수 실패: {e}")
        self.status_label.config(text="검수 완료")

    def save_files(self, overwrite):
        count = 0
        for item, path in self.file_data.items():
            if item not in self.temp_contents: continue
            save_path = path if overwrite else os.path.join(os.path.dirname(path), f"{os.path.splitext(os.path.basename(path))[0]}_변환완료.smi")
            try:
                # 2. 저장 시 인코딩: 한글이 깨지지 않게 'utf-8-sig' 사용 (BOM 포함)
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
                content = self.read_file(f)
                
                # 1. {\an1} ~ {\an9} 검출
                an_issues = [f'{{\\an{i}}}' for i in range(1, 10) if f'{{\\an{i}}}' in content]
                
                # 2. Class 계열 검출 (Class= 뒤에 KRCC가 아닌 것이 오면 검출)
                class_matches = re.findall(r'Class=([^>\s]+)', content, flags=re.IGNORECASE)
                class_issues = [f"Class={c}" for c in set(class_matches) if c.upper() != "KRCC"]
                
                # 3. KOKRCC / KOKR 검출
                k_issues = []
                if 'KOKRCC' in content.upper(): k_issues.append('KOKRCC')
                elif 'KOKR' in content.upper(): k_issues.append('KOKR')
                
                # 결과 합치기
                all_issues = an_issues + class_issues + k_issues
                info_text = ", ".join(all_issues) + " 발견" if all_issues else "이상 없음"
                
                # 인코딩 체크 (간단하게)
                enc = "ANSI" if any(c > 127 for c in content.encode('cp949', errors='ignore') if c > 127) else "UTF-8"
                
                item = self.tree.insert("", "end", values=(os.path.basename(f), "준비됨", enc, info_text))
                self.file_data[item] = f

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SMIEditor(root)
    root.mainloop()

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
        # 1. 트리뷰와 스크롤바를 담을 프레임 생성
        tree_frame = tk.Frame(root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 2. 스크롤바 생성
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        
        # 3. 트리뷰 생성 (여기서 yscrollcommand 추가!)
        self.tree = ttk.Treeview(tree_frame, columns=("Name", "Status", "Encode", "Info"), 
                                 show="headings", yscrollcommand=scrollbar.set)
        
        # 4. 스크롤바를 트리뷰의 yview와 연결
        scrollbar.config(command=self.tree.yview)
        
        # 5. 배치 (스크롤바를 오른쪽에, 트리뷰를 왼쪽에)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 기존 heading의 command는 제거하고 이벤트 바인딩으로 통합 처리
        self.tree.heading("Name", text="Name")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Encode", text="Encode")
        self.tree.heading("Info", text="Info")
        
        self.root.update()
        self.tree.column("Name", width=250)
        self.tree.column("Status", width=100)
        self.tree.column("Encode", width=80)
        self.tree.column("Info", width=150)
        
        # 한 번 클릭 시 -> 정렬 실행
        self.tree.bind('<Button-1>', self.on_header_double_click)
        # 더블 클릭 시 -> 컬럼 너비 자동 조절 실행
        self.tree.bind('<Double-1>', self.on_header_double_click_width)
        self.root.bind('<F5>', self.clear_list)

        # 하단 상태 라벨 (초기 문구 수정)
        self.status_label = tk.Label(root, text="파일을 드래그하여 추가하세요.", fg="black", anchor="w", bd=1, relief="sunken")
        self.status_label.pack(fill=tk.X, padx=10, pady=5)

        # __init__ 내 버튼 구성
        btn_frame = tk.Frame(root, pady=10)
        btn_frame.pack(fill=tk.X, padx=5)

        tk.Button(btn_frame, text="파일 변환 실행", command=self.run_all_process, bg="skyblue", width=12).pack(side=tk.LEFT, expand=True, padx=2)
        tk.Button(btn_frame, text="변환 파일 검수", command=self.review_original, bg="khaki", width=12).pack(side=tk.LEFT, expand=True, padx=2)
        tk.Button(btn_frame, text="원본 덮어쓰기", command=lambda: self.save_files(True), bg="lightgreen", width=12).pack(side=tk.LEFT, expand=True, padx=2)
        tk.Button(btn_frame, text="다른이름 저장", command=lambda: self.save_files(False), bg="orange", width=12).pack(side=tk.LEFT, expand=True, padx=2)

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
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.file_data.clear()
        self.temp_contents.clear()
        self.status_label.config(text="목록 초기화됨. 파일을 드래그하세요.")

    def on_header_double_click(self, event):
        # 1. 헤더 영역을 '한 번 클릭'했을 때의 정렬 처리
        region = self.tree.identify_region(event.x, event.y)
        if region == 'heading':
            col = self.tree.identify_column(event.x)
            col_id = self.tree.column(col, "id")
            
            # 현재 컬럼 데이터 가져오기
            data = [(self.tree.set(child, col_id), child) for child in self.tree.get_children('')]
            
            # 오름차순/내림차순 토글 (컬럼별로 정렬 상태 관리)
            if not hasattr(self, "sort_states"):
                self.sort_states = {}
            reverse = self.sort_states.get(col_id, False)
            
            data.sort(reverse=reverse)
            
            for i, (val, child) in enumerate(data):
                self.tree.move(child, '', i)
                
            self.sort_states[col_id] = not reverse

    def on_header_double_click_width(self, event):
        # 2. 기존의 '더블클릭' 시 열 너비 자동 조절 기능 유지
        if self.tree.identify_region(event.x, event.y) == 'heading':
            col = self.tree.identify_column(event.x)
            col_id = self.tree.column(col, "id")
            f = font.nametofont("TkHeadingFont")
            max_width = f.measure(self.tree.heading(col_id, "text"))
            for child in self.tree.get_children(): 
                max_width = max(max_width, f.measure(self.tree.set(child, col_id)))
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

        # 4. 추가 요구사항: '…' -> '...' 변경
        content = content.replace('…', '...')
        
        # 5. [수정] '맞는구나' -> '맞구나' 자동 변경
        content = content.replace('맞는구나', '맞구나')
        
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
                # 1. 원본 내용을 가져올지, 가상 영역의 내용을 가져올지 결정
                # 가상 영역에 변환된 내용이 있으면 그것을 우선 검사
                content = self.temp_contents.get(item, self.read_file(path))
                
                # 2. 인코딩 예측: 변환 후에는 항상 'utf-8-sig'로 저장될 예정이므로
                # '저장 시 인코딩'을 명시적으로 표시하는 것이 훨씬 정확합니다.
                self.tree.set(item, "Encode", "UTF-8(BOM)")
                
                # 3. Info 영역 검수 (메모리상 content 기준)
                an_issues = [f'{{\\an{i}}}' for i in range(1, 10) if f'{{\\an{i}}}' in content]
                classes = re.findall(r'<P\s+Class=([^>]+)>', content, flags=re.IGNORECASE)
                class_issues = [c for c in set(classes) if c.upper() not in ["KRCC", "KOKR", "KOKRCC"]]
                
                k_issues = []
                if 'KOKRCC' in content.upper(): k_issues.append('KOKRCC')
                elif 'KOKR' in content.upper(): k_issues.append('KOKR')

                # '맞는다'의 경우 확인 필요
                matching_issues = []
                if '맞는다' in content:
                    matching_issues.append('맞는다 검수')

                # 말줄임표(…) 검사 추가
                dot_issues = []
                if '…' in content:
                    dot_issues.append('… 발견')
                
                all_issues = an_issues + class_issues + k_issues + matching_issues + dot_issues
                if all_issues:
                    info_parts = []
                    if an_issues or class_issues or k_issues:
                        info_parts.append(", ".join(an_issues + class_issues + k_issues) + " 발견")
                    if matching_issues:
                        info_parts.append("맞는다 검수")
                    if dot_issues:
                        info_parts.append("… 발견")
                    info_text = " / ".join(info_parts)
                else:
                    info_text = "이상 없음"
                
                self.tree.set(item, "Info", info_text)
                
            except Exception as e:
                self.tree.set(item, "Info", f"검수 실패: {e}")
        self.status_label.config(text=f"{len(self.file_data)}개 파일 검수 완료.")

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
        self.status_label.config(text=f"총 {count}개 파일 저장 완료.")

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.endswith('.smi'):
                content = self.read_file(f)
                an_issues = [f'{{\\an{i}}}' for i in range(1, 10) if f'{{\\an{i}}}' in content]
                classes = re.findall(r'<P\s+Class=([^>]+)>', content, flags=re.IGNORECASE)
                class_issues = [c for c in set(classes) if c.upper() not in ["KRCC", "KOKR", "KOKRCC"]]
                k_issues = []
                if 'KOKRCC' in content.upper(): k_issues.append('KOKRCC')
                elif 'KOKR' in content.upper(): k_issues.append('KOKR')
                
                # '맞는다'만 검수 대상으로 잡음
                matching_issues = ['맞는다 검수'] if '맞는다' in content else []
                dot_issues = ['… 발견'] if '…' in content else []

                all_issues = an_issues + class_issues + k_issues + matching_issues + dot_issues
                
                if all_issues:
                    info_parts = []
                    if an_issues or class_issues or k_issues:
                        info_parts.append(", ".join(an_issues + class_issues + k_issues) + " 발견")
                    if matching_issues:
                        info_parts.append("맞는다 검수")
                    if dot_issues:
                        info_parts.append("… 발견")
                    info_text = " / ".join(info_parts)
                else:
                    info_text = "이상 없음"
                
                enc = self.get_encoding(f)
                item = self.tree.insert("", "end", values=(os.path.basename(f), "준비됨", enc, info_text))
                self.file_data[item] = f
        
        # 1. 컬럼 너비 조정
        for col in ["Name", "Status", "Encode", "Info"]:
            self.auto_resize_column(col)
        
        # 2. 상태 라벨 강제 업데이트
        msg = f"총 {len(self.file_data)}개의 파일이 추가되었습니다."
        self.status_label.config(text=msg)
        self.root.update_idletasks() # 화면에 즉시 반영되도록 강제 지시
        print(msg) # 디버그용: 터미널에도 찍히는지 확인

    def get_encoding(self, path):
        with open(path, 'rb') as f:
            raw = f.read(3)
            if raw == b'\xef\xbb\xbf': return "UTF-8(BOM)"
        for enc in ['utf-8', 'cp949']:
            try:
                with open(path, 'r', encoding=enc) as f: f.read()
                return "UTF-8" if enc == 'utf-8' else "ANSI"
            except: continue
        return "Unknown"

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SMIEditor(root)
    root.mainloop()

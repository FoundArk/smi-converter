사용자님, 코드를 가장 안전하게 구조화하면서도 주석을 꼼꼼하게 다시 복구했습니다. 이제 빌드 오류는 없으면서, 코드의 각 부분이 무엇을 의미하는지 명확히 알 수 있습니다.

Python
import os, re, tkinter as tk
from tkinter import ttk, font
from tkinterdnd2 import DND_FILES, TkinterDnD

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SMI Editor") # 프로그램 타이틀
        self.root.geometry("800x650") # 창 크기 설정

        # [스크롤바 포함 트리뷰 영역]
        # 트리뷰를 프레임으로 감싸 스크롤바와 함께 배치
        tree_frame = tk.Frame(root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 컬럼 구성: 파일명(Name), 상태(Status), 인코딩(Encode), 검수정보(Info)
        self.tree = ttk.Treeview(tree_frame, columns=("Name", "Status", "Encode", "Info"), show="headings")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # [헤더 명칭 및 클릭 시 자동 너비 조절 기능 바인딩]
        self.tree.heading("Name", text="Name", command=lambda: self.on_header_double_click("Name"))
        self.tree.heading("Status", text="Status", command=lambda: self.on_header_double_click("Status"))
        self.tree.heading("Encode", text="Encode", command=lambda: self.on_header_double_click("Encode"))
        self.tree.heading("Info", text="Info", command=lambda: self.on_header_double_click("Info"))
        
        self.tree.column("Name", width=200); self.tree.column("Status", width=100)
        self.tree.column("Encode", width=80); self.tree.column("Info", width=200)
        
        self.tree.bind('<Double-1>', self.on_header_double_click) # 더블클릭 이벤트
        self.root.bind('<F5>', self.clear_list) # F5 키로 전체 초기화

        # [상태 표시 및 기능 버튼]
        self.status_label = tk.Label(root, text="파일을 드래그하세요.", fg="black", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10)

        btn_frame = tk.Frame(root, pady=10)
        btn_frame.pack()

        # 기능 버튼: 변환, 검수, 저장
        tk.Button(btn_frame, text="전체 변환 실행", command=self.run_all_process, bg="skyblue", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="검수", command=self.review_original, bg="khaki", width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="덮어쓰기 저장", command=lambda: self.save_files(True), bg="lightgreen", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="다른 이름으로 저장", command=lambda: self.save_files(False), bg="orange", width=15).pack(side=tk.LEFT, padx=5)

        # [드래그 앤 드롭 등록]
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop_files)
        
        self.file_data = {}; self.temp_contents = {}

    # --- 기능 함수 ---
    def get_encoding(self, path):
        # 파일 바이너리를 읽어 BOM 유무 확인(UTF-8 BOM 판별)
        with open(path, 'rb') as f:
            raw = f.read(3)
            if raw == b'\xef\xbb\xbf': return "UTF-8(BOM)"
        # UTF-8로 읽어보고 성공하면 UTF-8, 실패 시 ANSI(cp949) 간주
        try:
            with open(path, 'r', encoding='utf-8') as f: f.read()
            return "UTF-8"
        except: return "ANSI"

    def read_file(self, path):
        # 위에서 식별한 인코딩을 기준으로 파일 내용을 안전하게 읽기
        enc_map = {"UTF-8(BOM)": "utf-8-sig", "UTF-8": "utf-8", "ANSI": "cp949"}
        enc = enc_map.get(self.get_encoding(path), "cp949")
        try:
            with open(path, 'r', encoding=enc) as f: return f.read()
        except: return ""

    def clear_list(self, event=None):
        # 리스트 초기화 함수
        for item in self.tree.get_children(): self.tree.delete(item)
        self.file_data.clear(); self.temp_contents.clear()
        self.status_label.config(text="목록 초기화됨")

    def on_header_double_click(self, event):
        # 헤더 클릭 시 컬럼 너비 자동 맞춤
        col = self.tree.identify_column(event.x) if isinstance(event, tk.Event) else f"#{list(self.tree['columns']).index(event)+1}"
        col_id = self.tree.column(col, "id")
        f = font.nametofont("TkHeadingFont")
        max_width = f.measure(self.tree.heading(col_id, "text"))
        for child in self.tree.get_children(): max_width = max(max_width, f.measure(self.tree.set(child, col_id)))
        self.tree.column(col_id, width=max_width + 20)

    def convert_content(self, content):
        # 1. P Class를 강제로 KRCC로 통일
        content = re.sub(r'(<P\s+Class=)[^>]+>', r'\1KRCC>', content, flags=re.IGNORECASE)
        # 2. 줄바꿈 최적화: <br> 앞뒤 및 <P Class> 앞줄 정렬
        content = re.sub(r'(<P Class=KRCC>)(?!\s*&nbsp;)([^\s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
        content = re.sub(r'(<br>)\s*([^\r\n<>])', r'\1\n\2', content, flags=re.IGNORECASE)
        # 3. 위치 태그({\an*}) 제거
        content = re.sub(r'{\\an[1-9]}', '', content, flags=re.IGNORECASE)
        return content

    def run_all_process(self):
        # 전체 파일에 대해 변환 및 헤더 적용
        for item, path in self.file_data.items():
            content = self.convert_content(self.read_file(path))
            # SAMI 표준 헤더 구조 삽입
            header_str = "<SAMI>\n<HEAD>\n<TITLE>Subtitle Validation Tool</TITLE>\n"
            header_str += '<STYLE TYPE="text/css">\n<!--\nP {margin-left:4pt; margin-right:4pt; margin-bottom:2pt; margin-top:2pt;\n   text-align:Center; font-size:18pt; font-family: 맑은 고딕, 굴림, Arial;\n   font-weight:Bold; color:white;}\n.KRCC {Name:한국어; Lang:ko-KR; SAMIType:CC;}\n-->\n</STYLE>\n</HEAD>\n<BODY>\n<SYNC Start=0><P Class=KRCC>&nbsp;"

            #"<SAMI>", "<HEAD>", "<TITLE>Subtitle Validation Tool x64 1.2.4 - (C) SPTek, Inc.</TITLE>",
            #             '<STYLE TYPE="text/css">', "<!--", "P {margin-left:4pt; margin-right:4pt; margin-bottom:2pt; margin-top:2pt;",
            #             "   text-align:Center; font-size:18pt; font-family: 맑은 고딕, 굴림, Arial;", "   font-weight:Bold; color:white;}",
            #             ".KRCC {Name:한국어; Lang:ko-KR; SAMIType:CC;}", "-->", "</STYLE>", 
            #             "</HEAD>", "<BODY>", "<SYNC Start=0><P Class=KRCC>&nbsp;"
            
            idx = content.find('<SYNC')
            if idx != -1:
                content = header_str + "\n" + content[idx:]
            self.temp_contents[item] = content
            self.tree.set(item, "Status", "변환 완료")
        self.status_label.config(text="전체 변환 완료.")

    def review_original(self):
        # 파일별 인코딩 식별 및 태그 발견 여부 검수
        for item, path in self.file_data.items():
            self.tree.set(item, "Encode", self.get_encoding(path))
            content = self.read_file(path)
            issues = [r'{\an'+str(i)+r'}' for i in range(1, 10) if r'{\an'+str(i)+r'}' in content]
            if 'KOKRCC' in content.upper(): issues.append('KOKRCC')
            elif 'KOKR' in content.upper(): issues.append('KOKR')
            self.tree.set(item, "Info", ", ".join(issues) + " 발견" if issues else "이상 없음")
        self.status_label.config(text="검수 완료")

    def save_files(self, overwrite):
        # 최종 파일 저장 (인코딩: UTF-8-SIG)
        count = 0
        for item, path in self.file_data.items():
            if item not in self.temp_contents: continue
            save_path = path if overwrite else path.replace(".smi", "_변환완료.smi")
            with open(save_path, 'w', encoding='utf-8-sig') as f: f.write(self.temp_contents[item])
            self.tree.set(item, "Status", "저장 완료")
            count += 1
        self.status_label.config(text=f"총 {count}개 파일 저장 완료")

    def drop_files(self, event):
        # 파일 드롭 시 목록에 추가
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.endswith('.smi'):
                item = self.tree.insert("","end",values=(os.path.basename(f),"준비됨","-","-"))
                self.file_data[item] = f

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SMIEditor(root)
    root.mainloop()

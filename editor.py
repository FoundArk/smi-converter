import os, re, tkinter as tk
from tkinter import ttk, font
from tkinterdnd2 import DND_FILES, TkinterDnD

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SMI Editor")
        self.root.geometry("800x650")

        # [스크롤바 포함 트리뷰 영역]
        # 트리뷰를 프레임으로 감싸 스크롤바와 함께 배치
        tree_frame = tk.Frame(root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 컬럼: Name(파일명), Status(진행상태), Encode(인코딩), Info(검수결과)
        self.tree = ttk.Treeview(tree_frame, columns=("Name", "Status", "Encode", "Info"), show="headings")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # [헤더 설정]
        self.tree.heading("Name", text="Name", command=lambda: self.on_header_double_click("Name"))
        self.tree.heading("Status", text="Status", command=lambda: self.on_header_double_click("Status"))
        self.tree.heading("Encode", text="Encode", command=lambda: self.on_header_double_click("Encode"))
        self.tree.heading("Info", text="Info", command=lambda: self.on_header_double_click("Info"))
        
        self.tree.column("Name", width=200); self.tree.column("Status", width=100)
        self.tree.column("Encode", width=80); self.tree.column("Info", width=200)
        
        # 이벤트 바인딩
        self.tree.bind('<Double-1>', self.on_header_double_click)
        self.root.bind('<F5>', self.clear_list)

        # [하단 상태 라벨 및 버튼]
        self.status_label = tk.Label(root, text="파일을 드래그하세요.", fg="black", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10)

        btn_frame = tk.Frame(root, pady=10)
        btn_frame.pack()

        tk.Button(btn_frame, text="전체 변환 실행", command=self.run_all_process, bg="skyblue", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="검수", command=self.review_original, bg="khaki", width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="덮어쓰기 저장", command=lambda: self.save_files(True), bg="lightgreen", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="다른 이름으로 저장", command=lambda: self.save_files(False), bg="orange", width=15).pack(side=tk.LEFT, padx=5)

        # [파일 드래그 앤 드롭 설정]
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop_files)
        
        self.file_data = {}; self.temp_contents = {}

    # --- 기능함수 모음 ---
    def get_encoding(self, path):
        # 1. 파일의 첫 3바이트를 읽어 BOM(UTF-8-SIG) 여부 확인
        with open(path, 'rb') as f:
            raw = f.read(3)
            if raw == b'\xef\xbb\xbf': return "UTF-8(BOM)"
        # 2. UTF-8로 디코딩 시도 후 성공하면 UTF-8, 실패하면 ANSI(cp949)로 판별
        try:
            with open(path, 'r', encoding='utf-8') as f: f.read()
            return "UTF-8"
        except: return "ANSI"

    def read_file(self, path):
        # 판별된 인코딩을 기준으로 파일 읽기
        enc_map = {"UTF-8(BOM)": "utf-8-sig", "UTF-8": "utf-8", "ANSI": "cp949"}
        enc = enc_map.get(self.get_encoding(path), "cp949")
        try:
            with open(path, 'r', encoding=enc) as f: return f.read()
        except: return ""

    def clear_list(self, event=None):
        # F5 리스트 초기화
        for item in self.tree.get_children(): self.tree.delete(item)
        self.file_data.clear(); self.temp_contents.clear()
        self.status_label.config(text="목록 초기화됨")

    def on_header_double_click(self, event):
        # 헤더 영역 더블클릭 시 너비 자동 조절
        col = self.tree.identify_column(event.x) if isinstance(event, tk.Event) else f"#{list(self.tree['columns']).index(event)+1}"
        col_id = self.tree.column(col, "id")
        f = font.nametofont("TkHeadingFont")
        max_width = f.measure(self.tree.heading(col_id, "text"))
        for child in self.tree.get_children(): max_width = max(max_width, f.measure(self.tree.set(child, col_id)))
        self.tree.column(col_id, width=max_width + 20)

    def convert_content(self, content):
        # 1. 모든 P Class를 KRCC로 통일
        content = re.sub(r'(<P\s+Class=)[^>]+>', r'\1KRCC>', content, flags=re.IGNORECASE)
        # 2. 줄바꿈 최적화
        content = re.sub(r'(<P Class=KRCC>)(?!\s*&nbsp;)([^\s\r\n])', r'\1\n\2', content, flags=re.IGNORECASE)
        content = re.sub(r'(<br>)\s*([^\r\n<>])', r'\1\n\2', content, flags=re.IGNORECASE)
        # 3. {\an*} 위치 태그 삭제
        content = re.sub(r'{\\an[1-9]}', '', content, flags=re.IGNORECASE)
        return content

    def run_all_process(self):
        # 전체 파일 변환
        for item, path in self.file_data.items():
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
        # 원본 검수 (인코딩 식별 및 태그 발견)
        for item, path in self.file_data.items():
            self.tree.set(item, "Encode", self.get_encoding(path))
            content = self.read_file(path)
            issues = [r'{\an'+str(i)+r'}' for i in range(1, 10) if r'{\an'+str(i)+r'}' in content]
            if 'KOKRCC' in content.upper(): issues.append('KOKRCC')
            elif 'KOKR' in content.upper(): issues.append('KOKR')
            self.tree.set(item, "Info", ", ".join(issues) + " 발견" if issues else "이상 없음")
        self.status_label.config(text="검수 완료")

    def save_files(self, overwrite):
        # 파일 저장 (저장 시에는 UTF-8-SIG로 인코딩하여 호환성 유지)
        count = 0
        for item, path in self.file_data.items():
            if item not in self.temp_contents: continue
            save_path = path if overwrite else path.replace(".smi", "_변환완료.smi")
            with open(save_path, 'w', encoding='utf-8-sig') as f: f.write(self.temp_contents[item])
            self.tree.set(item, "Status", "저장 완료")
            count += 1
        self.status_label.config(text=f"총 {count}개 파일 저장 완료")

    def drop_files(self, event):
        # 파일 드롭 이벤트 처리
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.endswith('.smi'):
                item = self.tree.insert("","end",values=(os.path.basename(f),"준비됨","-","-"))
                self.file_data[item] = f

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SMIEditor(root)
    root.mainloop()

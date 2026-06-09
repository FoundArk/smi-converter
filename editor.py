import os, re, tkinter as tk
from tkinter import ttk, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD

class SMIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SMI Editor - 안전 변환 모드")
        self.root.geometry("800x700")

        # [상단: 트리뷰]
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(top_frame, columns=("File Name", "Status", "Review"), show="headings", height=12)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.heading("File Name", text="File Name"); self.tree.heading("Status", text="Status"); self.tree.heading("Review", text="Review")
        self.tree.column("File Name", width=250); self.tree.column("Status", width=120); self.tree.column("Review", width=150)
        
        # [하단: 좌측 버튼 5개 + 우측 로그 5줄]
        bottom_frame = tk.Frame(root, padx=10, pady=10)
        bottom_frame.pack(fill=tk.X)

        # 좌측 버튼 영역
        btn_frame = tk.Frame(bottom_frame)
        btn_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        # 우측 로그 영역 (5줄 고정)
        log_frame = tk.Frame(bottom_frame, relief="solid", borderwidth=1, bg="white")
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.logs = []
        btn_texts = ["완료 자막 검수", "전체 변환 실행", "변환 자막 검수", "덮어쓰기 저장", "다른 이름 저장"]
        colors = ["khaki", "skyblue", "violet", "lightgreen", "orange"]
        commands = [self.review_original, self.run_all_process, self.review_converted, 
                    lambda: self.save_files(True), lambda: self.save_files(False)]

        for i in range(5):
            tk.Button(btn_frame, text=btn_texts[i], bg=colors[i], width=18, command=commands[i]).pack(pady=3)
            log = tk.Label(log_frame, text=f"{i+1}.", anchor="w", bg="white", height=2)
            log.pack(fill=tk.X, padx=5)
            self.logs.append(log)

        self.file_data = {}; self.temp_contents = {}
        self.tree.drop_target_register(DND_FILES); self.tree.dnd_bind('<<Drop>>', self.drop_files)

    def update_log(self, idx, text):
        self.logs[idx].config(text=f"{idx+1}. {text}")

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
                self.tree.set(item, "Status", "변환 완료")
            except Exception as e:
                self.tree.set(item, "Status", f"오류: {e}")
        self.update_log(1, "전체 변환 실행 완료: KOKR->KRCC, 줄바꿈, 헤더 교체 적용")

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
        self.update_log(0, "원본 검수 완료: {\an*}, KOKR 등 이상 유무 기록")

    def review_converted(self):
        for item, path in self.file_data.items():
            if item not in self.temp_contents:
                self.tree.set(item, "Review", "변환 미실행")
                continue
            content = self.temp_contents[item]
            if any(x in content for x in [r'{\an', 'KOKR']):
                self.tree.set(item, "Review", "오류: 태그 남아있음")
            else:
                self.tree.set(item, "Review", "변환 파일 이상 없음")
        self.update_log(2, "변환 자막 검수 완료: 오류 유무 기록")

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
        self.update_log(3 if overwrite else 4, f"파일 저장 방식 선택: {'덮어쓰기' if overwrite else '다른 이름 저장'} 완료")

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

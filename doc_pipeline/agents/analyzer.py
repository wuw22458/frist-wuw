"""Agent 3: 摘要生成 + 标签分类 + 文档关系检测。"""
import re
import time

from utils import TAG_TAXONOMY, save_manifest, setup_logging

STUDENT_ID = "2024XXXX01"
_RE_VERSION = re.compile(r"_\s*优化版|\(\d+\)")
_RE_EXT = re.compile(r"\.\w+$")
_RE_CN = re.compile(r"[一-鿿]{2,}")


class AnalyzerAgent:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.logger = setup_logging(output_dir)

    def run(self, manifest):
        self.logger.info("=" * 50)
        self.logger.info("[ANALYZER] 开始分析")
        t0 = time.time()

        files = manifest.get("files", [])
        non_dup = [f for f in files if not f.get("is_duplicate") and f.get("text_content")]

        for f in non_dup:
            f["summary"] = self._gen_summary(f)
            f["tags"] = self._assign_tags(f)
            f["category"] = f["tags"][0] if f["tags"] else "unclassified"

        # 预计算 token 集合
        token_sets = {f["path"]: set(_RE_CN.findall(f["filename"])) for f in non_dup}

        relations_count = self._detect_relationships(files, non_dup, token_sets)

        manifest["files"] = files
        manifest["stats"]["analyzed_count"] = len(non_dup)
        manifest["stats"]["relations_count"] = relations_count
        manifest["stats"]["categories"] = {}
        for f in files:
            cat = f.get("category", "unclassified")
            manifest["stats"]["categories"][cat] = manifest["stats"]["categories"].get(cat, 0) + 1

        save_manifest(manifest, self.output_dir)
        manifest["stats"]["analyzer_time"] = round(time.time() - t0, 2)
        self.logger.info("[ANALYZER] 完成 — %d 文档分析，%d 关系", len(non_dup), relations_count)
        return manifest

    def _gen_summary(self, f):
        ext = f["ext"]
        fn = f["filename"]
        text = f.get("text_content", "") or ""

        if ext == ".ipynb":
            return f"Python 编程作业，含 {text[:100].count('In[')} 个单元格。"
        if ext == ".pptx":
            slide_count = text.count("--- Slide")
            return f"演示文稿，约 {slide_count} 页幻灯片。"
        if ext == ".xlsx":
            sheet_count = text.count("--- Sheet:")
            return f"电子表格，{sheet_count} 个工作表。"
        if ext == ".csv":
            lines = text.split("\n")[:5]
            return f"CSV 数据，字段：{', '.join(l for l in lines if l)[:80]}"

        first_line = text.split("\n")[0][:80]
        if len(first_line) > 15:
            return first_line + ("..." if len(text) > 80 else "")
        return f"文档：{fn}"

    def _assign_tags(self, f):
        fn = f["filename"]
        text = f.get("text_content", "")[:3000] or ""
        tags = []

        rules = [
            (lambda: "课程记录册" in fn, "course_record"),
            (lambda: any(w in text for w in ["职业生涯", "职业规划", "生涯规划"]), "career_planning"),
            (lambda: "AIGC" in text or "AIGC" in fn, "aigc_research"),
            (lambda: f["ext"] == ".ipynb" or "作业" in fn, "course_assignment"),
            (lambda: any(w in fn for w in ["小组", "第七组", "第五小组"]), "group_project"),
            (lambda: any(w in text for w in ["视频", "脚本", "韦拔群"]), "video_production"),
            (lambda: any(w in fn for w in ["入学登记", "作息时间", "操作手册"]), "student_admin"),
            (lambda: any(w in text for w in ["AI平台", "DeepSeek"]), "ai_experiment"),
            (lambda: any(w in fn for w in ["课件", "练习题", "答案", "参考答案"]), "reference_material"),
            (lambda: any(w in fn for w in ["影评"]), "creative_writing"),
            (lambda: any(w in text for w in ["不定积分", "定积分", "导数"]), "math_exercise"),
            (lambda: f["ext"] == ".ipynb" or "Python" in text, "python_code"),
        ]
        for check, tag in rules:
            if check():
                tags.append(tag)

        return tags if tags else ["reference_material"]

    def _detect_relationships(self, all_files, non_dup, token_sets):
        count = 0
        for f in all_files:
            f.setdefault("relationships", [])

        # 1. 版本关系（before_after）
        name_map = {}
        for f in non_dup:
            base = _RE_VERSION.sub("", f["filename"])
            base = _RE_EXT.sub("", base)
            name_map.setdefault(base, []).append(f)

        for base, group in name_map.items():
            if len(group) < 2:
                continue
            group.sort(key=lambda x: x.get("mod_time", ""))
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    if group[i]["ext"] == group[j]["ext"]:
                        group[i].setdefault("relationships", []).append({
                            "type": "before_after", "target": group[j]["path"],
                            "description": f"「{group[i]['filename']}」→「{group[j]['filename']}」"})
                        group[j].setdefault("relationships", []).append({
                            "type": "before_after", "target": group[i]["path"],
                            "description": f"「{group[i]['filename']}」→「{group[j]['filename']}」"})
                        count += 2

        # 2. 跨格式关系
        for f in non_dup:
            f_tokens = token_sets[f["path"]]
            for other in non_dup:
                if other["path"] <= f["path"]:
                    continue
                shared = f_tokens & token_sets[other["path"]]
                if len(shared) >= 2 and f["ext"] != other["ext"]:
                    desc = f"共享关键词：{'、'.join(shared)}"
                    f.setdefault("relationships", []).append(
                        {"type": "cross_format", "target": other["path"], "description": desc})
                    other.setdefault("relationships", []).append(
                        {"type": "cross_format", "target": f["path"], "description": desc})
                    count += 2

        # 3. 同学号
        same_student = [f for f in non_dup if STUDENT_ID in (f.get("text_content") or "")]
        for i, f in enumerate(same_student):
            for other in same_student[i + 1:]:
                f.setdefault("relationships", []).append(
                    {"type": "same_student", "target": other["path"],
                     "description": f"学号 {STUDENT_ID} 相关文档"})
                count += 1

        # 4. 同主题（3+ 共享中文 token + 不同格式）
        for i, f in enumerate(non_dup):
            f_tokens = token_sets[f["path"]]
            for other in non_dup[i + 1:]:
                shared = f_tokens & token_sets[other["path"]]
                if len(shared) >= 3 and f["ext"] != other["ext"]:
                    desc = f"共同主题：{'、'.join(shared)}"
                    f.setdefault("relationships", []).append(
                        {"type": "same_topic", "target": other["path"], "description": desc})
                    count += 1

        return count

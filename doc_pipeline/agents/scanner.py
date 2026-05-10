"""Agent 1: 目录扫描 + SHA256 哈希去重。"""
import os
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from utils import (
    ALLOWED_EXTENSIONS,
    compute_sha256,
    format_bytes,
    save_manifest,
    setup_logging,
)

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".claude", "venv"}


class ScannerAgent:
    def __init__(self, source_dir, output_dir):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.logger = setup_logging(output_dir)

    def run(self, manifest):
        self.logger.info("=" * 50)
        self.logger.info("[SCANNER] 开始扫描: %s", self.source_dir)
        t0 = time.time()

        files = []
        ext_counter = Counter()
        skipped = total_scanned = 0

        for root, dirs, filenames in os.walk(self.source_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for fname in filenames:
                total_scanned += 1
                ext = Path(fname).suffix.lower()
                if ext not in ALLOWED_EXTENSIONS:
                    skipped += 1
                    continue
                filepath = os.path.join(root, fname)
                try:
                    stat = os.stat(filepath)
                    files.append({
                        "path": filepath,
                        "filename": fname,
                        "ext": ext,
                        "size_bytes": stat.st_size,
                        "mod_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
                    ext_counter[ext] += 1
                except (PermissionError, FileNotFoundError):
                    skipped += 1

        self.logger.info("[SCANNER] 总文件 %d，匹配 %d 个文档，跳过 %d",
                         total_scanned, len(files), skipped)

        # 哈希去重
        hash_groups = {}
        for f in files:
            try:
                h = compute_sha256(f["path"], quick=True)
                f["sha256"] = h
                hash_groups.setdefault(h, []).append(f)
            except Exception as e:
                f["sha256"] = ""
                f["hash_error"] = str(e)

        duplicates = []
        duplicate_groups = []
        for h, group in hash_groups.items():
            group.sort(key=lambda x: x.get("mod_time", ""))
            group[0]["is_duplicate"] = False
            group[0]["duplicate_of"] = None
            for dup in group[1:]:
                dup["is_duplicate"] = True
                dup["duplicate_of"] = group[0]["path"]
                duplicates.append(dup)
            if len(group) > 1:
                duplicate_groups.append([f["path"] for f in group])

        wasted = sum(f["size_bytes"] for f in duplicates)
        manifest["files"] = files
        manifest["duplicate_groups"] = duplicate_groups
        manifest["stats"]["total_files"] = len(files)
        manifest["stats"]["unique_files"] = len(files) - len(duplicates)
        manifest["stats"]["duplicate_count"] = len(duplicates)
        manifest["stats"]["duplicate_groups"] = len(duplicate_groups)
        manifest["stats"]["formats"] = dict(ext_counter)
        manifest["stats"]["wasted_bytes"] = wasted

        self.logger.info("[SCANNER] 完成 — %d 文件，%d 唯一，%d 重复组（浪费 %s）",
                         len(files), manifest["stats"]["unique_files"],
                         len(duplicate_groups), format_bytes(wasted))

        save_manifest(manifest, self.output_dir)
        manifest["stats"]["scanner_time"] = round(time.time() - t0, 2)
        return manifest

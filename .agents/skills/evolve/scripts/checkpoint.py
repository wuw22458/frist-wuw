#!/usr/bin/env python3
"""
Checkpoint 管理器 — 迭代审查技能的存档系统

用法:
  checkpoint.py init <task_dir>              初始化工作目录
  checkpoint.py save <task_dir> <round>      保存当前状态为第 N 轮快照
  checkpoint.py restore <task_dir> <round>   回滚到第 N 轮
  checkpoint.py diff <task_dir> <r1> <r2>    比较两轮的差异
  checkpoint.py list <task_dir>              列出所有快照

每轮快照存储在 <task_dir>/checkpoints/round-<N>/ 目录下。
"""

import sys
import os
import shutil
import difflib
import json
from pathlib import Path
from datetime import datetime


def get_checkpoints_dir(task_dir: str) -> Path:
    return Path(task_dir) / "checkpoints"


def init(task_dir: str):
    """初始化工作目录结构"""
    base = Path(task_dir)
    base.mkdir(parents=True, exist_ok=True)
    checkpoints = get_checkpoints_dir(task_dir)
    checkpoints.mkdir(exist_ok=True)
    
    meta_file = base / "meta.json"
    if not meta_file.exists():
        meta = {
            "created_at": datetime.now().isoformat(),
            "rounds": [],
            "current_round": 0,
        }
        meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
        print(f"✓ 工作目录已初始化: {task_dir}")
    else:
        print(f"✓ 工作目录已存在: {task_dir}")


def save(task_dir: str, round_num: int):
    """保存当前文件状态为第 N 轮快照"""
    base = Path(task_dir)
    if not base.exists():
        print(f"✗ 工作目录不存在: {task_dir}")
        sys.exit(1)

    checkpoints = get_checkpoints_dir(task_dir)
    checkpoints.mkdir(parents=True, exist_ok=True)
    round_dir = checkpoints / f"round-{round_num}"
    round_dir.mkdir(exist_ok=True)

    # 复制 task_dir 下的所有文件（排除 checkpoints 目录本身和 meta.json）
    copied = []
    skipped = []
    for item in base.iterdir():
        if item.name == "checkpoints" or item.name == "meta.json":
            continue
        try:
            if item.is_file():
                shutil.copy2(item, round_dir / item.name)
                copied.append(item.name)
            elif item.is_dir():
                dest = round_dir / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
                copied.append(f"{item.name}/")
        except PermissionError:
            skipped.append(item.name)
        except OSError as e:
            skipped.append(f"{item.name} ({e})")

    if skipped:
        print(f"⚠ 跳过 {len(skipped)} 个被锁定的文件: {', '.join(skipped)}")
    
    # 更新 meta
    meta_file = base / "meta.json"
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("⚠ meta.json 损坏，重新创建")
            meta = {"created_at": datetime.now().isoformat(), "rounds": []}
    else:
        meta = {"created_at": datetime.now().isoformat(), "rounds": []}
    
    meta["current_round"] = round_num
    meta["rounds"].append({
        "round": round_num,
        "timestamp": datetime.now().isoformat(),
        "files": copied,
    })
    meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    
    print(f"✓ 快照已保存: round-{round_num} ({len(copied)} 个文件)")


def restore(task_dir: str, round_num: int):
    """回滚到第 N 轮的状态"""
    round_dir = get_checkpoints_dir(task_dir) / f"round-{round_num}"
    if not round_dir.exists():
        print(f"✗ 快照 round-{round_num} 不存在")
        sys.exit(1)
    
    base = Path(task_dir)
    restored = []
    for item in round_dir.iterdir():
        dest = base / item.name
        if item.is_file():
            shutil.copy2(item, dest)
            restored.append(item.name)
        elif item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
            restored.append(f"{item.name}/")
    
    print(f"✓ 已回滚到 round-{round_num} ({len(restored)} 个文件)")


def diff(task_dir: str, r1: int, r2: int):
    """比较两轮快照的差异"""
    dir1 = get_checkpoints_dir(task_dir) / f"round-{r1}"
    dir2 = get_checkpoints_dir(task_dir) / f"round-{r2}"
    
    if not dir1.exists():
        print(f"✗ 快照 round-{r1} 不存在")
        sys.exit(1)
    if not dir2.exists():
        print(f"✗ 快照 round-{r2} 不存在")
        sys.exit(1)
    
    files1 = set()
    files2 = set()
    
    for f in dir1.rglob("*"):
        if f.is_file():
            files1.add(f.relative_to(dir1))
    for f in dir2.rglob("*"):
        if f.is_file():
            files2.add(f.relative_to(dir2))
    
    added = files2 - files1
    removed = files1 - files2
    common = files1 & files2
    
    if added:
        print(f"+ 新增文件: {', '.join(str(f) for f in sorted(added))}")
    if removed:
        print(f"- 删除文件: {', '.join(str(f) for f in sorted(removed))}")
    
    for f in sorted(common):
        content1 = (dir1 / f).read_text(errors="replace").splitlines()
        content2 = (dir2 / f).read_text(errors="replace").splitlines()
        
        if content1 != content2:
            print(f"\n{'='*60}")
            print(f"文件: {f}")
            print(f"{'='*60}")
            diff_lines = difflib.unified_diff(
                content1, content2,
                fromfile=f"round-{r1}/{f}",
                tofile=f"round-{r2}/{f}",
                lineterm=""
            )
            for line in diff_lines:
                print(line)
    
    if not added and not removed and all(
        (dir1 / f).read_text(errors="replace") == (dir2 / f).read_text(errors="replace")
        for f in common
    ):
        print("两个快照完全相同")


def list_snapshots(task_dir: str):
    """列出所有快照"""
    checkpoints = get_checkpoints_dir(task_dir)
    if not checkpoints.exists():
        print("没有快照")
        return
    
    rounds = sorted(checkpoints.iterdir())
    if not rounds:
        print("没有快照")
        return
    
    meta_file = Path(task_dir) / "meta.json"
    meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
    
    for r in rounds:
        if r.is_dir() and r.name.startswith("round-"):
            n = r.name.replace("round-", "")
            files = list(r.rglob("*"))
            file_count = sum(1 for f in files if f.is_file())
            print(f"  round-{n}: {file_count} 个文件")
    
    current = meta.get("current_round", "?")
    print(f"\n当前轮次: {current}")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    action = sys.argv[1]
    task_dir = sys.argv[2]
    
    if action == "init":
        init(task_dir)
    elif action == "save":
        if len(sys.argv) < 4:
            print("用法: checkpoint.py save <task_dir> <round>")
            sys.exit(1)
        save(task_dir, int(sys.argv[3]))
    elif action == "restore":
        if len(sys.argv) < 4:
            print("用法: checkpoint.py restore <task_dir> <round>")
            sys.exit(1)
        restore(task_dir, int(sys.argv[3]))
    elif action == "diff":
        if len(sys.argv) < 5:
            print("用法: checkpoint.py diff <task_dir> <r1> <r2>")
            sys.exit(1)
        diff(task_dir, int(sys.argv[3]), int(sys.argv[4]))
    elif action == "list":
        list_snapshots(task_dir)
    else:
        print(f"未知操作: {action}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

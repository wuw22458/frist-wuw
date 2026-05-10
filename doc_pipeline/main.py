"""Multi-Agent Document Intelligence Pipeline (MADIP) — CLI 入口。"""
import argparse
import os
import time

from agents.scanner import ScannerAgent
from agents.extractor import ExtractorAgent
from agents.analyzer import AnalyzerAgent
from agents.converter import ConverterAgent
from agents.reporter import ReporterAgent


def run_pipeline(source_dir, output_dir, formats):
    os.makedirs(output_dir, exist_ok=True)

    agents = [
        ("Scanner", ScannerAgent(source_dir, output_dir)),
        ("Extractor", ExtractorAgent(output_dir)),
        ("Analyzer", AnalyzerAgent(output_dir)),
        ("Converter", ConverterAgent(output_dir, formats)),
        ("Reporter", ReporterAgent(output_dir)),
    ]

    manifest = {"pipeline_run_id": time.strftime("%Y%m%d-%H%M%S"),
                "source_dir": source_dir, "output_dir": output_dir,
                "stats": {}}

    total_start = time.time()
    for name, agent in agents:
        t0 = time.time()
        print(f"\n{'=' * 60}")
        print(f"  AGENT: {name}")
        print(f"{'=' * 60}")
        manifest = agent.run(manifest)
        elapsed = time.time() - t0
        print(f"  {name} 完成，耗时 {elapsed:.1f}s")

    total_elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"Pipeline 全部完成！总耗时 {total_elapsed:.1f}s")
    print(f"报告: {output_dir}/report.html")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Agent Document Intelligence Pipeline")
    parser.add_argument("--source", default="E:/download", help="源目录（默认 E:/download）")
    parser.add_argument("--output", default="output", help="输出目录（默认 output/）")
    parser.add_argument("--formats", default="md,pdf,py", help="转换格式（逗号分隔，默认 md,pdf,py）")
    args = parser.parse_args()

    # 处理相对路径
    if not os.path.isabs(args.output):
        args.output = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)

    run_pipeline(args.source, args.output, args.formats.split(","))

#!/usr/bin/env python3
"""
VEP Manifest 验证脚本
用途：只读检查 configs/cwe_manifest.yml 与实际文件系统的一致性
阶段：Phase 1 - 不修改任何文件，只报告问题
"""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌ 缺少 PyYAML 依赖")
    print("请运行: pip install pyyaml")
    sys.exit(1)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_FILE = PROJECT_ROOT / "configs" / "cwe_manifest.yml"


def load_manifest():
    """加载 manifest 配置"""
    if not MANIFEST_FILE.exists():
        print(f"❌ 找不到 manifest 文件: {MANIFEST_FILE}")
        sys.exit(1)

    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_file_exists(file_path, description):
    """检查文件是否存在"""
    full_path = PROJECT_ROOT / file_path
    if full_path.exists():
        print(f"  ✅ {description}: {file_path}")
        return True
    else:
        print(f"  ❌ {description} 不存在: {file_path}")
        return False


def check_directory_exists(dir_path, description):
    """检查目录是否存在"""
    full_path = PROJECT_ROOT / dir_path
    if full_path.exists() and full_path.is_dir():
        print(f"  ✅ {description}: {dir_path}")
        return True
    else:
        print(f"  ❌ {description} 不存在: {dir_path}")
        return False


def verify_cwe(cwe_config):
    """验证单个 CWE 配置"""
    cwe_id = cwe_config["id"]
    cwe_name = cwe_config["name"]

    print(f"\n[{cwe_name}]")

    all_ok = True

    # 验证 CodeFuse 规则
    if "codefuse" in cwe_config and "rule_file" in cwe_config["codefuse"]:
        if not check_file_exists(cwe_config["codefuse"]["rule_file"], "CodeFuse 规则"):
            all_ok = False

    # 验证 CodeFuse 分析文档
    if "codefuse" in cwe_config and "analysis_file" in cwe_config["codefuse"]:
        check_file_exists(cwe_config["codefuse"]["analysis_file"], "CodeFuse 分析")

    # 验证 CodeQL 规则目录
    if "codeql" in cwe_config and "rule_directory" in cwe_config["codeql"]:
        if not check_directory_exists(cwe_config["codeql"]["rule_directory"], "CodeQL 规则目录"):
            all_ok = False

    # 验证测试目录
    if "tests" in cwe_config and "directory" in cwe_config["tests"]:
        check_directory_exists(cwe_config["tests"]["directory"], "测试样例目录")

    # 验证实验目录
    if "experiments" in cwe_config and "directory" in cwe_config["experiments"]:
        check_directory_exists(cwe_config["experiments"]["directory"], "实验目录")

    return all_ok


def verify_libraries(manifest):
    """验证共享库"""
    print("\n[共享库检查]")

    if "libraries" not in manifest:
        print("  ⚠️  manifest 中未配置 libraries")
        return True

    libs = manifest["libraries"]

    # CodeFuse 本地库
    if "codefuse" in libs and "local" in libs["codefuse"]:
        local_lib = libs["codefuse"]["local"]
        check_directory_exists(local_lib, "CodeFuse 本地库")

    return True


def verify_ground_truth(manifest):
    """验证 Ground Truth 文件"""
    print("\n[Ground Truth 检查]")

    if "ground_truth" not in manifest:
        print("  ⚠️  manifest 中未配置 ground_truth")
        return True

    gt_file = manifest["ground_truth"]["file"]
    return check_file_exists(gt_file, "Ground Truth 文件")


def report_naming_conventions(manifest):
    """报告命名约定差异（非错误，仅提示）"""
    print("\n[命名约定分析]")

    cwes = manifest.get("cwes", [])

    print(f"  ℹ️  当前管理 {len(cwes)} 个 CWE")
    print("  ℹ️  检测到的命名约定：")
    print("     - 规则目录: CWE-{ID} (例如 CWE-022)")
    print("     - 测试目录: cwe{id} (例如 cwe022)")
    print("     - 实验目录: cwe-{id} (例如 cwe-022)")
    print("     - manifest slug: cwe-{id}")
    print("  ⚠️  命名不一致是已知问题，Phase 2 将统一处理")


def main():
    """主函数"""
    print("=" * 60)
    print("VEP Manifest 验证工具 (Phase 1 - 只读检查)")
    print("=" * 60)

    manifest = load_manifest()
    print(f"✅ 成功加载 manifest: {MANIFEST_FILE.relative_to(PROJECT_ROOT)}")
    print(f"   版本: {manifest.get('version', 'unknown')}")
    print(f"   更新日期: {manifest.get('updated', 'unknown')}")

    # 验证 Ground Truth
    verify_ground_truth(manifest)

    # 验证共享库
    verify_libraries(manifest)

    # 验证每个 CWE
    cwes = manifest.get("cwes", [])
    all_cwes_ok = True

    for cwe in cwes:
        if not verify_cwe(cwe):
            all_cwes_ok = False

    # 命名约定分析
    report_naming_conventions(manifest)

    # 总结
    print("\n" + "=" * 60)
    if all_cwes_ok:
        print("✅ 验证通过：所有核心规则文件存在")
    else:
        print("⚠️  验证发现缺失文件，请检查上述输出")
    print("=" * 60)

    print("\n说明：")
    print("  - ✅ 表示文件/目录存在")
    print("  - ❌ 表示文件/目录不存在（可能导致评测失败）")
    print("  - ⚠️  表示非关键问题或已知限制")
    print("  - ℹ️  表示信息提示")
    print("\nPhase 1 承诺：本脚本只读检查，不修改任何文件。")


if __name__ == "__main__":
    main()

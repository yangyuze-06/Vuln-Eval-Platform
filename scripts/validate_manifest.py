#!/usr/bin/env python3
"""
VEP Manifest 验证脚本（兼容入口）
用途：调用 verify_manifest.py 的实现
阶段：Phase 1 - 命名兼容性包装器
"""

from verify_manifest import main

if __name__ == "__main__":
    main()

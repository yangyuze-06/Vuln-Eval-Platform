#!/bin/bash

# ===============================
# CWE 实验目录自动创建脚本
# ===============================

BASE_DIR="templates"

CWE_LIST=(
    cwe-022
    cwe-078
    cwe-079
    cwe-089
    cwe-090
    cwe-327
    cwe-328
    cwe-330
    cwe-501
    cwe-614
    cwe-643
)

echo "开始创建实验目录结构..."

for cwe in "${CWE_LIST[@]}"; do
    mkdir -p "$BASE_DIR/$cwe/eval"
    mkdir -p "$BASE_DIR/$cwe/logs"
    mkdir -p "$BASE_DIR/$cwe/results/codeql"
    mkdir -p "$BASE_DIR/$cwe/results/codefuse-query"

    echo "已创建: $cwe"
done

echo "全部实验目录创建完成！"

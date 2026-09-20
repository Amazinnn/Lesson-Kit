# Tasks

## 1. Spec

- [x] 1.1 proposal + specs delta（ADDED Environment self-check，三场景）strict 通过

## 2. 实现

- [x] 2.1 新增 `workbench/cli/doctor.py`：注册表 / 各工作区池库 / provider 可执行文件 / 守护进程与端口 / goals 与 plan 文件，全只读
- [x] 2.2 `workbench/cli/main.py`：`cmd_doctor` 接线（全过退 0，否则逐项列出退 2）

## 3. 测试

- [x] 3.1 健康夹具全过且零写入（registry 前后一致）
- [x] 3.2 缺失池库 → FAIL 逐项列出、退 2、什么都不修
- [x] 3.3 provider 可执行文件缺失 → FAIL 列出名字与路径
- [x] 3.4 记录的 pid 已死 → 报 "not running"（算通过，不算故障）

## 4. 验证与交付

- [x] 4.1 全量基线：pytest / node --test / compileall / openspec specs strict / guard
- [x] 4.2 真机 doctor：真实环境全绿 exit 0
- [x] 4.3 文档：README / PRODUCT-MANUAL / ACTION-GRAPH L2（19→20 命令）
- [x] 4.4 归档 change

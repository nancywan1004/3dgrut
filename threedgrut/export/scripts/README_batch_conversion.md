# 批量PLY到USDZ转换工具

这个工具可以批量转换一个文件夹中的所有PLY文件（包括递归所有子文件夹）到USDZ格式，并保持原有的目录结构。

## 功能特性

- **递归搜索**: 自动搜索输入目录及其所有子目录中的PLY文件
- **保持目录结构**: 输出目录会保持与输入目录相同的文件夹层级结构
- **并行处理**: 支持多线程并行转换以提高效率
- **Isaac Sim兼容**: 默认使用0阶球谐函数，确保与Isaac Sim 5.0兼容
- **详细日志**: 提供详细的转换进度和结果信息
- **干运行模式**: 可以预览将要转换的文件而不实际执行转换

## 使用方法

### 基本用法

```bash
# 转换input_folder中的所有PLY文件到output_folder
python -m threedgrut.export.scripts.batch_ply_to_usdz input_folder output_folder
```

### 高级用法

```bash
# 使用4个并行工作线程
python -m threedgrut.export.scripts.batch_ply_to_usdz input_folder output_folder --workers 4

# 强制使用0阶球谐函数（Isaac Sim兼容，默认已启用）
python -m threedgrut.export.scripts.batch_ply_to_usdz input_folder output_folder --force_zero_order_sh

# 干运行模式 - 只显示将要转换的文件，不实际转换
python -m threedgrut.export.scripts.batch_ply_to_usdz input_folder output_folder --dry_run

# 组合使用多个选项
python -m threedgrut.export.scripts.batch_ply_to_usdz input_folder output_folder --workers 8 --force_zero_order_sh --dry_run
```

## 参数说明

- `input_dir`: 输入目录，包含PLY文件（会递归搜索所有子目录）
- `output_dir`: 输出目录，USDZ文件将保存在这里（会保持原有目录结构）
- `--workers`: 并行工作线程数量（默认：1）
- `--force_zero_order_sh`: 强制使用0阶球谐函数，确保Isaac Sim 5.0兼容性（默认：True）
- `--dry_run`: 干运行模式，只显示计划转换的文件而不实际执行

## 目录结构示例

假设您有以下输入目录结构：

```
input_folder/
├── model1.ply
├── subfolder1/
│   ├── model2.ply
│   └── model3.ply
└── subfolder2/
    └── deep/
        └── model4.ply
```

运行转换后，输出目录将是：

```
output_folder/
├── model1.usdz
├── subfolder1/
│   ├── model2.usdz
│   └── model3.usdz
└── subfolder2/
    └── deep/
        └── model4.usdz
```

## 性能建议

1. **并行处理**: 对于大量文件，建议使用多个工作线程：
   ```bash
   python -m threedgrut.export.scripts.batch_ply_to_usdz input_folder output_folder --workers 4
   ```

2. **内存考虑**: 每个工作线程会加载一个模型实例，请根据系统内存调整工作线程数量

3. **存储空间**: USDZ文件通常比PLY文件大，请确保输出目录有足够的存储空间

## 错误处理

- 如果某个PLY文件转换失败，工具会继续处理其他文件
- 所有错误都会记录在日志中
- 转换完成后会显示成功和失败的统计信息

## 日志输出示例

```
2025-01-XX XX:XX:XX - batch_ply_to_usdz - INFO - Found 4 PLY files in input_folder
2025-01-XX XX:XX:XX - batch_ply_to_usdz - INFO - Planning to convert 4 files
2025-01-XX XX:XX:XX - batch_ply_to_usdz - INFO - Input directory: input_folder
2025-01-XX XX:XX:XX - batch_ply_to_usdz - INFO - Output directory: output_folder
2025-01-XX XX:XX:XX - batch_ply_to_usdz - INFO - Workers: 4
2025-01-XX XX:XX:XX - batch_ply_to_usdz - INFO - Force zero-order SH: True
2025-01-XX XX:XX:XX - batch_ply_to_usdz - INFO - [1/4] Processing model1.ply
2025-01-XX XX:XX:XX - batch_ply_to_usdz - INFO - ✅ model1.ply -> model1.usdz
...
============================================================
CONVERSION SUMMARY
============================================================
Total files: 4
Successful: 4
Failed: 0
🎉 All conversions completed successfully!
```

## 故障排除

1. **找不到PLY文件**: 确保输入目录路径正确，且包含.ply文件
2. **权限错误**: 确保对输入目录有读权限，对输出目录有写权限
3. **内存不足**: 减少工作线程数量或处理较小的文件批次
4. **转换失败**: 检查PLY文件格式是否正确，查看详细错误日志

## 与单文件转换工具的关系

这个批量转换工具基于现有的单文件转换工具 `ply_to_usd.py`，使用相同的转换逻辑和配置，只是增加了批量处理和目录结构保持功能。

# 批量PLY到USDZ转换 - 快速开始指南

这个工具可以批量转换一个文件夹中的所有PLY文件（包括递归所有子文件夹）到USDZ格式，并保持原有的目录结构。

## 🚀 快速开始

### 1. 基本用法

```bash
# 转换input_folder中的所有PLY文件到output_folder
python -m threedgrut.export.scripts.batch_ply_to_usdz input_folder output_folder
```

### 2. 预览模式（推荐先运行）

```bash
# 查看将要转换的文件，不实际执行转换
python -m threedgrut.export.scripts.batch_ply_to_usdz input_folder output_folder --dry_run
```

### 3. 高性能转换

```bash
# 使用4个并行线程加速转换
python -m threedgrut.export.scripts.batch_ply_to_usdz input_folder output_folder --workers 4
```

## 📁 目录结构示例

**输入目录结构：**
```
my_models/
├── car.ply
├── buildings/
│   ├── house.ply
│   └── office.ply
└── nature/
    └── trees/
        └── oak.ply
```

**输出目录结构：**
```
converted_models/
├── car.usdz
├── buildings/
│   ├── house.usdz
│   └── office.usdz
└── nature/
    └── trees/
        └── oak.usdz
```

## ⚡ 常用命令组合

```bash
# 1. 先预览要转换的文件
python -m threedgrut.export.scripts.batch_ply_to_usdz my_ply_files output_usdz --dry_run

# 2. 确认无误后执行转换（使用多线程）
python -m threedgrut.export.scripts.batch_ply_to_usdz my_ply_files output_usdz --workers 4

# 3. 如果需要Isaac Sim兼容性（默认已启用）
python -m threedgrut.export.scripts.batch_ply_to_usdz my_ply_files output_usdz --force_zero_order_sh
```

## 🔧 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `input_dir` | 输入目录（必需） | - |
| `output_dir` | 输出目录（必需） | - |
| `--workers` | 并行线程数 | 1 |
| `--force_zero_order_sh` | Isaac Sim兼容模式 | True |
| `--dry_run` | 预览模式 | False |

## 📊 性能建议

- **小批量（<10个文件）**: 使用默认单线程
- **中等批量（10-50个文件）**: 使用 `--workers 2` 或 `--workers 4`
- **大批量（>50个文件）**: 使用 `--workers 4` 到 `--workers 8`

## ⚠️ 注意事项

1. **内存使用**: 每个工作线程会占用一定内存，根据系统配置调整线程数
2. **存储空间**: USDZ文件通常比PLY文件大，确保有足够存储空间
3. **文件格式**: 只处理.ply文件，其他文件会被忽略
4. **Isaac Sim兼容**: 默认启用0阶球谐函数，确保与Isaac Sim 5.0兼容

## 🐛 故障排除

### 常见问题

**问题**: "找不到PLY文件"
```bash
# 解决: 检查输入目录路径是否正确
ls input_folder/*.ply
```

**问题**: "权限错误"
```bash
# 解决: 确保有读写权限
chmod -R 755 input_folder
mkdir -p output_folder
```

**问题**: "内存不足"
```bash
# 解决: 减少工作线程数
python -m threedgrut.export.scripts.batch_ply_to_usdz input_folder output_folder --workers 1
```

## 📝 测试工具

我们提供了测试脚本来验证工具是否正常工作：

```bash
# 运行测试脚本
python test_batch_conversion.py

# 查看使用示例
python example_batch_usage.py
```

## 📚 更多信息

- 详细文档: `threedgrut/export/scripts/README_batch_conversion.md`
- 单文件转换: `threedgrut/export/scripts/ply_to_usd.py`
- Isaac Sim兼容性: `ISAAC_SIM_COMPATIBILITY.md`

## 🎯 实际使用示例

```bash
# 示例1: 转换游戏资产
python -m threedgrut.export.scripts.batch_ply_to_usdz \
    ./game_assets/models \
    ./game_assets/usdz_models \
    --workers 4

# 示例2: 转换建筑模型
python -m threedgrut.export.scripts.batch_ply_to_usdz \
    /path/to/building_scans \
    /path/to/isaac_sim_assets \
    --workers 2 \
    --force_zero_order_sh

# 示例3: 预览大批量转换
python -m threedgrut.export.scripts.batch_ply_to_usdz \
    ./large_dataset \
    ./converted_dataset \
    --dry_run
```

---

🎉 **开始使用吧！** 如果遇到问题，请查看详细文档或运行测试脚本。

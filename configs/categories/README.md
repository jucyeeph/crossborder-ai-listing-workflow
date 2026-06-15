# Shopee菲律宾站点分类ID数据字典

## 概述
这份数据集包含了Shopee菲律宾站点(Shopee PH)最新的完整商品分类指南数据。该数据专为电商自动工作流运营（如BigSeller ERP集成）而准备，可用于自动化上架、分类映射和数据分析。

## 数据内容
- **总记录数**: 1,339条分类数据
- **数据层级**: 支持最高5级分类（Category -> Sub-category -> 3rd Level -> 4th Level -> 5th Level）
- **唯一标识**: 每条记录包含官方Category ID

## 文件说明
提供两种格式的数据文件，满足不同使用场景：

1. `shopee_ph_categories.csv`
   - **格式**: 标准CSV（逗号分隔），UTF-8编码
   - **用途**: 适合直接导入Excel查看，或作为ERP系统（如BigSeller）的批量映射表
   - **字段**: Category, Sub-category, 3rd Level Category, 4th Level Category, 5th Level Category, Category ID

2. `shopee_categories.json`
   - **格式**: JSON数组，结构化键值对
   - **用途**: 适合开发自动工作流Skill时，直接在代码中作为配置字典加载
   - **字段**: `category`, `sub_category`, `level_3`, `level_4`, `level_5`, `category_id`

## BigSeller集成建议
在使用这些数据进行BigSeller自动工作流开发时，建议：
1. 构建分类映射字典：将您的源数据分类名称映射到此数据集中的`category_id`。
2. 自动化刊登：在使用BigSeller API或自动化脚本刊登产品时，直接使用提取出的`category_id`作为目标分类。

## 数据来源
- **来源页面**: [Shopee PH Product Category Guide](https://seller.shopee.ph/edu/category-guide/)
- **采集时间**: 2026年6月15日
- **覆盖范围**: 1-84页全部可见分类数据

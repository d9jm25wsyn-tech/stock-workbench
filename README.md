# 2026丙午年上证指数行情预测工作台

基于干支命理模型的上证指数行情预测工作台，通过 GitHub Actions 每日自动更新。

## 功能特点

- **三层数据结构**
  - 第一层：1966丙午年道琼斯指数历史参照涨跌
  - 第二层：2026丙午年每月走势预测 + 实际月度涨跌幅对照
  - 第三层：每日明细数据（实际行情 + 未来预测）

- **每日自动更新**：GitHub Actions 每个交易日收盘后（北京时间16:30）自动获取最新上证指数数据，重新生成工作台

- **交互功能**：行情走势图、预测走势与实际涨跌对照、每日数据搜索/筛选/排序、上涨概率标注

## 自动更新机制

- **触发时间**：周一至周五 北京时间 16:30（收盘后）
- **数据来源**：akshare（东方财富/新浪财经接口）
- **更新内容**：获取最新上证指数日线数据 → 计算干支 → 匹配命理预测 → 生成 index.html
- **部署方式**：更新后的 index.html 自动提交到仓库，通过 GitHub Pages 访问

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行更新脚本
python3 update_workbench.py

# 打开生成的工作台
open index.html
```

## 文件结构

```
├── .github/workflows/
│   └── daily_update.yml    # GitHub Actions 自动更新配置
├── update_workbench.py      # 核心更新脚本
├── gz_predict.py            # 60甲子命理预测表
├── template.html            # HTML模板（数据占位符）
├── requirements.txt         # Python依赖
├── index.html               # 生成的工作台（自动更新）
└── README.md                # 说明文档
```

## 免责声明

本工作台基于干支命理模型进行行情预测，数据仅供参考和学习研究，不构成任何投资建议。股市有风险，投资需谨慎。

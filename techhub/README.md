# TechHub 研发协同管理平台

## 项目简介
TechHub 是一个基于 Flask + Vue.js 的研发团队任务协同系统，支持任务分配、进度跟踪、审批流转与数据分析。

## 团队分工
- **陈思言**：数据基座与权限管理
- **于然**：人力资源管理（项目管理模块）
- **程思同**：客户关系管理（数据中心模块）
- **郝益墨**：财务与行政管理（工作台、审批中心模块）

## 技术栈
- **后端**：Python Flask + SQLAlchemy + JWT
- **前端**：Vue.js 3 + Element Plus + ECharts
- **数据库**：SQLite（开发）/ MySQL（生产）

## 项目结构
```
techhub/
├── backend/          # Flask 后端
│   ├── app/         # 应用代码
│   ├── migrations/  # 数据库迁移
│   └── requirements.txt
├── frontend/        # Vue.js 前端
│   ├── src/        # 源代码
│   └── package.json
└── docs/           # 文档
```

## 快速开始

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd techhub
```

### 2. 启动后端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### 3. 启动前端
```bash
cd frontend
npm install
npm run dev
```

## 功能模块
- 个人协同工作台
- 项目与任务管理（看板视图）
- 审批中心
- 数据大屏

## 许可证
MIT

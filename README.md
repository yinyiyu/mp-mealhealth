# 大学生心理健康测评系统

基于 **Python Flask + 微信小程序 + Vue.js** 构建的完整心理健康测评系统。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      大学生心理健康测评系统                         │
├──────────────┬────────────────────────┬─────────────────────────┤
│  微信小程序    │      Vue.js管理后台      │    Python Flask后端       │
│  (学生端)     │   (管理员/老师使用)      │   (RESTful API)           │
│              │                        │                           │
│  ・登录       │  ・数据看板              │  ・JWT认证授权             │
│  ・测评列表   │  ・问卷管理              │  ・问卷模板管理            │
│  ・答题       │  ・测评发布              │  ・测评任务管理            │
│  ・查看报告   │  ・数据统计              │  ・答题提交与计分          │
│  ・个人信息   │  ・学生管理              │  ・报告自动生成            │
│              │  ・重点跟进              │  ・统计数据接口            │
└──────────────┴────────────────────────┴─────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │       MySQL数据库      │
                    │   (核心数据持久化)     │
                    └───────────────────────┘
```

---

## 目录结构

```
mp-mealhealth/
├── backend/                    # Python Flask 后端
│   ├── app/
│   │   ├── __init__.py        # 应用工厂函数
│   │   ├── models.py          # 数据库模型（ORM）
│   │   ├── utils.py           # 工具函数（权限装饰器）
│   │   ├── auth/              # 认证模块（登录/微信登录）
│   │   ├── questionnaire/     # 问卷模板管理
│   │   ├── assessment/        # 测评任务与答题
│   │   ├── report/            # 报告生成与查询
│   │   ├── student/           # 学生信息管理
│   │   ├── followup/          # 重点学生跟进
│   │   └── statistics/        # 数据统计
│   ├── config.py              # 应用配置
│   ├── run.py                 # 启动入口
│   └── requirements.txt       # Python依赖
│
├── miniprogram/                # 微信小程序（学生端）
│   ├── app.js                 # 全局逻辑（HTTP封装）
│   ├── app.json               # 全局配置（页面路由、TabBar）
│   ├── app.wxss               # 全局样式
│   └── pages/
│       ├── login/             # 登录页
│       ├── assessment/        # 测评列表页
│       ├── answer/            # 答题页（核心）
│       ├── report/            # 报告查询页
│       └── profile/           # 个人信息页
│
└── admin/                      # Vue.js 管理后台
    ├── src/
    │   ├── main.js            # Vue应用入口
    │   ├── App.vue            # 根组件
    │   ├── api/               # API接口定义（Axios封装）
    │   ├── router/            # 路由配置（含权限守卫）
    │   ├── store/             # Vuex状态管理
    │   └── views/
    │       ├── Login.vue      # 登录页
    │       ├── Layout.vue     # 主布局（侧边栏+顶栏）
    │       ├── Dashboard.vue  # 数据看板（ECharts图表）
    │       ├── questionnaire/ # 问卷管理模块
    │       ├── assessment/    # 测评管理模块
    │       ├── statistics/    # 数据统计模块
    │       ├── student/       # 学生管理模块
    │       └── followup/      # 重点跟进模块
    ├── package.json
    └── vue.config.js
```

---

## 数据库设计（MySQL）

### 核心数据表

| 表名 | 说明 |
|------|------|
| `users` | 用户表（学生/老师/管理员，角色区分） |
| `questionnaire_templates` | 问卷模板表（含计分规则、维度定义） |
| `questions` | 题目表（单选/多选，含选项和分值） |
| `assessments` | 测评任务表（管理员发布的测评） |
| `answer_submissions` | 答题提交记录（含答案数据JSON） |
| `assessment_reports` | 测评报告表（得分、风险等级、解读） |
| `follow_ups` | 跟进记录表（高风险学生跟进状态） |

### 关键字段说明

**users表 - role字段：**
- `student`：学生（可参加测评、查看自己报告）
- `teacher`：心理老师（可查看学生报告、管理跟进）
- `admin`：管理员（问卷/测评管理、学生管理）
- `super_admin`：超级管理员（所有权限）

**assessment_reports表 - risk_level字段：**
- `normal`：正常
- `low_risk`：低风险
- `medium_risk`：中风险（建议咨询）
- `high_risk`：高风险（自动标记+创建跟进记录）

---

## 快速开始

### 1. 启动后端（Flask）

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置数据库（修改 config.py 中的 DATABASE_URL）
# 默认：mysql+pymysql://root:password@localhost:3306/mental_health_db

# 初始化数据库（创建表 + 创建超级管理员账号）
export FLASK_APP=run.py
flask init-db

# 启动开发服务器
python run.py
# 服务启动在 http://localhost:5000
```

**默认管理员账号：** `admin` / `Admin@123`

### 2. 启动管理后台（Vue.js）

```bash
cd admin

# 安装依赖
npm install

# 启动开发服务器（已配置代理到 Flask http://localhost:5000）
npm run serve
# 访问 http://localhost:8080
```

### 3. 微信小程序

1. 使用微信开发者工具打开 `miniprogram/` 目录
2. 修改 `app.js` 中的 `baseUrl` 为Flask服务器地址
3. 修改 `backend/app/auth/routes.py` 中的 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`
4. 编译并在模拟器中预览

---

## API接口规范

### 请求格式
- **Header：** `Authorization: Bearer <JWT Token>`
- **Content-Type：** `application/json`

### 响应格式（统一）
```json
{
  "code": 200,
  "message": "操作成功",
  "data": { ... }
}
```

### 主要接口列表

| 模块 | 接口 | 说明 |
|------|------|------|
| 认证 | `POST /api/auth/login` | 账号密码登录 |
| 认证 | `POST /api/auth/wechat-login` | 微信小程序登录 |
| 问卷 | `GET /api/questionnaire/` | 获取问卷列表 |
| 问卷 | `POST /api/questionnaire/` | 创建问卷（管理员） |
| 问卷 | `PUT /api/questionnaire/{id}/status` | 上架/下架问卷 |
| 测评 | `GET /api/assessment/` | 获取测评列表 |
| 测评 | `POST /api/assessment/` | 发布测评（管理员） |
| 测评 | `POST /api/assessment/{id}/start` | 学生开始答题 |
| 测评 | `POST /api/assessment/submissions/{id}/submit` | 提交答题 |
| 报告 | `GET /api/report/my` | 我的历史报告 |
| 报告 | `GET /api/report/{id}` | 报告详情 |
| 报告 | `GET /api/report/high-risk` | 高风险学生列表 |
| 学生 | `GET /api/student/` | 学生列表 |
| 学生 | `POST /api/student/` | 新增学生 |
| 跟进 | `GET /api/followup/` | 跟进记录列表 |
| 跟进 | `PUT /api/followup/{id}` | 更新跟进状态 |
| 统计 | `GET /api/statistics/overview` | 系统概览数据 |
| 统计 | `GET /api/statistics/assessment/{id}` | 测评统计数据 |

---

## 核心功能说明

### 计分逻辑（backend/app/report/service.py）

```
1. 遍历所有题目
2. 单选题：学生选择的选项对应分值直接相加
3. 多选题：所有选中选项分值相加
4. 按维度汇总（维度定义在问卷模板的 dimensions 字段）
5. 根据 scoring_rules 中的分段规则判定风险等级
```

### 风险等级判定

```python
# 计分规则示例（PHQ-9抑郁量表）
scoring_rules = {
    "总分": {
        "正常": "0-4",
        "轻度": "5-9",
        "中度": "10-19",
        "重度": "20+"
    }
}
# 正常/低 -> normal
# 轻度    -> low_risk
# 中度    -> medium_risk
# 重度/高 -> high_risk
```

### 高风险自动处理

当学生测评结果为 `high_risk` 时，系统自动：
1. 将报告 `is_flagged` 设为 `True`
2. 在 `follow_ups` 表中创建跟进记录（状态：`pending`）
3. 管理员/老师在后台可看到待跟进列表

---

## 角色权限矩阵

| 功能 | 学生 | 心理老师 | 管理员 | 超级管理员 |
|------|:----:|:-------:|:------:|:---------:|
| 参加测评/查看本人报告 | ✅ | - | - | ✅ |
| 查看所有学生报告 | ❌ | ✅ | ✅ | ✅ |
| 跟进状态管理 | ❌ | ✅(限自己) | ✅ | ✅ |
| 问卷模板管理 | ❌ | ❌ | ✅ | ✅ |
| 发布/管理测评 | ❌ | ❌ | ✅ | ✅ |
| 学生增删改查 | ❌ | 查 | ✅ | ✅ |
| 删除学生/问卷 | ❌ | ❌ | ❌ | ✅ |

---

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端框架 | Python 3.9+ / Flask 2.3 |
| 数据库 ORM | Flask-SQLAlchemy |
| 认证 | Flask-JWT-Extended（JWT Token） |
| 跨域 | Flask-CORS |
| 数据库 | MySQL 8.0（推荐） |
| 前端框架 | Vue.js 2.7 + Element UI 2.15 |
| 状态管理 | Vuex 3 |
| 路由 | Vue Router 3 |
| HTTP客户端 | Axios |
| 图表 | ECharts 5 |
| 小程序 | 微信小程序（原生开发） |

20260206_dpl_auto/
├── src/             # 核心逻辑：存放主要的自动化脚本、业务逻辑封装
├── configs/         # 配置中心：存放环境参数、设备 IP、账号等配置文件 (yaml, json)
├── data/            # 数据素材：存放测试所需的输入数据、图片、固件等
├── reports/         # 测试报告：存放自动化运行后生成的 HTML 或 XML 报告
├── logs/            # 运行日志：存放程序运行过程中的打印日志
├── docs/            # 项目文档：存放 README、设计说明、流程图
├── .gitignore       # Git 配置：指定不需进入版本控制的文件（如 logs/）
└── requirements.txt # 依赖管理：列出项目所需的 Python 第三方库
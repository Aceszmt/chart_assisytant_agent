# 
backend/
├── app.py              # FastAPI主应用
├── agents/
│   ├── __init__.py
│   ├── chart_agent.py  # LangChain Agent
│   └── tools.py        # 自定义工具
├── mcp/
│   ├── __init__.py
│   └── mcp_server.py   # MCP Server实现
├── utils/
│   ├── __init__.py
│   ├── data_processor.py  # 数据处理
│   └── chart_generator.py  # 图表生成
└── requirements.txt

frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.js
│   │   ├── ChartDisplay.js
│   │   ├── FileUpload.js
│   │   └── MessageList.js
│   ├── services/
│   │   └── api.js
│   ├── App.js
│   ├── App.css
│   └── index.js
├── package.json
└── public/
    └── index.html

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import os
import sys
import shutil
from dotenv import load_dotenv
import json

# 确保可以导入本地模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.chart_agent import ChartAgent

# ... 其余代码

load_dotenv()

app = FastAPI(title="智能图表助手API")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 初始化Agent
agent = ChartAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))

# 存储WebSocket连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传Excel文件"""
    try:
        # 保存文件
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 自动加载文件
        result = agent.process_message(f"请加载Excel文件：{file_path}")
        
        return JSONResponse(content={
            "success": True,
            "message": f"文件 {file.filename} 上传成功",
            "file_path": file_path,
            "load_result": result
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": f"文件上传失败: {str(e)}"
        }, status_code=500)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接处理"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # 处理消息
            result = agent.process_message(message_data["message"])
            
            # 发送响应
            await manager.send_message(json.dumps({
                "type": "response",
                "data": result
            }), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "智能图表助手正在运行"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
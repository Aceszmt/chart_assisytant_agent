import asyncio
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import websockets
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToolType(Enum):
    """工具类型枚举"""
    LOAD_EXCEL = "load_excel"
    GET_DATA_INFO = "get_data_info"
    GENERATE_CHART = "generate_chart"
    FILTER_DATA = "filter_data"
    AGGREGATE_DATA = "aggregate_data"

@dataclass
class Tool:
    """工具定义"""
    name: str
    type: ToolType
    description: str
    parameters: Dict[str, Any]
    required_params: List[str]

@dataclass
class ToolCall:
    """工具调用请求"""
    id: str
    tool: str
    arguments: Dict[str, Any]

@dataclass
class ToolResult:
    """工具调用结果"""
    call_id: str
    result: Any
    error: Optional[str] = None

class MCPServer:
    """Model Context Protocol Server实现"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.tools = self._initialize_tools()
        self.connections = set()
        self.context = {}  # 存储上下文信息
        
    def _initialize_tools(self) -> Dict[str, Tool]:
        """初始化可用工具"""
        return {
            "load_excel": Tool(
                name="load_excel",
                type=ToolType.LOAD_EXCEL,
                description="加载Excel文件进行数据分析",
                parameters={
                    "file_path": {
                        "type": "string",
                        "description": "Excel文件的路径"
                    }
                },
                required_params=["file_path"]
            ),
            "get_data_info": Tool(
                name="get_data_info",
                type=ToolType.GET_DATA_INFO,
                description="获取已加载数据的详细信息",
                parameters={},
                required_params=[]
            ),
            "generate_chart": Tool(
                name="generate_chart",
                type=ToolType.GENERATE_CHART,
                description="生成数据图表",
                parameters={
                    "chart_type": {
                        "type": "string",
                        "enum": ["bar", "line", "scatter", "pie"],
                        "description": "图表类型"
                    },
                    "x_column": {
                        "type": "string",
                        "description": "X轴数据列"
                    },
                    "y_column": {
                        "type": "string",
                        "description": "Y轴数据列"
                    },
                    "title": {
                        "type": "string",
                        "description": "图表标题"
                    }
                },
                required_params=["chart_type"]
            ),
            "filter_data": Tool(
                name="filter_data",
                type=ToolType.FILTER_DATA,
                description="根据条件筛选数据",
                parameters={
                    "conditions": {
                        "type": "object",
                        "description": "筛选条件，格式为 {column: {operator: value}}"
                    }
                },
                required_params=["conditions"]
            ),
            "aggregate_data": Tool(
                name="aggregate_data",
                type=ToolType.AGGREGATE_DATA,
                description="对数据进行聚合分析",
                parameters={
                    "group_by": {
                        "type": "array",
                        "description": "分组字段"
                    },
                    "aggregations": {
                        "type": "object",
                        "description": "聚合操作，格式为 {column: operation}"
                    }
                },
                required_params=["aggregations"]
            )
        }
    
    async def handle_connection(self, websocket, path):
        """处理WebSocket连接"""
        self.connections.add(websocket)
        logger.info(f"新连接建立: {websocket.remote_address}")
        
        try:
            # 发送初始化消息
            await self.send_initialization(websocket)
            
            # 处理消息
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"连接关闭: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"连接错误: {e}")
        finally:
            self.connections.remove(websocket)
    
    async def send_initialization(self, websocket):
        """发送初始化信息"""
        init_message = {
            "type": "initialization",
            "protocol_version": "1.0",
            "capabilities": {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                        "required": tool.required_params
                    }
                    for tool in self.tools.values()
                ]
            },
            "context": self.context
        }
        await websocket.send(json.dumps(init_message))
    
    async def handle_message(self, websocket, message: str):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "tool_call":
                await self.handle_tool_call(websocket, data)
            elif message_type == "context_update":
                await self.handle_context_update(websocket, data)
            elif message_type == "query":
                await self.handle_query(websocket, data)
            else:
                await self.send_error(websocket, f"未知消息类型: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "无效的JSON格式")
        except Exception as e:
            await self.send_error(websocket, f"处理消息时出错: {str(e)}")
    
    async def handle_tool_call(self, websocket, data: Dict[str, Any]):
        """处理工具调用请求"""
        call_id = data.get("id")
        tool_name = data.get("tool")
        arguments = data.get("arguments", {})
        
        if tool_name not in self.tools:
            await self.send_tool_result(websocket, ToolResult(
                call_id=call_id,
                result=None,
                error=f"未知工具: {tool_name}"
            ))
            return
        
        tool = self.tools[tool_name]
        
        # 验证必需参数
        missing_params = [p for p in tool.required_params if p not in arguments]
        if missing_params:
            await self.send_tool_result(websocket, ToolResult(
                call_id=call_id,
                result=None,
                error=f"缺少必需参数: {', '.join(missing_params)}"
            ))
            return
        
        # 执行工具
        try:
            result = await self.execute_tool(tool_name, arguments)
            await self.send_tool_result(websocket, ToolResult(
                call_id=call_id,
                result=result,
                error=None
            ))
        except Exception as e:
            await self.send_tool_result(websocket, ToolResult(
                call_id=call_id,
                result=None,
                error=str(e)
            ))
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """执行具体的工具"""
        # 这里需要与实际的工具实现进行集成
        # 为了演示，我们返回模拟结果
        
        if tool_name == "load_excel":
            return {
                "success": True,
                "message": f"已加载文件: {arguments['file_path']}",
                "rows": 100,
                "columns": ["日期", "产品", "销售额", "数量"]
            }
        
        elif tool_name == "get_data_info":
            return {
                "columns": ["日期", "产品", "销售额", "数量"],
                "dtypes": {
                    "日期": "datetime",
                    "产品": "string",
                    "销售额": "float",
                    "数量": "int"
                },
                "shape": [100, 4],
                "null_counts": {"日期": 0, "产品": 0, "销售额": 2, "数量": 0}
            }
        
        elif tool_name == "generate_chart":
            chart_type = arguments.get("chart_type")
            return {
                "success": True,
                "chart_type": chart_type,
                "chart_id": f"chart_{datetime.now().timestamp()}",
                "message": f"已生成{chart_type}图表"
            }
        
        elif tool_name == "filter_data":
            return {
                "success": True,
                "filtered_rows": 45,
                "message": "数据筛选完成"
            }
        
        elif tool_name == "aggregate_data":
            return {
                "success": True,
                "result": {
                    "产品A": {"销售额": 10000, "数量": 100},
                    "产品B": {"销售额": 15000, "数量": 150}
                }
            }
        
        return {"error": "工具执行未实现"}
    
    async def handle_context_update(self, websocket, data: Dict[str, Any]):
        """处理上下文更新"""
        context_data = data.get("context", {})
        self.context.update(context_data)
        
        # 通知所有连接上下文已更新
        update_message = {
            "type": "context_updated",
            "context": self.context,
            "timestamp": datetime.now().isoformat()
        }
        
        await asyncio.gather(
            *[conn.send(json.dumps(update_message)) for conn in self.connections]
        )
    
    async def handle_query(self, websocket, data: Dict[str, Any]):
        """处理查询请求"""
        query_type = data.get("query_type")
        
        if query_type == "available_tools":
            response = {
                "type": "query_response",
                "query_type": query_type,
                "result": list(self.tools.keys())
            }
        elif query_type == "tool_info":
            tool_name = data.get("tool_name")
            if tool_name in self.tools:
                tool = self.tools[tool_name]
                response = {
                    "type": "query_response",
                    "query_type": query_type,
                    "result": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                        "required": tool.required_params
                    }
                }
            else:
                response = {
                    "type": "error",
                    "message": f"未找到工具: {tool_name}"
                }
        else:
            response = {
                "type": "error",
                "message": f"未知查询类型: {query_type}"
            }
        
        await websocket.send(json.dumps(response))
    
    async def send_tool_result(self, websocket, result: ToolResult):
        """发送工具执行结果"""
        message = {
            "type": "tool_result",
            "id": result.call_id,
            "result": result.result,
            "error": result.error,
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(message))
    
    async def send_error(self, websocket, error_message: str):
        """发送错误消息"""
        message = {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(message))
    
    def start(self):
        """启动MCP服务器"""
        logger.info(f"MCP Server 启动在 {self.host}:{self.port}")
        start_server = websockets.serve(
            self.handle_connection, 
            self.host, 
            self.port
        )
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

# MCP客户端类，用于与MCP服务器通信
class MCPClient:
    """MCP客户端实现"""
    
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.tools = {}
        self.pending_calls = {}
        
    async def connect(self):
        """连接到MCP服务器"""
        self.websocket = await websockets.connect(self.server_url)
        
        # 接收初始化消息
        init_message = await self.websocket.recv()
        init_data = json.loads(init_message)
        
        if init_data["type"] == "initialization":
            self.tools = {
                tool["name"]: tool 
                for tool in init_data["capabilities"]["tools"]
            }
            logger.info("MCP客户端连接成功")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具"""
        if not self.websocket:
            raise Exception("未连接到MCP服务器")
        
        call_id = f"call_{datetime.now().timestamp()}"
        
        # 发送工具调用请求
        message = {
            "type": "tool_call",
            "id": call_id,
            "tool": tool_name,
            "arguments": arguments
        }
        
        await self.websocket.send(json.dumps(message))
        
        # 等待结果
        while True:
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data["type"] == "tool_result" and data["id"] == call_id:
                if data["error"]:
                    raise Exception(data["error"])
                return data["result"]
    
    async def update_context(self, context: Dict[str, Any]):
        """更新上下文"""
        if not self.websocket:
            raise Exception("未连接到MCP服务器")
        
        message = {
            "type": "context_update",
            "context": context
        }
        
        await self.websocket.send(json.dumps(message))
    
    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()

# 启动脚本
if __name__ == "__main__":
    server = MCPServer()
    server.start()
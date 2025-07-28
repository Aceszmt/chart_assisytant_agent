from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain.tools import BaseTool
from typing import List, Dict, Any, Type, Optional
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatTongyi
import os
import sys
import asyncio
import json

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 现在可以导入mcp模块
from mcp.mcp_server import MCPClient

# ... 其余代码

# MCP工具包装器
class MCPTool(BaseTool):
    """将MCP工具包装成LangChain工具"""

    name: str = ""
    description: str = ""

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, mcp_client: MCPClient, tool_info: Dict[str, Any], **kwargs):
        # 提取名称和描述
        name = tool_info["name"]
        description = tool_info["description"]

        # 初始化父类
        super().__init__(name=name, description=description, **kwargs)

        # 保存客户端和工具信息
        self.mcp_client = mcp_client
        self.tool_info = tool_info

        # 动态创建参数模型
        self._create_args_schema()

    def _create_args_schema(self):
        """动态创建参数schema"""
        class_name = f"{self.name.title().replace('_', '')}Input"
        fields = {}

        for param_name, param_info in self.tool_info.get("parameters", {}).items():
            # 根据类型信息确定字段类型
            param_type = param_info.get("type", "string")
            if param_type == "string":
                field_type = str
            elif param_type == "integer":
                field_type = int
            elif param_type == "number":
                field_type = float
            elif param_type == "boolean":
                field_type = bool
            elif param_type == "array":
                field_type = List[Any]
            elif param_type == "object":
                field_type = Dict[str, Any]
            else:
                field_type = Any

            is_required = param_name in self.tool_info.get("required", [])

            if is_required:
                fields[param_name] = (field_type, Field(description=param_info.get("description", "")))
            else:
                fields[param_name] = (
                Optional[field_type], Field(default=None, description=param_info.get("description", "")))

        # 只有在有参数时才创建schema
        if fields:
            self.args_schema = type(class_name, (BaseModel,), fields)

    def _run(self, **kwargs) -> str:
        """同步运行工具"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self._arun(**kwargs))
        loop.close()
        return result

    async def _arun(self, **kwargs) -> str:
        """异步运行工具"""
        try:
            result = await self.mcp_client.call_tool(self.name, kwargs)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return f"工具调用失败: {str(e)}"


class ChartAgent:
    def __init__(self, openai_api_key: str, mcp_server_url: str = "ws://localhost:8765"):
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-4",
            openai_api_key=openai_api_key
        )

        self.mcp_client = MCPClient(mcp_server_url)
        self.tools: List[BaseTool] = []
        self.agent_executor: Optional[AgentExecutor] = None

        # 初始化MCP连接
        asyncio.run(self._initialize_mcp())

    async def _initialize_mcp(self):
        """初始化MCP连接并创建工具"""
        await self.mcp_client.connect()

        # 为每个MCP工具创建LangChain工具
        for tool_name, tool_info in self.mcp_client.tools.items():
            langchain_tool = MCPTool(self.mcp_client, tool_info)
            self.tools.append(langchain_tool)

        # 创建Agent
        self._create_agent()

    def _create_agent(self):
        """创建LangChain Agent"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的数据分析和图表生成助手。你的任务是：
1. 理解用户的自然语言指令
2. 使用提供的工具加载Excel文件并分析数据
3. 根据用户需求生成合适的图表（柱状图、折线图、散点图、饼图）
4. 提供清晰的解释和建议

在生成图表时，请根据数据特点选择合适的图表类型：
- 柱状图：适合比较不同类别的数值
- 折线图：适合展示数据随时间的变化趋势
- 散点图：适合展示两个变量之间的关系
- 饼图：适合展示各部分占总体的比例

请始终先了解数据的结构和内容，然后再生成图表。"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=5
        )

        agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            return_intermediate_steps=True
        )

    def process_message(self, message: str) -> Dict[str, Any]:
        """处理用户消息"""
        if not self.agent_executor:
            return {
                "success": False,
                "response": "Agent尚未初始化",
                "chart_data": None
            }

        try:
            result = self.agent_executor.invoke({"input": message})

            # 提取图表数据
            chart_data = None
            for step in result.get("intermediate_steps", []):
                if len(step) > 1:
                    try:
                        tool_result = json.loads(step[1])
                        if isinstance(tool_result, dict) and tool_result.get("chart_type"):
                            chart_data = tool_result
                            break
                    except:
                        pass

            return {
                "success": True,
                "response": result["output"],
                "chart_data": chart_data
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"处理消息时出错: {str(e)}",
                "chart_data": None
            }

    async def update_context(self, context: Dict[str, Any]):
        """更新MCP上下文"""
        await self.mcp_client.update_context(context)

    def close(self):
        """关闭连接"""
        asyncio.run(self.mcp_client.close())
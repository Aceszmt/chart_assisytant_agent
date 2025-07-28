


#!/usr/bin/env python
"""
MCP Server启动脚本
"""
import sys
import os

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from mcp.mcp_server import MCPServer

if __name__ == "__main__":
    print("启动MCP Server...")
    server = MCPServer(host="localhost", port=8765)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nMCP Server已停止")
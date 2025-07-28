from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
import os
import sys

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_processor import DataProcessor
from utils.chart_generator import ChartGenerator

# 全局实例
data_processor = DataProcessor()
chart_generator = ChartGenerator()

# ... 其余代码保持不变

class LoadExcelInput(BaseModel):
    file_path: str = Field(description="Excel文件路径")

class LoadExcelTool(BaseTool):
    name = "load_excel"
    description = "加载Excel文件到内存中进行分析"
    args_schema: Type[BaseModel] = LoadExcelInput
    
    def _run(self, file_path: str) -> str:
        result = data_processor.load_excel(file_path)
        return str(result)

class GetDataInfoTool(BaseTool):
    name = "get_data_info"
    description = "获取当前加载的数据的详细信息，包括列名、数据类型、统计信息等"
    
    def _run(self) -> str:
        result = data_processor.get_data_info()
        return str(result)

class GenerateChartInput(BaseModel):
    chart_type: str = Field(description="图表类型: bar, line, scatter, pie")
    x_column: Optional[str] = Field(description="X轴列名")
    y_column: Optional[str] = Field(description="Y轴列名")
    values_column: Optional[str] = Field(description="饼图的值列名")
    names_column: Optional[str] = Field(description="饼图的名称列名")
    title: Optional[str] = Field(description="图表标题")

class GenerateChartTool(BaseTool):
    name = "generate_chart"
    description = "根据指定的参数生成图表"
    args_schema: Type[BaseModel] = GenerateChartInput
    
    def _run(self, chart_type: str, x_column: Optional[str] = None,
             y_column: Optional[str] = None, values_column: Optional[str] = None,
             names_column: Optional[str] = None, title: Optional[str] = None) -> str:
        
        if data_processor.current_df is None:
            return "错误：请先加载Excel文件"
        
        df = data_processor.current_df
        
        if chart_type == "bar":
            result = chart_generator.generate_bar_chart(df, x_column, y_column, title)
        elif chart_type == "line":
            result = chart_generator.generate_line_chart(df, x_column, y_column, title)
        elif chart_type == "scatter":
            result = chart_generator.generate_scatter_plot(df, x_column, y_column, title)
        elif chart_type == "pie":
            result = chart_generator.generate_pie_chart(df, values_column, names_column, title)
        else:
            result = {"success": False, "message": f"不支持的图表类型: {chart_type}"}
        
        return str(result)
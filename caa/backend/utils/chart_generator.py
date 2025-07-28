import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, Optional
import base64
from io import BytesIO
import json

class ChartGenerator:
    def __init__(self):
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def generate_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                          title: Optional[str] = None) -> Dict[str, Any]:
        """生成柱状图"""
        try:
            fig = px.bar(df, x=x_col, y=y_col, title=title or f"{y_col} by {x_col}")
            
            return {
                "success": True,
                "chart_type": "bar",
                "chart_data": fig.to_json(),
                "message": "柱状图生成成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"生成柱状图失败: {str(e)}"
            }
    
    def generate_line_chart(self, df: pd.DataFrame, x_col: str, y_col: str,
                           title: Optional[str] = None) -> Dict[str, Any]:
        """生成折线图"""
        try:
            fig = px.line(df, x=x_col, y=y_col, title=title or f"{y_col} over {x_col}")
            
            return {
                "success": True,
                "chart_type": "line",
                "chart_data": fig.to_json(),
                "message": "折线图生成成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"生成折线图失败: {str(e)}"
            }
    
    def generate_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str,
                             title: Optional[str] = None, size_col: Optional[str] = None) -> Dict[str, Any]:
        """生成散点图"""
        try:
            fig = px.scatter(df, x=x_col, y=y_col, size=size_col,
                           title=title or f"{y_col} vs {x_col}")
            
            return {
                "success": True,
                "chart_type": "scatter",
                "chart_data": fig.to_json(),
                "message": "散点图生成成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"生成散点图失败: {str(e)}"
            }
    
    def generate_pie_chart(self, df: pd.DataFrame, values_col: str, names_col: str,
                          title: Optional[str] = None) -> Dict[str, Any]:
        """生成饼图"""
        try:
            fig = px.pie(df, values=values_col, names=names_col,
                        title=title or f"{values_col} Distribution")
            
            return {
                "success": True,
                "chart_type": "pie",
                "chart_data": fig.to_json(),
                "message": "饼图生成成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"生成饼图失败: {str(e)}"
            }
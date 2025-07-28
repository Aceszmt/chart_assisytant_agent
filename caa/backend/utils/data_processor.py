import pandas as pd
from typing import Optional, Dict, Any
import os

class DataProcessor:
    def __init__(self):
        self.current_df: Optional[pd.DataFrame] = None
        self.file_path: Optional[str] = None
    
    def load_excel(self, file_path: str) -> Dict[str, Any]:
        """加载Excel文件"""
        try:
            self.file_path = file_path
            self.current_df = pd.read_excel(file_path)
            
            return {
                "success": True,
                "message": f"成功加载文件: {os.path.basename(file_path)}",
                "shape": self.current_df.shape,
                "columns": list(self.current_df.columns),
                "preview": self.current_df.head().to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"加载文件失败: {str(e)}"
            }
    
    def get_data_info(self) -> Dict[str, Any]:
        """获取当前数据信息"""
        if self.current_df is None:
            return {"error": "没有加载数据"}
        
        return {
            "shape": self.current_df.shape,
            "columns": list(self.current_df.columns),
            "dtypes": self.current_df.dtypes.to_dict(),
            "null_counts": self.current_df.isnull().sum().to_dict(),
            "description": self.current_df.describe().to_dict()
        }
    
    def filter_data(self, conditions: Dict[str, Any]) -> pd.DataFrame:
        """根据条件筛选数据"""
        if self.current_df is None:
            raise ValueError("没有加载数据")
        
        filtered_df = self.current_df.copy()
        
        for column, condition in conditions.items():
            if column in filtered_df.columns:
                if isinstance(condition, dict):
                    if "min" in condition:
                        filtered_df = filtered_df[filtered_df[column] >= condition["min"]]
                    if "max" in condition:
                        filtered_df = filtered_df[filtered_df[column] <= condition["max"]]
                    if "equals" in condition:
                        filtered_df = filtered_df[filtered_df[column] == condition["equals"]]
                    if "in" in condition:
                        filtered_df = filtered_df[filtered_df[column].isin(condition["in"])]
        
        return filtered_df
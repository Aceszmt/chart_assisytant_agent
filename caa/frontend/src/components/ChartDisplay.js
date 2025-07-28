import React from 'react';
import Plot from 'react-plotly.js';
import { Card } from 'antd';

const ChartDisplay = ({ chartData }) => {
  if (!chartData || !chartData.chart_data) {
    return null;
  }

  try {
    const plotData = JSON.parse(chartData.chart_data);
    
    return (
      <Card title="生成的图表" className="chart-card">
        <Plot
          data={plotData.data}
          layout={{
            ...plotData.layout,
            autosize: true,
            width: undefined,
            height: 400
          }}
          config={{ responsive: true }}
          style={{ width: '100%' }}
        />
      </Card>
    );
  } catch (error) {
    console.error('解析图表数据失败:', error);
    return null;
  }
};

export default ChartDisplay;
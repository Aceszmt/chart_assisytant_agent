import React, { useState, useEffect, useRef } from 'react';
import { Layout, Card, Space, Typography, Divider } from 'antd';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';
import MessageList from './components/MessageList';
import ChartDisplay from './components/ChartDisplay';
import apiService from './services/api';
import './App.css';

const { Header, Content } = Layout;
const { Title } = Typography;

function App() {
  const [messages, setMessages] = useState([]);
  const [currentChart, setCurrentChart] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // 建立WebSocket连接
    apiService.connectWebSocket((data) => {
      if (data.type === 'response') {
        const response = data.data;
        
        // 添加助手消息
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'assistant',
          text: response.response,
          timestamp: new Date()
        }]);

        // 如果有图表数据，更新图表
        if (response.chart_data) {
          setCurrentChart(response.chart_data);
        }
      }
    });

    return () => {
      apiService.disconnect();
    };
  }, []);

  const handleUploadSuccess = (result) => {
    setUploadedFile(result.file_path);
    setMessages(prev => [...prev, {
      id: Date.now(),
      sender: 'assistant',
      text: `文件上传成功！我已经加载了文件，其中包含 ${result.load_result?.response || '数据'}。你可以让我生成各种图表了。`,
      timestamp: new Date()
    }]);
  };

  const handleSendMessage = (message) => {
    // 添加用户消息
    setMessages(prev => [...prev, {
      id: Date.now(),
      sender: 'user',
      text: message,
      timestamp: new Date()
    }]);

    // 发送到后端
    apiService.sendMessage(message);
  };

  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <Title level={2} style={{ color: 'white', margin: 0 }}>
          智能图表助手
        </Title>
      </Header>
      <Content className="app-content">
        <div className="content-wrapper">
          <Card className="upload-section">
            <Space>
              <FileUpload onUploadSuccess={handleUploadSuccess} />
              {uploadedFile && (
                <span>当前文件: {uploadedFile.split('/').pop()}</span>
              )}
            </Space>
          </Card>

          <div className="main-section">
            <Card className="chat-section">
              <div className="messages-container">
                <MessageList messages={messages} />
                <div ref={messagesEndRef} />
              </div>
              <Divider />
              <ChatInterface onSendMessage={handleSendMessage} />
            </Card>

            {currentChart && (
              <div className="chart-section">
                <ChartDisplay chartData={currentChart} />
              </div>
            )}
          </div>
        </div>
      </Content>
    </Layout>
  );
}

export default App;
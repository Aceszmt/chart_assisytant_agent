import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

class ApiService {
  constructor() {
    this.ws = null;
    this.messageHandlers = [];
  }

  // 上传文件
  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('上传文件失败:', error);
      throw error;
    }
  }

  // 建立WebSocket连接
  connectWebSocket(onMessage) {
    this.ws = new WebSocket(WS_URL);

    this.ws.onopen = () => {
      console.log('WebSocket连接已建立');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket连接已关闭');
      // 5秒后重连
      setTimeout(() => this.connectWebSocket(onMessage), 5000);
    };
  }

  // 发送消息
  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message }));
    } else {
      console.error('WebSocket未连接');
    }
  }

  // 断开连接
  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

export default new ApiService();
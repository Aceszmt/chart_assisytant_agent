import React, { useState } from 'react';
import { Input, Button, Space } from 'antd';
import { SendOutlined } from '@ant-design/icons';

const { TextArea } = Input;

const ChatInterface = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim()) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-interface">
      <Space.Compact style={{ width: '100%' }}>
        <TextArea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="输入消息，例如：'请生成销售额的柱状图' 或 '展示月度趋势'"
          autoSize={{ minRows: 2, maxRows: 4 }}
          style={{ width: 'calc(100% - 80px)' }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          style={{ width: '80px', height: '100%' }}
        >
          发送
        </Button>
      </Space.Compact>
    </div>
  );
};

export default ChatInterface;
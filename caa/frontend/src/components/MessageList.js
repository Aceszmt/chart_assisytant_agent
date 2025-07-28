import React from 'react';
import { List, Avatar } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';

const MessageList = ({ messages }) => {
  return (
    <List
      className="message-list"
      itemLayout="horizontal"
      dataSource={messages}
      renderItem={(item) => (
        <List.Item className={`message-item ${item.sender}`}>
          <List.Item.Meta
            avatar={
              <Avatar icon={item.sender === 'user' ? <UserOutlined /> : <RobotOutlined />} />
            }
            title={item.sender === 'user' ? '用户' : '助手'}
            description={
              <div className="message-content">
                {item.text}
              </div>
            }
          />
        </List.Item>
      )}
    />
  );
};

export default MessageList;
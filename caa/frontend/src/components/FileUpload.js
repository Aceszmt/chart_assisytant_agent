import React from 'react';
import { Upload, Button, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import apiService from '../services/api';

const FileUpload = ({ onUploadSuccess }) => {
  const props = {
    name: 'file',
    accept: '.xlsx,.xls',
    showUploadList: false,
    customRequest: async ({ file, onSuccess, onError }) => {
      try {
        const result = await apiService.uploadFile(file);
        if (result.success) {
          message.success('文件上传成功');
          onSuccess(result);
          onUploadSuccess(result);
        } else {
          message.error(result.message);
          onError(new Error(result.message));
        }
      } catch (error) {
        message.error('上传失败');
        onError(error);
      }
    },
  };

  return (
    <Upload {...props}>
      <Button icon={<UploadOutlined />} type="primary">
        上传Excel文件
      </Button>
    </Upload>
  );
};

export default FileUpload;
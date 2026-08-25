import { useState } from 'react'
import { Button, Card, Form, Input, Tabs, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

export default function Login() {
  const [mode, setMode] = useState('login')
  const [loading, setLoading] = useState(false)
  const nav = useNavigate()

  const onFinish = async (values) => {
    setLoading(true)
    try {
      if (mode === 'login') {
        const { data } = await client.post('/auth/login', values)
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify(data.user))
        message.success('登录成功')
        nav('/')
      } else {
        await client.post('/auth/register', values)
        message.success('注册成功，请登录')
        setMode('login')
      }
    } catch (e) {
      message.error(e.response?.data?.detail || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f0f2f5',
      }}
    >
      <Card style={{ width: 380 }}>
        <h2 style={{ textAlign: 'center', marginTop: 0 }}>RAG 知识库问答系统</h2>
        <Tabs
          activeKey={mode}
          onChange={setMode}
          items={[
            { key: 'login', label: '登录' },
            { key: 'register', label: '注册' },
          ]}
        />
        <Form onFinish={onFinish} layout="vertical">
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="用户名" />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="密码" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block loading={loading}>
            {mode === 'login' ? '登录' : '注册'}
          </Button>
        </Form>
        <p style={{ marginTop: 16, color: '#999', fontSize: 12 }}>
          管理员默认账号：admin / 123456
        </p>
      </Card>
    </div>
  )
}

import { useEffect, useState } from 'react'
import {
  Button,
  Card,
  Input,
  Layout,
  List,
  Modal,
  Popconfirm,
  Space,
  Tag,
  Typography,
  Upload,
  message,
} from 'antd'
import { DeleteOutlined, InboxOutlined, PlusOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

const { Header, Content } = Layout

export default function KBManage() {
  const nav = useNavigate()
  const [kbs, setKbs] = useState([])
  const [activeKb, setActiveKb] = useState(null)
  const [docs, setDocs] = useState([])
  const [createOpen, setCreateOpen] = useState(false)
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')

  const loadKbs = () =>
    client.get('/kb').then((r) => {
      setKbs(r.data)
      if (!activeKb && r.data.length) setActiveKb(r.data[0].id)
    })

  const loadDocs = (kbId) =>
    client.get(`/kb/${kbId}/documents`).then((r) => setDocs(r.data))

  useEffect(() => {
    loadKbs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 轮询文档状态（解析中 → 已入库）
  useEffect(() => {
    if (!activeKb) return
    loadDocs(activeKb)
    const timer = setInterval(() => loadDocs(activeKb), 3000)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeKb])

  const createKb = async () => {
    if (!name.trim()) return message.warning('请输入知识库名称')
    await client.post('/kb', { name, description: desc })
    message.success('创建成功')
    setName('')
    setDesc('')
    setCreateOpen(false)
    loadKbs()
  }

  const deleteKb = async (id) => {
    await client.delete(`/kb/${id}`)
    message.success('已删除')
    if (activeKb === id) setActiveKb(null)
    loadKbs()
  }

  const deleteDoc = async (id) => {
    await client.delete(`/kb/${activeKb}/documents/${id}`)
    message.success('已删除')
    loadDocs(activeKb)
  }

  const uploadProps = {
    multiple: true,
    accept: '.pdf,.docx,.txt,.md,.csv',
    customRequest: async ({ file, onSuccess, onError }) => {
      const form = new FormData()
      form.append('file', file)
      try {
        await client.post(`/kb/${activeKb}/documents`, form)
        onSuccess()
        message.success(`${file.name} 上传成功，开始解析`)
        loadDocs(activeKb)
      } catch (e) {
        onError(e)
        message.error(e.response?.data?.detail || '上传失败')
      }
    },
  }

  return (
    <Layout style={{ height: '100%' }}>
      <Header
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
      >
        <Typography.Title level={4} style={{ color: '#fff', margin: 0 }}>
          知识库管理
        </Typography.Title>
        <Button size="small" onClick={() => nav('/')}>
          返回问答
        </Button>
      </Header>

      <Content style={{ padding: 24, display: 'flex', gap: 16 }}>
        <Card
          title="知识库"
          style={{ width: 280 }}
          extra={
            <Button size="small" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
              新建
            </Button>
          }
        >
          <List
            dataSource={kbs}
            renderItem={(k) => (
              <List.Item
                onClick={() => setActiveKb(k.id)}
                style={{
                  cursor: 'pointer',
                  background: k.id === activeKb ? '#e6f4ff' : 'transparent',
                  padding: '8px 12px',
                }}
                actions={[
                  <Popconfirm
                    key="del"
                    title="删除知识库及其中所有文档？"
                    onConfirm={() => deleteKb(k.id)}
                  >
                    <DeleteOutlined onClick={(e) => e.stopPropagation()} />
                  </Popconfirm>,
                ]}
              >
                <div>
                  <div>{k.name}</div>
                  {k.description && (
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {k.description}
                    </Typography.Text>
                  )}
                </div>
              </List.Item>
            )}
          />
        </Card>

        <Card
          title={activeKb ? '文档' : '请选择知识库'}
          style={{ flex: 1 }}
          extra={
            activeKb ? (
              <Upload {...uploadProps}>
                <Button icon={<InboxOutlined />}>上传文档</Button>
              </Upload>
            ) : null
          }
        >
          <List
            dataSource={docs}
            locale={{ emptyText: '暂无文档，点击右上角上传' }}
            renderItem={(d) => (
              <List.Item
                actions={[
                  <Popconfirm key="del" title="删除该文档？" onConfirm={() => deleteDoc(d.id)}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>,
                ]}
              >
                <div style={{ flex: 1 }}>
                  <div>{d.filename}</div>
                  {d.error && (
                    <Typography.Text type="danger" style={{ fontSize: 12 }}>
                      错误：{d.error}
                    </Typography.Text>
                  )}
                </div>
                <StatusTag status={d.status} />
                <span style={{ fontSize: 12, color: '#999', marginLeft: 12 }}>
                  {d.chunk_count} 分块
                </span>
              </List.Item>
            )}
          />
        </Card>
      </Content>

      <Modal
        title="新建知识库"
        open={createOpen}
        onOk={createKb}
        onCancel={() => setCreateOpen(false)}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input
            placeholder="知识库名称"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Input.TextArea
            placeholder="描述（可选）"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            rows={3}
          />
        </Space>
      </Modal>
    </Layout>
  )
}

function StatusTag({ status }) {
  if (status === 'ready') return <Tag color="green">已入库</Tag>
  if (status === 'parsing') return <Tag color="blue">解析中</Tag>
  if (status === 'failed') return <Tag color="red">失败</Tag>
  return <Tag>{status}</Tag>
}

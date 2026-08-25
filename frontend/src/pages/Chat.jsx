import { useEffect, useRef, useState } from 'react'
import {
  Button,
  Empty,
  Input,
  Layout,
  List,
  Modal,
  Popconfirm,
  Select,
  Spin,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  SendOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

const { Header, Content, Sider } = Layout

export default function Chat() {
  const nav = useNavigate()
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [kbs, setKbs] = useState([])
  const [kbId, setKbId] = useState(null)
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [rename, setRename] = useState({ open: false, id: null, title: '' })
  const listRef = useRef(null)

  useEffect(() => {
    client.get('/conversations').then((r) => setConversations(r.data))
    client.get('/kb').then((r) => {
      setKbs(r.data)
      if (r.data.length) setKbId(r.data[0].id)
    })
  }, [])

  useEffect(() => {
    if (!activeId) return
    client.get(`/conversations/${activeId}/messages`).then((r) => setMessages(r.data))
  }, [activeId])

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages])

  const newConversation = async () => {
    const { data } = await client.post('/conversations', {})
    setConversations((prev) => [data, ...prev])
    setActiveId(data.id)
    setMessages([])
  }

  const removeConversation = async (id) => {
    await client.delete(`/conversations/${id}`)
    setConversations((prev) => prev.filter((c) => c.id !== id))
    if (activeId === id) {
      setActiveId(null)
      setMessages([])
    }
  }

  const submitRename = async () => {
    if (!rename.title.trim()) return setRename({ open: false, id: null, title: '' })
    await client.patch(`/conversations/${rename.id}`, { title: rename.title })
    setConversations((prev) =>
      prev.map((c) => (c.id === rename.id ? { ...c, title: rename.title } : c)),
    )
    setRename({ open: false, id: null, title: '' })
  }

  const send = async () => {
    const question = input.trim()
    if (!question || streaming) return
    let cid = activeId
    if (!cid) {
      const { data } = await client.post('/conversations', {})
      setConversations((prev) => [data, ...prev])
      cid = data.id
      setActiveId(cid)
      setMessages([])
    }
    setInput('')
    const userMsg = { role: 'user', content: question }
    const asstMsg = { role: 'assistant', content: '', citations: [], streaming: true }
    setMessages((prev) => [...prev, userMsg, asstMsg])
    setStreaming(true)

    try {
      const res = await fetch(`/api/chat/${cid}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ question, kb_id: kbId }),
      })
      if (!res.ok || !res.body) throw new Error('请求失败，请稍后重试')
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        let idx
        while ((idx = buffer.indexOf('\n')) >= 0) {
          const line = buffer.slice(0, idx).trim()
          buffer = buffer.slice(idx + 1)
          if (!line) continue
          const evt = JSON.parse(line)
          if (evt.type === 'citations') {
            setMessages((prev) =>
              prev.map((m) => (m === asstMsg ? { ...m, citations: evt.data } : m)),
            )
          } else if (evt.type === 'token') {
            setMessages((prev) =>
              prev.map((m) => (m === asstMsg ? { ...m, content: m.content + evt.data } : m)),
            )
          } else if (evt.type === 'done') {
            setMessages((prev) =>
              prev.map((m) =>
                m === asstMsg ? { ...m, id: evt.data.message_id, streaming: false } : m,
              ),
            )
          } else if (evt.type === 'error') {
            setMessages((prev) =>
              prev.map((m) =>
                m === asstMsg
                  ? { ...m, content: m.content || evt.data, streaming: false, error: true }
                  : m,
              ),
            )
          }
        }
      }
      client.get('/conversations').then((r) => setConversations(r.data))
    } catch (e) {
      setMessages((prev) =>
        prev.map((m) =>
          m === asstMsg
            ? { ...m, content: m.content || String(e.message || e), streaming: false, error: true }
            : m,
        ),
      )
    } finally {
      setStreaming(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    nav('/login')
  }

  return (
    <Layout style={{ height: '100%' }}>
      <Header
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
      >
        <Typography.Title level={4} style={{ color: '#fff', margin: 0 }}>
          RAG 知识库问答
        </Typography.Title>
        <span style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#fff' }}>
          <Select
            size="small"
            style={{ width: 180 }}
            placeholder="选择知识库"
            value={kbId}
            onChange={setKbId}
            options={kbs.map((k) => ({ value: k.id, label: k.name }))}
          />
          {user.role === 'admin' && (
            <Button size="small" onClick={() => nav('/kb')}>
              知识库管理
            </Button>
          )}
          <span>
            {user.username}（{user.role === 'admin' ? '管理员' : '用户'}）
          </span>
          <Button size="small" onClick={logout}>
            退出
          </Button>
        </span>
      </Header>

      <Layout>
        <Sider width={240} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
          <div style={{ padding: 12 }}>
            <Button type="primary" icon={<PlusOutlined />} block onClick={newConversation}>
              新建会话
            </Button>
          </div>
          <List
            dataSource={conversations}
            renderItem={(c) => (
              <List.Item
                onClick={() => setActiveId(c.id)}
                style={{
                  cursor: 'pointer',
                  padding: '8px 16px',
                  background: c.id === activeId ? '#e6f4ff' : 'transparent',
                }}
                actions={[
                  <EditOutlined
                    key="edit"
                    onClick={(e) => {
                      e.stopPropagation()
                      setRename({ open: true, id: c.id, title: c.title })
                    }}
                  />,
                  <Popconfirm
                    key="del"
                    title="删除该会话？"
                    onConfirm={(e) => {
                      e?.stopPropagation?.()
                      removeConversation(c.id)
                    }}
                  >
                    <DeleteOutlined onClick={(e) => e.stopPropagation()} />
                  </Popconfirm>,
                ]}
              >
                <Typography.Text ellipsis style={{ width: 150 }}>
                  {c.title}
                </Typography.Text>
              </List.Item>
            )}
          />
        </Sider>

        <Content style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div ref={listRef} style={{ flex: 1, overflow: 'auto', padding: 24 }}>
            {messages.length === 0 && (
              <Empty description="新建会话，开始提问" style={{ marginTop: 80 }} />
            )}
            {messages.map((m, i) => (
              <MessageBubble key={i} msg={m} />
            ))}
          </div>
          <div style={{ padding: 16, borderTop: '1px solid #f0f0f0' }}>
            <Input.TextArea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault()
                  send()
                }
              }}
              placeholder="输入问题，Enter 发送，Shift+Enter 换行"
              autoSize={{ minRows: 1, maxRows: 4 }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
              <Button type="primary" icon={<SendOutlined />} onClick={send} loading={streaming}>
                发送
              </Button>
            </div>
          </div>
        </Content>
      </Layout>

      <Modal
        title="重命名会话"
        open={rename.open}
        onOk={submitRename}
        onCancel={() => setRename({ open: false, id: null, title: '' })}
      >
        <Input
          value={rename.title}
          onChange={(e) => setRename((prev) => ({ ...prev, title: e.target.value }))}
        />
      </Modal>
    </Layout>
  )
}

function MessageBubble({ msg }) {
  if (msg.role === 'user') {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <div
          style={{
            maxWidth: '70%',
            background: '#1677ff',
            color: '#fff',
            padding: '10px 14px',
            borderRadius: 8,
            whiteSpace: 'pre-wrap',
          }}
        >
          {msg.content}
        </div>
      </div>
    )
  }

  const pending = msg.streaming && !msg.content
  return (
    <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 16 }}>
      <div
        style={{
          maxWidth: '75%',
          background: msg.error ? '#fff2f0' : '#f5f5f5',
          padding: '10px 14px',
          borderRadius: 8,
        }}
      >
        <div style={{ whiteSpace: 'pre-wrap' }}>
          {pending ? <Spin size="small" /> : msg.content}
        </div>
        {!pending && msg.citations && msg.citations.length > 0 && (
          <div style={{ marginTop: 8, borderTop: '1px solid #e8e8e8', paddingTop: 8 }}>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              引用来源（{msg.citations.length} 条）：
            </Typography.Text>
            {msg.citations.map((c, i) => (
              <div key={i} style={{ fontSize: 12, color: '#666', marginTop: 6 }}>
                <Tag color="blue" style={{ marginRight: 4 }}>
                  [{i + 1}]
                </Tag>
                {c.document && <span style={{ fontWeight: 600 }}>{c.document}</span>}
                <div style={{ marginTop: 2 }}>{c.content}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

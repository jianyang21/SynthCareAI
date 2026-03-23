import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { chatWithAgent } from '../api/client'
import { Send, Bot } from 'lucide-react'

const ROLE_CONTEXT = {
  patient: (u) => `You are SynthCare AI. The logged-in user is patient ${u.name} (patient_id: ${u.patientId}). Only answer questions about this patient's own data. Never reveal other patients' data.`,
  doctor:  (u) => `You are SynthCare AI. The logged-in user is Dr. ${u.name} (doctor_id: ${u.doctorId}, specialization: ${u.specialization}). Only answer questions relevant to this doctor's appointments and their patients.`,
  admin:   (u) => `You are SynthCare AI. The logged-in user is admin ${u.name}. You have full access to all hospital data including patients, doctors, medicines, inventory, and analytics.`,
}

const SUGGESTIONS = {
  patient: ['What are my upcoming appointments?', 'Show my prescriptions', 'What medicines am I taking?'],
  doctor:  ['Show my appointments today', 'List my patients', 'Which medicines are low stock?'],
  admin:   ['Show dashboard analytics', 'Which medicines are low stock?', 'List all doctors'],
}

export default function ChatBot() {
  const { user } = useAuth()
  const [messages, setMessages] = useState([
    { from: 'bot', text: `Hi ${user?.name?.split(' ')[0]}! I'm SynthCare AI. How can I help you today?` }
  ])
  const [input, setInput]     = useState('')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])
  const bottomRef             = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')
    setMessages(p => [...p, { from: 'user', text: msg }])
    setLoading(true)
    try {
      const ctx    = ROLE_CONTEXT[user.role]?.(user) ?? ''
      const full   = `${ctx}\n\nUser: ${msg}`
      const res    = await chatWithAgent(full, history)
      const answer = res.answer || 'Sorry, I could not get a response.'
      setMessages(p => [...p, { from: 'bot', text: answer }])
      setHistory(p => [...p, { role: 'user', content: msg }, { role: 'assistant', content: answer }])
    } catch {
      setMessages(p => [...p, { from: 'bot', text: '⚠️ Backend unreachable. Is the server running on port 8000?' }])
    } finally { setLoading(false) }
  }

  const ROLE_COLOR = { patient: 'text-accent', doctor: 'text-accent2', admin: 'text-accent3' }

  return (
    <div className="flex flex-col h-full bg-bg">
      {/* Role tag */}
      <div className="flex items-center gap-2 px-5 py-2.5 border-b border-white/[0.07] bg-bg2 text-xs text-muted flex-shrink-0">
        <Bot size={13} />
        Chatting as
        <span className={`font-semibold capitalize ${ROLE_COLOR[user?.role]}`}>{user?.role}</span>
        <span className="opacity-40 ml-1">· context isolated to your role</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.from === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.from === 'user'
              ? <div className="bubble-user">{m.text}</div>
              : <div className="bubble-bot">{m.text}</div>
            }
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bubble-bot text-muted italic">Thinking…</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      <div className="px-5 pb-2 flex gap-2 flex-wrap flex-shrink-0">
        {SUGGESTIONS[user?.role]?.map((s, i) => (
          <button key={i} onClick={() => send(s)}
            className="text-xs px-3 py-1.5 rounded-full border border-white/[0.07] bg-bg3
                       text-muted hover:text-accent hover:border-accent/40 transition-all">
            {s}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/[0.07] bg-bg2 flex gap-3 flex-shrink-0">
        <textarea rows={1}
          className="form-input flex-1 !rounded-xl resize-none py-2.5"
          placeholder="Ask anything…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
        />
        <button onClick={() => send()} disabled={!input.trim() || loading}
          className="btn btn-primary self-end !px-3.5 disabled:opacity-40">
          <Send size={15} />
        </button>
      </div>
    </div>
  )
}

import React from 'react'
import { createSession, createTask, getTask, cancelTask } from './api.js'
import { debounce } from './api.js'
import Icons from './Icons.jsx'

function NewPage({ setActive, search, setSearch, poll, setPoll, saveSessionLocal, saveHistoryLocal }) {
  const [title, setTitle] = React.useState('')
  const isLoading = search.isLoading

  const submit = async () => {
    try {
      try { if (poll.taskId) { cancelTask(poll.taskId).catch(() => {}) } } catch (e) {}
      try { poll.timer && clearInterval(poll.timer) } catch (e) {}
      setPoll({ taskId: null, timer: null })

      setSearch({ currentSessionId: null, title: '', messages: [], historyItems: [], isLoading: true, error: null, cancelNoticeTs: 0 })
      const session = await createSession()
      saveSessionLocal(session)
      setSearch({ currentSessionId: session.id, title: title, messages: [{ role: 'user', text: title }], historyItems: [], isLoading: true, error: null, cancelNoticeTs: 0 })
      setTitle('')
      setActive('Search')
      const created = await createTask(title, session.id)
      const taskId = created.task_id
      const timer = setInterval(async () => {
        try {
          const st = await getTask(taskId)
          if (st.status === 'done') {
            clearInterval(timer)
            setPoll({ taskId: null, timer: null })
            setSearch(s => ({ ...s, isLoading: false, messages: [...s.messages, { role: 'bot', text: st.answer || '' }], historyItems: [...s.historyItems, { id: st.history_id, user_input: title, answer: st.answer || '' }] }))
            saveHistoryLocal(session.id, title, st.answer || '')
          } else if (st.status === 'error') {
            clearInterval(timer)
            setPoll({ taskId: null, timer: null })
            setSearch(s => ({ ...s, isLoading: false, error: st.error || 'Task failed' }))
          }
        } catch (e) {
          clearInterval(timer)
          setPoll({ taskId: null, timer: null })
          setSearch(s => ({ ...s, isLoading: false, error: 'Failed to get task status: ' + e.message }))
        }
      }, 1000)
      setPoll({ taskId, timer })
    } catch (e) {
      setSearch(s => ({ ...s, isLoading: false, error: String(e && e.message ? e.message : e) }))
    }
  }

  const debouncedSubmit = React.useMemo(() => debounce(submit, 150), [title])

  return (
    <div className='container home'>
      <div className='title'>DeepSearch</div>
      <div className='searchbox'>
        <input className='input' placeholder='Ask anything' value={title} onChange={e => setTitle(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); debouncedSubmit() } }} />
        <button className={'send'} onClick={debouncedSubmit} disabled={isLoading}>{<Icons.Plane />}</button>
      </div>
    </div>
  )
}

export default NewPage
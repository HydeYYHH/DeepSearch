import React from 'react'
import { createTask, getTask, cancelTask } from './api.js'
import { debounce, renderMarkdown } from './api.js'
import Icons from './Icons.jsx'
import NewPage from './NewPage.jsx'

function ErrorBanner({ error }) {
  if (!error) return null
  return <div className='error'>{String(error)}</div>
}

function SearchPage({ setActive, search, setSearch, poll, setPoll, saveSessionLocal, saveHistoryLocal }) {
  const [input, setInput] = React.useState('')
  const { messages, isLoading, currentSessionId } = search
  const showNew = !currentSessionId
  const bottomInputRef = React.useRef(null)

  const submit = async () => {
    if (!currentSessionId) return
    const text = input.trim()
    if (!text) return
    try { if (poll.taskId) { cancelTask(poll.taskId).catch(() => {}) } } catch (e) {}
    try { poll.timer && clearInterval(poll.timer) } catch (e) {}
    setPoll({ taskId: null, timer: null })
    setSearch(s => ({ ...s, title: text, messages: [...s.messages, { role: 'user', text }], isLoading: true }))
    setInput('')
    const created = await createTask(text, currentSessionId)
    const taskId = created.task_id
    const timer = setInterval(async () => {
      try {
        const st = await getTask(taskId)
        if (st.status === 'done') {
          clearInterval(timer)
          setPoll({ taskId: null, timer: null })
          setSearch(s => ({ ...s, isLoading: false, messages: [...s.messages, { role: 'bot', text: st.answer || '' }], historyItems: [...s.historyItems, { id: st.history_id, user_input: text, answer: st.answer || '' }] }))
          saveHistoryLocal(currentSessionId, text, st.answer || '')
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
  }

  const debouncedSubmit = React.useMemo(() => debounce(submit, 150), [currentSessionId, input])

  const cancel = () => {
    try { if (poll.taskId) { cancelTask(poll.taskId).catch(() => {}) } } catch (e) {}
    try { poll.timer && clearInterval(poll.timer) } catch (e) {}
    setPoll({ taskId: null, timer: null })
    setSearch(s => ({ ...s, isLoading: false, cancelNoticeTs: Date.now(), error: null }))
  }

  React.useEffect(() => {
    const el = bottomInputRef.current
    const scroller = document.querySelector('.content')
    if (el && scroller) {
      const top = 20
      scroller.scrollTo({ top, behavior: 'smooth' })
    }
  }, [messages, isLoading])

  const pairs = (() => {
    const out = []
    let pending = null
    messages.forEach(m => {
      if (m.role === 'user') {
        if (pending) { out.push({ title: pending.text, answer: '' }) }
        pending = m
      } else {
        if (pending) { out.push({ title: pending.text, answer: m.text }); pending = null }
        else { out.push({ title: '', answer: m.text }) }
      }
    })
    if (pending) { out.push({ title: pending.text, answer: '' }) }
    return out
  })()

  const Skeleton = () => <div className='qa-answer'><div className='sk-line'></div><div className='sk-line'></div><div className='sk-line long'></div><div className='sk-line'></div><div className='sk-block'></div></div>
  const renderAnswer = (text) => <div className='qa-answer' dangerouslySetInnerHTML={{ __html: renderMarkdown(text) }}></div>

  if (showNew) {
    return <NewPage setActive={setActive} search={search} setSearch={setSearch} poll={poll} setPoll={setPoll} saveSessionLocal={saveSessionLocal} saveHistoryLocal={saveHistoryLocal} />
  }

  return (
    <div className='container search'>
      <ErrorBanner error={search.error} />
      {pairs.map((p, i) => <div className='qa-current' key={i}><div className='qa-title'>{p.title || ''}</div>{p.answer ? renderAnswer(p.answer) : <Skeleton />}</div>)}
      <div className='align-guides'><div className='guide'></div></div>
      <div className='bottom-input'>
        <input className='input' placeholder='Ask anything' value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (!isLoading && e.key === 'Enter') { e.preventDefault(); debouncedSubmit() } }} />
        <button className={'send' + (isLoading ? ' cancel' : '')} onClick={isLoading ? cancel : debouncedSubmit}>{isLoading ? <Icons.StopSquare /> : <Icons.Plane />}</button>
      </div>
      <div ref={bottomInputRef} style={{height:1}}></div>
    </div>
  )
}

export default SearchPage
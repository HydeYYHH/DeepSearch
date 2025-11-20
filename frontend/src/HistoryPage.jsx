import React from 'react'
import { getSessions, getHistories, deleteSession, cancelTask } from './api.js'
import Icons from './Icons.jsx'

function HistoryPage({ setActive, search, setSearch, sessions, setSessions, poll, setPoll }) {
  const [isLoading, setIsLoading] = React.useState(true)

  React.useEffect(() => {
    (async () => {
      setIsLoading(true)
      try {
        const serverList = await getSessions()
        const sorted = serverList.slice().sort((a,b)=>((b.created_at||0) - (a.created_at||0)))
        setSessions(sorted)
      } catch (e) {
        console.error('Failed to load sessions:', e)
      } finally {
        setIsLoading(false)
      }
    })()
  }, [])

  const openSession = async (id) => {
    const histories = await getHistories(id)
    const msgs = histories.map(hh => [{ role: 'user', text: hh.user_input }, { role: 'bot', text: hh.answer || '' }]).flat()
    setSearch({ currentSessionId: id, title: (histories[histories.length - 1] && histories[histories.length - 1].user_input) || '', messages: msgs, historyItems: histories, isLoading: false, error: null, cancelNoticeTs: 0 })
    setActive('Search')
  }

  const removeSession = async (id) => {
    try {
      await deleteSession(id)
      setSessions((sessions || []).filter(x => x.id !== id))
      if (search.currentSessionId === id) {
        try { if (poll.taskId) { cancelTask(poll.taskId).catch(() => {}) } } catch (e) {}
        try { poll.timer && clearInterval(poll.timer) } catch (e) {}
        setPoll({ taskId: null, timer: null })
        setSearch({ currentSessionId: null, title: '', messages: [], historyItems: [], isLoading: false, error: null, cancelNoticeTs: 0 })
        setActive('New')
      }
    } catch (e) {}
  }

  return (
    <div className='container'>
      <div className='section-title'>History</div>
      {isLoading ? <div className='loading-dots'><span></span><span></span><span></span></div> : sessions.map(s => {
        const created = (s.created_at ?? Math.floor(Date.now()/1000))
        const createdMs = created > 1e12 ? created : created * 1000
        return <div className='session-card' key={s.id} onClick={() => openSession(s.id)}>
          <div className='session-header'>Session {new Date(createdMs).toLocaleString()}</div>
          <div className='session-line'>{s.abstract || ''}</div>
          <button className='trash-btn' aria-label='Delete session' onClick={(e) => { e.stopPropagation(); removeSession(s.id) }}>{<Icons.Trash />}</button>
        </div>
      })}
    </div>
  )
}

export default HistoryPage

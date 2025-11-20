import React from 'react'
import { cancelTask, StorageService } from './api.js'
import NewPage from './NewPage.jsx'
import SearchPage from './SearchPage.jsx'
import HistoryPage from './HistoryPage.jsx'
import Icons from './Icons.jsx'


export default function App(){
  const [active,setActive] = React.useState('New')
  const [search,setSearch] = React.useState({currentSessionId:null,title:'',messages:[],historyItems:[],isLoading:false,error:null,cancelNoticeTs:0})
  const [sessions,setSessions] = React.useState([])
  const [poll,setPoll] = React.useState({taskId:null,timer:null})


  const saveSessionLocal = (session)=>{
    const key='ds:sessions'
    const list=StorageService.get(key)||[]
    const exists=list.find(x=>x.id===session.id)
    const now=Date.now()
    const item={id:session.id,createdAt:session.created_at||now,abstract:session.abstract||'',lastUpdated:now}
    StorageService.set(key, exists? list.map(x=>x.id===item.id?item:x):[item].concat(list))
  }
  const saveHistoryLocal = (sessionId,userInput,answer)=>{
    const key='ds:session:'+sessionId
    const list=StorageService.get(key)||[]
    const now=Date.now()
    const item={id:now,timestamp:now,userInput,answer}
    StorageService.set(key,list.concat([item]))
    const sessionsKey='ds:sessions'
    const sessionsList=StorageService.get(sessionsKey)||[]
    const updated=sessionsList.map(x=>x.id===sessionId?{...x,abstract:x.abstract||userInput,lastUpdated:now}:x)
    StorageService.set(sessionsKey,updated)
  }

  const Sidebar=()=>{
    const btn=(icon,tab)=> <button className={'nav-btn'+(active===tab?' active':'')} onClick={()=>setActive(tab)}>{React.createElement(Icons[icon])}</button>
    return <div className='sidebar'>{btn('Plus','New')}{btn('Search','Search')}{btn('History','History')}</div>
  }

  

  return <div className='layout'>
    <Sidebar />
    <div className='content'>
      {active==='New'? <NewPage setActive={setActive} search={search} setSearch={setSearch} poll={poll} setPoll={setPoll} saveSessionLocal={saveSessionLocal} saveHistoryLocal={saveHistoryLocal} /> : active==='Search'? <SearchPage setActive={setActive} search={search} setSearch={setSearch} poll={poll} setPoll={setPoll} saveSessionLocal={saveSessionLocal} saveHistoryLocal={saveHistoryLocal} /> : <HistoryPage setActive={setActive} search={search} setSearch={setSearch} sessions={sessions} setSessions={setSessions} poll={poll} setPoll={setPoll} />}
    </div>
  </div>
}
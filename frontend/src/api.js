import MarkdownIt from 'markdown-it'
import mdKatex from '@vscode/markdown-it-katex'
import DOMPurify from 'dompurify'

const API_BASE = '/api'

export async function createSession(){
  const r = await fetch(`${API_BASE}/sessions`,{method:'POST'})
  if(!r.ok) throw new Error('sessions_failed')
  return r.json()
}

export async function createTask(query,sessionId){
  const r = await fetch(`${API_BASE}/tasks`,{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({query,session_id:sessionId})
  })
  if(!r.ok) throw new Error('task_create_failed')
  return r.json()
}

export async function getTask(taskId){
  const r = await fetch(`${API_BASE}/tasks/${taskId}`)
  if(!r.ok) throw new Error('task_status_failed')
  return r.json()
}

export async function cancelTask(taskId){
  const r = await fetch(`${API_BASE}/tasks/${taskId}`,{method:'DELETE'})
  if(!r.ok) throw new Error('task_cancel_failed')
  return r.json()
}

export async function getSessions(){
  const r = await fetch(`${API_BASE}/sessions`)
  if(!r.ok) throw new Error('list_failed')
  return r.json()
}

export async function getHistories(sessionId){
  const r = await fetch(`${API_BASE}/sessions/${sessionId}/histories`)
  if(!r.ok) throw new Error('hist_failed')
  return r.json()
}

export async function deleteSession(id){
  const r = await fetch(`${API_BASE}/sessions/${id}`,{method:'DELETE'})
  if(!r.ok) throw new Error('del_session_failed')
  return r.json()
}

export async function deleteHistory(id){
  const r = await fetch(`${API_BASE}/histories/${id}`,{method:'DELETE'})
  if(!r.ok) throw new Error('del_history_failed')
  return r.json()
}

export const StorageService = {
  set:(k,v)=>localStorage.setItem(k,JSON.stringify(v)),
  get:(k)=>{const v=localStorage.getItem(k);return v?JSON.parse(v):null},
  remove:(k)=>localStorage.removeItem(k)
}

export const debounce=(fn,wait)=>{let t;return function(){const ctx=this,args=arguments;clearTimeout(t);t=setTimeout(()=>fn.apply(ctx,args),wait)}}

const mdRenderer = new MarkdownIt({ html: false, linkify: true, breaks: true, typographer: true })
mdRenderer.use(mdKatex)
const normalizeHref = (s) => {
  let href = String(s || '').trim()
  href = href.replace(/^['"`(]+/, '')
  href = href.replace(/["'`),.;，、]+$/, '')
  href = href.replace(/>$/, '')
  return href
}
mdRenderer.renderer.rules.link_open = function(tokens, idx, options, env, self) {
  const t = tokens[idx]
  const next = tokens[idx + 1]
  const targetIdx = t.attrIndex('target')
  if (targetIdx < 0) t.attrPush(['target', '_blank'])
  else t.attrs[targetIdx][1] = '_blank'
  const relIdx = t.attrIndex('rel')
  if (relIdx < 0) t.attrPush(['rel', 'noopener noreferrer'])
  else t.attrs[relIdx][1] = 'noopener noreferrer'
  if (next && next.type === 'text' && /^source\d+$/.test(next.content)) {
    const classIdx = t.attrIndex('class')
    if (classIdx < 0) t.attrPush(['class', 'cite'])
    else t.attrs[classIdx][1] = (t.attrs[classIdx][1] + ' cite').trim()
    const hrefIdx = t.attrIndex('href')
    if (hrefIdx >= 0) t.attrs[hrefIdx][1] = normalizeHref(t.attrs[hrefIdx][1])
  }
  return self.renderToken(tokens, idx, options)
}

export function renderMarkdown(md){
  let text = String(md || '')
  let counter = 0
  const seen = new Map()
  const clean = (s) => {
    let href = String(s || '').trim()
    href = href.replace(/^['"`(]+/, '')
    href = href.replace(/["'`),.;，、]+$/, '')
    href = href.replace(/>$/, '')
    return href
  }
  text = text.replace(/\[cite:\s*([^\]]+)\]/gi, (_, list) => {
    const urls = String(list)
      .split(/\s*,\s*/)
      .map(clean)
      .filter(Boolean)
    const parts = urls.map((href) => {
      let idx = seen.get(href)
      if (!idx) { counter += 1; idx = counter; seen.set(href, idx) }
      return `[source${idx}](${href})`
    })
    return parts.join(' ')
  })
  let html = mdRenderer.render(text)
  html = html.replace(/<a[^>]*href=\"([^\"]+)\"[^>]*>source(\d+)<\/a>/g, (_, href, n) => {
    const cleanHref = normalizeHref(href)
    return `<a class=\"cite\" href=\"${cleanHref}\" target=\"_blank\" rel=\"noopener noreferrer\">source${n}</a>`
  })
  return DOMPurify.sanitize(html)
}

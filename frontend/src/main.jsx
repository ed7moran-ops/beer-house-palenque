import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BarChart3, Beer, Boxes, Camera, Download, FileSpreadsheet, FileText, Home, Info, LogOut, Moon, Plus, ReceiptText, Search, Settings, ShoppingCart, Smartphone, Sun, Trash2, TrendingUp, Users, WalletCards } from 'lucide-react'
import './index.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'
const currency = new Intl.NumberFormat('es-EC', { style: 'currency', currency: 'USD' })
const dateFmt = new Intl.DateTimeFormat('es-EC', { dateStyle: 'medium', timeStyle: 'short' })

function apiPath(path) {
  if (!path) return ''
  return path.startsWith('data:') || path.startsWith('http') ? path : `${API_URL}${path}`
}

function App() {
  const [token, setToken] = useState(localStorage.getItem('bhp_token'))
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('bhp_user') || 'null'))
  const [error, setError] = useState('')
  const [dark, setDark] = useState(localStorage.getItem('bhp_theme') !== 'light')

  useEffect(() => {
    document.documentElement.classList.toggle('light-mode', !dark)
    localStorage.setItem('bhp_theme', dark ? 'dark' : 'light')
  }, [dark])

  useEffect(() => {
    if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('/service-worker.js'))
  }, [])

  const request = async (path, options = {}) => {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {})
      }
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(data.message || 'Error inesperado')
    return data
  }

  const onLogin = (payload) => {
    setToken(payload.token)
    setUser(payload.user)
    localStorage.setItem('bhp_token', payload.token)
    localStorage.setItem('bhp_user', JSON.stringify(payload.user))
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('bhp_token')
    localStorage.removeItem('bhp_user')
  }

  if (!token || !user) return <Login onLogin={onLogin} setError={setError} error={error} />

  return (
    <Shell user={user} logout={logout} dark={dark} setDark={setDark}>
      {user.role === 'admin' ? <AdminApp request={request} token={token} /> : <SellerApp request={request} user={user} />}
    </Shell>
  )
}

function Login({ onLogin, setError, error }) {
  const [form, setForm] = useState({ username: 'admin', password: 'admin123' })
  const [loading, setLoading] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`${API_URL}/api/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
      const data = await response.json()
      if (!response.ok) throw new Error(data.message)
      onLogin(data)
    } catch (err) { setError(err.message) } finally { setLoading(false) }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(247,201,72,0.24),_transparent_32%),#0b0b0f] px-4 py-8 text-white sm:py-10">
      <section className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-6xl items-center gap-8 lg:grid-cols-[1.2fr_0.8fr]">
        <div>
          <LogoMark className="h-20 w-20" />
          <span className="badge mt-6 inline-flex">PWA · Dashboard · Caja · Reportes</span>
          <h1 className="mt-6 text-4xl font-black tracking-tight sm:text-5xl md:text-6xl">Beer House Palenque</h1>
          <p className="mt-5 max-w-2xl text-base text-zinc-300 sm:text-lg">Sistema profesional amarillo y negro para un bar real: ventas, stock, gastos, corte diario, rankings y exportación para gerencia.</p>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">{['Computadora y tablet', 'Android instalable', 'Datos demo incluidos'].map((item) => <div key={item} className="glass-panel rounded-2xl p-4 text-sm text-zinc-200">{item}</div>)}</div>
        </div>
        <form onSubmit={submit} className="glass-panel rounded-3xl p-5 sm:p-6 md:p-8">
          <div className="mb-8 flex items-center gap-3"><LogoMark className="h-12 w-12" /><div><h2 className="text-2xl font-black">Iniciar sesión</h2><p className="text-sm text-zinc-400">Credenciales de demostración</p></div></div>
          {error && <p className="mb-4 rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
          <label className="text-sm font-semibold text-zinc-300">Usuario</label><input className="input mt-2" autoComplete="username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
          <label className="mt-4 block text-sm font-semibold text-zinc-300">Contraseña</label><input className="input mt-2" autoComplete="current-password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <button className="btn-primary mt-6 w-full" disabled={loading}>{loading ? 'Ingresando...' : 'Entrar al sistema'}</button>
          <div className="mt-5 rounded-2xl bg-white/5 p-4 text-sm text-zinc-300"><p><b>Admin:</b> admin / admin123</p><p><b>Vendedor:</b> vendedor / vendedor123</p></div>
        </form>
      </section>
    </main>
  )
}

function Shell({ user, logout, dark, setDark, children }) {
  return (
    <div className="min-h-screen bg-beer-black text-white lg:grid lg:grid-cols-[17rem_1fr]">
      <aside className="desktop-sidebar hidden min-h-screen border-r border-beer-gold/20 bg-zinc-950/80 p-5 lg:flex lg:flex-col">
        <BrandBlock user={user} />
        <div className="mt-8 space-y-3 rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-zinc-300"><p className="flex items-center gap-2 font-bold text-beer-amber"><Home size={16} /> Centro operativo</p><p>Dashboard, inventario, vendedores, gastos, caja y reportes exportables.</p></div>
        <div className="mt-auto space-y-3"><ThemeButton dark={dark} setDark={setDark} /><InstallAppButton compact={false} /><button onClick={logout} className="btn-secondary flex w-full items-center justify-center gap-2"><LogOut size={16} /> Salir</button></div>
      </aside>
      <div className="min-w-0"><header className="sticky top-0 z-30 border-b border-beer-gold/20 bg-beer-black/95 backdrop-blur lg:hidden"><div className="flex items-center justify-between gap-3 px-4 py-3"><BrandBlock user={user} small /><div className="flex gap-2"><ThemeButton dark={dark} setDark={setDark} compact /><button onClick={logout} className="btn-secondary flex items-center gap-2 px-3 py-2"><LogOut size={16} /></button></div></div></header><main className="mx-auto max-w-7xl px-4 py-5 pb-32 sm:px-6 lg:px-8 lg:py-8 lg:pb-8">{children}</main></div>
    </div>
  )
}

function LogoMark({ className = '' }) { return <div className={`${className} gold-gradient grid shrink-0 place-items-center rounded-2xl text-beer-black shadow-xl shadow-beer-gold/20`}><Beer /></div> }
function BrandBlock({ user, small = false }) { return <div className="flex min-w-0 items-center gap-3"><LogoMark className={small ? 'h-10 w-10' : 'h-12 w-12'} /><div className="min-w-0"><h1 className={`${small ? 'text-sm' : 'text-lg'} truncate font-black`}>Beer House Palenque</h1><p className="truncate text-xs text-zinc-400">{user.role === 'admin' ? 'Administrador' : 'Vendedor'} · {user.name}</p></div></div> }
function ThemeButton({ dark, setDark, compact = false }) { const Icon = dark ? Moon : Sun; return <button onClick={() => setDark(!dark)} className={`btn-secondary flex items-center justify-center gap-2 ${compact ? 'px-3 py-2' : 'w-full'}`}><Icon size={16} />{compact ? '' : dark ? 'Modo oscuro' : 'Modo claro'}</button> }

function InstallAppButton({ compact = true }) {
  const [installEvent, setInstallEvent] = useState(null)
  const [installed, setInstalled] = useState(window.matchMedia?.('(display-mode: standalone)').matches)
  useEffect(() => { const handlePrompt = (event) => { event.preventDefault(); setInstallEvent(event) }; const handleInstalled = () => setInstalled(true); window.addEventListener('beforeinstallprompt', handlePrompt); window.addEventListener('appinstalled', handleInstalled); return () => { window.removeEventListener('beforeinstallprompt', handlePrompt); window.removeEventListener('appinstalled', handleInstalled) } }, [])
  const install = async () => { if (!installEvent) return; installEvent.prompt(); await installEvent.userChoice; setInstallEvent(null) }
  if (installed) return <p className="rounded-2xl border border-green-500/30 bg-green-500/10 p-3 text-xs text-green-200">App instalada en este dispositivo.</p>
  return <div id={compact ? 'install' : undefined} className={`${compact ? 'rounded-2xl p-3' : 'rounded-3xl p-4'} border border-beer-gold/25 bg-beer-gold/10 text-sm text-zinc-200`}><p className="flex items-center gap-2 font-bold text-beer-amber"><Smartphone size={16} /> Instalar en Android</p>{installEvent ? <button className="btn-primary mt-3 flex w-full items-center justify-center gap-2 py-2" onClick={install}><Download size={16} /> Instalar app</button> : <p className="mt-2 text-xs text-zinc-300">En Chrome Android: menú ⋮ y “Instalar app”.</p>}</div>
}

const adminTabs = [['dashboard', BarChart3, 'Dashboard'], ['cash', ReceiptText, 'Caja'], ['expenses', WalletCards, 'Gastos'], ['inventory', Boxes, 'Inventario'], ['sales', FileText, 'Reportes'], ['settings', Settings, 'Negocio'], ['users', Users, 'Vendedores']]

function AdminApp({ request, token }) {
  const [tab, setTab] = useState('dashboard')
  const [products, setProducts] = useState([])
  const [sales, setSales] = useState([])
  const [users, setUsers] = useState([])
  const [summary, setSummary] = useState(null)
  const [message, setMessage] = useState('')
  const refresh = async () => { const [productData, saleData, userData, summaryData] = await Promise.all([request('/api/products'), request('/api/sales'), request('/api/users'), request('/api/reports/summary')]); setProducts(productData.products); setSales(saleData.sales); setUsers(userData.users); setSummary(summaryData) }
  useEffect(() => { refresh().catch((err) => setMessage(err.message)) }, [])
  return <div className="lg:grid lg:grid-cols-[13rem_1fr] lg:gap-6"><nav className="hidden h-fit rounded-3xl border border-beer-gold/20 bg-white/5 p-3 lg:sticky lg:top-8 lg:block">{adminTabs.map(([id, Icon, label]) => <NavButton key={id} id={id} Icon={Icon} label={label} active={tab === id} onClick={() => setTab(id)} />)}</nav><div className="min-w-0 space-y-6"><MobileTitle title={adminTabs.find(([id]) => id === tab)?.[2] || 'Dashboard'} /><InstallAppButton />{message && <p className="rounded-xl border border-beer-gold/30 bg-beer-gold/10 p-3 text-sm text-beer-amber">{message}</p>}{tab === 'dashboard' && <Dashboard summary={summary} products={products} />}{tab === 'cash' && <CashCut summary={summary} />}{tab === 'expenses' && <ExpensesPanel summary={summary} request={request} refresh={refresh} />}{tab === 'inventory' && <Inventory products={products} request={request} refresh={refresh} />}{tab === 'sales' && <SalesHistory sales={sales} summary={summary} token={token} />}{tab === 'settings' && <SettingsPanel summary={summary} request={request} refresh={refresh} />}{tab === 'users' && <UsersPanel users={users} request={request} refresh={refresh} />}</div><MobileBottomNav items={adminTabs.slice(0, 4)} active={tab} onChange={setTab} /></div>
}

function NavButton({ id, Icon, label, active, onClick }) { return <button onClick={onClick} className={`mb-2 flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-bold transition ${active ? 'bg-beer-gold text-beer-black' : 'text-zinc-300 hover:bg-white/10'}`}><Icon size={18} />{label}</button> }
function MobileBottomNav({ items, active, onChange }) { return <nav className="fixed inset-x-3 bottom-3 z-40 grid grid-cols-4 gap-1 rounded-3xl border border-beer-gold/20 bg-zinc-950/95 p-2 shadow-2xl backdrop-blur lg:hidden" style={{ paddingBottom: 'max(0.5rem, env(safe-area-inset-bottom))' }}>{items.map(([id, Icon, label]) => <button key={id} onClick={() => onChange(id)} className={`rounded-2xl px-2 py-2 text-[0.68rem] font-bold ${active === id ? 'bg-beer-gold text-beer-black' : 'text-zinc-300'}`}><Icon className="mx-auto mb-1" size={19} />{label}</button>)}</nav> }
function MobileTitle({ title }) { return <div className="lg:hidden"><p className="text-sm text-beer-amber">Modo aplicación móvil</p><h2 className="text-2xl font-black">{title}</h2></div> }

function Dashboard({ summary, products }) {
  const totals = summary?.totals || {}
  const cards = [['Ganancia diaria', totals.daily?.net_profit || 0, TrendingUp], ['Ganancia semanal', totals.weekly?.net_profit || 0, WalletCards], ['Ganancia mensual', totals.monthly?.net_profit || 0, BarChart3], ['Ganancia anual', totals.annual?.net_profit || 0, Beer], ['Ventas hoy', totals.daily?.sales || 0, ReceiptText], ['Unidades stock', summary?.inventory?.units || 0, Boxes], ['Productos', summary?.inventory?.products || products.length, Beer], ['Alertas stock', summary?.low_stock?.length || 0, Info]]
  return <section className="space-y-6"><div className="rounded-3xl border border-beer-gold/20 bg-[radial-gradient(circle_at_top_right,_rgba(247,201,72,0.16),_transparent_35%),rgba(255,255,255,0.04)] p-6"><h2 className="text-3xl font-black">Dashboard profesional</h2><p className="mt-2 text-zinc-400">KPIs reales de ventas, ganancias, caja, inventario y desempeño comercial.</p></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([label, value, Icon]) => <MetricCard key={label} label={label} value={label.includes('stock') || label === 'Productos' || label.includes('Alertas') ? value : currency.format(value)} Icon={Icon} />)}</div><div className="grid gap-6 xl:grid-cols-2"><Panel title="Ventas y ganancias diarias"><BarChart data={summary?.charts?.daily || []} valueKey="sales" secondKey="profit" /></Panel><Panel title="Tendencia mensual"><BarChart data={summary?.charts?.monthly || []} valueKey="sales" secondKey="profit" /></Panel></div><div className="grid gap-6 xl:grid-cols-3"><Panel title="Alertas de stock bajo">{summary?.low_stock?.length ? summary.low_stock.map((p) => <ListRow key={p.id} left={p.name} right={`${p.stock}/${p.min_stock} uds`} danger />) : <Empty text="Sin alertas de stock bajo" />}</Panel><Panel title="Ranking productos más vendidos">{summary?.top_products?.length ? summary.top_products.map((p, i) => <ListRow key={p.product_name} left={`${i + 1}. ${p.product_name}`} right={`${p.quantity} uds`} />) : <Empty text="Aún no hay ventas" />}</Panel><Panel title="Ranking vendedores">{summary?.by_seller?.length ? summary.by_seller.map((seller, i) => <ListRow key={seller.seller_name} left={`${i + 1}. ${seller.seller_name}`} right={currency.format(seller.total)} />) : <Empty text="Aún no hay ventas por vendedor" />}</Panel></div></section>
}

function BarChart({ data, valueKey, secondKey }) { const max = Math.max(...data.map((i) => i[valueKey] || 0), 1); return <div className="flex h-64 items-end gap-2 overflow-x-auto rounded-2xl bg-black/20 p-4">{data.map((item) => <div key={item.label} className="flex min-w-12 flex-1 flex-col items-center gap-2"><div className="flex h-44 w-full items-end gap-1"><div className="w-full rounded-t-xl bg-beer-gold" style={{ height: `${Math.max(6, (item[valueKey] / max) * 100)}%` }} /><div className="w-full rounded-t-xl bg-yellow-200/70" style={{ height: `${Math.max(6, ((item[secondKey] || 0) / max) * 100)}%` }} /></div><span className="text-[0.65rem] text-zinc-400">{item.label.slice(-5)}</span></div>)}</div> }
function MetricCard({ label, value, Icon }) { return <div className="glass-panel rounded-3xl p-5"><div className="flex items-center justify-between"><p className="text-sm text-zinc-400">{label}</p><Icon className="text-beer-gold" /></div><p className="mt-4 text-2xl font-black sm:text-3xl">{value}</p></div> }
function Panel({ title, children, className = '' }) { return <section className={`glass-panel rounded-3xl p-4 sm:p-5 ${className}`}><h3 className="mb-4 text-lg font-black text-beer-amber">{title}</h3><div className="space-y-3">{children}</div></section> }
function ListRow({ left, right, danger }) { return <div className={`flex items-center justify-between gap-3 rounded-2xl p-3 text-sm ${danger ? 'bg-red-500/10 text-red-200' : 'bg-white/5 text-zinc-200'}`}><span className="min-w-0 truncate">{left}</span><b className="shrink-0">{right}</b></div> }
function Empty({ text }) { return <p className="rounded-2xl bg-white/5 p-4 text-sm text-zinc-400">{text}</p> }

function CashCut({ summary }) { const cash = summary?.cash_cut || {}; return <div className="grid gap-6 xl:grid-cols-[1fr_1fr]"><Panel title="Corte de caja diario"><ListRow left="Fondo inicial" right={currency.format(cash.opening_cash || 0)} /><ListRow left="Ventas cobradas" right={currency.format(cash.sales || 0)} /><ListRow left="Gastos del día" right={currency.format(cash.expenses || 0)} danger /><ListRow left="Efectivo esperado" right={currency.format(cash.expected_cash || 0)} /><ListRow left="Ganancia neta diaria" right={currency.format(cash.net_profit || 0)} /></Panel><Panel title="Checklist de cierre"><Empty text="1. Contar caja física · 2. Comparar con efectivo esperado · 3. Registrar gastos faltantes · 4. Exportar reporte PDF/Excel" /></Panel></div> }

function ExpensesPanel({ summary, request, refresh }) { const [form, setForm] = useState({ concept: '', category: 'Operación', amount: '' }); const save = async (e) => { e.preventDefault(); await request('/api/expenses', { method: 'POST', body: JSON.stringify(form) }); setForm({ concept: '', category: 'Operación', amount: '' }); refresh() }; const remove = async (id) => { await request(`/api/expenses/${id}`, { method: 'DELETE' }); refresh() }; return <div className="grid gap-6 xl:grid-cols-[0.8fr_1.4fr]"><form onSubmit={save} className="glass-panel h-fit rounded-3xl p-5"><h2 className="text-xl font-black text-beer-amber">Registrar gasto</h2><input className="input mt-4" placeholder="Concepto" value={form.concept} onChange={(e) => setForm({ ...form, concept: e.target.value })} required /><input className="input mt-4" placeholder="Categoría" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} required /><input className="input mt-4" type="number" step="0.01" placeholder="Monto" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required /><button className="btn-primary mt-5 w-full"><Plus className="inline" size={16} /> Guardar gasto</button></form><Panel title="Últimos gastos">{summary?.expenses?.length ? summary.expenses.map((e) => <div key={e.id} className="flex items-center justify-between gap-3 rounded-2xl bg-white/5 p-3 text-sm"><div><b>{e.concept}</b><p className="text-xs text-zinc-400">{e.category} · {dateFmt.format(new Date(e.created_at))}</p></div><div className="flex items-center gap-3"><b className="text-red-200">{currency.format(e.amount)}</b><button onClick={() => remove(e.id)} className="text-red-300"><Trash2 size={16} /></button></div></div>) : <Empty text="Sin gastos" />}</Panel></div> }

function Inventory({ products, request, refresh }) { const blank = { name: '', description: '', price: 0, cost_price: 0, stock: 0, min_stock: 5 }; const [editing, setEditing] = useState(blank); const [isNew, setIsNew] = useState(true); const [query, setQuery] = useState(''); const filtered = products.filter((p) => p.name.toLowerCase().includes(query.toLowerCase())); const save = async (event) => { event.preventDefault(); await request(isNew ? '/api/products' : `/api/products/${editing.id}`, { method: isNew ? 'POST' : 'PUT', body: JSON.stringify(editing) }); setEditing(blank); setIsNew(true); refresh() }; const remove = async (id) => { if (confirm('¿Eliminar producto?')) { await request(`/api/products/${id}`, { method: 'DELETE' }); refresh() } }; const upload = async (id, file) => { const data = new FormData(); data.append('image', file); await request(`/api/products/${id}/image`, { method: 'POST', body: data }); refresh() }; return <div className="grid gap-6 xl:grid-cols-[0.85fr_1.6fr]"><form onSubmit={save} className="glass-panel h-fit rounded-3xl p-4 sm:p-5 xl:sticky xl:top-8"><h2 className="text-xl font-black text-beer-amber">{isNew ? 'Agregar producto' : 'Editar producto'}</h2><div className="grid gap-x-3 sm:grid-cols-2 xl:grid-cols-1">{['name', 'description', 'price', 'cost_price', 'stock', 'min_stock'].map((field) => <label key={field} className="mt-4 block text-sm text-zinc-300">{labels[field]}<input className="input mt-2" type={['price','cost_price','stock','min_stock'].includes(field) ? 'number' : 'text'} step="0.01" value={editing[field]} onChange={(e) => setEditing({ ...editing, [field]: e.target.value })} required={field === 'name'} /></label>)}</div><div className="mt-5 flex gap-3"><button className="btn-primary flex-1">Guardar</button><button type="button" className="btn-secondary" onClick={() => { setEditing(blank); setIsNew(true) }}>Nuevo</button></div></form><section className="space-y-4"><div className="relative"><Search className="absolute left-4 top-3.5 text-zinc-500" size={18} /><input className="input pl-11" placeholder="Buscar producto..." value={query} onChange={(e) => setQuery(e.target.value)} /></div><div className="grid gap-4 md:grid-cols-2">{filtered.map((product) => <ProductAdminCard key={product.id} product={product} onEdit={() => { setEditing(product); setIsNew(false) }} onDelete={() => remove(product.id)} onUpload={(file) => upload(product.id, file)} />)}</div></section></div> }
const labels = { name: 'Nombre', description: 'Descripción', price: 'Precio venta', cost_price: 'Costo', stock: 'Stock', min_stock: 'Stock mínimo' }
function ProductAdminCard({ product, onEdit, onDelete, onUpload }) { return <article className="glass-panel overflow-hidden rounded-3xl"><img className="h-36 w-full object-cover sm:h-44" loading="lazy" src={apiPath(product.image_url)} alt={product.name} /><div className="space-y-3 p-4"><div className="flex justify-between gap-3"><div className="min-w-0"><h3 className="truncate font-black">{product.name}</h3><p className="line-clamp-2 text-sm text-zinc-400">{product.description}</p></div><b className="shrink-0 text-beer-amber">{currency.format(product.price)}</b></div><div className="flex flex-wrap items-center justify-between gap-2 text-sm"><span>Stock: <b className={product.stock <= product.min_stock ? 'text-red-300' : 'text-white'}>{product.stock}</b></span><span>Ganancia/u: {currency.format(product.price - product.cost_price)}</span></div><div className="flex flex-wrap gap-2"><button className="btn-secondary py-2" onClick={onEdit}>Editar</button><button className="rounded-xl border border-red-500/40 px-3 py-2 text-sm text-red-200 hover:bg-red-500/10" onClick={onDelete}><Trash2 size={16} /></button><label className="btn-secondary cursor-pointer py-2"><Camera className="inline" size={16} /> Foto<input type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files[0] && onUpload(e.target.files[0])} /></label></div></div></article> }

function SalesHistory({ sales, summary, token }) { const download = (fmt) => { window.open(`${API_URL}/api/reports/export/${fmt}?token=${token}`, '_blank') }; return <div className="grid gap-6 xl:grid-cols-[0.8fr_2fr]"><Panel title="Exportar reportes"><button onClick={() => download('excel')} className="btn-primary flex w-full items-center justify-center gap-2"><FileSpreadsheet size={18} /> Exportar Excel</button><button onClick={() => download('pdf')} className="btn-secondary flex w-full items-center justify-center gap-2"><FileText size={18} /> Exportar PDF</button><ListRow left="Ventas mensuales" right={currency.format(summary?.totals.monthly?.sales || 0)} /><ListRow left="Ganancia mensual" right={currency.format(summary?.totals.monthly?.net_profit || 0)} /><ListRow left="Órdenes" right={summary?.totals.monthly?.orders || 0} /></Panel><Panel title="Historial de ventas">{sales.length ? sales.map((sale) => <div key={sale.id} className="rounded-2xl bg-white/5 p-4"><div className="flex flex-wrap justify-between gap-2"><b>Venta #{sale.id} · {sale.seller_name}</b><span className="text-beer-amber">{currency.format(sale.total)}</span></div><p className="text-xs text-zinc-400">{dateFmt.format(new Date(sale.created_at))} · Ganancia {currency.format(sale.profit)}</p><p className="mt-2 text-sm text-zinc-300">{sale.items.map((i) => `${i.product_name} x${i.quantity}`).join(' · ')}</p></div>) : <Empty text="Sin ventas registradas" />}</Panel></div> }

function SettingsPanel({ summary, request, refresh }) { const [form, setForm] = useState(summary?.settings || {}); useEffect(() => setForm(summary?.settings || {}), [summary]); const save = async (e) => { e.preventDefault(); await request('/api/settings', { method: 'PUT', body: JSON.stringify(form) }); refresh() }; return <form onSubmit={save} className="glass-panel max-w-3xl rounded-3xl p-5"><div className="mb-5 flex items-center gap-3"><img src={apiPath(form.logo_url)} className="h-16 w-16 rounded-2xl" /><div><h2 className="text-2xl font-black text-beer-amber">Configuración del negocio</h2><p className="text-sm text-zinc-400">Datos usados en reportes y operación diaria.</p></div></div>{[['business_name','Nombre del negocio'], ['tax_id','RUC / ID fiscal'], ['address','Dirección'], ['phone','Teléfono'], ['daily_cash_opening','Fondo inicial caja']].map(([key, label]) => <label key={key} className="mt-4 block text-sm text-zinc-300">{label}<input className="input mt-2" value={form[key] || ''} onChange={(e) => setForm({ ...form, [key]: e.target.value })} /></label>)}<button className="btn-primary mt-6">Guardar configuración</button></form> }

function UsersPanel({ users, request, refresh }) { const [form, setForm] = useState({ name: '', username: '', password: '', role: 'seller' }); const submit = async (event) => { event.preventDefault(); await request('/api/users', { method: 'POST', body: JSON.stringify(form) }); setForm({ name: '', username: '', password: '', role: 'seller' }); refresh() }; return <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]"><form onSubmit={submit} className="glass-panel h-fit rounded-3xl p-5"><h2 className="text-xl font-black text-beer-amber">Crear vendedor</h2>{['name','username','password'].map((field) => <input key={field} className="input mt-4" type={field === 'password' ? 'password' : 'text'} placeholder={labelsUser[field]} value={form[field]} onChange={(e) => setForm({ ...form, [field]: e.target.value })} required />)}<select className="input mt-4" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}><option value="seller">Vendedor</option><option value="admin">Administrador</option></select><button className="btn-primary mt-5 w-full"><Plus className="inline" size={16} /> Crear usuario</button></form><Panel title="Usuarios registrados">{users.map((u) => <ListRow key={u.id} left={`${u.name} (${u.username})`} right={u.role === 'admin' ? 'Admin' : 'Vendedor'} />)}</Panel></div> }
const labelsUser = { name: 'Nombre completo', username: 'Usuario', password: 'Contraseña' }

function SellerApp({ request, user }) { const [products, setProducts] = useState([]); const [cart, setCart] = useState([]); const [query, setQuery] = useState(''); const [message, setMessage] = useState(''); const refresh = async () => setProducts((await request('/api/products')).products); useEffect(() => { refresh() }, []); const filtered = products.filter((p) => p.name.toLowerCase().includes(query.toLowerCase())); const total = useMemo(() => cart.reduce((sum, item) => sum + item.price * item.quantity, 0), [cart]); const add = (product) => setCart((current) => { const found = current.find((item) => item.id === product.id); if (found) return current.map((item) => item.id === product.id ? { ...item, quantity: Math.min(item.quantity + 1, product.stock) } : item); return [...current, { ...product, quantity: 1 }] }); const updateQty = (id, quantity) => setCart((current) => current.map((item) => item.id === id ? { ...item, quantity: Math.max(1, Math.min(Number(quantity), item.stock)) } : item)); const sell = async () => { const result = await request('/api/sales', { method: 'POST', body: JSON.stringify({ items: cart.map((item) => ({ product_id: item.id, quantity: item.quantity })) }) }); setCart([]); setMessage(`Venta registrada por ${result.seller}: ${currency.format(result.total)}`); refresh() }; const sellerMenu = [['products', Boxes, 'Productos'], ['cart', ShoppingCart, 'Carrito'], ['install', Download, 'Instalar'], ['info', Info, 'Ayuda']]; return <div className="space-y-5"><MobileTitle title="Venta rápida" /><InstallAppButton /><div className="grid gap-6 xl:grid-cols-[1.45fr_0.8fr]"><section id="products" className="min-w-0 space-y-4"><div className="hidden lg:block"><h2 className="text-3xl font-black">Panel de vendedor</h2><p className="text-zinc-400">Busca productos, selecciona cantidades y cobra desde el carrito.</p></div>{message && <p className="rounded-xl border border-green-500/40 bg-green-500/10 p-3 text-sm text-green-200">{message}</p>}<div className="relative"><Search className="absolute left-4 top-3.5 text-zinc-500" size={18} /><input className="input pl-11" placeholder="Buscar producto..." value={query} onChange={(e) => setQuery(e.target.value)} /></div><div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:gap-4 xl:grid-cols-3">{filtered.map((product) => <SellerProductCard key={product.id} product={product} onAdd={() => add(product)} />)}</div></section><aside id="cart" className="glass-panel h-fit rounded-3xl p-4 sm:p-5 xl:sticky xl:top-8"><h2 className="flex items-center gap-2 text-xl font-black text-beer-amber"><ShoppingCart /> Carrito</h2><p className="mt-1 text-sm text-zinc-400">Vendedor: {user.name}</p><div className="mt-5 space-y-3">{cart.length ? cart.map((item) => <div key={item.id} className="rounded-2xl bg-white/5 p-3"><div className="flex justify-between gap-2"><b>{item.name}</b><button onClick={() => setCart(cart.filter((p) => p.id !== item.id))} className="text-red-300"><Trash2 size={16} /></button></div><div className="mt-3 flex items-center justify-between gap-3"><input className="input w-24 py-2" type="number" min="1" max={item.stock} value={item.quantity} onChange={(e) => updateQty(item.id, e.target.value)} /><span>{currency.format(item.price * item.quantity)}</span></div></div>) : <Empty text="El carrito está vacío" />}</div><div className="mt-5 border-t border-white/10 pt-5"><div className="flex justify-between text-lg"><span>Total a cobrar</span><b className="text-2xl text-beer-amber">{currency.format(total)}</b></div><button className="btn-primary mt-5 w-full" disabled={!cart.length} onClick={sell}>Registrar venta</button></div></aside></div><div className="fixed inset-x-0 bottom-[5.6rem] z-30 px-4 lg:hidden"><a href="#cart" className="mx-auto flex max-w-md items-center justify-between rounded-3xl border border-beer-gold/30 bg-beer-gold px-4 py-3 font-black text-beer-black shadow-2xl"><span>{cart.length} productos</span><span>Cobrar {currency.format(total)}</span></a></div><nav className="fixed inset-x-3 bottom-3 z-40 grid grid-cols-4 gap-1 rounded-3xl border border-beer-gold/20 bg-zinc-950/95 p-2 shadow-2xl backdrop-blur lg:hidden" style={{ paddingBottom: 'max(0.5rem, env(safe-area-inset-bottom))' }}>{sellerMenu.map(([id, Icon, label]) => <a key={id} href={id === 'install' ? '#install' : `#${id}`} className="rounded-2xl px-2 py-2 text-center text-[0.68rem] font-bold text-zinc-300"><Icon className="mx-auto mb-1" size={19} />{label}</a>)}</nav></div> }
function SellerProductCard({ product, onAdd }) { return <article className="glass-panel overflow-hidden rounded-3xl"><img src={apiPath(product.image_url)} alt={product.name} loading="lazy" className="h-28 w-full object-cover sm:h-36" /><div className="p-3 sm:p-4"><div className="min-h-[3rem]"><h3 className="line-clamp-2 font-black leading-tight">{product.name}</h3><b className="text-lg text-beer-amber">{currency.format(product.price)}</b></div><p className="mt-1 text-xs text-zinc-400 sm:text-sm">Stock: {product.stock}</p><button className="btn-primary mt-3 w-full py-3 text-base" disabled={product.stock < 1} onClick={onAdd}>+ Agregar</button></div></article> }

createRoot(document.getElementById('root')).render(<App />)

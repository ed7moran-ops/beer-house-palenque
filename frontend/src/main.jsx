import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BarChart3, Beer, Boxes, Camera, Download, Home, Info, LogOut, Plus, Search, ShoppingCart, Smartphone, Trash2, Users, WalletCards } from 'lucide-react'
import './index.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'
const currency = new Intl.NumberFormat('es-EC', { style: 'currency', currency: 'USD' })

function apiPath(path) {
  if (!path) return ''
  return path.startsWith('data:') || path.startsWith('http') ? path : `${API_URL}${path}`
}

function App() {
  const [token, setToken] = useState(localStorage.getItem('bhp_token'))
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('bhp_user') || 'null'))
  const [error, setError] = useState('')

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => navigator.serviceWorker.register('/service-worker.js'))
    }
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
    <Shell user={user} logout={logout}>
      {user.role === 'admin' ? <AdminApp request={request} /> : <SellerApp request={request} user={user} />}
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
      const response = await fetch(`${API_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.message)
      onLogin(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(247,201,72,0.24),_transparent_32%),#0b0b0f] px-4 py-8 text-white sm:py-10">
      <section className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-6xl items-center gap-8 lg:grid-cols-[1.2fr_0.8fr]">
        <div>
          <span className="badge">PWA · Inventario · Ventas · Reportes</span>
          <h1 className="mt-6 text-4xl font-black tracking-tight sm:text-5xl md:text-6xl">Beer House Palenque</h1>
          <p className="mt-5 max-w-2xl text-base text-zinc-300 sm:text-lg">Aplicación web profesional para controlar productos, stock automático, vendedores, ventas y ganancias en tiempo real desde computador o teléfono.</p>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {['Instalable en Android', 'Venta rápida móvil', 'Dashboard amplio PC'].map((item) => <div key={item} className="glass-panel rounded-2xl p-4 text-sm text-zinc-200">{item}</div>)}
          </div>
        </div>
        <form onSubmit={submit} className="glass-panel rounded-3xl p-5 sm:p-6 md:p-8">
          <div className="mb-8 flex items-center gap-3">
            <div className="gold-gradient grid h-12 w-12 place-items-center rounded-2xl text-beer-black"><Beer /></div>
            <div><h2 className="text-2xl font-black">Iniciar sesión</h2><p className="text-sm text-zinc-400">Usa las credenciales de prueba</p></div>
          </div>
          {error && <p className="mb-4 rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
          <label className="text-sm font-semibold text-zinc-300">Usuario</label>
          <input className="input mt-2" autoComplete="username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
          <label className="mt-4 block text-sm font-semibold text-zinc-300">Contraseña</label>
          <input className="input mt-2" autoComplete="current-password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <button className="btn-primary mt-6 w-full" disabled={loading}>{loading ? 'Ingresando...' : 'Entrar al sistema'}</button>
          <div className="mt-5 rounded-2xl bg-white/5 p-4 text-sm text-zinc-300">
            <p><b>Admin:</b> admin / admin123</p>
            <p><b>Vendedor:</b> vendedor / vendedor123</p>
          </div>
        </form>
      </section>
    </main>
  )
}

function Shell({ user, logout, children }) {
  return (
    <div className="min-h-screen bg-beer-black text-white lg:grid lg:grid-cols-[17rem_1fr]">
      <aside className="desktop-sidebar hidden min-h-screen border-r border-beer-gold/20 bg-zinc-950/80 p-5 lg:flex lg:flex-col">
        <BrandBlock user={user} />
        <div className="mt-8 space-y-3 rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-zinc-300">
          <p className="flex items-center gap-2 font-bold text-beer-amber"><Home size={16} /> Menú lateral PC</p>
          <p>Usa el panel central con ancho completo para dashboard, inventario, ventas y reportes.</p>
        </div>
        <div className="mt-auto space-y-3">
          <InstallAppButton compact={false} />
          <button onClick={logout} className="btn-secondary flex w-full items-center justify-center gap-2"><LogOut size={16} /> Salir</button>
        </div>
      </aside>
      <div className="min-w-0">
        <header className="sticky top-0 z-30 border-b border-beer-gold/20 bg-beer-black/95 backdrop-blur lg:hidden">
          <div className="flex items-center justify-between gap-3 px-4 py-3">
            <BrandBlock user={user} small />
            <button onClick={logout} className="btn-secondary flex items-center gap-2 px-3 py-2"><LogOut size={16} /><span className="sr-only sm:not-sr-only">Salir</span></button>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-5 pb-32 sm:px-6 lg:px-8 lg:py-8 lg:pb-8">{children}</main>
      </div>
    </div>
  )
}

function BrandBlock({ user, small = false }) {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <div className={`${small ? 'h-10 w-10 rounded-xl' : 'h-12 w-12 rounded-2xl'} gold-gradient grid shrink-0 place-items-center text-beer-black`}><Beer /></div>
      <div className="min-w-0">
        <h1 className={`${small ? 'text-sm' : 'text-lg'} truncate font-black`}>Beer House Palenque</h1>
        <p className="truncate text-xs text-zinc-400">{user.role === 'admin' ? 'Administrador' : 'Vendedor'} · {user.name}</p>
      </div>
    </div>
  )
}

function InstallAppButton({ compact = true }) {
  const [installEvent, setInstallEvent] = useState(null)
  const [installed, setInstalled] = useState(window.matchMedia?.('(display-mode: standalone)').matches)

  useEffect(() => {
    const handlePrompt = (event) => {
      event.preventDefault()
      setInstallEvent(event)
    }
    const handleInstalled = () => setInstalled(true)
    window.addEventListener('beforeinstallprompt', handlePrompt)
    window.addEventListener('appinstalled', handleInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', handlePrompt)
      window.removeEventListener('appinstalled', handleInstalled)
    }
  }, [])

  const install = async () => {
    if (!installEvent) return
    installEvent.prompt()
    await installEvent.userChoice
    setInstallEvent(null)
  }

  if (installed) return <p className="rounded-2xl border border-green-500/30 bg-green-500/10 p-3 text-xs text-green-200">App instalada en este dispositivo.</p>

  return (
    <div id={compact ? 'install' : undefined} className={`${compact ? 'rounded-2xl p-3' : 'rounded-3xl p-4'} border border-beer-gold/25 bg-beer-gold/10 text-sm text-zinc-200`}>
      <p className="flex items-center gap-2 font-bold text-beer-amber"><Smartphone size={16} /> Instalar en Android</p>
      {installEvent ? (
        <button className="btn-primary mt-3 flex w-full items-center justify-center gap-2 py-2" onClick={install}><Download size={16} /> Instalar app</button>
      ) : (
        <p className="mt-2 text-xs text-zinc-300">En Chrome Android: abre el menú ⋮ y toca “Instalar app” o “Agregar a pantalla principal”.</p>
      )}
    </div>
  )
}

const adminTabs = [
  ['dashboard', BarChart3, 'Dashboard'],
  ['inventory', Boxes, 'Inventario'],
  ['sales', WalletCards, 'Ventas'],
  ['users', Users, 'Vendedores']
]

function AdminApp({ request }) {
  const [tab, setTab] = useState('dashboard')
  const [products, setProducts] = useState([])
  const [sales, setSales] = useState([])
  const [users, setUsers] = useState([])
  const [summary, setSummary] = useState(null)
  const [message, setMessage] = useState('')

  const refresh = async () => {
    const [productData, saleData, userData, summaryData] = await Promise.all([
      request('/api/products'), request('/api/sales'), request('/api/users'), request('/api/reports/summary')
    ])
    setProducts(productData.products)
    setSales(saleData.sales)
    setUsers(userData.users)
    setSummary(summaryData)
  }

  useEffect(() => { refresh().catch((err) => setMessage(err.message)) }, [])

  return (
    <div className="lg:grid lg:grid-cols-[13rem_1fr] lg:gap-6">
      <nav className="hidden h-fit rounded-3xl border border-beer-gold/20 bg-white/5 p-3 lg:sticky lg:top-8 lg:block">
        {adminTabs.map(([id, Icon, label]) => <NavButton key={id} id={id} Icon={Icon} label={label} active={tab === id} onClick={() => setTab(id)} />)}
      </nav>
      <div className="min-w-0 space-y-6">
        <MobileTitle title={adminTabs.find(([id]) => id === tab)?.[2] || 'Dashboard'} />
        <InstallAppButton />
        {message && <p className="rounded-xl border border-beer-gold/30 bg-beer-gold/10 p-3 text-sm text-beer-amber">{message}</p>}
        {tab === 'dashboard' && <Dashboard summary={summary} products={products} />}
        {tab === 'inventory' && <Inventory products={products} request={request} refresh={refresh} />}
        {tab === 'sales' && <SalesHistory sales={sales} summary={summary} />}
        {tab === 'users' && <UsersPanel users={users} request={request} refresh={refresh} />}
      </div>
      <MobileBottomNav items={adminTabs} active={tab} onChange={setTab} />
    </div>
  )
}

function NavButton({ id, Icon, label, active, onClick }) {
  return <button onClick={onClick} className={`mb-2 flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-bold transition ${active ? 'bg-beer-gold text-beer-black' : 'text-zinc-300 hover:bg-white/10'}`}><Icon size={18} />{label}</button>
}

function MobileBottomNav({ items, active, onChange }) {
  return (
    <nav className="fixed inset-x-3 bottom-3 z-40 grid grid-cols-4 gap-1 rounded-3xl border border-beer-gold/20 bg-zinc-950/95 p-2 shadow-2xl backdrop-blur lg:hidden" style={{ paddingBottom: 'max(0.5rem, env(safe-area-inset-bottom))' }}>
      {items.map(([id, Icon, label]) => <button key={id} onClick={() => onChange(id)} className={`rounded-2xl px-2 py-2 text-[0.68rem] font-bold ${active === id ? 'bg-beer-gold text-beer-black' : 'text-zinc-300'}`}><Icon className="mx-auto mb-1" size={19} />{label}</button>)}
    </nav>
  )
}

function MobileTitle({ title }) {
  return <div className="lg:hidden"><p className="text-sm text-beer-amber">Modo aplicación móvil</p><h2 className="text-2xl font-black">{title}</h2></div>
}

function Dashboard({ summary, products }) {
  const cards = [
    ['Ventas hoy', summary?.totals.daily.sales || 0, BarChart3],
    ['Ganancia semanal', summary?.totals.weekly.profit || 0, WalletCards],
    ['Unidades en stock', summary?.inventory.units || 0, Boxes],
    ['Productos registrados', summary?.inventory.products || products.length, Beer]
  ]
  return (
    <section className="space-y-6">
      <div className="hidden rounded-3xl border border-beer-gold/20 bg-[radial-gradient(circle_at_top_right,_rgba(247,201,72,0.16),_transparent_35%),rgba(255,255,255,0.04)] p-6 lg:block">
        <h2 className="text-3xl font-black">Dashboard administrativo amplio</h2>
        <p className="mt-2 text-zinc-400">Vista optimizada para computador con indicadores, reportes y control de operación.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([label, value, Icon]) => <MetricCard key={label} label={label} value={label.includes('stock') || label.includes('registrados') ? value : currency.format(value)} Icon={Icon} />)}</div>
      <div className="grid gap-6 xl:grid-cols-3">
        <Panel title="Stock bajo" className="xl:col-span-1">{summary?.low_stock.length ? summary.low_stock.map((p) => <ListRow key={p.id} left={p.name} right={`${p.stock} uds`} danger />) : <Empty text="Sin alertas de stock bajo" />}</Panel>
        <Panel title="Productos más vendidos">{summary?.top_products.length ? summary.top_products.map((p) => <ListRow key={p.product_name} left={p.product_name} right={`${p.quantity} uds`} />) : <Empty text="Aún no hay ventas" />}</Panel>
        <Panel title="Ventas por vendedor">{summary?.by_seller.length ? summary.by_seller.map((seller) => <ListRow key={seller.seller_name} left={seller.seller_name} right={currency.format(seller.total)} />) : <Empty text="Aún no hay ventas por vendedor" />}</Panel>
      </div>
    </section>
  )
}

function MetricCard({ label, value, Icon }) {
  return <div className="glass-panel rounded-3xl p-5"><div className="flex items-center justify-between"><p className="text-sm text-zinc-400">{label}</p><Icon className="text-beer-gold" /></div><p className="mt-4 text-2xl font-black sm:text-3xl">{value}</p></div>
}

function Panel({ title, children, className = '' }) {
  return <section className={`glass-panel rounded-3xl p-4 sm:p-5 ${className}`}><h3 className="mb-4 text-lg font-black text-beer-amber">{title}</h3><div className="space-y-3">{children}</div></section>
}

function ListRow({ left, right, danger }) {
  return <div className={`flex items-center justify-between gap-3 rounded-2xl p-3 text-sm ${danger ? 'bg-red-500/10 text-red-200' : 'bg-white/5 text-zinc-200'}`}><span className="min-w-0 truncate">{left}</span><b className="shrink-0">{right}</b></div>
}

function Empty({ text }) { return <p className="rounded-2xl bg-white/5 p-4 text-sm text-zinc-400">{text}</p> }

function Inventory({ products, request, refresh }) {
  const blank = { name: '', description: '', price: 0, cost_price: 0, stock: 0, min_stock: 5 }
  const [editing, setEditing] = useState(blank)
  const [isNew, setIsNew] = useState(true)
  const [query, setQuery] = useState('')
  const filtered = products.filter((p) => p.name.toLowerCase().includes(query.toLowerCase()))

  const save = async (event) => {
    event.preventDefault()
    await request(isNew ? '/api/products' : `/api/products/${editing.id}`, { method: isNew ? 'POST' : 'PUT', body: JSON.stringify(editing) })
    setEditing(blank)
    setIsNew(true)
    refresh()
  }
  const remove = async (id) => { if (confirm('¿Eliminar producto?')) { await request(`/api/products/${id}`, { method: 'DELETE' }); refresh() } }
  const upload = async (id, file) => { const data = new FormData(); data.append('image', file); await request(`/api/products/${id}/image`, { method: 'POST', body: data }); refresh() }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.85fr_1.6fr]">
      <form onSubmit={save} className="glass-panel h-fit rounded-3xl p-4 sm:p-5 xl:sticky xl:top-8">
        <h2 className="text-xl font-black text-beer-amber">{isNew ? 'Agregar producto' : 'Editar producto'}</h2>
        <div className="grid gap-x-3 sm:grid-cols-2 xl:grid-cols-1">
          {['name', 'description', 'price', 'cost_price', 'stock', 'min_stock'].map((field) => <label key={field} className="mt-4 block text-sm text-zinc-300">{labels[field]}<input className="input mt-2" type={['price','cost_price','stock','min_stock'].includes(field) ? 'number' : 'text'} step="0.01" value={editing[field]} onChange={(e) => setEditing({ ...editing, [field]: e.target.value })} required={field === 'name'} /></label>)}
        </div>
        <div className="mt-5 flex gap-3"><button className="btn-primary flex-1">Guardar</button><button type="button" className="btn-secondary" onClick={() => { setEditing(blank); setIsNew(true) }}>Nuevo</button></div>
      </form>
      <section className="space-y-4">
        <div className="relative"><Search className="absolute left-4 top-3.5 text-zinc-500" size={18} /><input className="input pl-11" placeholder="Buscar cerveza..." value={query} onChange={(e) => setQuery(e.target.value)} /></div>
        <div className="grid gap-4 md:grid-cols-2">{filtered.map((product) => <ProductAdminCard key={product.id} product={product} onEdit={() => { setEditing(product); setIsNew(false) }} onDelete={() => remove(product.id)} onUpload={(file) => upload(product.id, file)} />)}</div>
      </section>
    </div>
  )
}

const labels = { name: 'Nombre', description: 'Descripción', price: 'Precio venta', cost_price: 'Costo', stock: 'Stock', min_stock: 'Stock mínimo' }

function ProductAdminCard({ product, onEdit, onDelete, onUpload }) {
  return <article className="glass-panel overflow-hidden rounded-3xl"><img className="h-36 w-full object-cover sm:h-44" loading="lazy" src={apiPath(product.image_url)} alt={product.name} /><div className="space-y-3 p-4"><div className="flex justify-between gap-3"><div className="min-w-0"><h3 className="truncate font-black">{product.name}</h3><p className="line-clamp-2 text-sm text-zinc-400">{product.description}</p></div><b className="shrink-0 text-beer-amber">{currency.format(product.price)}</b></div><div className="flex flex-wrap items-center justify-between gap-2 text-sm"><span>Stock: <b className={product.stock <= product.min_stock ? 'text-red-300' : 'text-white'}>{product.stock}</b></span><span>Ganancia/u: {currency.format(product.price - product.cost_price)}</span></div><div className="flex flex-wrap gap-2"><button className="btn-secondary py-2" onClick={onEdit}>Editar</button><button className="rounded-xl border border-red-500/40 px-3 py-2 text-sm text-red-200 hover:bg-red-500/10" onClick={onDelete}><Trash2 size={16} /></button><label className="btn-secondary cursor-pointer py-2"><Camera className="inline" size={16} /> Foto<input type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files[0] && onUpload(e.target.files[0])} /></label></div></div></article>
}

function SalesHistory({ sales, summary }) {
  return <div className="grid gap-6 xl:grid-cols-[0.8fr_2fr]"><Panel title="Resumen mensual"><ListRow left="Ventas" right={currency.format(summary?.totals.monthly.sales || 0)} /><ListRow left="Ganancias" right={currency.format(summary?.totals.monthly.profit || 0)} /><ListRow left="Órdenes" right={summary?.totals.monthly.orders || 0} /></Panel><Panel title="Historial de ventas">{sales.length ? sales.map((sale) => <div key={sale.id} className="rounded-2xl bg-white/5 p-4"><div className="flex flex-wrap justify-between gap-2"><b>Venta #{sale.id} · {sale.seller_name}</b><span className="text-beer-amber">{currency.format(sale.total)}</span></div><p className="text-xs text-zinc-400">{new Date(sale.created_at).toLocaleString()}</p><p className="mt-2 text-sm text-zinc-300">{sale.items.map((i) => `${i.product_name} x${i.quantity}`).join(' · ')}</p></div>) : <Empty text="Sin ventas registradas" />}</Panel></div>
}

function UsersPanel({ users, request, refresh }) {
  const [form, setForm] = useState({ name: '', username: '', password: '', role: 'seller' })
  const submit = async (event) => { event.preventDefault(); await request('/api/users', { method: 'POST', body: JSON.stringify(form) }); setForm({ name: '', username: '', password: '', role: 'seller' }); refresh() }
  return <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]"><form onSubmit={submit} className="glass-panel h-fit rounded-3xl p-5"><h2 className="text-xl font-black text-beer-amber">Crear vendedor</h2>{['name','username','password'].map((field) => <input key={field} className="input mt-4" type={field === 'password' ? 'password' : 'text'} placeholder={labelsUser[field]} value={form[field]} onChange={(e) => setForm({ ...form, [field]: e.target.value })} required />)}<select className="input mt-4" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}><option value="seller">Vendedor</option><option value="admin">Administrador</option></select><button className="btn-primary mt-5 w-full"><Plus className="inline" size={16} /> Crear usuario</button></form><Panel title="Usuarios registrados">{users.map((u) => <ListRow key={u.id} left={`${u.name} (${u.username})`} right={u.role === 'admin' ? 'Admin' : 'Vendedor'} />)}</Panel></div>
}
const labelsUser = { name: 'Nombre completo', username: 'Usuario', password: 'Contraseña' }

function SellerApp({ request, user }) {
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [query, setQuery] = useState('')
  const [message, setMessage] = useState('')
  const refresh = async () => setProducts((await request('/api/products')).products)
  useEffect(() => { refresh() }, [])
  const filtered = products.filter((p) => p.name.toLowerCase().includes(query.toLowerCase()))
  const total = useMemo(() => cart.reduce((sum, item) => sum + item.price * item.quantity, 0), [cart])
  const add = (product) => setCart((current) => { const found = current.find((item) => item.id === product.id); if (found) return current.map((item) => item.id === product.id ? { ...item, quantity: Math.min(item.quantity + 1, product.stock) } : item); return [...current, { ...product, quantity: 1 }] })
  const updateQty = (id, quantity) => setCart((current) => current.map((item) => item.id === id ? { ...item, quantity: Math.max(1, Math.min(Number(quantity), item.stock)) } : item))
  const sell = async () => { const result = await request('/api/sales', { method: 'POST', body: JSON.stringify({ items: cart.map((item) => ({ product_id: item.id, quantity: item.quantity })) }) }); setCart([]); setMessage(`Venta registrada por ${result.seller}: ${currency.format(result.total)}`); refresh() }
  const sellerMenu = [['products', Boxes, 'Productos'], ['cart', ShoppingCart, 'Carrito'], ['install', Download, 'Instalar'], ['info', Info, 'Ayuda']]

  return (
    <div className="space-y-5">
      <MobileTitle title="Venta rápida" />
      <InstallAppButton />
      <div className="grid gap-6 xl:grid-cols-[1.45fr_0.8fr]">
        <section id="products" className="min-w-0 space-y-4">
          <div className="hidden lg:block"><h2 className="text-3xl font-black">Panel de vendedor</h2><p className="text-zinc-400">Busca productos, selecciona cantidades y cobra desde el carrito. Los precios son solo lectura.</p></div>
          {message && <p className="rounded-xl border border-green-500/40 bg-green-500/10 p-3 text-sm text-green-200">{message}</p>}
          <div className="relative"><Search className="absolute left-4 top-3.5 text-zinc-500" size={18} /><input className="input pl-11" placeholder="Buscar producto..." value={query} onChange={(e) => setQuery(e.target.value)} /></div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:gap-4 xl:grid-cols-3">{filtered.map((product) => <SellerProductCard key={product.id} product={product} onAdd={() => add(product)} />)}</div>
        </section>
        <aside id="cart" className="glass-panel h-fit rounded-3xl p-4 sm:p-5 xl:sticky xl:top-8">
          <h2 className="flex items-center gap-2 text-xl font-black text-beer-amber"><ShoppingCart /> Carrito</h2>
          <p className="mt-1 text-sm text-zinc-400">Vendedor: {user.name}</p>
          <div className="mt-5 space-y-3">{cart.length ? cart.map((item) => <div key={item.id} className="rounded-2xl bg-white/5 p-3"><div className="flex justify-between gap-2"><b>{item.name}</b><button onClick={() => setCart(cart.filter((p) => p.id !== item.id))} className="text-red-300"><Trash2 size={16} /></button></div><div className="mt-3 flex items-center justify-between gap-3"><input className="input w-24 py-2" type="number" min="1" max={item.stock} value={item.quantity} onChange={(e) => updateQty(item.id, e.target.value)} /><span>{currency.format(item.price * item.quantity)}</span></div></div>) : <Empty text="El carrito está vacío" />}</div>
          <div className="mt-5 border-t border-white/10 pt-5"><div className="flex justify-between text-lg"><span>Total a cobrar</span><b className="text-2xl text-beer-amber">{currency.format(total)}</b></div><button className="btn-primary mt-5 w-full" disabled={!cart.length} onClick={sell}>Registrar venta</button></div>
        </aside>
      </div>
      <div className="fixed inset-x-0 bottom-[5.6rem] z-30 px-4 lg:hidden">
        <a href="#cart" className="mx-auto flex max-w-md items-center justify-between rounded-3xl border border-beer-gold/30 bg-beer-gold px-4 py-3 font-black text-beer-black shadow-2xl"><span>{cart.length} productos</span><span>Cobrar {currency.format(total)}</span></a>
      </div>
      <nav className="fixed inset-x-3 bottom-3 z-40 grid grid-cols-4 gap-1 rounded-3xl border border-beer-gold/20 bg-zinc-950/95 p-2 shadow-2xl backdrop-blur lg:hidden" style={{ paddingBottom: 'max(0.5rem, env(safe-area-inset-bottom))' }}>
        {sellerMenu.map(([id, Icon, label]) => <a key={id} href={id === 'install' ? '#install' : `#${id}`} className="rounded-2xl px-2 py-2 text-center text-[0.68rem] font-bold text-zinc-300"><Icon className="mx-auto mb-1" size={19} />{label}</a>)}
      </nav>
    </div>
  )
}

function SellerProductCard({ product, onAdd }) {
  return (
    <article className="glass-panel overflow-hidden rounded-3xl">
      <img src={apiPath(product.image_url)} alt={product.name} loading="lazy" className="h-28 w-full object-cover sm:h-36" />
      <div className="p-3 sm:p-4">
        <div className="min-h-[3rem]"><h3 className="line-clamp-2 font-black leading-tight">{product.name}</h3><b className="text-lg text-beer-amber">{currency.format(product.price)}</b></div>
        <p className="mt-1 text-xs text-zinc-400 sm:text-sm">Stock: {product.stock}</p>
        <button className="btn-primary mt-3 w-full py-3 text-base" disabled={product.stock < 1} onClick={onAdd}>+ Agregar</button>
      </div>
    </article>
  )
}

createRoot(document.getElementById('root')).render(<App />)

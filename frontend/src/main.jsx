import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BarChart3, Beer, Boxes, Camera, LogOut, Plus, Search, ShoppingCart, Trash2, Users, WalletCards } from 'lucide-react'
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
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(247,201,72,0.24),_transparent_32%),#0b0b0f] px-4 py-10 text-white">
      <section className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-10 lg:grid-cols-[1.2fr_0.8fr]">
        <div>
          <span className="badge">Inventario · Ventas · Reportes</span>
          <h1 className="mt-6 text-4xl font-black tracking-tight md:text-6xl">Beer House Palenque</h1>
          <p className="mt-5 max-w-2xl text-lg text-zinc-300">Aplicación web profesional para controlar productos, stock automático, vendedores, ventas y ganancias en tiempo real.</p>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {['Administrador completo', 'Vendedor simple', 'SQLite inicial'].map((item) => <div key={item} className="glass-panel rounded-2xl p-4 text-sm text-zinc-200">{item}</div>)}
          </div>
        </div>
        <form onSubmit={submit} className="glass-panel rounded-3xl p-6 md:p-8">
          <div className="mb-8 flex items-center gap-3">
            <div className="gold-gradient grid h-12 w-12 place-items-center rounded-2xl text-beer-black"><Beer /></div>
            <div><h2 className="text-2xl font-black">Iniciar sesión</h2><p className="text-sm text-zinc-400">Usa las credenciales de prueba</p></div>
          </div>
          {error && <p className="mb-4 rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
          <label className="text-sm font-semibold text-zinc-300">Usuario</label>
          <input className="input mt-2" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
          <label className="mt-4 block text-sm font-semibold text-zinc-300">Contraseña</label>
          <input className="input mt-2" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
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
    <div className="min-h-screen bg-beer-black text-white">
      <header className="sticky top-0 z-20 border-b border-beer-gold/20 bg-beer-black/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3"><div className="gold-gradient grid h-11 w-11 place-items-center rounded-2xl text-beer-black"><Beer /></div><div><h1 className="font-black">Beer House Palenque</h1><p className="text-xs text-zinc-400">{user.role === 'admin' ? 'Administrador' : 'Vendedor'} · {user.name}</p></div></div>
          <button onClick={logout} className="btn-secondary flex items-center gap-2"><LogOut size={16} /> Salir</button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
    </div>
  )
}

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
    <div className="space-y-6">
      <nav className="flex flex-wrap gap-3">
        {[['dashboard', BarChart3, 'Dashboard'], ['inventory', Boxes, 'Inventario'], ['sales', WalletCards, 'Ventas'], ['users', Users, 'Vendedores']].map(([id, Icon, label]) => (
          <button key={id} onClick={() => setTab(id)} className={`rounded-2xl px-4 py-3 text-sm font-bold transition ${tab === id ? 'bg-beer-gold text-beer-black' : 'bg-white/5 text-zinc-300 hover:bg-white/10'}`}><Icon className="mr-2 inline" size={17} />{label}</button>
        ))}
      </nav>
      {message && <p className="rounded-xl border border-beer-gold/30 bg-beer-gold/10 p-3 text-sm text-beer-amber">{message}</p>}
      {tab === 'dashboard' && <Dashboard summary={summary} products={products} />}
      {tab === 'inventory' && <Inventory products={products} request={request} refresh={refresh} />}
      {tab === 'sales' && <SalesHistory sales={sales} summary={summary} />}
      {tab === 'users' && <UsersPanel users={users} request={request} refresh={refresh} />}
    </div>
  )
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
      <div className="grid gap-4 md:grid-cols-4">{cards.map(([label, value, Icon]) => <MetricCard key={label} label={label} value={label.includes('stock') || label.includes('registrados') ? value : currency.format(value)} Icon={Icon} />)}</div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Panel title="Stock bajo" className="lg:col-span-1">{summary?.low_stock.length ? summary.low_stock.map((p) => <ListRow key={p.id} left={p.name} right={`${p.stock} uds`} danger />) : <Empty text="Sin alertas de stock bajo" />}</Panel>
        <Panel title="Productos más vendidos">{summary?.top_products.length ? summary.top_products.map((p) => <ListRow key={p.product_name} left={p.product_name} right={`${p.quantity} uds`} />) : <Empty text="Aún no hay ventas" />}</Panel>
        <Panel title="Ventas por vendedor">{summary?.by_seller.map((seller) => <ListRow key={seller.seller_name} left={seller.seller_name} right={currency.format(seller.total)} />)}</Panel>
      </div>
    </section>
  )
}

function MetricCard({ label, value, Icon }) {
  return <div className="glass-panel rounded-3xl p-5"><div className="flex items-center justify-between"><p className="text-sm text-zinc-400">{label}</p><Icon className="text-beer-gold" /></div><p className="mt-4 text-3xl font-black">{value}</p></div>
}

function Panel({ title, children, className = '' }) {
  return <section className={`glass-panel rounded-3xl p-5 ${className}`}><h3 className="mb-4 text-lg font-black text-beer-amber">{title}</h3><div className="space-y-3">{children}</div></section>
}

function ListRow({ left, right, danger }) {
  return <div className={`flex items-center justify-between rounded-2xl p-3 text-sm ${danger ? 'bg-red-500/10 text-red-200' : 'bg-white/5 text-zinc-200'}`}><span>{left}</span><b>{right}</b></div>
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
    setEditing(blank); setIsNew(true); refresh()
  }
  const remove = async (id) => { if (confirm('¿Eliminar producto?')) { await request(`/api/products/${id}`, { method: 'DELETE' }); refresh() } }
  const upload = async (id, file) => { const data = new FormData(); data.append('image', file); await request(`/api/products/${id}/image`, { method: 'POST', body: data }); refresh() }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.6fr]">
      <form onSubmit={save} className="glass-panel h-fit rounded-3xl p-5">
        <h2 className="text-xl font-black text-beer-amber">{isNew ? 'Agregar producto' : 'Editar producto'}</h2>
        {['name', 'description', 'price', 'cost_price', 'stock', 'min_stock'].map((field) => <label key={field} className="mt-4 block text-sm text-zinc-300">{labels[field]}<input className="input mt-2" type={['price','cost_price','stock','min_stock'].includes(field) ? 'number' : 'text'} step="0.01" value={editing[field]} onChange={(e) => setEditing({ ...editing, [field]: e.target.value })} required={field === 'name'} /></label>)}
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
  return <article className="glass-panel overflow-hidden rounded-3xl"><img className="h-40 w-full object-cover" src={apiPath(product.image_url)} alt={product.name} /><div className="space-y-3 p-4"><div className="flex justify-between gap-3"><div><h3 className="font-black">{product.name}</h3><p className="text-sm text-zinc-400">{product.description}</p></div><b className="text-beer-amber">{currency.format(product.price)}</b></div><div className="flex items-center justify-between text-sm"><span>Stock: <b className={product.stock <= product.min_stock ? 'text-red-300' : 'text-white'}>{product.stock}</b></span><span>Ganancia/u: {currency.format(product.price - product.cost_price)}</span></div><div className="flex flex-wrap gap-2"><button className="btn-secondary py-2" onClick={onEdit}>Editar</button><button className="rounded-xl border border-red-500/40 px-3 py-2 text-sm text-red-200 hover:bg-red-500/10" onClick={onDelete}><Trash2 size={16} /></button><label className="btn-secondary cursor-pointer py-2"><Camera className="inline" size={16} /> Foto<input type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files[0] && onUpload(e.target.files[0])} /></label></div></div></article>
}

function SalesHistory({ sales, summary }) {
  return <div className="grid gap-6 lg:grid-cols-[1fr_2fr]"><Panel title="Resumen mensual"><ListRow left="Ventas" right={currency.format(summary?.totals.monthly.sales || 0)} /><ListRow left="Ganancias" right={currency.format(summary?.totals.monthly.profit || 0)} /><ListRow left="Órdenes" right={summary?.totals.monthly.orders || 0} /></Panel><Panel title="Historial de ventas">{sales.length ? sales.map((sale) => <div key={sale.id} className="rounded-2xl bg-white/5 p-4"><div className="flex flex-wrap justify-between gap-2"><b>Venta #{sale.id} · {sale.seller_name}</b><span className="text-beer-amber">{currency.format(sale.total)}</span></div><p className="text-xs text-zinc-400">{new Date(sale.created_at).toLocaleString()}</p><p className="mt-2 text-sm text-zinc-300">{sale.items.map((i) => `${i.product_name} x${i.quantity}`).join(' · ')}</p></div>) : <Empty text="Sin ventas registradas" />}</Panel></div>
}

function UsersPanel({ users, request, refresh }) {
  const [form, setForm] = useState({ name: '', username: '', password: '', role: 'seller' })
  const submit = async (event) => { event.preventDefault(); await request('/api/users', { method: 'POST', body: JSON.stringify(form) }); setForm({ name: '', username: '', password: '', role: 'seller' }); refresh() }
  return <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]"><form onSubmit={submit} className="glass-panel h-fit rounded-3xl p-5"><h2 className="text-xl font-black text-beer-amber">Crear vendedor</h2>{['name','username','password'].map((field) => <input key={field} className="input mt-4" type={field === 'password' ? 'password' : 'text'} placeholder={labelsUser[field]} value={form[field]} onChange={(e) => setForm({ ...form, [field]: e.target.value })} required />)}<select className="input mt-4" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}><option value="seller">Vendedor</option><option value="admin">Administrador</option></select><button className="btn-primary mt-5 w-full"><Plus className="inline" size={16} /> Crear usuario</button></form><Panel title="Usuarios registrados">{users.map((u) => <ListRow key={u.id} left={`${u.name} (${u.username})`} right={u.role === 'admin' ? 'Admin' : 'Vendedor'} />)}</Panel></div>
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
  return <div className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr]"><section className="space-y-4"><div><h2 className="text-3xl font-black">Panel de vendedor</h2><p className="text-zinc-400">Busca productos, selecciona cantidades y cobra desde el carrito. Los precios son solo lectura.</p></div>{message && <p className="rounded-xl border border-green-500/40 bg-green-500/10 p-3 text-sm text-green-200">{message}</p>}<div className="relative"><Search className="absolute left-4 top-3.5 text-zinc-500" size={18} /><input className="input pl-11" placeholder="Buscar producto..." value={query} onChange={(e) => setQuery(e.target.value)} /></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{filtered.map((product) => <article key={product.id} className="glass-panel overflow-hidden rounded-3xl"><img src={apiPath(product.image_url)} alt={product.name} className="h-36 w-full object-cover" /><div className="p-4"><div className="flex justify-between gap-3"><h3 className="font-black">{product.name}</h3><b className="text-beer-amber">{currency.format(product.price)}</b></div><p className="mt-1 text-sm text-zinc-400">Stock disponible: {product.stock}</p><button className="btn-primary mt-4 w-full" disabled={product.stock < 1} onClick={() => add(product)}>Agregar</button></div></article>)}</div></section><aside className="glass-panel sticky top-24 h-fit rounded-3xl p-5"><h2 className="flex items-center gap-2 text-xl font-black text-beer-amber"><ShoppingCart /> Carrito</h2><p className="mt-1 text-sm text-zinc-400">Vendedor: {user.name}</p><div className="mt-5 space-y-3">{cart.length ? cart.map((item) => <div key={item.id} className="rounded-2xl bg-white/5 p-3"><div className="flex justify-between gap-2"><b>{item.name}</b><button onClick={() => setCart(cart.filter((p) => p.id !== item.id))} className="text-red-300"><Trash2 size={16} /></button></div><div className="mt-3 flex items-center justify-between"><input className="input w-24 py-2" type="number" min="1" max={item.stock} value={item.quantity} onChange={(e) => updateQty(item.id, e.target.value)} /><span>{currency.format(item.price * item.quantity)}</span></div></div>) : <Empty text="El carrito está vacío" />}</div><div className="mt-5 border-t border-white/10 pt-5"><div className="flex justify-between text-lg"><span>Total a cobrar</span><b className="text-2xl text-beer-amber">{currency.format(total)}</b></div><button className="btn-primary mt-5 w-full" disabled={!cart.length} onClick={sell}>Registrar venta</button></div></aside></div>
}

createRoot(document.getElementById('root')).render(<App />)

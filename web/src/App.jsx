import { useState, useEffect, useMemo } from 'react';
import { 
  LayoutDashboard, 
  PackageSearch, 
  CheckCircle, 
  Trash2, 
  Tags,
  Plus,
  Image as ImageIcon,
  Box,
  Search,
  Filter,
  History,
  FileText,
  ChevronRight,
  ChevronDown,
  Edit3,
  MapPin,
  XCircle,
  Undo2,
  Redo2,
  ArrowUpDown,
  ArrowUp,
  ArrowDown
} from 'lucide-react';

const API_URL = '/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [hierarchy, setHierarchy] = useState([]);

  // Fetch data
  const fetchData = async () => {
    const fetchRes = async (url, setter) => {
      try {
        const res = await fetch(url);
        if (res.ok) setter(await res.json());
        else console.error(`Error fetching ${url}:`, res.statusText);
      } catch (e) {
        console.error(`Fetch failed for ${url}:`, e);
      }
    };

    await Promise.all([
      fetchRes(`${API_URL}/stats`, setStats),
      fetchRes(`${API_URL}/items`, setItems),
      fetchRes(`${API_URL}/categories`, setCategories),
      fetchRes(`${API_URL}/categories/hierarchy`, setHierarchy)
    ]);
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo">
          <Box className="logo-icon" size={28} />
          <span>Система Обліку</span>
        </div>
        
        <nav className="nav-links">
          <a 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={20} />
            Дашборд
          </a>
          <a 
            className={`nav-item ${activeTab === 'inventory' ? 'active' : ''}`}
            onClick={() => setActiveTab('inventory')}
          >
            <PackageSearch size={20} />
            Майно
          </a>
          <a 
            className={`nav-item ${activeTab === 'categories' ? 'active' : ''}`}
            onClick={() => setActiveTab('categories')}
          >
            <Tags size={20} />
            Категорії
          </a>
          <a 
            className={`nav-item ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            <FileText size={20} />
            Звіти
          </a>
        </nav>

        <div className="sidebar-footer" style={{ padding: '1rem', borderTop: '1px solid #1e293b', display: 'flex', gap: '0.5rem' }}>
          <button onClick={() => fetch(`${API_URL}/undo`, {method: 'POST'}).then(fetchData)} title="Undo" className="btn btn-icon">
            <Undo2 size={18} />
          </button>
          <button onClick={() => fetch(`${API_URL}/redo`, {method: 'POST'}).then(fetchData)} title="Redo" className="btn btn-icon">
            <Redo2 size={18} />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <div className="fade-in">
          {activeTab === 'dashboard' && <Dashboard stats={stats} />}
          {activeTab === 'inventory' && (
            <Inventory 
              items={items} 
              categories={categories} 
              onUpdate={fetchData} 
            />
          )}
          {activeTab === 'categories' && (
            <Categories 
              hierarchy={hierarchy} 
              onUpdate={fetchData} 
            />
          )}
          {activeTab === 'reports' && <Reports />}
        </div>
      </main>
    </div>
  );
}

// ─── DASHBOARD ──────────────────────────────────────────────

function Dashboard({ stats }) {
  if (!stats) return <div className="loading">Завантаження...</div>;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Дашборд</h1>
        <p className="page-subtitle">Загальна статистика майна установи</p>
      </div>

      <div className="stats-grid">
        <StatCard icon={<Tags size={28}/>} label="Категорій" value={stats.categories} color="#4f46e5" />
        <StatCard icon={<PackageSearch size={28}/>} label="Всього об'єктів" value={stats.total_items} color="#10b981" />
        <StatCard icon={<CheckCircle size={28}/>} label="Активних" value={stats.active_items} color="#0ea5e9" />
        <StatCard icon={<Trash2 size={28}/>} label="Списано" value={stats.written_off} color="#ef4444" />
      </div>

      <div className="form-card" style={{ maxWidth: '400px', marginTop: '2rem' }}>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem', fontWeight: '600' }}>ЗАГАЛЬНА ВАРТІСТЬ МАЙНА</p>
        <h2 style={{ fontSize: '2.5rem', fontWeight: '800', color: '#10b981' }}>
          {stats.total_cost.toLocaleString()} ₴
        </h2>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: `${color}15`, color: color }}>
        {icon}
      </div>
      <div className="stat-info">
        <p>{label}</p>
        <h3>{value}</h3>
      </div>
    </div>
  );
}

// ─── INVENTORY ──────────────────────────────────────────────

function Inventory({ items, categories, onUpdate }) {
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [selectedItemHistory, setSelectedItemHistory] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [viewingPhoto, setViewingPhoto] = useState(null);
  const [activeFilterPopover, setActiveFilterPopover] = useState(null);
  const [costFilter, setCostFilter] = useState({ min: '', max: '' });
  const [dateFilter, setDateFilter] = useState({ from: '', to: '' });
  const [sortConfig, setSortConfig] = useState({ key: null, direction: null });

  const filteredItems = items.filter(item => {
    const sq = searchQuery.toLowerCase();
    const itemName = item.name ? item.name.toLowerCase() : '';
    const itemInv = item.inventory_number ? String(item.inventory_number).toLowerCase() : '';
    const itemCat = item.category ? item.category.toLowerCase() : '';
    
    const matchesSearch = itemName.includes(sq) || itemInv.includes(sq) || itemCat.includes(sq);
    const matchesStatus = filterStatus ? item.status === filterStatus : true;

    let matchesCost = true;
    if (costFilter.min !== '') matchesCost = matchesCost && (Number(item.cost) || 0) >= Number(costFilter.min);
    if (costFilter.max !== '') matchesCost = matchesCost && (Number(item.cost) || 0) <= Number(costFilter.max);

    let matchesDate = true;
    const pDate = item.purchase_date || '';
    if (dateFilter.from !== '') matchesDate = matchesDate && pDate >= dateFilter.from;
    if (dateFilter.to !== '') matchesDate = matchesDate && pDate <= dateFilter.to;

    return matchesSearch && matchesStatus && matchesCost && matchesDate;
  });

  const sortedItems = useMemo(() => {
    if (!sortConfig.key || !sortConfig.direction) return filteredItems;
    const sorted = [...filteredItems];
    sorted.sort((a, b) => {
      if (sortConfig.key === 'cost') {
        const ca = Number(a.cost) || 0;
        const cb = Number(b.cost) || 0;
        return sortConfig.direction === 'asc' ? ca - cb : cb - ca;
      }
      if (sortConfig.key === 'purchase_date') {
        const da = a.purchase_date || '';
        const db = b.purchase_date || '';
        if (!da && !db) return 0;
        if (!da) return 1;
        if (!db) return -1;
        return sortConfig.direction === 'asc' ? da.localeCompare(db) : db.localeCompare(da);
      }
      return 0;
    });
    return sorted;
  }, [filteredItems, sortConfig]);

  const handleAdd = async (e) => {
    e.preventDefault();
    setError('');
    const form = e.target;
    
    // Explicitly extract values to be safe
    const data = {
      inventory_number: form.inventory_number.value,
      name: form.name.value,
      category: form.category.value,
      cost: parseFloat(form.cost.value) || 0,
      location: form.location.value || "",
      description: form.description.value || "",
      purchase_date: form.purchase_date.value || ""
    };

    try {
      const res = await fetch(`${API_URL}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      
      if (!res.ok) {
        const data = await res.json();
        // Перетворюємо в рядок, щоб catch міг розпарсити
        throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
      }

      const fileInput = form.photo;
      if (fileInput && fileInput.files.length > 0) {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        await fetch(`${API_URL}/items/${data.inventory_number}/photo`, {
          method: 'POST',
          body: formData
        });
      }
      
      form.reset();
      onUpdate();
    } catch (err) {
      let msg = err.message;
      try {
        const parsed = JSON.parse(msg);
        if (Array.isArray(parsed)) {
          msg = parsed.map(e => `${e.loc[e.loc.length-1]}: ${e.msg}`).join(', ');
        } else if (typeof parsed === 'object') {
          msg = parsed.msg || JSON.stringify(parsed);
        }
      } catch (e) { /* не JSON */ }
      
      if (msg.includes('[object Object]')) {
        msg = "Помилка валідації: перевірте правильність заповнення полів";
      }
      setError(msg);
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = {
      name: form.name.value,
      category: form.category.value,
      cost: parseFloat(form.cost.value) || 0,
      location: form.location.value || "",
      description: form.description.value || "",
      purchase_date: form.purchase_date.value || ""
    };

    try {
      const res = await fetch(`${API_URL}/items/${editingItem.inventory_number}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Помилка при оновленні");

      const fileInput = form.photo;
      if (fileInput && fileInput.files.length > 0) {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        await fetch(`${API_URL}/items/${editingItem.inventory_number}/photo`, {
          method: 'POST',
          body: formData
        });
      }

      setEditingItem(null);
      onUpdate();
    } catch (err) { alert(err.message); }
  };

  const handleDelete = async (inventory_number) => {
    if (!confirm("Ви дійсно хочете видалити цей об'єкт?")) return;
    try {
      const res = await fetch(`${API_URL}/items/${inventory_number}`, { method: 'DELETE' });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Помилка при видаленні");
      }
      onUpdate();
    } catch (err) { alert(err.message); }
  };

  const handleWriteOff = async (inv) => {
    const reason = prompt("Причина списання:");
    if (reason === null) return;
    await fetch(`${API_URL}/items/${inv}/write_off?reason=${encodeURIComponent(reason)}`, { method: 'POST' });
    onUpdate();
  };

  const handleMove = async (inv) => {
    const loc = prompt("Нове місце знаходження:");
    if (loc === null) return;
    await fetch(`${API_URL}/items/${inv}/move?to=${encodeURIComponent(loc)}`, { method: 'POST' });
    onUpdate();
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Управління Майном</h1>
        <p className="page-subtitle">Додавання, пошук та редагування інвентарю</p>
      </div>

      <div className="inventory-actions">
        <div className="search-box">
          <Search size={18} className="search-icon" />
          <input 
            type="text" 
            placeholder="Пошук за назвою, номером або категорією..." 
            className="input-control"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="filter-box">
          <Filter size={18} />
          <select className="input-control" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="">Всі статуси</option>
            <option value="active">Активні</option>
            <option value="moved">Переміщені</option>
            <option value="written_off">Списані</option>
          </select>
        </div>
      </div>

      <div className="form-card">
        <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {editingItem ? <Edit3 size={20} /> : <Plus size={20} />}
          {editingItem ? 'Редагувати майно' : 'Додати нове майно'}
        </h3>
        <form onSubmit={editingItem ? handleEditSubmit : handleAdd} className="form-grid inventory-form">
          <div className="form-group">
            <label>Інвентарний номер</label>
            <input name="inventory_number" className="input-control" required defaultValue={editingItem?.inventory_number} disabled={!!editingItem} />
          </div>
          <div className="form-group">
            <label>Назва майна</label>
            <input name="name" className="input-control" required defaultValue={editingItem?.name} />
          </div>
          <div className="form-group">
            <label>Категорія</label>
            <select name="category" className="input-control" defaultValue={editingItem?.category}>
              <option value="">-- {categories.length === 0 ? 'Категорії завантажуються...' : 'Виберіть категорію'} --</option>
              {categories.map(c => (
                <option key={c.name || c} value={c.name || c}>
                  {c.label || c}
                </option>
              ))}
            </select>
            {categories.length === 0 && <button type="button" onClick={onUpdate} style={{ fontSize: '0.7rem', color: '#4f46e5', background: 'none', border: 'none', cursor: 'pointer' }}>Оновити список</button>}
          </div>
          <div className="form-group">
            <label>Вартість (грн)</label>
            <input name="cost" type="number" step="0.01" className="input-control" required defaultValue={editingItem?.cost} />
          </div>
          <div className="form-group">
            <label>Локація</label>
            <input name="location" className="input-control" defaultValue={editingItem?.location} />
          </div>
          <div className="form-group">
            <label>Опис</label>
            <input name="description" className="input-control" defaultValue={editingItem?.description} />
          </div>
          <div className="form-group">
            <label>Дата придбання</label>
            <input name="purchase_date" type="date" className="input-control" defaultValue={editingItem?.purchase_date} />
          </div>
          <div className="form-group">
            <label>Фото</label>
            <input name="photo" type="file" accept="image/*" className="input-control" />
          </div>
          
          <div style={{ gridColumn: '1 / -1', marginTop: '1rem', display: 'flex', gap: '1rem' }}>
            {error && <p style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</p>}
            <button type="submit" className="btn btn-primary">
              {editingItem ? 'Зберегти зміни' : 'Додати майно'}
            </button>
            {editingItem && (
              <button type="button" className="btn" onClick={() => setEditingItem(null)}>Скасувати</button>
            )}
          </div>
        </form>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Інв. номер</th>
              <th>Назва</th>
              <th>Категорія</th>
              <th>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Вартість 
                  <button className="btn-icon" style={{ padding: '2px', color: (costFilter.min || costFilter.max) ? '#10b981' : '#94a3b8' }} onClick={() => setActiveFilterPopover('cost')} title="Фільтр по вартості">
                    <Filter size={14} />
                  </button>
                </div>
              </th>
              <th>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Дата придбання 
                  <button className="btn-icon" style={{ padding: '2px', color: (dateFilter.from || dateFilter.to) ? '#10b981' : '#94a3b8' }} onClick={() => setActiveFilterPopover('date')} title="Фільтр по даті">
                    <Filter size={14} />
                  </button>
                </div>
              </th>
              <th>Статус</th>
              <th style={{ textAlign: 'center' }}>Фото</th>
              <th>Дії</th>
            </tr>
          </thead>
          <tbody>
            {sortedItems.map(item => (
              <tr key={item.inventory_number}>
                <td><code>{item.inventory_number}</code></td>
                <td style={{ fontWeight: 600, color: '#fff' }}>{item.name}</td>
                <td><span className="badge-category">{item.category}</span></td>
                <td style={{ color: '#10b981', fontWeight: '600' }}>{(Number(item.cost) || 0).toLocaleString()} ₴</td>
                <td style={{ color: '#94a3b8' }}>{item.purchase_date ? new Date(item.purchase_date).toLocaleDateString('uk-UA') : '—'}</td>
                <td>
                  <span className={`status-badge status-${item.status}`}>
                    {item.status === 'active' ? 'Активне' : item.status === 'moved' ? 'Переміщено' : 'Списано'}
                  </span>
                </td>
                <td style={{ textAlign: 'center' }}>
                  {item.photo_path ? <CheckCircle size={18} color="#10b981" /> : <XCircle size={18} color="#ef4444" />}
                </td>
                <td className="actions-cell">
                  {item.photo_path ? (
                    <button onClick={() => setViewingPhoto(item.photo_path)} title="Переглянути фото" style={{ color: '#3b82f6' }}><ImageIcon size={16}/></button>
                  ) : (
                    <button disabled title="Немає фото" style={{ opacity: 0.3, cursor: 'not-allowed' }}><ImageIcon size={16}/></button>
                  )}
                  <button onClick={() => setEditingItem(item)} title="Редагувати"><Edit3 size={16}/></button>
                  <button onClick={() => handleMove(item.inventory_number)} title="Перемістити"><MapPin size={16}/></button>
                  <button onClick={() => handleWriteOff(item.inventory_number)} title="Списати"><XCircle size={16}/></button>
                  <button onClick={() => setSelectedItemHistory(item.inventory_number)} title="Історія"><History size={16}/></button>
                  <button onClick={() => handleDelete(item.inventory_number)} title="Видалити" className="text-danger"><Trash2 size={16}/></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedItemHistory && (
        <HistoryModal inv={selectedItemHistory} onClose={() => setSelectedItemHistory(null)} />
      )}
      {viewingPhoto && (
        <PhotoModal photoUrl={viewingPhoto} onClose={() => setViewingPhoto(null)} />
      )}
      
      {activeFilterPopover === 'cost' && (
        <div className="modal-overlay" style={{ background: 'transparent', backdropFilter: 'none' }} onClick={() => setActiveFilterPopover(null)}>
          <div className="modal-content fade-in" style={{ maxWidth: '380px', padding: '2.5rem', border: '1px solid var(--border-color)', boxShadow: '0 10px 25px rgba(0,0,0,0.5)' }} onClick={e => e.stopPropagation()}>
            <h3 style={{ marginTop: 0, marginBottom: '1.5rem', color: '#fff', fontSize: '1.25rem' }}>Фільтр за Вартістю</h3>
            <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#94a3b8', paddingLeft: '0.2rem' }}>Вартість від:</div>
            <input type="number" className="input-control" value={costFilter.min} onChange={e => setCostFilter({...costFilter, min: e.target.value})} style={{ marginBottom: '1.25rem' }} />
            <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#94a3b8', paddingLeft: '0.2rem' }}>Вартість до:</div>
            <input type="number" className="input-control" value={costFilter.max} onChange={e => setCostFilter({...costFilter, max: e.target.value})} style={{ marginBottom: '1.5rem' }} />
            <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ fontSize: '0.9rem', color: '#94a3b8', paddingLeft: '0.2rem' }}>Сортування:</div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className={`btn ${sortConfig.key === 'cost' && sortConfig.direction === 'asc' ? 'btn-primary' : ''}`} style={{ padding: '0.5rem 0.75rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={() => setSortConfig({ key: 'cost', direction: 'asc' })}>
                  <ArrowUp size={14} /> Зростання
                </button>
                <button className={`btn ${sortConfig.key === 'cost' && sortConfig.direction === 'desc' ? 'btn-primary' : ''}`} style={{ padding: '0.5rem 0.75rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={() => setSortConfig({ key: 'cost', direction: 'desc' })}>
                  <ArrowDown size={14} /> Спадання
                </button>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button className="btn btn-primary" style={{ flex: 1, padding: '0.6rem' }} onClick={() => setActiveFilterPopover(null)}>ОК</button>
              <button className="btn" style={{ padding: '0.6rem' }} onClick={() => { setCostFilter({min:'', max:''}); setSortConfig({key: null, direction: null}); setActiveFilterPopover(null); }}>Скинути</button>
            </div>
          </div>
        </div>
      )}
      
      {activeFilterPopover === 'date' && (
        <div className="modal-overlay" style={{ background: 'transparent', backdropFilter: 'none' }} onClick={() => setActiveFilterPopover(null)}>
          <div className="modal-content fade-in" style={{ maxWidth: '380px', padding: '2.5rem', border: '1px solid var(--border-color)', boxShadow: '0 10px 25px rgba(0,0,0,0.5)' }} onClick={e => e.stopPropagation()}>
            <h3 style={{ marginTop: 0, marginBottom: '1.5rem', color: '#fff', fontSize: '1.25rem' }}>Фільтр за Датою</h3>
            <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#94a3b8', paddingLeft: '0.2rem' }}>Дата від:</div>
            <input type="date" className="input-control" value={dateFilter.from} onChange={e => setDateFilter({...dateFilter, from: e.target.value})} style={{ marginBottom: '1.25rem' }} />
            <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#94a3b8', paddingLeft: '0.2rem' }}>Дата до:</div>
            <input type="date" className="input-control" value={dateFilter.to} onChange={e => setDateFilter({...dateFilter, to: e.target.value})} style={{ marginBottom: '1.5rem' }} />
            <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ fontSize: '0.9rem', color: '#94a3b8', paddingLeft: '0.2rem' }}>Сортування:</div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className={`btn ${sortConfig.key === 'purchase_date' && sortConfig.direction === 'asc' ? 'btn-primary' : ''}`} style={{ padding: '0.5rem 0.75rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={() => setSortConfig({ key: 'purchase_date', direction: 'asc' })}>
                  <ArrowUp size={14} /> Старіші
                </button>
                <button className={`btn ${sortConfig.key === 'purchase_date' && sortConfig.direction === 'desc' ? 'btn-primary' : ''}`} style={{ padding: '0.5rem 0.75rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={() => setSortConfig({ key: 'purchase_date', direction: 'desc' })}>
                  <ArrowDown size={14} /> Новіші
                </button>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button className="btn btn-primary" style={{ flex: 1, padding: '0.6rem' }} onClick={() => setActiveFilterPopover(null)}>ОК</button>
              <button className="btn" style={{ padding: '0.6rem' }} onClick={() => { setDateFilter({from:'', to:''}); setSortConfig({key: null, direction: null}); setActiveFilterPopover(null); }}>Скинути</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PhotoModal({ photoUrl, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content fade-in" style={{ background: 'transparent', border: 'none', boxShadow: 'none', alignItems: 'center' }} onClick={e => e.stopPropagation()}>
        <div style={{ position: 'relative', maxWidth: '100%', maxHeight: '90vh' }}>
          <img src={photoUrl} alt="Фото майна" style={{ maxWidth: '100%', maxHeight: '85vh', borderRadius: '12px', objectFit: 'contain' }} />
          <button onClick={onClose} className="btn-icon" style={{ position: 'absolute', top: '-40px', right: '0', background: 'rgba(0,0,0,0.5)', color: 'white' }}>
            <XCircle size={24}/>
          </button>
        </div>
      </div>
    </div>
  );
}

function HistoryModal({ inv, onClose }) {
  const [history, setHistory] = useState([]);
  useEffect(() => {
    fetch(`${API_URL}/history/${inv}`).then(r => r.json()).then(setHistory);
  }, [inv]);

  return (
    <div className="modal-overlay">
      <div className="modal-content fade-in">
        <div className="modal-header">
          <h3>Історія змін: {inv}</h3>
          <button onClick={onClose} className="btn-icon"><XCircle size={20}/></button>
        </div>
        <div className="history-list">
          {history.length === 0 && <p style={{ color: '#94a3b8', textAlign: 'center', padding: '2rem' }}>Історія порожня</p>}
          {history.map(h => (
            <div key={h.id} className="history-item">
              <div className="history-meta">
                <span className={`op-badge op-${h.operation}`}>{h.operation}</span>
                <span className="history-date">{new Date(h.performed_at).toLocaleString()}</span>
              </div>
              <p className="history-details">{h.details}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── CATEGORIES ─────────────────────────────────────────────

function Categories({ hierarchy, onUpdate }) {
  const [isAdding, setIsAdding] = useState(false);
  
  const handleAdd = async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    if (!data.parent_name) delete data.parent_name;
    
    await fetch(`${API_URL}/categories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    setIsAdding(false);
    onUpdate();
  };

  const handleDelete = async (name) => {
    if (!confirm(`Видалити категорію ${name}?`)) return;
    const res = await fetch(`${API_URL}/categories/${name}`, { method: 'DELETE' });
    if (!res.ok) alert((await res.json()).detail);
    onUpdate();
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Категорії Майна</h1>
        <button className="btn btn-primary" onClick={() => setIsAdding(true)}>
          <Plus size={18} /> Нова категорія
        </button>
      </div>

      <div className="categories-layout">
        <div className="category-tree card">
          <h3 style={{ marginBottom: '1.5rem' }}>Ієрархія категорій</h3>
          {hierarchy.length === 0 && <p style={{ color: '#94a3b8' }}>Категорії не знайдено</p>}
          {hierarchy.map(node => <CategoryNode key={node.name} node={node} onDelete={handleDelete} />)}
        </div>

        {isAdding && (
          <div className="form-card" style={{ flex: 1 }}>
            <h3>Додати категорію</h3>
            <form onSubmit={handleAdd} className="form-grid" style={{ marginTop: '1rem' }}>
              <div className="form-group">
                <label>ID (код)</label>
                <input name="name" className="input-control" required placeholder="напр. electronics" />
              </div>
              <div className="form-group">
                <label>Назва</label>
                <input name="label" className="input-control" required placeholder="напр. Електроніка" />
              </div>
              <div className="form-group">
                <label>Батьківська категорія (ID)</label>
                <input name="parent_name" className="input-control" placeholder="напр. it (залишити порожнім для корня)" />
              </div>
              <div style={{ gridColumn: '1 / -1', display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="submit" className="btn btn-primary">Зберегти</button>
                <button type="button" className="btn" onClick={() => setIsAdding(false)}>Скасувати</button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}

function CategoryNode({ node, onDelete }) {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className="category-node">
      <div className="node-content">
        <button className="toggle-btn" onClick={() => setExpanded(!expanded)} style={{ opacity: hasChildren ? 1 : 0 }}>
          {expanded ? <ChevronDown size={16}/> : <ChevronRight size={16}/>}
        </button>
        <span className="node-label">{node.label}</span>
        <span className="node-name">({node.name})</span>
        <button className="delete-node" onClick={() => onDelete(node.name)} title="Видалити"><Trash2 size={14}/></button>
      </div>
      {expanded && hasChildren && (
        <div className="node-children">
          {node.children.map(child => <CategoryNode key={child.name} node={child} onDelete={onDelete} />)}
        </div>
      )}
    </div>
  );
}

// ─── REPORTS ────────────────────────────────────────────────

function Reports() {
  const [reportType, setReportType] = useState('summary');
  const [dateFrom, setDateFrom] = useState('2024-01-01');
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0]);
  const [reportText, setReportText] = useState('');
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      let url = `${API_URL}/report/${reportType}`;
      if (reportType === 'value_period') {
        url += `?date_from=${dateFrom}&date_to=${dateTo}`;
      }
      const res = await fetch(url);
      const data = await res.json();
      setReportText(data.report);
    } catch (e) {
      alert("Помилка при генерації звіту");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Звітність</h1>
        <p className="page-subtitle">Генерація аналітичних звітів по майну</p>
      </div>

      <div className="form-card">
        <div className="form-grid">
          <div className="form-group">
            <label>Тип звіту</label>
            <select className="input-control" value={reportType} onChange={e => setReportType(e.target.value)}>
              <option value="summary">Зведений звіт</option>
              <option value="category">По категоріях</option>
              <option value="written_off">Списане майно</option>
              <option value="value_period">Вартість за період</option>
              <option value="csv">Експорт CSV</option>
            </select>
          </div>
          {reportType === 'value_period' && (
            <>
              <div className="form-group">
                <label>З дати</label>
                <input type="date" className="input-control" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
              </div>
              <div className="form-group">
                <label>По дату</label>
                <input type="date" className="input-control" value={dateTo} onChange={e => setDateTo(e.target.value)} />
              </div>
            </>
          )}
        </div>
        <button onClick={generate} className="btn btn-primary" style={{ marginTop: '1.5rem' }} disabled={loading}>
          {loading ? 'Генерація...' : 'Згенерувати звіт'}
        </button>
      </div>

      {reportText && (
        <pre className="report-output card fade-in">
          {reportText}
        </pre>
      )}
    </div>
  );
}

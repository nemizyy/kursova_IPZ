import { useState, useEffect } from 'react';
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
  Redo2
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

  const filteredItems = items.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          item.inventory_number.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus ? item.status === filterStatus : true;
    return matchesSearch && matchesStatus;
  });

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
      description: form.description.value || ""
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
      description: form.description.value || ""
    };

    try {
      const res = await fetch(`${API_URL}/items/${editingItem.inventory_number}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Помилка при оновленні");
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
            placeholder="Пошук за назвою або номером..." 
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
        <form onSubmit={editingItem ? handleEditSubmit : handleAdd} className="form-grid">
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
              <th>Вартість</th>
              <th>Статус</th>
              <th>Дії</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map(item => (
              <tr key={item.inventory_number}>
                <td><code>{item.inventory_number}</code></td>
                <td style={{ fontWeight: 600, color: '#fff' }}>{item.name}</td>
                <td><span className="badge-category">{item.category}</span></td>
                <td style={{ color: '#10b981', fontWeight: '600' }}>{item.cost.toLocaleString()} ₴</td>
                <td>
                  <span className={`status-badge status-${item.status}`}>
                    {item.status === 'active' ? 'Активне' : item.status === 'moved' ? 'Переміщено' : 'Списано'}
                  </span>
                </td>
                <td className="actions-cell">
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
              <option value="value_period">Вартість за період (Req 7.2)</option>
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

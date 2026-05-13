import { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  PackageSearch, 
  CheckCircle, 
  Trash2, 
  Tags,
  Plus,
  Image as ImageIcon,
  Box
} from 'lucide-react';

const API_URL = 'http://127.0.0.1:8000/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);

  // Fetch data
  const fetchData = async () => {
    try {
      const statsRes = await fetch(`${API_URL}/stats`);
      const itemsRes = await fetch(`${API_URL}/items`);
      const catsRes = await fetch(`${API_URL}/categories`);
      
      if (statsRes.ok) setStats(await statsRes.json());
      if (itemsRes.ok) setItems(await itemsRes.json());
      if (catsRes.ok) setCategories(await catsRes.json());
    } catch (error) {
      console.error("Error fetching data:", error);
    }
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
        </nav>
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
        </div>
      </main>
    </div>
  );
}

function Dashboard({ stats }) {
  if (!stats) return <div>Завантаження...</div>;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Дашборд</h1>
        <p className="page-subtitle">Загальна статистика майна установи</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(79, 70, 229, 0.1)', color: '#4f46e5' }}>
            <Tags size={28} />
          </div>
          <div className="stat-info">
            <p>Категорій</p>
            <h3>{stats.categories}</h3>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
            <PackageSearch size={28} />
          </div>
          <div className="stat-info">
            <p>Всього об'єктів</p>
            <h3>{stats.total_items}</h3>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(14, 165, 233, 0.1)', color: '#0ea5e9' }}>
            <CheckCircle size={28} />
          </div>
          <div className="stat-info">
            <p>Активних</p>
            <h3>{stats.active_items}</h3>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' }}>
            <Trash2 size={28} />
          </div>
          <div className="stat-info">
            <p>Списано</p>
            <h3>{stats.written_off}</h3>
          </div>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '400px' }}>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>ЗАГАЛЬНА ВАРТІСТЬ МАЙНА</p>
        <h2 style={{ fontSize: '2.5rem', fontWeight: '700', color: '#10b981' }}>
          {stats.total_cost.toLocaleString()} ₴
        </h2>
      </div>
    </div>
  );
}

function Inventory({ items, categories, onUpdate }) {
  const [error, setError] = useState('');

  const handleAdd = async (e) => {
    e.preventDefault();
    setError('');
    const form = e.target;
    const formData = new FormData(form);

    try {
      const res = await fetch(`${API_URL}/items`, {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Помилка при додаванні");
      }
      
      form.reset();
      onUpdate();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (inventory_number) => {
    try {
      const res = await fetch(`${API_URL}/items/${inventory_number}`, {
        method: 'DELETE',
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Помилка при видаленні");
      }
      onUpdate();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Управління Майном</h1>
        <p className="page-subtitle">Додавання та перегляд інвентарю</p>
      </div>

      <div className="form-card">
        <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Додати нове майно</h3>
        <form onSubmit={handleAdd} className="form-grid">
          <div className="form-group">
            <label>Інвентарний номер</label>
            <input name="inventory_number" className="input-control" required />
          </div>
          <div className="form-group">
            <label>Назва майна</label>
            <input name="name" className="input-control" required />
          </div>
          <div className="form-group">
            <label>Категорія</label>
            <select name="category" className="input-control">
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Вартість (грн)</label>
            <input name="cost" type="number" step="0.01" className="input-control" required />
          </div>
          <div className="form-group">
            <label>Локація</label>
            <input name="location" className="input-control" />
          </div>
          <div className="form-group">
            <label>Фото</label>
            <input name="photo" type="file" className="input-control" accept="image/*" style={{ padding: '0.5rem' }} />
          </div>
          
          <div style={{ gridColumn: '1 / -1', marginTop: '1rem' }}>
            {error && <p style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</p>}
            <button type="submit" className="btn btn-primary">
              <Plus size={18} /> Додати майно
            </button>
          </div>
        </form>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Фото</th>
              <th>Інв. номер</th>
              <th>Назва</th>
              <th>Категорія</th>
              <th>Вартість</th>
              <th>Статус</th>
              <th>Дії</th>
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.inventory_number}>
                <td>
                  {item.photo_path ? (
                    <ImageIcon size={20} color="#10b981" />
                  ) : (
                    <span style={{ color: '#64748b' }}>—</span>
                  )}
                </td>
                <td>{item.inventory_number}</td>
                <td style={{ fontWeight: 500, color: '#fff' }}>{item.name}</td>
                <td><span style={{ textTransform: 'capitalize' }}>{item.category}</span></td>
                <td>{item.cost.toLocaleString()} ₴</td>
                <td>
                  <span className={`status-badge status-${item.status}`}>
                    {item.status}
                  </span>
                </td>
                <td>
                  <button 
                    onClick={() => handleDelete(item.inventory_number)}
                    className="btn btn-danger"
                    style={{ padding: '0.4rem 0.8rem', fontSize: '0.875rem' }}
                  >
                    Видалити
                  </button>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', color: '#94a3b8' }}>
                  Список майна порожній
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

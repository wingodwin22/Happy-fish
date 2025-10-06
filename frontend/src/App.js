import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [products, setProducts] = useState([]);
  const [clients, setClients] = useState([]);
  const [sales, setSales] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [loading, setLoading] = useState(false);

  // Product form state
  const [productForm, setProductForm] = useState({
    name: '', category: 'poisson', price: '', stock: '', unit: 'kg'
  });

  // Client form state
  const [clientForm, setClientForm] = useState({
    name: '', phone: '', email: '', address: '', credit_limit: 0
  });

  // Editing states
  const [editingProduct, setEditingProduct] = useState(null);
  const [editingClient, setEditingClient] = useState(null);

  // Product suggestions
  const [productSuggestions, setProductSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Sale form state
  const [saleForm, setSaleForm] = useState({
    client_id: '',
    client_name: '',
    items: [{ product_id: '', quantity: 1 }],
    discount: 0,
    payment_method: 'espèces'
  });

  // Load data on component mount
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [productsRes, clientsRes, salesRes, statsRes] = await Promise.all([
        axios.get(`${API}/products`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/sales`),
        axios.get(`${API}/dashboard/stats`)
      ]);
      
      setProducts(productsRes.data);
      setClients(clientsRes.data);
      setSales(salesRes.data);
      setDashboardStats(statsRes.data);
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProductSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/products`, {
        ...productForm,
        price: parseFloat(productForm.price),
        stock: parseFloat(productForm.stock)
      });
      setProductForm({ name: '', category: 'poisson', price: '', stock: '', unit: 'kg' });
      loadDashboardData();
    } catch (error) {
      console.error('Erreur lors de la création du produit:', error);
    }
  };

  const handleClientSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/clients`, {
        ...clientForm,
        credit_limit: parseFloat(clientForm.credit_limit)
      });
      setClientForm({ name: '', phone: '', email: '', address: '', credit_limit: 0 });
      loadDashboardData();
    } catch (error) {
      console.error('Erreur lors de la création du client:', error);
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce produit ?')) {
      try {
        await axios.delete(`${API}/products/${productId}`);
        loadDashboardData();
      } catch (error) {
        console.error('Erreur lors de la suppression du produit:', error);
      }
    }
  };

  const handleDeleteClient = async (clientId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce client ?')) {
      try {
        await axios.delete(`${API}/clients/${clientId}`);
        loadDashboardData();
      } catch (error) {
        console.error('Erreur lors de la suppression du client:', error);
      }
    }
  };

  const handleEditProduct = (product) => {
    setEditingProduct(product);
    setProductForm({
      name: product.name,
      category: product.category,
      price: product.price.toString(),
      stock: product.stock.toString(),
      unit: product.unit
    });
  };

  const handleEditClient = (client) => {
    setEditingClient(client);
    setClientForm({
      name: client.name,
      phone: client.phone || '',
      email: client.email || '',
      address: client.address || '',
      credit_limit: client.credit_limit.toString()
    });
  };

  const handleUpdateProduct = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/products/${editingProduct.id}`, {
        ...productForm,
        price: parseFloat(productForm.price),
        stock: parseFloat(productForm.stock)
      });
      setEditingProduct(null);
      setProductForm({ name: '', category: 'poisson', price: '', stock: '', unit: 'kg' });
      loadDashboardData();
    } catch (error) {
      console.error('Erreur lors de la modification du produit:', error);
    }
  };

  const handleUpdateClient = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/clients/${editingClient.id}`, {
        ...clientForm,
        credit_limit: parseFloat(clientForm.credit_limit)
      });
      setEditingClient(null);
      setClientForm({ name: '', phone: '', email: '', address: '', credit_limit: 0 });
      loadDashboardData();
    } catch (error) {
      console.error('Erreur lors de la modification du client:', error);
    }
  };

  const cancelEdit = () => {
    setEditingProduct(null);
    setEditingClient(null);
    setProductForm({ name: '', category: 'poisson', price: '', stock: '', unit: 'kg' });
    setClientForm({ name: '', phone: '', email: '', address: '', credit_limit: 0 });
  };

  const searchProducts = async (query) => {
    if (query.length < 2) {
      setProductSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    
    try {
      const response = await axios.get(`${API}/products/search/${encodeURIComponent(query)}`);
      setProductSuggestions(response.data);
      setShowSuggestions(true);
    } catch (error) {
      console.error('Erreur lors de la recherche de produits:', error);
    }
  };

  const selectProductSuggestion = (product) => {
    setProductForm({
      name: product.name,
      category: 'poisson', // Will be updated when we get full product details
      price: product.price.toString(),
      stock: product.stock.toString(),
      unit: product.unit
    });
    setShowSuggestions(false);
    setProductSuggestions([]);
  };

  const handleSaleSubmit = async (e) => {
    e.preventDefault();
    try {
      let clientId = saleForm.client_id;
      let clientName = saleForm.client_name;

      // Si un nouveau client est saisi, le créer automatiquement
      if (!clientId && clientName && clientName !== 'Client Anonyme') {
        const newClient = {
          name: clientName,
          phone: '',
          email: '',
          address: '',
          credit_limit: 0
        };
        const clientResponse = await axios.post(`${API}/clients`, newClient);
        clientId = clientResponse.data.id;
        clientName = clientResponse.data.name;
      }

      const saleData = {
        client_id: clientId || null,
        client_name: clientName || 'Client Anonyme',
        items: saleForm.items.map(item => ({
          product_id: item.product_id,
          quantity: parseFloat(item.quantity)
        })),
        discount: parseFloat(saleForm.discount),
        payment_method: saleForm.payment_method
      };
      
      await axios.post(`${API}/sales`, saleData);
      setSaleForm({
        client_id: '',
        client_name: '',
        items: [{ product_id: '', quantity: 1 }],
        discount: 0,
        payment_method: 'espèces'
      });
      loadDashboardData();
    } catch (error) {
      console.error('Erreur lors de la création de la vente:', error);
      alert('Erreur: ' + (error.response?.data?.detail || 'Erreur inconnue'));
    }
  };

  const addSaleItem = () => {
    setSaleForm({
      ...saleForm,
      items: [...saleForm.items, { product_id: '', quantity: 1 }]
    });
  };

  const removeSaleItem = (index) => {
    const newItems = saleForm.items.filter((_, i) => i !== index);
    setSaleForm({ ...saleForm, items: newItems });
  };

  const updateSaleItem = (index, field, value) => {
    const newItems = [...saleForm.items];
    newItems[index][field] = value;
    setSaleForm({ ...saleForm, items: newItems });
  };

  const NavButton = ({ view, label, icon }) => (
    <button
      onClick={() => setCurrentView(view)}
      className={`nav-btn ${
        currentView === view ? 'nav-btn-active' : 'nav-btn-inactive'
      }`}
    >
      <span className="nav-icon">{icon}</span>
      {label}
    </button>
  );

  const StatCard = ({ title, value, subtitle, color }) => (
    <div className={`stat-card stat-card-${color}`}>
      <h3 className="stat-title">{title}</h3>
      <p className="stat-value">{value}</p>
      {subtitle && <p className="stat-subtitle">{subtitle}</p>}
    </div>
  );

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1 className="header-title">
            ❄️ Boutique Surgelés
          </h1>
          <p className="header-subtitle">Gestion moderne de votre activité</p>
        </div>
      </header>

      {/* Navigation */}
      <nav className="nav">
        <NavButton view="dashboard" label="Tableau de Bord" icon="📊" />
        <NavButton view="products" label="Produits" icon="🐟" />
        <NavButton view="sales" label="Ventes" icon="💰" />
        <NavButton view="clients" label="Clients" icon="👥" />
      </nav>

      {/* Main Content */}
      <main className="main">
        {loading && (
          <div className="loading">
            <div className="loading-spinner"></div>
            <p>Chargement...</p>
          </div>
        )}

        {/* Dashboard */}
        {currentView === 'dashboard' && (
          <div className="dashboard">
            <h2 className="page-title">Tableau de Bord</h2>
            
            <div className="stats-grid">
              <StatCard 
                title="Produits" 
                value={dashboardStats.total_products || 0}
                color="blue"
              />
              <StatCard 
                title="Ventes Aujourd'hui" 
                value={dashboardStats.today_sales_count || 0}
                subtitle={`${(dashboardStats.today_revenue || 0).toFixed(2)}€`}
                color="green"
              />
              <StatCard 
                title="Clients" 
                value={dashboardStats.total_clients || 0}
                color="purple"
              />
              <StatCard 
                title="Stock Faible" 
                value={dashboardStats.low_stock_count || 0}
                color="red"
              />
            </div>

            {dashboardStats.low_stock_products && dashboardStats.low_stock_products.length > 0 && (
              <div className="alert alert-warning">
                <h3>⚠️ Produits en stock faible:</h3>
                <ul>
                  {dashboardStats.low_stock_products.map(product => (
                    <li key={product.id}>
                      <strong>{product.name}</strong> - Stock: {product.stock} {product.unit}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Products */}
        {currentView === 'products' && (
          <div className="products">
            <h2 className="page-title">Gestion des Produits</h2>
            
            {/* Add/Edit Product Form */}
            <div className="form-card">
              <h3>{editingProduct ? 'Modifier le Produit' : 'Ajouter un Produit'}</h3>
              <form onSubmit={editingProduct ? handleUpdateProduct : handleProductSubmit} className="form">
                <div className="form-row">
                  <div className="input-container">
                    <input
                      type="text"
                      placeholder="Nom du produit"
                      value={productForm.name}
                      onChange={(e) => {
                        setProductForm({...productForm, name: e.target.value});
                        if (!editingProduct) {
                          searchProducts(e.target.value);
                        }
                      }}
                      onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                      required
                      className="form-input"
                    />
                    {showSuggestions && productSuggestions.length > 0 && (
                      <div className="suggestions">
                        {productSuggestions.map(product => (
                          <div
                            key={product.id}
                            className="suggestion-item"
                            onClick={() => selectProductSuggestion(product)}
                          >
                            <strong>{product.name}</strong> - {product.price}€/{product.unit} (Stock: {product.stock})
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <select
                    value={productForm.category}
                    onChange={(e) => setProductForm({...productForm, category: e.target.value})}
                    className="form-select"
                  >
                    <option value="poisson">🐟 Poisson</option>
                    <option value="viande">🥩 Viande</option>
                  </select>
                </div>
                <div className="form-row">
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="Prix (€)"
                    value={productForm.price}
                    onChange={(e) => setProductForm({...productForm, price: e.target.value})}
                    required
                    className="form-input"
                  />
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="Stock"
                    value={productForm.stock}
                    onChange={(e) => setProductForm({...productForm, stock: e.target.value})}
                    required
                    className="form-input"
                  />
                  <select
                    value={productForm.unit}
                    onChange={(e) => setProductForm({...productForm, unit: e.target.value})}
                    className="form-select"
                  >
                    <option value="kg">kg</option>
                    <option value="pièce">pièce</option>
                    <option value="barquette">barquette</option>
                  </select>
                </div>
                <div className="form-actions">
                  <button type="submit" className="btn btn-primary">
                    {editingProduct ? 'Modifier' : 'Ajouter'} Produit
                  </button>
                  {editingProduct && (
                    <button type="button" onClick={cancelEdit} className="btn btn-secondary">
                      Annuler
                    </button>
                  )}
                </div>
              </form>
            </div>

            {/* Products List */}
            <div className="table-card">
              <h3>Liste des Produits ({products.length})</h3>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Nom</th>
                      <th>Catégorie</th>
                      <th>Prix</th>
                      <th>Stock</th>
                      <th>Unité</th>
                      <th>Statut</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map(product => (
                      <tr key={product.id}>
                        <td>{product.name}</td>
                        <td>
                          <span className={`category-badge category-${product.category}`}>
                            {product.category === 'poisson' ? '🐟' : '🥩'} {product.category}
                          </span>
                        </td>
                        <td>{product.price.toFixed(2)}€</td>
                        <td className={product.stock <= 5 ? 'text-red' : ''}>
                          {product.stock}
                        </td>
                        <td>{product.unit}</td>
                        <td>
                          <span className={`status-badge ${
                            product.stock <= 0 ? 'status-danger' : 
                            product.stock <= 5 ? 'status-warning' : 'status-success'
                          }`}>
                            {product.stock <= 0 ? 'Rupture' : 
                             product.stock <= 5 ? 'Stock Faible' : 'Disponible'}
                          </span>
                        </td>
                        <td>
                          <div className="action-buttons">
                            <button
                              onClick={() => handleEditProduct(product)}
                              className="btn btn-secondary btn-sm"
                              title="Modifier le produit"
                            >
                              ✏️
                            </button>
                            <button
                              onClick={() => handleDeleteProduct(product.id)}
                              className="btn btn-danger btn-sm"
                              title="Supprimer le produit"
                            >
                              🗑️
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Sales */}
        {currentView === 'sales' && (
          <div className="sales">
            <h2 className="page-title">Gestion des Ventes</h2>
            
            {/* New Sale Form */}
            <div className="form-card">
              <h3>Nouvelle Vente</h3>
              <form onSubmit={handleSaleSubmit} className="form">
                <div className="form-row">
                  <select
                    value={saleForm.client_id}
                    onChange={(e) => {
                      const selectedClient = clients.find(c => c.id === e.target.value);
                      setSaleForm({
                        ...saleForm,
                        client_id: e.target.value,
                        client_name: selectedClient ? selectedClient.name : ''
                      });
                    }}
                    className="form-select"
                  >
                    <option value="">Sélectionner un client existant</option>
                    {clients.map(client => (
                      <option key={client.id} value={client.id}>
                        {client.name} {client.phone ? `(${client.phone})` : ''}
                      </option>
                    ))}
                  </select>
                  
                  <input
                    type="text"
                    placeholder="Ou saisir nouveau client"
                    value={saleForm.client_name}
                    onChange={(e) => setSaleForm({
                      ...saleForm, 
                      client_id: '', 
                      client_name: e.target.value
                    })}
                    className="form-input"
                  />
                  
                  <select
                    value={saleForm.payment_method}
                    onChange={(e) => setSaleForm({...saleForm, payment_method: e.target.value})}
                    className="form-select"
                  >
                    <option value="espèces">💰 Espèces</option>
                    <option value="carte">💳 Carte</option>
                    <option value="crédit">📋 Crédit</option>
                  </select>
                </div>

                {/* Sale Items */}
                <div className="sale-items">
                  <h4>Articles:</h4>
                  {saleForm.items.map((item, index) => (
                    <div key={index} className="sale-item">
                      <select
                        value={item.product_id}
                        onChange={(e) => updateSaleItem(index, 'product_id', e.target.value)}
                        required
                        className="form-select"
                      >
                        <option value="">Sélectionner un produit</option>
                        {products.filter(p => p.stock > 0).map(product => (
                          <option key={product.id} value={product.id}>
                            {product.name} - {product.price}€/{product.unit} (Stock: {product.stock})
                          </option>
                        ))}
                      </select>
                      <input
                        type="number"
                        step="0.1"
                        min="0.01"
                        placeholder="Quantité"
                        value={item.quantity}
                        onChange={(e) => {
                          const value = parseFloat(e.target.value);
                          if (value > 0) {
                            updateSaleItem(index, 'quantity', e.target.value);
                          }
                        }}
                        required
                        className="form-input quantity-input"
                      />
                      {saleForm.items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeSaleItem(index)}
                          className="btn btn-danger btn-sm"
                        >
                          ❌
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={addSaleItem}
                    className="btn btn-secondary btn-sm"
                  >
                    ➕ Ajouter un article
                  </button>
                </div>

                <div className="form-row">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="Réduction (€)"
                    value={saleForm.discount}
                    onChange={(e) => setSaleForm({...saleForm, discount: e.target.value})}
                    className="form-input"
                  />
                </div>
                
                <button type="submit" className="btn btn-primary">Enregistrer Vente</button>
              </form>
            </div>

            {/* Sales List */}
            <div className="table-card">
              <h3>Historique des Ventes ({sales.length})</h3>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>N° Facture</th>
                      <th>Client</th>
                      <th>Articles</th>
                      <th>Total</th>
                      <th>Paiement</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sales.map(sale => (
                      <tr key={sale.id}>
                        <td><strong>{sale.invoice_number}</strong></td>
                        <td>{sale.client_name}</td>
                        <td>{sale.items.length} article(s)</td>
                        <td><strong>{sale.total.toFixed(2)}€</strong></td>
                        <td>
                          <span className={`payment-badge payment-${sale.payment_method}`}>
                            {sale.payment_method === 'espèces' ? '💰' : 
                             sale.payment_method === 'carte' ? '💳' : '📋'} 
                            {sale.payment_method}
                          </span>
                        </td>
                        <td>{new Date(sale.created_at).toLocaleDateString('fr-FR')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Clients */}
        {currentView === 'clients' && (
          <div className="clients">
            <h2 className="page-title">Gestion des Clients</h2>
            
            {/* Add/Edit Client Form */}
            <div className="form-card">
              <h3>{editingClient ? 'Modifier le Client' : 'Ajouter un Client'}</h3>
              <form onSubmit={editingClient ? handleUpdateClient : handleClientSubmit} className="form">
                <div className="form-row">
                  <input
                    type="text"
                    placeholder="Nom du client *"
                    value={clientForm.name}
                    onChange={(e) => setClientForm({...clientForm, name: e.target.value})}
                    required
                    className="form-input"
                  />
                  <input
                    type="tel"
                    placeholder="Téléphone"
                    value={clientForm.phone}
                    onChange={(e) => setClientForm({...clientForm, phone: e.target.value})}
                    className="form-input"
                  />
                </div>
                <div className="form-row">
                  <input
                    type="email"
                    placeholder="Email"
                    value={clientForm.email}
                    onChange={(e) => setClientForm({...clientForm, email: e.target.value})}
                    className="form-input"
                  />
                  <input
                    type="text"
                    placeholder="Adresse"
                    value={clientForm.address}
                    onChange={(e) => setClientForm({...clientForm, address: e.target.value})}
                    className="form-input"
                  />
                </div>
                <div className="form-row">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="Limite de crédit (€)"
                    value={clientForm.credit_limit}
                    onChange={(e) => setClientForm({...clientForm, credit_limit: e.target.value})}
                    className="form-input"
                  />
                </div>
                <div className="form-actions">
                  <button type="submit" className="btn btn-primary">
                    {editingClient ? 'Modifier' : 'Ajouter'} Client
                  </button>
                  {editingClient && (
                    <button type="button" onClick={cancelEdit} className="btn btn-secondary">
                      Annuler
                    </button>
                  )}
                </div>
              </form>
            </div>

            {/* Clients List */}
            <div className="table-card">
              <h3>Liste des Clients ({clients.length})</h3>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Nom</th>
                      <th>Téléphone</th>
                      <th>Email</th>
                      <th>Adresse</th>
                      <th>Limite Crédit</th>
                      <th>Dette Actuelle</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clients.map(client => (
                      <tr key={client.id}>
                        <td><strong>{client.name}</strong></td>
                        <td>{client.phone || '-'}</td>
                        <td>{client.email || '-'}</td>
                        <td>{client.address || '-'}</td>
                        <td>{client.credit_limit.toFixed(2)}€</td>
                        <td className={client.current_debt > 0 ? 'text-red' : ''}>
                          {client.current_debt.toFixed(2)}€
                        </td>
                        <td>
                          <div className="action-buttons">
                            <button
                              onClick={() => handleEditClient(client)}
                              className="btn btn-secondary btn-sm"
                              title="Modifier le client"
                            >
                              ✏️
                            </button>
                            <button
                              onClick={() => handleDeleteClient(client.id)}
                              className="btn btn-danger btn-sm"
                              title="Supprimer le client"
                            >
                              🗑️
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
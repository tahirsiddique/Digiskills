import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { tickets as ticketsApi, categories as categoriesApi } from '../api/client';
import { ArrowLeft, Save } from 'lucide-react';

const CreateTicket = () => {
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    category_id: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await categoriesApi.list();
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = {
        ...formData,
        category_id: formData.category_id ? parseInt(formData.category_id) : null,
      };

      const response = await ticketsApi.create(data);
      navigate(`/tickets/${response.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create ticket');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="container">
      <button onClick={() => navigate('/tickets')} className="btn btn-secondary" style={styles.backBtn}>
        <ArrowLeft size={18} />
        Back to Tickets
      </button>

      <div className="card">
        <h1 style={styles.title}>Create New Ticket</h1>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Title *</label>
            <input
              type="text"
              name="title"
              className="form-input"
              value={formData.title}
              onChange={handleChange}
              required
              placeholder="Brief description of the issue"
              maxLength={200}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description *</label>
            <textarea
              name="description"
              className="form-textarea"
              value={formData.description}
              onChange={handleChange}
              required
              placeholder="Provide detailed information about the issue..."
              rows={6}
            />
          </div>

          <div style={styles.row}>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Priority *</label>
              <select
                name="priority"
                className="form-select"
                value={formData.priority}
                onChange={handleChange}
                required
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Category</label>
              <select
                name="category_id"
                className="form-select"
                value={formData.category_id}
                onChange={handleChange}
              >
                <option value="">Select a category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div style={styles.actions}>
            <button
              type="button"
              onClick={() => navigate('/tickets')}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              <Save size={18} />
              {loading ? 'Creating...' : 'Create Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const styles = {
  backBtn: {
    marginBottom: '20px',
  },
  title: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: '24px',
  },
  row: {
    display: 'flex',
    gap: '16px',
  },
  actions: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'flex-end',
    marginTop: '24px',
  },
};

export default CreateTicket;

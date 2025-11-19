import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogIn, Ticket } from 'lucide-react';

const Login = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(credentials);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card} className="card">
        <div style={styles.header}>
          <Ticket size={48} color="#2563eb" />
          <h1 style={styles.title}>Digiskills Helpdesk</h1>
          <p style={styles.subtitle}>Sign in to your account</p>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              type="text"
              className="form-input"
              value={credentials.username}
              onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              value={credentials.password}
              onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={styles.submitBtn}
            disabled={loading}
          >
            <LogIn size={18} />
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={styles.footer}>
          <p>
            Don't have an account?{' '}
            <Link to="/register" style={styles.link}>
              Register here
            </Link>
          </p>
        </div>

        <div className="alert alert-info" style={styles.hint}>
          <strong>Default Admin:</strong> username: admin / password: admin123
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f5f5f5',
  },
  card: {
    width: '100%',
    maxWidth: '400px',
  },
  header: {
    textAlign: 'center',
    marginBottom: '32px',
  },
  title: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#1e293b',
    marginTop: '16px',
  },
  subtitle: {
    color: '#64748b',
    marginTop: '8px',
  },
  submitBtn: {
    width: '100%',
    justifyContent: 'center',
  },
  footer: {
    marginTop: '24px',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '14px',
  },
  link: {
    color: '#2563eb',
    textDecoration: 'none',
    fontWeight: '500',
  },
  hint: {
    marginTop: '16px',
    fontSize: '12px',
  },
};

export default Login;

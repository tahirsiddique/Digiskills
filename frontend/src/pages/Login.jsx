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
          <div style={styles.iconWrapper}>
            <Ticket size={48} color="white" strokeWidth={2.5} />
          </div>
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
    background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
  },
  card: {
    width: '100%',
    maxWidth: '440px',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)',
  },
  header: {
    textAlign: 'center',
    marginBottom: '40px',
  },
  iconWrapper: {
    width: '100px',
    height: '100px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 20px',
    boxShadow: '0 10px 30px rgba(102, 126, 234, 0.3)',
  },
  title: {
    fontSize: '28px',
    fontWeight: '800',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    marginTop: '16px',
  },
  subtitle: {
    color: '#64748b',
    marginTop: '8px',
    fontSize: '15px',
  },
  submitBtn: {
    width: '100%',
    justifyContent: 'center',
    padding: '14px',
    fontSize: '15px',
  },
  footer: {
    marginTop: '28px',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '14px',
  },
  link: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    textDecoration: 'none',
    fontWeight: '700',
  },
  hint: {
    marginTop: '20px',
    fontSize: '12px',
  },
};

export default Login;

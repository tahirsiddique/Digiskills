import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, Ticket, Home } from 'lucide-react';

const Navbar = () => {
  const { user, logout, isAdmin, isTechnician } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <nav style={styles.nav}>
      <div style={styles.container}>
        <Link to="/" style={styles.brand}>
          <Ticket size={24} />
          <span>Digiskills Helpdesk</span>
        </Link>

        <div style={styles.links}>
          <Link to="/" style={styles.link}>
            <Home size={18} />
            Dashboard
          </Link>
          <Link to="/tickets" style={styles.link}>
            <Ticket size={18} />
            Tickets
          </Link>
          {isAdmin() && (
            <Link to="/users" style={styles.link}>
              <User size={18} />
              Users
            </Link>
          )}
        </div>

        <div style={styles.userSection}>
          <span style={styles.userName}>
            {user.first_name || user.username}
            <span style={styles.badge}>{user.role}</span>
          </span>
          <button onClick={handleLogout} style={styles.logoutBtn} className="btn btn-secondary">
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};

const styles = {
  nav: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '0 20px',
    boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
  },
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: '70px',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    fontSize: '20px',
    fontWeight: '700',
    color: 'white',
    textDecoration: 'none',
    transition: 'transform 0.2s',
  },
  links: {
    display: 'flex',
    gap: '28px',
    flex: 1,
    marginLeft: '48px',
  },
  link: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    color: 'white',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: '600',
    transition: 'all 0.3s',
    padding: '8px 16px',
    borderRadius: '8px',
  },
  userSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
  },
  userName: {
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontWeight: '500',
  },
  badge: {
    background: 'rgba(255, 255, 255, 0.25)',
    padding: '4px 12px',
    borderRadius: '16px',
    fontSize: '11px',
    textTransform: 'uppercase',
    fontWeight: '700',
    letterSpacing: '0.5px',
  },
  logoutBtn: {
    fontSize: '14px',
  },
};

export default Navbar;

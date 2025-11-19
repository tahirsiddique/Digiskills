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
    backgroundColor: '#1e293b',
    color: 'white',
    padding: '0 20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: '64px',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    fontSize: '18px',
    fontWeight: '600',
    color: 'white',
    textDecoration: 'none',
  },
  links: {
    display: 'flex',
    gap: '24px',
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
    fontWeight: '500',
    transition: 'opacity 0.2s',
  },
  userSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  userName: {
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  badge: {
    backgroundColor: '#3b82f6',
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '12px',
    textTransform: 'capitalize',
  },
  logoutBtn: {
    fontSize: '14px',
  },
};

export default Navbar;

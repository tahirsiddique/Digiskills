import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { tickets as ticketsApi } from '../api/client';
import { Ticket, Plus, TrendingUp, Clock, CheckCircle } from 'lucide-react';

const Dashboard = () => {
  const { user, isTechnician } = useAuth();
  const [stats, setStats] = useState({
    total: 0,
    new: 0,
    assigned: 0,
    inProgress: 0,
    resolved: 0,
  });
  const [recentTickets, setRecentTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await ticketsApi.list({ limit: 5 });
      const allTickets = response.data;

      setRecentTickets(allTickets);

      // Calculate stats
      setStats({
        total: allTickets.length,
        new: allTickets.filter(t => t.status === 'new').length,
        assigned: allTickets.filter(t => t.status === 'assigned').length,
        inProgress: allTickets.filter(t => t.status === 'in_progress').length,
        resolved: allTickets.filter(t => t.status === 'resolved').length,
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="spinner" />;
  }

  return (
    <div className="container">
      <div style={styles.header}>
        <h1>Dashboard</h1>
        <Link to="/tickets/new" className="btn btn-primary">
          <Plus size={18} />
          New Ticket
        </Link>
      </div>

      <div style={styles.statsGrid}>
        <StatCard
          title="Total Tickets"
          value={stats.total}
          icon={<Ticket />}
          gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        />
        <StatCard
          title="New"
          value={stats.new}
          icon={<Clock />}
          gradient="linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
        />
        <StatCard
          title="In Progress"
          value={stats.inProgress}
          icon={<TrendingUp />}
          gradient="linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
        />
        <StatCard
          title="Resolved"
          value={stats.resolved}
          icon={<CheckCircle />}
          gradient="linear-gradient(135deg, #30cfd0 0%, #38ef7d 100%)"
        />
      </div>

      <div className="card">
        <div className="card-header" style={styles.cardHeader}>
          <h2>Recent Tickets</h2>
          <Link to="/tickets" style={styles.viewAll}>
            View All →
          </Link>
        </div>

        {recentTickets.length === 0 ? (
          <p style={styles.empty}>No tickets yet. Create your first ticket to get started!</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Ticket #</th>
                <th>Title</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {recentTickets.map((ticket) => (
                <tr key={ticket.id} onClick={() => window.location.href = `/tickets/${ticket.id}`}>
                  <td>{ticket.ticket_number}</td>
                  <td>{ticket.title}</td>
                  <td>
                    <span className={`badge badge-${ticket.priority}`}>
                      {ticket.priority}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-${ticket.status.replace('_', '-')}`}>
                      {ticket.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td>{new Date(ticket.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon, gradient }) => (
  <div style={{ ...styles.statCard, background: gradient }}>
    <div style={styles.iconWrapper}>
      {React.cloneElement(icon, { size: 32, color: 'white', strokeWidth: 2.5 })}
    </div>
    <div style={styles.statContent}>
      <div style={styles.statValue}>{value}</div>
      <div style={styles.statTitle}>{title}</div>
    </div>
  </div>
);

const styles = {
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '40px',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: '24px',
    marginBottom: '40px',
  },
  statCard: {
    padding: '32px',
    borderRadius: '20px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.15)',
    transition: 'all 0.3s ease',
    cursor: 'pointer',
    border: 'none',
  },
  iconWrapper: {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
    marginBottom: '20px',
    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
  },
  statContent: {
    color: 'white',
  },
  statValue: {
    fontSize: '42px',
    fontWeight: '800',
    color: 'white',
    marginBottom: '8px',
  },
  statTitle: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.95)',
    fontWeight: '600',
    letterSpacing: '0.5px',
    textTransform: 'uppercase',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  viewAll: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: '700',
    transition: 'all 0.3s',
  },
  empty: {
    textAlign: 'center',
    color: '#64748b',
    padding: '40px 20px',
  },
};

export default Dashboard;

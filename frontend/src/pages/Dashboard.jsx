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
          color="#2563eb"
        />
        <StatCard
          title="New"
          value={stats.new}
          icon={<Clock />}
          color="#8b5cf6"
        />
        <StatCard
          title="In Progress"
          value={stats.inProgress}
          icon={<TrendingUp />}
          color="#f59e0b"
        />
        <StatCard
          title="Resolved"
          value={stats.resolved}
          icon={<CheckCircle />}
          color="#10b981"
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

const StatCard = ({ title, value, icon, color }) => (
  <div className="card" style={styles.statCard}>
    <div style={{ ...styles.iconWrapper, backgroundColor: `${color}20` }}>
      {React.cloneElement(icon, { size: 24, color })}
    </div>
    <div>
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
    marginBottom: '32px',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    marginBottom: '32px',
  },
  statCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  iconWrapper: {
    width: '48px',
    height: '48px',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  statValue: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#1e293b',
  },
  statTitle: {
    fontSize: '14px',
    color: '#64748b',
    marginTop: '4px',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  viewAll: {
    color: '#2563eb',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: '500',
  },
  empty: {
    textAlign: 'center',
    color: '#64748b',
    padding: '40px 20px',
  },
};

export default Dashboard;

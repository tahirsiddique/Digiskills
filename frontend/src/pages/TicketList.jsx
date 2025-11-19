import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { tickets as ticketsApi } from '../api/client';
import { Plus, Filter } from 'lucide-react';

const TicketList = () => {
  const { isTechnician } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    assigned_to_me: false,
    created_by_me: false,
  });

  useEffect(() => {
    loadTickets();
  }, [filters]);

  const loadTickets = async () => {
    try {
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.priority) params.priority = filters.priority;
      if (filters.assigned_to_me) params.assigned_to_me = true;
      if (filters.created_by_me) params.created_by_me = true;

      const response = await ticketsApi.list(params);
      setTickets(response.data);
    } catch (error) {
      console.error('Failed to load tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value });
  };

  if (loading) {
    return <div className="spinner" />;
  }

  return (
    <div className="container">
      <div style={styles.header}>
        <h1>Tickets</h1>
        <Link to="/tickets/new" className="btn btn-primary">
          <Plus size={18} />
          New Ticket
        </Link>
      </div>

      <div className="card" style={styles.filterCard}>
        <div style={styles.filters}>
          <div style={styles.filterGroup}>
            <label className="form-label">Status</label>
            <select
              className="form-select"
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
            >
              <option value="">All</option>
              <option value="new">New</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <div style={styles.filterGroup}>
            <label className="form-label">Priority</label>
            <select
              className="form-select"
              value={filters.priority}
              onChange={(e) => handleFilterChange('priority', e.target.value)}
            >
              <option value="">All</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          {isTechnician() && (
            <div style={styles.filterGroup}>
              <label className="form-label">Filter</label>
              <label style={styles.checkbox}>
                <input
                  type="checkbox"
                  checked={filters.assigned_to_me}
                  onChange={(e) => handleFilterChange('assigned_to_me', e.target.checked)}
                />
                Assigned to me
              </label>
            </div>
          )}

          <div style={styles.filterGroup}>
            <label className="form-label">&nbsp;</label>
            <label style={styles.checkbox}>
              <input
                type="checkbox"
                checked={filters.created_by_me}
                onChange={(e) => handleFilterChange('created_by_me', e.target.checked)}
              />
              Created by me
            </label>
          </div>
        </div>
      </div>

      <div className="card">
        {tickets.length === 0 ? (
          <p style={styles.empty}>No tickets found matching your filters.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Ticket #</th>
                <th>Title</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Created By</th>
                <th>Assigned To</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket) => (
                <tr
                  key={ticket.id}
                  onClick={() => window.location.href = `/tickets/${ticket.id}`}
                  style={styles.row}
                >
                  <td style={styles.ticketNumber}>{ticket.ticket_number}</td>
                  <td style={styles.title}>{ticket.title}</td>
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
                  <td>{ticket.creator?.username || 'Unknown'}</td>
                  <td>{ticket.assignee?.username || 'Unassigned'}</td>
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

const styles = {
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
  },
  filterCard: {
    marginBottom: '24px',
  },
  filters: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
  },
  filterGroup: {
    display: 'flex',
    flexDirection: 'column',
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    cursor: 'pointer',
  },
  empty: {
    textAlign: 'center',
    color: '#64748b',
    padding: '40px 20px',
  },
  row: {
    cursor: 'pointer',
  },
  ticketNumber: {
    fontWeight: '600',
    color: '#2563eb',
  },
  title: {
    fontWeight: '500',
  },
};

export default TicketList;

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { tickets as ticketsApi, comments as commentsApi, users } from '../api/client';
import { ArrowLeft, MessageSquare, Send, Trash2 } from 'lucide-react';

const TicketDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isTechnician } = useAuth();
  const [ticket, setTicket] = useState(null);
  const [comments, setComments] = useState([]);
  const [technicians, setTechnicians] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [isInternal, setIsInternal] = useState(false);

  useEffect(() => {
    loadTicketData();
  }, [id]);

  const loadTicketData = async () => {
    try {
      const [ticketRes, commentsRes] = await Promise.all([
        ticketsApi.get(id),
        commentsApi.list(id),
      ]);

      setTicket(ticketRes.data);
      setComments(commentsRes.data);

      // Load technicians if user is technician
      if (isTechnician()) {
        const usersRes = await users.list({ role: 'technician' });
        setTechnicians(usersRes.data);
      }
    } catch (error) {
      console.error('Failed to load ticket:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await ticketsApi.update(id, { status: newStatus });
      loadTicketData();
    } catch (error) {
      alert('Failed to update status');
    }
  };

  const handleAssign = async (assigneeId) => {
    try {
      await ticketsApi.assign(id, parseInt(assigneeId));
      loadTicketData();
    } catch (error) {
      alert('Failed to assign ticket');
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    try {
      await commentsApi.create({
        ticket_id: parseInt(id),
        comment_text: newComment,
        is_internal: isInternal,
      });

      setNewComment('');
      setIsInternal(false);
      loadTicketData();
    } catch (error) {
      alert('Failed to add comment');
    }
  };

  if (loading) {
    return <div className="spinner" />;
  }

  if (!ticket) {
    return <div className="container">Ticket not found</div>;
  }

  return (
    <div className="container">
      <button onClick={() => navigate('/tickets')} className="btn btn-secondary" style={styles.backBtn}>
        <ArrowLeft size={18} />
        Back to Tickets
      </button>

      <div className="card" style={styles.mainCard}>
        <div style={styles.header}>
          <div>
            <div style={styles.ticketNumber}>{ticket.ticket_number}</div>
            <h1 style={styles.title}>{ticket.title}</h1>
            <div style={styles.meta}>
              Created by {ticket.creator?.username} on{' '}
              {new Date(ticket.created_at).toLocaleString()}
            </div>
          </div>

          <div style={styles.badges}>
            <span className={`badge badge-${ticket.priority}`} style={styles.badge}>
              {ticket.priority}
            </span>
            <span className={`badge badge-${ticket.status.replace('_', '-')}`} style={styles.badge}>
              {ticket.status.replace('_', ' ')}
            </span>
          </div>
        </div>

        <div style={styles.description}>
          <h3>Description</h3>
          <p>{ticket.description}</p>
        </div>

        {isTechnician() && (
          <div style={styles.actions}>
            <div style={styles.actionGroup}>
              <label className="form-label">Status</label>
              <select
                className="form-select"
                value={ticket.status}
                onChange={(e) => handleStatusChange(e.target.value)}
              >
                <option value="new">New</option>
                <option value="assigned">Assigned</option>
                <option value="in_progress">In Progress</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
            </div>

            <div style={styles.actionGroup}>
              <label className="form-label">Assign To</label>
              <select
                className="form-select"
                value={ticket.assigned_to || ''}
                onChange={(e) => handleAssign(e.target.value)}
              >
                <option value="">Unassigned</option>
                {technicians.map((tech) => (
                  <option key={tech.id} value={tech.id}>
                    {tech.username} ({tech.first_name} {tech.last_name})
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <MessageSquare size={20} />
          Comments ({comments.length})
        </div>

        <div style={styles.comments}>
          {comments.map((comment) => (
            <div key={comment.id} style={styles.comment}>
              <div style={styles.commentHeader}>
                <div>
                  <strong>{comment.user?.username}</strong>
                  {comment.is_internal && (
                    <span className="badge badge-new" style={{ marginLeft: '8px' }}>
                      Internal
                    </span>
                  )}
                </div>
                <span style={styles.commentTime}>
                  {new Date(comment.created_at).toLocaleString()}
                </span>
              </div>
              <div style={styles.commentText}>{comment.comment_text}</div>
            </div>
          ))}

          {comments.length === 0 && (
            <p style={styles.noComments}>No comments yet. Be the first to comment!</p>
          )}
        </div>

        <form onSubmit={handleAddComment} style={styles.commentForm}>
          <textarea
            className="form-textarea"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a comment..."
            rows={3}
          />

          <div style={styles.commentActions}>
            {isTechnician() && (
              <label style={styles.checkbox}>
                <input
                  type="checkbox"
                  checked={isInternal}
                  onChange={(e) => setIsInternal(e.target.checked)}
                />
                Internal comment (only visible to technicians)
              </label>
            )}

            <button type="submit" className="btn btn-primary">
              <Send size={18} />
              Post Comment
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
  mainCard: {
    marginBottom: '24px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '24px',
    paddingBottom: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  ticketNumber: {
    fontSize: '14px',
    color: '#2563eb',
    fontWeight: '600',
    marginBottom: '8px',
  },
  title: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: '8px',
  },
  meta: {
    fontSize: '14px',
    color: '#64748b',
  },
  badges: {
    display: 'flex',
    gap: '8px',
  },
  badge: {
    fontSize: '14px',
  },
  description: {
    marginBottom: '24px',
  },
  actions: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    paddingTop: '20px',
    borderTop: '1px solid #e5e7eb',
  },
  actionGroup: {
    display: 'flex',
    flexDirection: 'column',
  },
  comments: {
    marginTop: '20px',
  },
  comment: {
    padding: '16px',
    backgroundColor: '#f8fafc',
    borderRadius: '8px',
    marginBottom: '12px',
  },
  commentHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  commentTime: {
    fontSize: '12px',
    color: '#64748b',
  },
  commentText: {
    color: '#1e293b',
    lineHeight: '1.6',
  },
  noComments: {
    textAlign: 'center',
    color: '#64748b',
    padding: '20px',
  },
  commentForm: {
    marginTop: '20px',
    paddingTop: '20px',
    borderTop: '1px solid #e5e7eb',
  },
  commentActions: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '12px',
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    cursor: 'pointer',
  },
};

export default TicketDetail;

# AI-Powered IT Helpdesk - Authentication and Authorization

## 2. User Authentication and Authorization

### 2.1 Authentication Strategy

#### Overview and Key Assumptions

**Organizational Context:**
- All users have `@digiskills.pk` email addresses
- Organization likely uses Google Workspace or Microsoft 365 for email and collaboration
- Users expect seamless single sign-on (SSO) experience
- Security requirements: Protect sensitive internal IT data, comply with organizational policies

**Recommended Approach: Single Sign-On (SSO) with OAuth 2.0 / OpenID Connect**

**Primary Recommendation: Google Workspace SSO** (if Digiskills.pk uses Google)
- Leverage existing Google Workspace accounts
- Users authenticate once with their Google credentials
- No need to manage separate passwords for helpdesk system
- Automatic user provisioning from Google directory

**Alternative: Microsoft Azure AD / Entra ID SSO** (if using Microsoft 365)
- Similar benefits to Google SSO
- SAML 2.0 or OpenID Connect integration
- Seamless experience for Windows users

**Fallback: Internal Identity Provider with OAuth 2.0**
- If neither Google nor Microsoft is used
- Build lightweight internal IdP with secure password policies
- Still use OAuth 2.0/OIDC standards for token-based authentication

---

### 2.2 Authentication Implementation Details

#### 2.2.1 SSO Flow (Google Workspace Example)

**Initial Authentication Flow:**

```
User → Helpdesk Portal → Redirect to Google Login → Google Authentication
  ↓                                                            ↓
  ← Redirect back with authorization code ←─────────────────────
  ↓
Exchange code for ID token + Access token → Google OAuth 2.0 API
  ↓
Validate ID token (verify signature, issuer, audience, expiry)
  ↓
Extract user claims (email, name, profile picture)
  ↓
Check if user exists in local database:
  - If yes: Load user profile and roles
  - If no: Auto-provision user account with default "End User" role
  ↓
Generate internal session token (JWT)
  ↓
Set secure HTTP-only cookie with JWT
  ↓
Redirect user to dashboard
```

**Key Implementation Points:**

1. **OAuth 2.0 Authorization Code Flow with PKCE** (Proof Key for Code Exchange)
   - Most secure flow for web applications
   - PKCE prevents authorization code interception attacks

2. **OpenID Connect (OIDC) ID Token**
   - Contains standardized user claims: `sub` (subject/user ID), `email`, `name`, `picture`
   - Verified using Google's public keys (fetched from `https://www.googleapis.com/oauth2/v3/certs`)

3. **Email Domain Validation**
   - After receiving ID token, verify `email` claim ends with `@digiskills.pk`
   - Reject authentication attempts from non-organizational emails
   - Prevents unauthorized access even if OAuth flow is compromised

4. **User Auto-Provisioning**
   - First-time login automatically creates user record:
     ```sql
     INSERT INTO users (email, full_name, profile_picture, role, created_at, auth_provider)
     VALUES ('john.doe@digiskills.pk', 'John Doe', 'https://...', 'end_user', NOW(), 'google');
     ```
   - Subsequent logins update `last_login_at` timestamp

#### 2.2.2 Session Management

**Token Strategy: JWT (JSON Web Tokens)**

**Why JWT?**
- Stateless: No need to store sessions in database or Redis for every request
- Self-contained: Token includes user ID, role, permissions
- Cryptographically signed: Cannot be tampered with
- Standard: Works across multiple backend services if architecture scales

**JWT Structure:**

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id_12345",
    "email": "john.doe@digiskills.pk",
    "role": "agent",
    "permissions": ["ticket:view_all", "ticket:edit", "kb:create_draft"],
    "iat": 1705651200,
    "exp": 1705737600
  },
  "signature": "HMACSHA256(base64UrlEncode(header) + '.' + base64UrlEncode(payload), secret)"
}
```

**Token Lifetime and Refresh:**

- **Access Token**: Short-lived (15-30 minutes)
  - Stored in HTTP-only, Secure, SameSite cookie
  - Used for API requests
  - If expired, client must refresh

- **Refresh Token**: Long-lived (7-30 days)
  - Stored in separate HTTP-only, Secure cookie
  - Used to obtain new access token without re-authentication
  - Rotated on each use (refresh token rotation for security)
  - Stored in database with revocation capability

**Token Storage:**

```
Set-Cookie: access_token=<JWT>; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=1800
Set-Cookie: refresh_token=<REFRESH_JWT>; HttpOnly; Secure; SameSite=Strict; Path=/api/auth/refresh; Max-Age=2592000
```

- **HttpOnly**: Prevents XSS attacks from stealing tokens via JavaScript
- **Secure**: Only sent over HTTPS
- **SameSite=Strict**: Prevents CSRF attacks
- **Path**: Restricts refresh token to refresh endpoint only

**Session Refresh Flow:**

```
Access token expires → Frontend makes API request → 401 Unauthorized
  ↓
Frontend automatically calls /api/auth/refresh with refresh token
  ↓
Backend validates refresh token:
  - Check signature
  - Check expiry
  - Check not revoked in database
  ↓
Generate new access token + new refresh token (rotation)
  ↓
Invalidate old refresh token in database
  ↓
Return new tokens to client
  ↓
Frontend retries original API request with new access token
```

**Token Revocation (Logout and Security):**

- On user logout:
  - Delete access and refresh token cookies on client
  - Add refresh token to revocation list in database (blacklist)
  - Set `revoked_at` timestamp in `refresh_tokens` table

- Periodic cleanup job removes expired revoked tokens (after expiry + grace period)

- For security incidents (compromised account):
  - Admin can revoke all sessions for a user
  - All refresh tokens for that user marked as revoked
  - User forced to re-authenticate on next request

#### 2.2.3 Multi-Factor Authentication (MFA)

**When MFA is Required:**

1. **Mandatory for Privileged Roles:**
   - Administrator role: Always requires MFA
   - Team Lead role: Strongly recommended, configurable
   - Agent role: Optional, user choice

2. **Mandatory for Sensitive Actions:**
   - Changing user roles/permissions
   - Accessing audit logs
   - Exporting bulk data
   - Modifying system configuration

3. **Risk-Based MFA (Future Enhancement):**
   - Trigger MFA for unusual login patterns:
     - Login from new device or location
     - Login outside business hours for sensitive roles
     - Multiple failed login attempts

**MFA Methods Supported:**

1. **TOTP (Time-Based One-Time Password)** - Primary Method
   - Google Authenticator, Microsoft Authenticator, Authy
   - User scans QR code during MFA setup
   - Backend generates secret key, stores encrypted in database
   - User enters 6-digit code on login

2. **SMS OTP** - Fallback Method
   - Send 6-digit code via SMS to registered mobile number
   - Less secure than TOTP but better than no MFA
   - Rate-limited to prevent abuse

3. **Backup Codes** - Recovery Method
   - Generate 10 single-use backup codes during MFA setup
   - User stores securely (printed or password manager)
   - Used if primary MFA method unavailable

**MFA Enrollment Flow:**

```
Admin enables MFA requirement → User logs in → Check MFA status
  ↓ (MFA not enrolled)
Redirect to MFA setup page
  ↓
User chooses TOTP method → Backend generates secret key
  ↓
Display QR code (encodes secret key + issuer "Digiskills Helpdesk")
  ↓
User scans with authenticator app
  ↓
User enters test code to verify setup
  ↓
Backend validates code → If valid:
  - Store encrypted secret key in database
  - Generate 10 backup codes, display to user
  - Mark MFA as enrolled
  ↓
User can now login with MFA
```

**MFA Login Flow:**

```
User enters email/password (or completes SSO) → Backend validates
  ↓
Check if MFA enrolled for user → Yes:
  ↓
Return 200 with `mfa_required: true` (do not issue access token yet)
  ↓
Frontend displays MFA code input
  ↓
User enters 6-digit code → Send to /api/auth/mfa/verify
  ↓
Backend validates code:
  - Compute expected TOTP code from stored secret
  - Allow ±1 time window (30 seconds) for clock drift
  - Check code not recently used (prevent replay attacks)
  ↓
If valid: Issue access token + refresh token, complete login
If invalid: Return error, allow 3 attempts before lockout
```

**MFA Bypass for Emergencies:**

- Admins can temporarily disable MFA for a user (e.g., lost phone)
- Requires another admin's approval (four-eyes principle)
- Logged in audit trail with justification
- User forced to re-enroll MFA within 24 hours

---

### 2.3 Authorization Model (Role-Based Access Control)

#### 2.3.1 RBAC Overview

**Core Principles:**
- Users are assigned one or more **roles**
- Roles have **permissions** (fine-grained capabilities)
- Permissions control access to **resources** (tickets, KB articles, reports, admin functions)
- Principle of least privilege: Users get minimum permissions needed for their job

**Five Primary Roles** (as defined in Application Overview):

1. **End User** - Default role, can create and view own tickets
2. **Agent** - Can manage assigned tickets, create KB drafts
3. **Team Lead** - Can manage team, view reports, handle escalations
4. **Administrator** - Full system access, user management, configuration
5. **Viewer** (optional) - Read-only access for auditors/executives

#### 2.3.2 Permission Granularity

**Permission Naming Convention:** `resource:action`

**Ticket Permissions:**
- `ticket:create` - Create new tickets
- `ticket:view_own` - View own tickets
- `ticket:view_team` - View team's tickets
- `ticket:view_all` - View all tickets across organization
- `ticket:edit_own` - Edit own tickets (limited fields: add comments)
- `ticket:edit_assigned` - Edit assigned tickets (status, priority, category)
- `ticket:edit_all` - Edit any ticket
- `ticket:delete` - Delete tickets (rare, admin only with audit log)
- `ticket:reassign` - Reassign tickets to other agents/teams
- `ticket:close` - Mark tickets as resolved/closed
- `ticket:reopen` - Reopen closed tickets
- `ticket:escalate` - Escalate tickets to team lead or other teams

**Knowledge Base Permissions:**
- `kb:view` - View published KB articles (all users)
- `kb:create_draft` - Create draft articles
- `kb:edit_draft` - Edit own draft articles
- `kb:publish` - Publish articles (team lead/admin)
- `kb:archive` - Archive outdated articles
- `kb:delete` - Delete articles (admin only)

**Report Permissions:**
- `report:view_own` - View personal performance reports
- `report:view_team` - View team reports
- `report:view_all` - View organization-wide reports
- `report:export` - Export reports to CSV/PDF
- `report:create_custom` - Create custom ad-hoc reports

**Admin Permissions:**
- `admin:user_read` - View user accounts
- `admin:user_write` - Create/edit/delete user accounts
- `admin:role_assign` - Assign roles to users
- `admin:config_read` - View system configuration
- `admin:config_write` - Modify system configuration
- `admin:audit_log_read` - View audit logs
- `admin:integration_manage` - Configure integrations (SSO, email, etc.)

**AI Permissions:**
- `ai:view_suggestions` - See AI suggestions (all agents)
- `ai:override` - Override AI decisions (team lead/admin)
- `ai:config` - Configure AI thresholds and models (admin only)

#### 2.3.3 Role-Permission Matrix

| Permission | End User | Agent | Team Lead | Admin | Viewer |
|------------|----------|-------|-----------|-------|--------|
| ticket:create | ✅ | ✅ | ✅ | ✅ | ❌ |
| ticket:view_own | ✅ | ✅ | ✅ | ✅ | ❌ |
| ticket:view_team | ❌ | ✅ | ✅ | ✅ | ✅ |
| ticket:view_all | ❌ | ❌ | ✅* | ✅ | ✅ |
| ticket:edit_assigned | ❌ | ✅ | ✅ | ✅ | ❌ |
| ticket:reassign | ❌ | ❌ | ✅ | ✅ | ❌ |
| ticket:delete | ❌ | ❌ | ❌ | ✅ | ❌ |
| kb:view | ✅ | ✅ | ✅ | ✅ | ✅ |
| kb:create_draft | ❌ | ✅ | ✅ | ✅ | ❌ |
| kb:publish | ❌ | ❌ | ✅ | ✅ | ❌ |
| report:view_team | ❌ | ❌ | ✅ | ✅ | ✅ |
| report:view_all | ❌ | ❌ | ❌ | ✅ | ✅ |
| report:export | ❌ | ❌ | ✅ | ✅ | ✅ |
| admin:user_write | ❌ | ❌ | ❌ | ✅ | ❌ |
| admin:config_write | ❌ | ❌ | ❌ | ✅ | ❌ |
| admin:audit_log_read | ❌ | ❌ | ❌ | ✅ | ❌** |
| ai:override | ❌ | ❌ | ✅ | ✅ | ❌ |

*Team Lead can view all tickets read-only, full edit only for own team
**Viewer audit log access configurable by admin

#### 2.3.4 Database Schema for RBAC

**Users Table:**
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255) NOT NULL,
  profile_picture VARCHAR(500),
  department VARCHAR(100),
  location VARCHAR(100),
  phone VARCHAR(20),
  auth_provider VARCHAR(50) DEFAULT 'google', -- 'google', 'microsoft', 'internal'
  mfa_enabled BOOLEAN DEFAULT FALSE,
  mfa_secret_encrypted TEXT, -- Encrypted TOTP secret
  backup_codes_encrypted TEXT[], -- Array of encrypted backup codes
  created_at TIMESTAMP DEFAULT NOW(),
  last_login_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  CONSTRAINT email_domain CHECK (email LIKE '%@digiskills.pk')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
```

**Roles Table:**
```sql
CREATE TABLE roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(50) UNIQUE NOT NULL, -- 'end_user', 'agent', 'team_lead', 'admin', 'viewer'
  display_name VARCHAR(100) NOT NULL, -- 'End User', 'Helpdesk Agent', etc.
  description TEXT,
  is_system_role BOOLEAN DEFAULT TRUE, -- System roles cannot be deleted
  created_at TIMESTAMP DEFAULT NOW()
);

-- Pre-populate with system roles
INSERT INTO roles (name, display_name, description, is_system_role) VALUES
  ('end_user', 'End User', 'Default role for all employees', TRUE),
  ('agent', 'Helpdesk Agent', 'IT support staff', TRUE),
  ('team_lead', 'Team Lead', 'IT support team supervisor', TRUE),
  ('admin', 'Administrator', 'System administrator with full access', TRUE),
  ('viewer', 'Viewer', 'Read-only access for reporting', TRUE);
```

**Permissions Table:**
```sql
CREATE TABLE permissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) UNIQUE NOT NULL, -- 'ticket:view_all', 'admin:user_write', etc.
  resource VARCHAR(50) NOT NULL, -- 'ticket', 'kb', 'report', 'admin', 'ai'
  action VARCHAR(50) NOT NULL, -- 'view_all', 'create', 'edit', 'delete', etc.
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_permissions_resource ON permissions(resource);
```

**Role-Permission Mapping (Many-to-Many):**
```sql
CREATE TABLE role_permissions (
  role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
  permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
  granted_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
```

**User-Role Assignment (Many-to-Many):**
```sql
CREATE TABLE user_roles (
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
  assigned_at TIMESTAMP DEFAULT NOW(),
  assigned_by UUID REFERENCES users(id), -- Admin who assigned the role
  PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
```

**Team Membership (for Agent and Team Lead roles):**
```sql
CREATE TABLE teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) UNIQUE NOT NULL, -- 'Desktop Support', 'Network Operations', etc.
  description TEXT,
  team_lead_id UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE team_members (
  team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  joined_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (team_id, user_id)
);

CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);
```

#### 2.3.5 Authorization Enforcement

**Backend API Authorization:**

Every API endpoint checks permissions before executing:

```javascript
// Example: Update Ticket endpoint
async function updateTicket(req, res) {
  const { ticketId } = req.params;
  const currentUser = req.user; // Extracted from JWT

  // Fetch ticket from database
  const ticket = await Ticket.findById(ticketId);
  if (!ticket) return res.status(404).json({ error: 'Ticket not found' });

  // Authorization checks
  const userPermissions = await getUserPermissions(currentUser.id);

  // Check if user can edit this ticket
  const canEdit =
    userPermissions.includes('ticket:edit_all') || // Admin
    (userPermissions.includes('ticket:edit_assigned') && ticket.assigned_to === currentUser.id) || // Assigned agent
    (userPermissions.includes('ticket:view_team') && ticket.team_id === currentUser.team_id); // Team lead

  if (!canEdit) {
    return res.status(403).json({ error: 'Insufficient permissions to edit this ticket' });
  }

  // Proceed with update
  await ticket.update(req.body);

  // Log action in audit trail
  await AuditLog.create({
    user_id: currentUser.id,
    action: 'ticket:update',
    resource_type: 'ticket',
    resource_id: ticketId,
    changes: req.body,
    timestamp: new Date()
  });

  return res.json({ success: true, ticket });
}
```

**Frontend Authorization (UI-Level):**

- Frontend receives user's roles and permissions in JWT
- UI components conditionally render based on permissions:

```javascript
// React example
function TicketDetailPage({ ticket }) {
  const { permissions } = useAuth(); // Extract from decoded JWT

  return (
    <div>
      <h1>Ticket {ticket.id}</h1>
      <p>{ticket.description}</p>

      {permissions.includes('ticket:edit_assigned') && ticket.assignedTo === currentUser.id && (
        <button onClick={handleEdit}>Edit Ticket</button>
      )}

      {permissions.includes('ticket:reassign') && (
        <ReassignButton ticketId={ticket.id} />
      )}

      {permissions.includes('ticket:delete') && (
        <button onClick={handleDelete} className="danger">Delete Ticket</button>
      )}
    </div>
  );
}
```

- Note: Frontend checks are for UX only; backend always enforces authorization

**Caching Permissions:**

- User's permissions loaded on login and embedded in JWT
- If roles/permissions change, user must re-login (or force token refresh)
- For immediate effect, invalidate user's refresh tokens on role change

---

### 2.4 Handling Privileged Actions

Certain actions require extra scrutiny and logging, even if user has permission.

#### 2.4.1 Privileged Actions List

- Assigning or removing admin role
- Viewing or exporting audit logs
- Modifying system-wide configuration (SLA policies, AI settings)
- Deleting tickets or comments (rare, for compliance)
- Bulk data exports (potential data leak risk)
- Disabling MFA for another user

#### 2.4.2 Additional Security Measures

**Step-Up Authentication:**
- For privileged actions, require re-authentication or MFA even if already logged in
- Example: Admin tries to delete a user → Prompt for MFA code

**Four-Eyes Principle (Optional for Critical Actions):**
- Some actions require approval from second admin
- Example: Deleting 100+ tickets → First admin requests, second admin approves
- Reduces risk of insider threats or mistakes

**Audit Logging:**
- All privileged actions logged with:
  - Who: User ID, name, email
  - What: Action performed, resource affected
  - When: Timestamp (UTC)
  - Why: Justification text (required for sensitive actions)
  - How: IP address, user agent, session ID
  - Result: Success or failure

**Example Audit Log Entry:**
```json
{
  "id": "audit_log_12345",
  "timestamp": "2025-01-19T14:32:15Z",
  "user_id": "user_abc123",
  "user_email": "admin@digiskills.pk",
  "action": "user:role_assign",
  "details": {
    "target_user": "john.doe@digiskills.pk",
    "old_role": "agent",
    "new_role": "team_lead",
    "justification": "Promoted to team lead after 2 years of excellent performance"
  },
  "ip_address": "203.0.113.42",
  "user_agent": "Mozilla/5.0 ...",
  "result": "success"
}
```

**Audit Log Retention:**
- Store audit logs for minimum 1 year (compliance requirement)
- Archive older logs to cold storage (S3 Glacier, Azure Archive)
- Immutable logs: Cannot be edited or deleted by anyone (append-only)

---

### 2.5 Session Security Best Practices

#### 2.5.1 Token Security

**JWT Signing:**
- Use strong secret key (minimum 256 bits, randomly generated)
- Store secret in environment variable or secrets manager (AWS Secrets Manager, Azure Key Vault)
- Rotate signing key annually (support multiple active keys for grace period)

**Token Claims Validation:**
- Always validate `iss` (issuer), `aud` (audience), `exp` (expiry), `nbf` (not before)
- Verify token signature using public key or shared secret
- Reject tokens with suspicious claims (e.g., future issue time)

#### 2.5.2 Session Timeout and Idle Logout

**Idle Timeout:**
- Absolute session timeout: 8 hours (re-login required)
- Idle timeout: 30 minutes of inactivity
- Frontend tracks user activity (mouse move, keyboard input)
- If idle for 25 minutes, show warning: "Session expires in 5 minutes"
- If user interacts, refresh access token

**Implementation:**
```javascript
// Frontend idle detection
let idleTimer;
const IDLE_TIMEOUT = 30 * 60 * 1000; // 30 minutes

function resetIdleTimer() {
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => {
    // Show warning at 25 minutes
    showSessionExpiryWarning();
  }, 25 * 60 * 1000);
}

document.addEventListener('mousemove', resetIdleTimer);
document.addEventListener('keypress', resetIdleTimer);
```

#### 2.5.3 Concurrent Session Management

**Policy: Allow Multiple Sessions**
- User can be logged in from multiple devices (desktop, mobile, tablet)
- Each session has separate refresh token
- User can view and revoke active sessions from account settings

**Session Management UI:**
- Display list of active sessions:
  - Device type, browser, IP address, last activity
  - "Revoke" button to terminate specific session
- "Revoke All Other Sessions" button for security

**Backend Implementation:**
```sql
CREATE TABLE refresh_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(64) UNIQUE NOT NULL, -- SHA-256 hash of refresh token
  device_info JSONB, -- {device: 'Chrome on Windows', ip: '203.0.113.42'}
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP NOT NULL,
  last_used_at TIMESTAMP,
  revoked_at TIMESTAMP,
  revoked_reason VARCHAR(100) -- 'user_logout', 'admin_revoke', 'security_incident'
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
```

---

### 2.6 Password Policies (for Internal IdP Fallback)

If not using SSO and managing passwords internally:

**Password Requirements:**
- Minimum 12 characters
- Must include: uppercase, lowercase, number, special character
- Cannot be in common password list (haveibeenpwned.com API check)
- Cannot reuse last 5 passwords
- Password expiry: 90 days (optional, less common in modern security)

**Password Reset Flow:**
1. User clicks "Forgot Password"
2. Enter email → Backend sends reset link (expires in 1 hour)
3. Reset link contains single-use token (stored in database)
4. User clicks link, enters new password
5. Token validated and marked as used
6. Password updated, all refresh tokens revoked (force re-login)

**Account Lockout:**
- After 5 failed login attempts: Lock account for 15 minutes
- After 10 failed attempts in 1 hour: Lock account for 1 hour
- Admin can manually unlock account

---

### 2.7 Integration with External Systems

#### 2.7.1 SSO Integration Architecture

**Google Workspace Integration:**

1. **Google Cloud Console Setup:**
   - Create OAuth 2.0 client ID
   - Configure authorized redirect URIs: `https://helpdesk.digiskills.pk/auth/google/callback`
   - Enable Google Workspace domain restriction: Only `@digiskills.pk` accounts

2. **Helpdesk Backend Configuration:**
   - Store client ID and client secret in environment variables
   - Use Google OAuth 2.0 library (Passport.js for Node, Authlib for Python, etc.)

3. **User Provisioning:**
   - On first login, fetch user details from Google People API
   - Store email, name, profile picture
   - Optionally sync department/location from Google Directory API

4. **Periodic Sync (Optional):**
   - Daily job to sync user list from Google Workspace
   - Deactivate helpdesk accounts for users removed from Google Workspace
   - Update user details if changed in Google

**Microsoft Azure AD Integration:**
- Similar flow using SAML 2.0 or OpenID Connect
- Azure AD group membership can map to helpdesk roles
  - Example: Azure AD group "IT Support" → Helpdesk role "Agent"

#### 2.7.2 API Authentication (for External Integrations)

**Use Case:** External monitoring systems need to create tickets programmatically

**API Key Authentication:**
- Generate API keys for external systems
- API key format: `dsk_live_<random_32_chars>` (easy to identify and rotate)
- Store hashed API key in database (never plaintext)
- Each API key has:
  - Name/description (e.g., "Nagios Monitoring Integration")
  - Scopes/permissions (e.g., `ticket:create`, `ticket:view_all`)
  - Expiry date (optional, recommend annual rotation)
  - Last used timestamp

**API Key Usage:**
```bash
curl -X POST https://helpdesk.digiskills.pk/api/v1/tickets \
  -H "Authorization: Bearer dsk_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"title": "Server CPU high", "priority": "high", ...}'
```

**Rate Limiting:**
- API keys rate-limited separately from user sessions
- Default: 100 requests per minute per API key
- Prevents abuse and DoS attacks

---

### 2.8 Security Monitoring and Incident Response

#### 2.8.1 Security Monitoring

**Automated Alerts:**
- Multiple failed login attempts from single IP → Alert admin
- Login from unusual location (geo-fencing if user typically logs in from Pakistan and suddenly from another country)
- Privilege escalation (role change to admin) → Immediate notification
- Bulk data export by non-admin user → Alert and require justification

**Security Dashboards:**
- Admin dashboard shows:
  - Recent failed login attempts
  - Active sessions count
  - Recent role changes
  - API key usage and anomalies

#### 2.8.2 Incident Response Procedures

**Compromised Account:**
1. Detect suspicious activity (multiple failed logins, unusual access patterns)
2. Admin revokes all user's refresh tokens (force logout)
3. Disable account temporarily
4. Contact user via phone/alternate email to verify
5. If confirmed compromised: Reset password, force MFA enrollment
6. Review audit logs for unauthorized actions
7. Restore account after verification

**Compromised Admin Account:**
1. Immediate revocation of all sessions
2. Emergency admin account used to restore system
3. Full audit log review
4. Rotate all API keys and secrets
5. Notify senior management

---

## Summary: Authentication and Authorization Architecture

**Authentication Strategy:**
- Primary: SSO with Google Workspace or Microsoft Azure AD (OAuth 2.0 / OIDC)
- Fallback: Internal IdP with secure password policies
- Session management: JWT-based with refresh token rotation
- MFA: TOTP mandatory for admins, optional for other roles
- Token lifetime: 15-30 min access token, 7-30 day refresh token

**Authorization Model:**
- RBAC with 5 predefined roles (End User, Agent, Team Lead, Admin, Viewer)
- Fine-grained permissions (50+ permission types)
- Role-permission and user-role many-to-many mappings
- Permissions enforced at API layer (backend) and UI layer (frontend for UX)
- Special handling for privileged actions (step-up auth, audit logging)

**Security Posture:**
- Defense in depth: SSO + MFA + RBAC + audit logging
- Least privilege principle enforced
- Comprehensive audit trail for compliance
- Token-based stateless authentication for scalability
- Session security: HttpOnly, Secure, SameSite cookies
- Rate limiting and anomaly detection for abuse prevention

This authentication and authorization architecture ensures that the AI-powered helpdesk is **secure, scalable, and compliant**, while providing a **seamless user experience** through SSO and intelligent access controls.

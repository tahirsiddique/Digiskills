# AI-Powered IT Helpdesk - Security Considerations

## 5. Security Considerations

### 5.1 Security Principles and Threat Model

#### 5.1.1 Core Security Principles

**Defense in Depth:**
Multiple layers of security controls so that if one layer fails, others still protect the system.

```
Perimeter Security (WAF, DDoS Protection)
  ↓
Network Security (VPC, Security Groups, Firewalls)
  ↓
Application Security (Authentication, Authorization, Input Validation)
  ↓
Data Security (Encryption, Access Controls)
  ↓
Monitoring & Incident Response (Logging, Alerting, SIEM)
```

**Principle of Least Privilege:**
- Users and services get minimum permissions needed
- Default deny, explicitly grant access
- Regular permission audits to remove unused access

**Security by Design:**
- Security considerations from day one, not bolted on later
- Secure defaults (e.g., HTTPS required, secure cookies)
- Regular security reviews during development

**Zero Trust:**
- Never trust, always verify
- Authenticate and authorize every request
- No implicit trust based on network location

#### 5.1.2 Threat Model

**Assets to Protect:**
1. **User Data**: Personal information, contact details, department info
2. **Ticket Data**: Issue descriptions (may contain sensitive info), attachments (logs, screenshots)
3. **Knowledge Base**: Proprietary troubleshooting procedures, internal configurations
4. **Authentication Credentials**: Passwords, API keys, OAuth tokens, MFA secrets
5. **Audit Logs**: Evidence of who did what (critical for compliance)
6. **System Configuration**: Database credentials, AI API keys, encryption keys

**Threat Actors:**
1. **External Attackers**: Attempting unauthorized access, data theft, or service disruption
2. **Malicious Insiders**: Employees with legitimate access abusing privileges
3. **Compromised Accounts**: Legitimate user accounts taken over via phishing or credential stuffing
4. **Automated Bots**: Attempting brute force, vulnerability scanning, spam

**Attack Vectors:**
1. **Web Application Attacks**: XSS, CSRF, SQL Injection, IDOR, SSRF
2. **Authentication Attacks**: Credential stuffing, brute force, session hijacking
3. **API Abuse**: Rate limit bypass, mass data extraction
4. **Social Engineering**: Phishing, pretexting (especially for password resets)
5. **Supply Chain Attacks**: Compromised dependencies, malicious npm packages
6. **Infrastructure Attacks**: DDoS, cloud account compromise

**Impact Assessment:**
- **Critical**: Data breach exposing all user data or tickets
- **High**: Unauthorized access to admin functions, service downtime >1 hour
- **Medium**: Individual account compromise, data integrity issues
- **Low**: Minor information disclosure, temporary degradation

---

### 5.2 Authentication and Authorization Security

#### 5.2.1 SSO Security Best Practices

**OAuth 2.0 / OIDC Hardening:**

```typescript
// auth/google-sso.strategy.ts
import { Strategy } from 'passport-google-oauth20';

passport.use(new Strategy({
  clientID: process.env.GOOGLE_CLIENT_ID,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET,
  callbackURL: 'https://helpdesk.digiskills.pk/auth/google/callback',
  scope: ['profile', 'email'],

  // Security enhancements
  state: true,  // CSRF protection via state parameter
  pkce: true,   // Proof Key for Code Exchange (prevents auth code interception)

}, async (accessToken, refreshToken, profile, done) => {
  // Validate email domain
  const email = profile.emails[0].value;
  if (!email.endsWith('@digiskills.pk')) {
    return done(new Error('Unauthorized domain'), null);
  }

  // Verify email is verified by Google
  if (!profile.emails[0].verified) {
    return done(new Error('Email not verified'), null);
  }

  // Find or create user
  const user = await userService.findOrCreateFromSSO(profile);
  return done(null, user);
}));
```

**SSO Configuration Security:**
- **Redirect URI Validation**: Only allow `https://helpdesk.digiskills.pk/auth/google/callback` (no wildcards)
- **Token Validation**: Always verify ID token signature, issuer, audience, expiry
- **State Parameter**: Prevent CSRF attacks on OAuth flow
- **PKCE**: Prevent authorization code interception (required for public clients)

#### 5.2.2 Password Security (For Internal IdP Fallback)

**Password Hashing:**
```typescript
import * as bcrypt from 'bcrypt';

// Hash password with bcrypt (cost factor 12)
async hashPassword(password: string): Promise<string> {
  const saltRounds = 12;  // 2^12 iterations (adjustable for future hardware)
  return bcrypt.hash(password, saltRounds);
}

// Verify password
async verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}
```

**Why bcrypt?**
- **Slow by Design**: Takes ~100-300ms to hash (prevents brute force)
- **Adaptive**: Cost factor can be increased as hardware improves
- **Salted**: Each password gets unique salt (prevents rainbow table attacks)

**Password Policy Enforcement:**
```typescript
// validators/password.validator.ts
import * as zxcvbn from 'zxcvbn';
import axios from 'axios';

export class PasswordValidator {
  private static readonly MIN_LENGTH = 12;
  private static readonly COMMON_PASSWORDS = new Set([/* top 10k passwords */]);

  static async validate(password: string, userInfo?: { email: string; name: string }): Promise<ValidationResult> {
    const errors: string[] = [];

    // Length check
    if (password.length < this.MIN_LENGTH) {
      errors.push(`Password must be at least ${this.MIN_LENGTH} characters`);
    }

    // Complexity check
    const hasUppercase = /[A-Z]/.test(password);
    const hasLowercase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecial = /[^A-Za-z0-9]/.test(password);

    if (!(hasUppercase && hasLowercase && hasNumber && hasSpecial)) {
      errors.push('Password must contain uppercase, lowercase, number, and special character');
    }

    // Common password check
    if (this.COMMON_PASSWORDS.has(password.toLowerCase())) {
      errors.push('Password is too common');
    }

    // Strength check (zxcvbn library)
    const strength = zxcvbn(password, [userInfo?.email, userInfo?.name]);
    if (strength.score < 3) {  // 0-4 scale, 3 is "strong"
      errors.push(`Password is too weak: ${strength.feedback.warning || 'Use a stronger password'}`);
    }

    // Have I Been Pwned check (optional, requires API call)
    const isPwned = await this.checkHaveIBeenPwned(password);
    if (isPwned) {
      errors.push('This password has been exposed in a data breach and cannot be used');
    }

    return {
      valid: errors.length === 0,
      errors,
      strength: strength.score,
    };
  }

  private static async checkHaveIBeenPwned(password: string): Promise<boolean> {
    // Hash password with SHA-1
    const crypto = require('crypto');
    const hash = crypto.createHash('sha1').update(password).digest('hex').toUpperCase();
    const prefix = hash.slice(0, 5);
    const suffix = hash.slice(5);

    try {
      // Query HaveIBeenPwned API (k-anonymity model, only sends first 5 chars)
      const response = await axios.get(`https://api.pwnedpasswords.com/range/${prefix}`, {
        timeout: 2000,
      });

      // Check if suffix appears in response
      return response.data.includes(suffix);
    } catch {
      // If API fails, don't block user (availability > perfect security)
      return false;
    }
  }
}
```

**Account Lockout:**
```typescript
// auth/login.service.ts
export class LoginService {
  private static readonly MAX_ATTEMPTS = 5;
  private static readonly LOCKOUT_DURATION_MINUTES = 15;

  async login(email: string, password: string, ipAddress: string): Promise<LoginResult> {
    // Check if account is locked
    const user = await this.prisma.user.findUnique({ where: { email } });
    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }

    if (user.lockedUntil && user.lockedUntil > new Date()) {
      const remainingMinutes = Math.ceil((user.lockedUntil.getTime() - Date.now()) / 60000);
      throw new UnauthorizedException(`Account locked. Try again in ${remainingMinutes} minutes.`);
    }

    // Verify password
    const valid = await this.verifyPassword(password, user.passwordHash);
    if (!valid) {
      // Increment failed attempts
      const failedAttempts = user.failedLoginAttempts + 1;

      if (failedAttempts >= this.MAX_ATTEMPTS) {
        // Lock account
        await this.prisma.user.update({
          where: { id: user.id },
          data: {
            failedLoginAttempts: failedAttempts,
            lockedUntil: new Date(Date.now() + this.LOCKOUT_DURATION_MINUTES * 60000),
          },
        });

        // Alert user via email
        await this.emailService.sendAccountLockedNotification(user.email);

        // Log security event
        await this.auditLog.create({
          userId: user.id,
          action: 'account_locked',
          details: { reason: 'max_failed_attempts', ipAddress },
        });

        throw new UnauthorizedException('Account locked due to too many failed login attempts');
      }

      // Update failed attempts
      await this.prisma.user.update({
        where: { id: user.id },
        data: { failedLoginAttempts: failedAttempts },
      });

      throw new UnauthorizedException('Invalid credentials');
    }

    // Reset failed attempts on successful login
    await this.prisma.user.update({
      where: { id: user.id },
      data: {
        failedLoginAttempts: 0,
        lockedUntil: null,
        lastLoginAt: new Date(),
        lastLoginIp: ipAddress,
      },
    });

    return this.generateTokens(user);
  }
}
```

#### 5.2.3 MFA Security

**TOTP Secret Storage:**
```typescript
import * as crypto from 'crypto';

export class MFAService {
  private static readonly ALGORITHM = 'aes-256-gcm';
  private static readonly ENCRYPTION_KEY = Buffer.from(process.env.MFA_ENCRYPTION_KEY, 'hex'); // 32 bytes

  // Encrypt TOTP secret before storing in database
  static encryptSecret(secret: string): string {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(this.ALGORITHM, this.ENCRYPTION_KEY, iv);

    let encrypted = cipher.update(secret, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    // Return: iv + authTag + encrypted (all hex)
    return iv.toString('hex') + authTag.toString('hex') + encrypted;
  }

  // Decrypt TOTP secret when verifying code
  static decryptSecret(encryptedData: string): string {
    const iv = Buffer.from(encryptedData.slice(0, 32), 'hex');
    const authTag = Buffer.from(encryptedData.slice(32, 64), 'hex');
    const encrypted = encryptedData.slice(64);

    const decipher = crypto.createDecipheriv(this.ALGORITHM, this.ENCRYPTION_KEY, iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }

  // Verify TOTP code
  async verifyTOTP(userId: string, code: string): Promise<boolean> {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      select: { mfaSecretEncrypted: true, mfaUsedCodes: true },
    });

    if (!user.mfaSecretEncrypted) {
      throw new Error('MFA not enabled for user');
    }

    // Decrypt secret
    const secret = this.decryptSecret(user.mfaSecretEncrypted);

    // Verify code (allow ±1 time window for clock drift)
    const speakeasy = require('speakeasy');
    const verified = speakeasy.totp.verify({
      secret,
      encoding: 'base32',
      token: code,
      window: 1,  // Allow ±30 seconds
    });

    if (!verified) {
      return false;
    }

    // Prevent code reuse (replay attack protection)
    if (user.mfaUsedCodes?.includes(code)) {
      throw new Error('Code already used');
    }

    // Store used code (keep last 5 codes)
    const usedCodes = [...(user.mfaUsedCodes || []), code].slice(-5);
    await this.prisma.user.update({
      where: { id: userId },
      data: { mfaUsedCodes: usedCodes },
    });

    return true;
  }
}
```

**MFA Backup Codes:**
```typescript
// Generate 10 single-use backup codes
generateBackupCodes(): string[] {
  const codes: string[] = [];
  for (let i = 0; i < 10; i++) {
    // Generate 8-character alphanumeric code
    const code = crypto.randomBytes(4).toString('hex').toUpperCase();
    codes.push(code);
  }
  return codes;
}

// Hash backup codes before storing (bcrypt)
async storeBackupCodes(userId: string, codes: string[]): Promise<void> {
  const hashedCodes = await Promise.all(codes.map(code => bcrypt.hash(code, 10)));

  await this.prisma.user.update({
    where: { id: userId },
    data: { backupCodesHashed: hashedCodes },
  });
}

// Verify and consume backup code
async verifyBackupCode(userId: string, code: string): Promise<boolean> {
  const user = await this.prisma.user.findUnique({
    where: { id: userId },
    select: { backupCodesHashed: true },
  });

  // Try each stored code
  for (let i = 0; i < user.backupCodesHashed.length; i++) {
    const valid = await bcrypt.compare(code, user.backupCodesHashed[i]);
    if (valid) {
      // Remove used code
      const updatedCodes = user.backupCodesHashed.filter((_, idx) => idx !== i);
      await this.prisma.user.update({
        where: { id: userId },
        data: { backupCodesHashed: updatedCodes },
      });

      // Alert user if running low on backup codes
      if (updatedCodes.length <= 3) {
        await this.emailService.sendLowBackupCodesAlert(user.email, updatedCodes.length);
      }

      return true;
    }
  }

  return false;
}
```

#### 5.2.4 JWT Security

**JWT Configuration:**
```typescript
// config/jwt.config.ts
export const jwtConfig = {
  secret: process.env.JWT_SECRET,  // Strong random secret (min 256 bits)
  signOptions: {
    expiresIn: '15m',  // Short-lived access token
    algorithm: 'HS256',
    issuer: 'helpdesk.digiskills.pk',
    audience: 'helpdesk-api',
  },
  verifyOptions: {
    algorithms: ['HS256'],  // Explicitly specify algorithm (prevent "none" attack)
    issuer: 'helpdesk.digiskills.pk',
    audience: 'helpdesk-api',
  },
};

// Refresh token config
export const refreshTokenConfig = {
  secret: process.env.REFRESH_TOKEN_SECRET,  // Different secret from access token
  expiresIn: '7d',
};
```

**JWT Payload Minimization:**
```typescript
// Don't include sensitive data in JWT (it's base64, not encrypted)
interface JWTPayload {
  sub: string;        // User ID
  email: string;      // Email (for convenience)
  role: string;       // Primary role
  iat: number;        // Issued at
  exp: number;        // Expiry
  jti: string;        // JWT ID (for revocation)
}

// DON'T include:
// - Passwords or password hashes
// - Full permission list (too large, can change)
// - Sensitive user data
```

**JWT Validation:**
```typescript
// guards/jwt-auth.guard.ts
@Injectable()
export class JwtAuthGuard implements CanActivate {
  constructor(private jwtService: JwtService) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const token = this.extractTokenFromHeader(request);

    if (!token) {
      throw new UnauthorizedException('No token provided');
    }

    try {
      // Verify token signature and claims
      const payload = await this.jwtService.verifyAsync(token, {
        secret: jwtConfig.secret,
        algorithms: ['HS256'],  // Prevent algorithm confusion attacks
      });

      // Check if token is revoked (check Redis or database)
      const revoked = await this.isTokenRevoked(payload.jti);
      if (revoked) {
        throw new UnauthorizedException('Token has been revoked');
      }

      // Attach user to request
      request['user'] = payload;

      return true;
    } catch (error) {
      if (error.name === 'TokenExpiredError') {
        throw new UnauthorizedException('Token has expired');
      }
      throw new UnauthorizedException('Invalid token');
    }
  }

  private extractTokenFromHeader(request: Request): string | undefined {
    const [type, token] = request.headers.authorization?.split(' ') ?? [];
    return type === 'Bearer' ? token : undefined;
  }

  private async isTokenRevoked(jti: string): Promise<boolean> {
    // Check Redis blacklist
    const revoked = await this.redis.get(`revoked:${jti}`);
    return revoked === '1';
  }
}
```

---

### 5.3 Data Encryption

#### 5.3.1 Encryption in Transit (TLS/HTTPS)

**TLS Configuration:**
- **Minimum Version**: TLS 1.2 (prefer TLS 1.3)
- **Certificate**: Use trusted CA (Let's Encrypt, DigiCert, AWS ACM)
- **Cipher Suites**: Strong ciphers only (no RC4, 3DES, MD5)

**ALB/Nginx TLS Configuration:**
```nginx
# nginx.conf
server {
  listen 443 ssl http2;
  server_name helpdesk.digiskills.pk;

  # TLS certificates
  ssl_certificate /etc/nginx/ssl/fullchain.pem;
  ssl_certificate_key /etc/nginx/ssl/privkey.pem;

  # TLS version
  ssl_protocols TLSv1.2 TLSv1.3;

  # Cipher suites (Mozilla Intermediate configuration)
  ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
  ssl_prefer_server_ciphers on;

  # HSTS (force HTTPS for 1 year)
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

  # OCSP stapling
  ssl_stapling on;
  ssl_stapling_verify on;

  # Diffie-Hellman parameters
  ssl_dhparam /etc/nginx/ssl/dhparam.pem;

  location / {
    proxy_pass http://backend-servers;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host $host;
  }
}

# Redirect HTTP to HTTPS
server {
  listen 80;
  server_name helpdesk.digiskills.pk;
  return 301 https://$server_name$request_uri;
}
```

**Internal Service Communication:**
- All internal communication (API → Database, API → Redis, API → OpenSearch) over TLS
- Use VPC endpoints or private subnets to avoid public internet

**Database Connection Encryption:**
```typescript
// DATABASE_URL with SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require&sslrootcert=/path/to/ca-cert.pem

// Prisma automatically uses SSL when sslmode=require
```

#### 5.3.2 Encryption at Rest

**Database Encryption:**
- **AWS RDS**: Enable encryption at rest (AES-256 using AWS KMS)
- **Azure Database**: Transparent Data Encryption (TDE) enabled by default
- **Self-managed PostgreSQL**: Use pgcrypto extension for column-level encryption

**Disk Encryption:**
```yaml
# AWS RDS configuration (Terraform example)
resource "aws_db_instance" "helpdesk" {
  identifier = "helpdesk-db"
  engine     = "postgres"

  # Enable encryption at rest
  storage_encrypted = true
  kms_key_id        = aws_kms_key.db_encryption.arn

  # Encrypted backups
  backup_retention_period = 7
  # Backups automatically encrypted if storage_encrypted = true
}
```

**S3 Encryption:**
```yaml
# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "attachments" {
  bucket = aws_s3_bucket.attachments.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_encryption.arn
    }
  }
}

# Enforce encryption (reject unencrypted uploads)
resource "aws_s3_bucket_policy" "enforce_encryption" {
  bucket = aws_s3_bucket.attachments.id

  policy = jsonencode({
    Statement = [{
      Effect = "Deny"
      Principal = "*"
      Action = "s3:PutObject"
      Resource = "${aws_s3_bucket.attachments.arn}/*"
      Condition = {
        StringNotEquals = {
          "s3:x-amz-server-side-encryption" = "aws:kms"
        }
      }
    }]
  })
}
```

**Application-Level Field Encryption (for Extra Sensitive Data):**

```typescript
// utils/encryption.util.ts
import * as crypto from 'crypto';

export class FieldEncryption {
  private static readonly ALGORITHM = 'aes-256-gcm';
  private static readonly KEY = Buffer.from(process.env.FIELD_ENCRYPTION_KEY, 'hex');

  static encrypt(plaintext: string): string {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(this.ALGORITHM, this.KEY, iv);

    let encrypted = cipher.update(plaintext, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    // Format: iv:authTag:ciphertext
    return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
  }

  static decrypt(encryptedData: string): string {
    const [ivHex, authTagHex, encrypted] = encryptedData.split(':');

    const iv = Buffer.from(ivHex, 'hex');
    const authTag = Buffer.from(authTagHex, 'hex');

    const decipher = crypto.createDecipheriv(this.ALGORITHM, this.KEY, iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }
}

// Usage: Encrypt sensitive fields before storing
await prisma.user.create({
  data: {
    email: 'user@digiskills.pk',
    phone: FieldEncryption.encrypt('+92 300 1234567'),  // Encrypt phone number
    // Other non-sensitive fields stored in plaintext
  },
});
```

---

### 5.4 Protection Against Common Vulnerabilities (OWASP Top 10)

#### 5.4.1 SQL Injection Prevention

**Use Parameterized Queries (Prisma automatically does this):**
```typescript
// Safe: Prisma uses parameterized queries
const tickets = await prisma.ticket.findMany({
  where: {
    status: userInput,  // Automatically escaped
  },
});

// Unsafe: Raw SQL with string concatenation (DON'T DO THIS)
const tickets = await prisma.$queryRawUnsafe(
  `SELECT * FROM tickets WHERE status = '${userInput}'`  // SQL injection vulnerability!
);

// If you must use raw SQL, use parameterized queries:
const tickets = await prisma.$queryRaw`
  SELECT * FROM tickets WHERE status = ${userInput}
`;  // Safe: Prisma escapes the parameter
```

#### 5.4.2 Cross-Site Scripting (XSS) Prevention

**Output Encoding (React automatically escapes by default):**
```tsx
// Safe: React escapes HTML by default
<div>{ticket.description}</div>  // If description contains "<script>", it's rendered as text

// Unsafe: Using dangerouslySetInnerHTML without sanitization
<div dangerouslySetInnerHTML={{ __html: ticket.description }} />  // XSS vulnerability!

// Safe: Sanitize before using dangerouslySetInnerHTML
import DOMPurify from 'dompurify';

<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(ticket.description) }} />
```

**Content Security Policy (CSP):**
```typescript
// Set CSP headers
app.use((req, res, next) => {
  res.setHeader(
    'Content-Security-Policy',
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; " +  // Allow Next.js eval (only in dev)
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data: https:; " +
    "font-src 'self' data:; " +
    "connect-src 'self' https://api.openai.com; " +
    "frame-ancestors 'none'; " +
    "base-uri 'self'; " +
    "form-action 'self'"
  );
  next();
});
```

#### 5.4.3 Cross-Site Request Forgery (CSRF) Prevention

**SameSite Cookies:**
```typescript
// Set SameSite attribute on cookies
res.cookie('access_token', token, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',  // Prevents CSRF attacks
  maxAge: 15 * 60 * 1000,  // 15 minutes
});
```

**CSRF Tokens (for form submissions):**
```typescript
// Install csurf middleware
import * as csurf from 'csurf';

app.use(csurf({ cookie: true }));

// Endpoint to get CSRF token
@Get('csrf-token')
getCsrfToken(@Req() req): { csrfToken: string } {
  return { csrfToken: req.csrfToken() };
}

// Frontend includes CSRF token in form submission
<form>
  <input type="hidden" name="_csrf" value={csrfToken} />
  {/* other fields */}
</form>
```

#### 5.4.4 Insecure Direct Object Reference (IDOR) Prevention

**Always Verify Ownership/Permission:**
```typescript
// Vulnerable: Trusting user input without authorization check
@Get('tickets/:id')
async getTicket(@Param('id') id: string) {
  return this.prisma.ticket.findUnique({ where: { id } });  // Any user can access any ticket!
}

// Secure: Verify user has permission to view this ticket
@Get('tickets/:id')
@UseGuards(JwtAuthGuard)
async getTicket(@Param('id') id: string, @CurrentUser() user: User) {
  const ticket = await this.prisma.ticket.findUnique({ where: { id } });

  if (!ticket) {
    throw new NotFoundException('Ticket not found');
  }

  // Authorization check
  const hasPermission = await this.permissionsService.canViewTicket(user, ticket);
  if (!hasPermission) {
    throw new ForbiddenException('You do not have permission to view this ticket');
  }

  return ticket;
}

// permissionsService.canViewTicket implementation
async canViewTicket(user: User, ticket: Ticket): Promise<boolean> {
  // Check if user is ticket creator
  if (ticket.createdBy === user.id) return true;

  // Check if user is assigned agent
  if (ticket.assignedTo === user.id) return true;

  // Check if user is team lead of ticket's team
  if (user.role === 'team_lead' && ticket.teamId === user.teamId) return true;

  // Check if user is admin
  if (user.role === 'admin') return true;

  return false;
}
```

#### 5.4.5 Server-Side Request Forgery (SSRF) Prevention

**Validate and Whitelist URLs:**
```typescript
// Vulnerable: Allowing user to specify arbitrary URL
@Post('fetch-url')
async fetchUrl(@Body('url') url: string) {
  const response = await axios.get(url);  // SSRF vulnerability! User could access internal services
  return response.data;
}

// Secure: Whitelist allowed domains
@Post('fetch-url')
async fetchUrl(@Body('url') url: string) {
  const allowedDomains = ['api.example.com', 'cdn.digiskills.pk'];

  const parsedUrl = new URL(url);

  // Check domain whitelist
  if (!allowedDomains.includes(parsedUrl.hostname)) {
    throw new BadRequestException('Domain not allowed');
  }

  // Prevent access to private IP ranges
  const ip = await dns.promises.resolve4(parsedUrl.hostname);
  if (this.isPrivateIP(ip[0])) {
    throw new BadRequestException('Cannot access private IP addresses');
  }

  const response = await axios.get(url, {
    maxRedirects: 0,  // Prevent redirect to internal services
    timeout: 5000,
  });

  return response.data;
}

private isPrivateIP(ip: string): boolean {
  // Check for private IP ranges (10.x.x.x, 172.16-31.x.x, 192.168.x.x, 127.x.x.x)
  return /^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.)/.test(ip);
}
```

#### 5.4.6 XML External Entity (XXE) Prevention

**Disable External Entity Processing:**
```typescript
// If parsing XML (e.g., for SAML SSO), disable external entities
import * as xmlparser from 'fast-xml-parser';

const options = {
  ignoreAttributes: false,
  // Security: Disable external entities
  processEntities: false,
  allowBooleanAttributes: true,
};

const parsed = xmlparser.parse(xmlString, options);
```

#### 5.4.7 Security Misconfiguration Prevention

**Security Headers:**
```typescript
// Use Helmet.js to set security headers
import helmet from 'helmet';

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },
  frameguard: { action: 'deny' },  // Prevent clickjacking
  noSniff: true,  // X-Content-Type-Options: nosniff
  xssFilter: true,  // X-XSS-Protection: 1; mode=block
}));

// Additional security headers
app.use((req, res, next) => {
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  next();
});
```

**Hide Server Information:**
```typescript
// Don't expose technology stack
app.disable('x-powered-by');  // Remove "X-Powered-By: Express" header
```

---

### 5.5 API Security

#### 5.5.1 Rate Limiting

**Global Rate Limiting:**
```typescript
import { rateLimit } from 'express-rate-limit';

// Global rate limit: 100 requests per 15 minutes per IP
app.use(rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: 'Too many requests from this IP, please try again later',
  standardHeaders: true,
  legacyHeaders: false,
}));
```

**Endpoint-Specific Rate Limiting:**
```typescript
// Strict rate limit for login endpoint (prevent brute force)
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,  // Only 5 login attempts per 15 minutes
  skipSuccessfulRequests: true,  // Don't count successful logins
});

@Post('auth/login')
@UseGuards(loginLimiter)
async login(@Body() credentials: LoginDto) {
  return this.authService.login(credentials);
}

// Moderate rate limit for ticket creation
const ticketCreationLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 10,  // 10 tickets per minute
});

@Post('tickets')
@UseGuards(JwtAuthGuard, ticketCreationLimiter)
async createTicket(@Body() data: CreateTicketDto) {
  return this.ticketsService.create(data);
}
```

**Distributed Rate Limiting (Redis-based):**
```typescript
import { RateLimiterRedis } from 'rate-limiter-flexible';

const rateLimiter = new RateLimiterRedis({
  storeClient: redisClient,
  keyPrefix: 'rl',
  points: 100,  // Number of requests
  duration: 60,  // Per 60 seconds
  blockDuration: 60 * 15,  // Block for 15 minutes if exceeded
});

@Injectable()
export class RateLimitGuard implements CanActivate {
  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const key = request.user?.id || request.ip;  // Rate limit by user ID or IP

    try {
      await rateLimiter.consume(key);
      return true;
    } catch {
      throw new TooManyRequestsException('Rate limit exceeded');
    }
  }
}
```

#### 5.5.2 Input Validation

**Use DTOs with class-validator:**
```typescript
// dto/create-ticket.dto.ts
import { IsString, IsEmail, IsEnum, IsOptional, MaxLength, MinLength } from 'class-validator';

export class CreateTicketDto {
  @IsString()
  @MinLength(10, { message: 'Title must be at least 10 characters' })
  @MaxLength(500, { message: 'Title cannot exceed 500 characters' })
  title: string;

  @IsString()
  @MinLength(20, { message: 'Description must be at least 20 characters' })
  @MaxLength(10000, { message: 'Description cannot exceed 10,000 characters' })
  description: string;

  @IsEnum(['critical', 'high', 'medium', 'low'], { message: 'Invalid priority' })
  priority: string;

  @IsOptional()
  @IsEmail({}, { message: 'Invalid email format' })
  ccEmail?: string;

  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  @MaxLength(50, { each: true, message: 'Tag cannot exceed 50 characters' })
  tags?: string[];
}

// Controller
@Post('tickets')
@UsePipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true }))
async createTicket(@Body() data: CreateTicketDto) {
  // Data is automatically validated
  return this.ticketsService.create(data);
}
```

**Sanitize User Input:**
```typescript
import * as sanitizeHtml from 'sanitize-html';

// Sanitize HTML content (allow safe tags only)
export function sanitizeDescription(html: string): string {
  return sanitizeHtml(html, {
    allowedTags: ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'code', 'pre'],
    allowedAttributes: {},
  });
}

// Usage
async createTicket(data: CreateTicketDto) {
  return this.prisma.ticket.create({
    data: {
      ...data,
      description: sanitizeDescription(data.description),
    },
  });
}
```

#### 5.5.3 API Versioning and Deprecation

```typescript
// Support v1 and v2 simultaneously
@Controller('api/v1/tickets')
export class TicketsV1Controller {
  // Old API
}

@Controller('api/v2/tickets')
export class TicketsV2Controller {
  // New API with breaking changes
}

// Add deprecation warning header
app.use('/api/v1/*', (req, res, next) => {
  res.setHeader('X-API-Deprecation-Warning', 'API v1 is deprecated. Migrate to v2 by 2025-12-31.');
  next();
});
```

---

### 5.6 Secrets Management

#### 5.6.1 Environment Variables

**Never commit secrets to Git:**
```bash
# .gitignore
.env
.env.local
.env.production
secrets/
*.pem
*.key
```

**Use environment variables for all secrets:**
```bash
# .env.example (committed to Git as template)
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379
JWT_SECRET=your-secret-key-here
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

#### 5.6.2 Secrets Manager (Cloud)

**AWS Secrets Manager:**
```typescript
// Load secrets from AWS Secrets Manager
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

const secretsManager = new SecretsManager({ region: 'us-east-1' });

export async function loadSecrets() {
  const response = await secretsManager.getSecretValue({
    SecretId: 'helpdesk-production-secrets',
  });

  const secrets = JSON.parse(response.SecretString);

  // Set environment variables
  process.env.DATABASE_URL = secrets.DATABASE_URL;
  process.env.JWT_SECRET = secrets.JWT_SECRET;
  process.env.OPENAI_API_KEY = secrets.OPENAI_API_KEY;
}

// Call before app starts
loadSecrets().then(() => {
  // Start application
  bootstrap();
});
```

**Kubernetes Secrets:**
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: helpdesk-secrets
type: Opaque
stringData:
  database-url: postgresql://user:password@host:5432/db
  jwt-secret: your-jwt-secret
  openai-api-key: sk-...
---
# Use secrets in deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: helpdesk-api
spec:
  template:
    spec:
      containers:
      - name: api
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: helpdesk-secrets
              key: database-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: helpdesk-secrets
              key: jwt-secret
```

#### 5.6.3 Secrets Rotation

**Automated Secrets Rotation (AWS example):**
```typescript
// Rotate database password every 90 days
// Use AWS Lambda function triggered by EventBridge (cron)

export async function rotateDBPassword() {
  // Generate new password
  const newPassword = crypto.randomBytes(32).toString('base64');

  // Update password in database
  await rdsClient.modifyDBInstance({
    DBInstanceIdentifier: 'helpdesk-db',
    MasterUserPassword: newPassword,
    ApplyImmediately: true,
  });

  // Update secret in Secrets Manager
  await secretsManager.updateSecret({
    SecretId: 'helpdesk-db-password',
    SecretString: newPassword,
  });

  // Restart application pods to pick up new secret
  await eksClient.restartDeployment('helpdesk-api');
}
```

---

### 5.7 Audit Logging and Compliance

#### 5.7.1 Comprehensive Audit Logging

**What to Log:**
1. Authentication events (login, logout, failed attempts)
2. Authorization failures (permission denied)
3. Data access (viewing tickets, reports)
4. Data modifications (create, update, delete)
5. Privilege escalation (role changes)
6. Configuration changes
7. Security events (MFA bypass, account lockout)

**Audit Log Implementation:**
```typescript
// audit-log.service.ts
@Injectable()
export class AuditLogService {
  async log(event: AuditEvent): Promise<void> {
    await this.prisma.auditLog.create({
      data: {
        timestamp: new Date(),
        userId: event.userId,
        userEmail: event.userEmail,
        action: event.action,
        resourceType: event.resourceType,
        resourceId: event.resourceId,
        details: event.details,
        ipAddress: event.ipAddress,
        userAgent: event.userAgent,
        result: event.result,
      },
    });
  }

  async logDataAccess(user: User, resource: string, resourceId: string, request: Request) {
    await this.log({
      userId: user.id,
      userEmail: user.email,
      action: `${resource}:view`,
      resourceType: resource,
      resourceId,
      details: {},
      ipAddress: request.ip,
      userAgent: request.headers['user-agent'],
      result: 'success',
    });
  }

  async logDataModification(user: User, action: string, resource: string, resourceId: string, changes: any, request: Request) {
    await this.log({
      userId: user.id,
      userEmail: user.email,
      action: `${resource}:${action}`,
      resourceType: resource,
      resourceId,
      details: { changes },
      ipAddress: request.ip,
      userAgent: request.headers['user-agent'],
      result: 'success',
    });
  }
}

// Interceptor to automatically log all API requests
@Injectable()
export class AuditInterceptor implements NestInterceptor {
  constructor(private auditLog: AuditLogService) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const user = request.user;

    // Only log authenticated requests
    if (!user) {
      return next.handle();
    }

    const { method, url, body } = request;

    // Log sensitive operations
    if (method !== 'GET') {
      this.auditLog.log({
        userId: user.id,
        userEmail: user.email,
        action: `api:${method}:${url}`,
        resourceType: 'api',
        resourceId: url,
        details: { body: this.sanitizeBody(body) },
        ipAddress: request.ip,
        userAgent: request.headers['user-agent'],
        result: 'pending',
      });
    }

    return next.handle();
  }

  private sanitizeBody(body: any): any {
    // Remove sensitive fields from log
    const sanitized = { ...body };
    delete sanitized.password;
    delete sanitized.token;
    delete sanitized.apiKey;
    return sanitized;
  }
}
```

#### 5.7.2 Tamper-Proof Logs

**Append-Only Logs:**
```sql
-- Audit logs table (no UPDATE or DELETE permissions for application)
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMP DEFAULT NOW(),
  user_id UUID,
  action VARCHAR(100),
  details JSONB,
  -- Add hash of previous log entry for tamper detection
  previous_hash VARCHAR(64),
  current_hash VARCHAR(64)
);

-- Revoke UPDATE and DELETE permissions
REVOKE UPDATE, DELETE ON audit_logs FROM app_user;
GRANT INSERT, SELECT ON audit_logs TO app_user;
```

**Log Integrity Verification:**
```typescript
// Compute hash chain for tamper detection
import * as crypto from 'crypto';

async createAuditLog(event: AuditEvent): Promise<void> {
  // Get hash of previous log entry
  const previousLog = await this.prisma.auditLog.findFirst({
    orderBy: { timestamp: 'desc' },
    select: { currentHash: true },
  });

  const previousHash = previousLog?.currentHash || '0';

  // Compute hash of current entry
  const data = JSON.stringify(event);
  const currentHash = crypto.createHash('sha256')
    .update(previousHash + data)
    .digest('hex');

  await this.prisma.auditLog.create({
    data: {
      ...event,
      previousHash,
      currentHash,
    },
  });
}

// Verify log integrity
async verifyLogIntegrity(): Promise<boolean> {
  const logs = await this.prisma.auditLog.findMany({
    orderBy: { timestamp: 'asc' },
  });

  for (let i = 1; i < logs.length; i++) {
    const prev = logs[i - 1];
    const curr = logs[i];

    // Verify previous hash matches
    if (curr.previousHash !== prev.currentHash) {
      console.error(`Log integrity violation at entry ${curr.id}`);
      return false;
    }

    // Verify current hash
    const data = JSON.stringify({
      timestamp: curr.timestamp,
      userId: curr.userId,
      action: curr.action,
      details: curr.details,
    });
    const expectedHash = crypto.createHash('sha256')
      .update(curr.previousHash + data)
      .digest('hex');

    if (curr.currentHash !== expectedHash) {
      console.error(`Log hash mismatch at entry ${curr.id}`);
      return false;
    }
  }

  return true;
}
```

#### 5.7.3 Log Retention and Archival

```sql
-- Partition audit logs by month
CREATE TABLE audit_logs (
  id UUID,
  timestamp TIMESTAMP NOT NULL,
  -- other fields
) PARTITION BY RANGE (timestamp);

-- Automatically create partitions
CREATE TABLE audit_logs_2025_01 PARTITION OF audit_logs
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Older partitions moved to cold storage (S3 Glacier) after 1 year
-- Implement with cron job:
-- 1. Export partition to CSV
-- 2. Upload to S3 Glacier
-- 3. Drop partition from database
```

---

### 5.8 Security Monitoring and Incident Response

#### 5.8.1 Security Event Monitoring

**Automated Alerts:**
```typescript
// Monitor for suspicious activity
export class SecurityMonitor {
  async checkFailedLogins(userId: string): Promise<void> {
    const recentFailures = await this.prisma.auditLog.count({
      where: {
        userId,
        action: 'auth:login_failed',
        timestamp: { gte: new Date(Date.now() - 15 * 60 * 1000) },
      },
    });

    if (recentFailures >= 5) {
      await this.alertService.sendSecurityAlert({
        severity: 'high',
        message: `User ${userId} has ${recentFailures} failed login attempts in last 15 minutes`,
        action: 'account_lockout_recommended',
      });
    }
  }

  async checkUnusualAccess(userId: string, ipAddress: string): Promise<void> {
    // Check if IP is from different country than usual
    const userCountry = await this.geoip.lookup(ipAddress);
    const usualCountry = await this.getUserUsualCountry(userId);

    if (userCountry !== usualCountry) {
      await this.alertService.sendSecurityAlert({
        severity: 'medium',
        message: `User ${userId} logged in from unusual location: ${userCountry}`,
        action: 'verify_user_identity',
      });

      // Optionally: Require MFA for this session
    }
  }

  async checkPrivilegeEscalation(adminId: string, targetUserId: string, oldRole: string, newRole: string): Promise<void> {
    if (newRole === 'admin') {
      await this.alertService.sendSecurityAlert({
        severity: 'critical',
        message: `Admin ${adminId} granted admin role to user ${targetUserId}`,
        action: 'review_action',
      });
    }
  }
}
```

#### 5.8.2 Intrusion Detection

**Web Application Firewall (WAF):**
```yaml
# AWS WAF rules (CloudFormation example)
Resources:
  HelpdeskWAF:
    Type: AWS::WAFv2::WebACL
    Properties:
      DefaultAction:
        Allow: {}
      Rules:
        # Block common SQL injection patterns
        - Name: SQLInjectionRule
          Priority: 1
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesSQLiRuleSet
          OverrideAction:
            None: {}

        # Block common XSS patterns
        - Name: XSSRule
          Priority: 2
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesKnownBadInputsRuleSet
          OverrideAction:
            None: {}

        # Rate limiting (block IPs exceeding 2000 requests per 5 minutes)
        - Name: RateLimitRule
          Priority: 3
          Statement:
            RateBasedStatement:
              Limit: 2000
              AggregateKeyType: IP
          Action:
            Block: {}
```

#### 5.8.3 Incident Response Plan

**Security Incident Classification:**
1. **Critical**: Data breach, admin account compromise, ransomware
2. **High**: User account compromise, service unavailability >1 hour
3. **Medium**: Failed intrusion attempt, anomalous activity
4. **Low**: Policy violation, minor misconfiguration

**Incident Response Steps:**
1. **Detect**: Security monitoring alerts
2. **Contain**: Isolate affected systems, revoke compromised credentials
3. **Investigate**: Analyze audit logs, determine scope
4. **Eradicate**: Remove malicious code, patch vulnerabilities
5. **Recover**: Restore services, validate security
6. **Post-Mortem**: Document lessons learned, update security controls

**Example: Compromised Admin Account Response:**
```typescript
async respondToCompromisedAdmin(adminId: string): Promise<void> {
  // 1. Immediately revoke all sessions
  await this.authService.revokeAllUserSessions(adminId);

  // 2. Disable account
  await this.prisma.user.update({
    where: { id: adminId },
    data: { isActive: false },
  });

  // 3. Alert all other admins
  await this.alertService.sendEmergencyAlert({
    recipients: await this.getAllAdminEmails(),
    subject: 'SECURITY INCIDENT: Admin account compromised',
    body: `Admin account ${adminId} has been compromised and disabled. Please review recent actions.`,
  });

  // 4. Review recent actions by this admin
  const recentActions = await this.prisma.auditLog.findMany({
    where: {
      userId: adminId,
      timestamp: { gte: new Date(Date.now() - 24 * 60 * 60 * 1000) },
    },
    orderBy: { timestamp: 'desc' },
  });

  // 5. Revert suspicious actions (e.g., unauthorized role changes)
  for (const action of recentActions) {
    if (action.action === 'user:role_change' && action.details.newRole === 'admin') {
      // Revert role change
      await this.usersService.changeRole(action.resourceId, action.details.oldRole);
    }
  }

  // 6. Rotate all API keys and secrets
  await this.secretsService.rotateAllSecrets();

  // 7. Document incident
  await this.incidentService.createIncident({
    type: 'compromised_account',
    severity: 'critical',
    affectedUserId: adminId,
    actions: recentActions,
    timestamp: new Date(),
  });
}
```

---

### 5.9 Third-Party Security

#### 5.9.1 AI Service Security (OpenAI)

**Data Minimization:**
```typescript
// Don't send full ticket data to OpenAI, only necessary fields
async categorizeTicket(ticket: Ticket): Promise<CategoryPrediction> {
  // Bad: Sending entire ticket object (may contain PII)
  // const response = await openai.chat.completions.create({ messages: [{ content: JSON.stringify(ticket) }] });

  // Good: Send only title and description (no user names, emails, etc.)
  const response = await openai.chat.completions.create({
    messages: [{
      role: 'user',
      content: `Categorize this IT issue:\nTitle: ${ticket.title}\nDescription: ${ticket.description}`,
    }],
  });

  return response;
}
```

**API Key Security:**
```typescript
// Rotate OpenAI API keys quarterly
// Store in Secrets Manager
// Monitor usage and costs
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  organization: process.env.OPENAI_ORG_ID,
});

// Set usage limits
// OpenAI dashboard → Set monthly spending limit ($500/month)
// Alert when 80% of limit reached
```

#### 5.9.2 Dependency Security

**Automated Vulnerability Scanning:**
```bash
# npm audit (check for known vulnerabilities)
npm audit

# Fix vulnerabilities automatically
npm audit fix

# Fail CI build if high/critical vulnerabilities found
npm audit --audit-level=high

# Use Snyk or Dependabot for continuous monitoring
# GitHub: Enable Dependabot alerts and security updates
```

**Dependency Review:**
```json
// package.json - Pin dependency versions
{
  "dependencies": {
    "@nestjs/core": "10.2.10",  // Exact version (not ^10.2.10 or ~10.2.10)
    "prisma": "5.7.1",
    // ...
  }
}
```

**Supply Chain Security:**
- Review new dependencies before adding
- Prefer well-maintained packages (recent commits, many downloads)
- Use `npm audit` and Snyk to scan dependencies
- Lock dependency versions to prevent supply chain attacks

---

## Summary: Security Posture

**Authentication & Authorization:**
- SSO with Google/Microsoft (OAuth 2.0 + PKCE)
- MFA mandatory for admins (TOTP)
- JWT with short lifetime (15 min access, 7 day refresh)
- RBAC with least privilege principle

**Data Protection:**
- TLS 1.2+ for all communication
- Database encryption at rest (AES-256)
- Field-level encryption for extra sensitive data
- S3 encryption with KMS

**Vulnerability Protection:**
- SQL injection: Parameterized queries (Prisma)
- XSS: React auto-escaping + CSP headers
- CSRF: SameSite cookies + CSRF tokens
- IDOR: Authorization checks on every request
- SSRF: URL whitelisting + private IP blocking

**API Security:**
- Rate limiting (global + per-endpoint)
- Input validation with DTOs
- Output encoding
- API versioning

**Secrets Management:**
- AWS Secrets Manager / Kubernetes Secrets
- No secrets in Git
- Automated rotation (quarterly)

**Monitoring & Response:**
- Comprehensive audit logging (tamper-proof)
- Security event alerts (failed logins, privilege escalation)
- Incident response plan
- WAF for common attack patterns

**Third-Party Security:**
- Data minimization for AI services
- Dependency scanning (npm audit, Snyk)
- API key rotation

This multi-layered security architecture ensures the helpdesk system is **resilient against common threats** while maintaining **usability and compliance** with industry best practices.

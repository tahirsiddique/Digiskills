# AI-Powered IT Helpdesk - Scalability and Performance

## 4. Scalability and Performance

### 4.1 Scalability Overview and Targets

#### 4.1.1 Current and Projected Scale

**Current Requirements (Year 1):**
- Users: 500-2,000 employees
- Daily tickets: 50-500
- Concurrent users: 50-200 during peak hours
- Knowledge base: 100-500 articles
- Database size: <10 GB
- Monthly attachment storage: 5-20 GB

**3-Year Growth Projection:**
- Users: 1,500-5,000 employees (2.5x growth)
- Daily tickets: 150-1,500 (3x growth)
- Concurrent users: 150-500
- Knowledge base: 500-2,000 articles (4x growth)
- Database size: 50-100 GB
- Monthly attachment storage: 20-100 GB

**5-Year Stretch Goal:**
- Users: 5,000-10,000 employees
- Daily tickets: 500-3,000
- Concurrent users: 500-1,000
- Knowledge base: 2,000-5,000 articles
- Database size: 200-500 GB

#### 4.1.2 Performance Targets (SLAs)

**Response Time SLAs:**
- **API Response Time (p95)**: <500ms for typical requests
- **API Response Time (p99)**: <1,000ms
- **Page Load Time (First Contentful Paint)**: <1.5s
- **Page Load Time (Largest Contentful Paint)**: <2.5s
- **Time to Interactive**: <3.5s
- **WebSocket Message Latency**: <100ms

**Throughput Targets:**
- **API Requests per Second (RPS)**: Support 500 RPS (peak load)
- **Database Transactions per Second (TPS)**: 1,000 TPS
- **Concurrent WebSocket Connections**: 500 connections

**Availability Target:**
- **Uptime SLA**: 99.5% (≈3.6 hours downtime per month)
- **Recovery Time Objective (RTO)**: <1 hour
- **Recovery Point Objective (RPO)**: <15 minutes (max data loss)

**Resource Utilization Targets:**
- **CPU Utilization**: <70% average, <90% peak
- **Memory Utilization**: <80% average
- **Database Connection Pool**: <80% utilization

---

### 4.2 Horizontal Scaling Strategies

#### 4.2.1 Application Server Scaling

**Stateless Application Design:**

The application is designed to be **stateless**, meaning any API server can handle any request. This enables easy horizontal scaling.

**Key Stateless Design Principles:**
- **No In-Memory Session Storage**: Sessions stored in JWT (client-side) or Redis (shared)
- **No In-Memory Caching**: Use Redis for shared cache across all servers
- **No Local File Storage**: All uploads go directly to S3
- **Idempotent Operations**: Requests can be retried safely

**Scaling Strategy:**

```
Initial Deployment (Year 1):
- 2 API servers (for redundancy)
- 1 worker server (background jobs)

Growth Phase (Year 2-3):
- 3-5 API servers (auto-scaling based on CPU/memory)
- 2-3 worker servers (dedicated for AI, email, reports)

Mature Phase (Year 4-5):
- 5-10 API servers (auto-scaling)
- 5+ worker servers (specialized: AI workers, email workers, report workers)
```

**Containerization with Docker:**

```dockerfile
# Dockerfile for API Server
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --production

# Copy application code
COPY dist ./dist
COPY prisma ./prisma

# Generate Prisma client
RUN npx prisma generate

EXPOSE 3000

CMD ["node", "dist/main.js"]
```

**Orchestration: Kubernetes or AWS ECS**

**Option 1: Kubernetes (Recommended for multi-cloud or on-prem)**

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: helpdesk-api
spec:
  replicas: 3  # Start with 3 replicas
  selector:
    matchLabels:
      app: helpdesk-api
  template:
    metadata:
      labels:
        app: helpdesk-api
    spec:
      containers:
      - name: api
        image: digiskills/helpdesk-api:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: connection-string
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: helpdesk-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: helpdesk-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Option 2: AWS ECS with Fargate (Simpler, Managed)**

```json
// ecs-task-definition.json
{
  "family": "helpdesk-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "digiskills/helpdesk-api:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "NODE_ENV", "value": "production"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:db-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/helpdesk-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

**ECS Auto-Scaling Policy:**
```json
{
  "ServiceName": "helpdesk-api-service",
  "MinCapacity": 2,
  "MaxCapacity": 10,
  "TargetTrackingScalingPolicies": [
    {
      "TargetValue": 70.0,
      "PredefinedMetricSpecification": {
        "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
      },
      "ScaleOutCooldown": 60,
      "ScaleInCooldown": 300
    }
  ]
}
```

#### 4.2.2 Load Balancing

**Architecture:**

```
Internet → CloudFront (CDN) → Application Load Balancer (ALB) → Target Group (API Servers)
```

**Application Load Balancer (ALB) Configuration:**

```yaml
# ALB configuration (pseudo-YAML)
LoadBalancer:
  Name: helpdesk-alb
  Scheme: internet-facing
  Type: application

  Listeners:
    - Port: 443
      Protocol: HTTPS
      Certificates:
        - CertificateArn: arn:aws:acm:region:account:certificate/...
      DefaultActions:
        - Type: forward
          TargetGroupArn: arn:aws:elasticloadbalancing:...

    - Port: 80
      Protocol: HTTP
      DefaultActions:
        - Type: redirect
          RedirectConfig:
            Protocol: HTTPS
            Port: 443
            StatusCode: HTTP_301

  TargetGroup:
    Name: helpdesk-api-tg
    Port: 3000
    Protocol: HTTP
    HealthCheck:
      Path: /health
      Interval: 30
      Timeout: 5
      HealthyThreshold: 2
      UnhealthyThreshold: 3
      Matcher: "200"

    Stickiness:
      Enabled: false  # Not needed for stateless API

    Deregistration Delay: 30  # Graceful shutdown time
```

**Load Balancing Algorithms:**
- **Round Robin** (default): Distribute requests evenly across all healthy targets
- **Least Outstanding Requests**: Send to server with fewest active requests (better for variable request durations)

**WebSocket Sticky Sessions:**
- WebSocket connections require sticky sessions (connection affinity)
- ALB supports WebSocket upgrade and maintains connection to same server
- Use separate target group for WebSocket servers if needed

**Health Checks:**

```typescript
// src/health.controller.ts
@Controller('health')
export class HealthController {
  constructor(
    private prisma: PrismaService,
    private redis: Redis,
  ) {}

  @Get()
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
    };
  }

  @Get('ready')
  async readinessCheck(): Promise<{ status: string; dependencies: any }> {
    // Check critical dependencies
    const dbHealthy = await this.checkDatabase();
    const redisHealthy = await this.checkRedis();

    const healthy = dbHealthy && redisHealthy;

    if (!healthy) {
      throw new HttpException('Service not ready', HttpStatus.SERVICE_UNAVAILABLE);
    }

    return {
      status: 'ready',
      dependencies: {
        database: dbHealthy ? 'healthy' : 'unhealthy',
        redis: redisHealthy ? 'healthy' : 'unhealthy',
      },
    };
  }

  private async checkDatabase(): Promise<boolean> {
    try {
      await this.prisma.$queryRaw`SELECT 1`;
      return true;
    } catch {
      return false;
    }
  }

  private async checkRedis(): Promise<boolean> {
    try {
      await this.redis.ping();
      return true;
    } catch {
      return false;
    }
  }
}
```

**Graceful Shutdown:**

```typescript
// src/main.ts
async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Enable graceful shutdown
  app.enableShutdownHooks();

  // Handle SIGTERM (from Kubernetes/ECS during scaling down)
  process.on('SIGTERM', async () => {
    console.log('SIGTERM received, starting graceful shutdown...');

    // Stop accepting new requests
    await app.close();

    // Allow in-flight requests to complete (up to 30 seconds)
    setTimeout(() => {
      console.log('Forced shutdown after 30s');
      process.exit(0);
    }, 30000);
  });

  await app.listen(3000);
}
```

#### 4.2.3 Database Scaling

**Vertical Scaling (Primary Strategy for Year 1-3):**
- Start with moderate instance: AWS RDS db.t3.large (2 vCPU, 8 GB RAM)
- Scale up as needed: db.m5.xlarge (4 vCPU, 16 GB), db.m5.2xlarge (8 vCPU, 32 GB)
- PostgreSQL can handle 1,000-5,000 TPS on modern hardware

**Read Replicas (For Heavy Read Workloads):**

```
Primary DB (Write) → Replication → Read Replica 1 (Read)
                                  → Read Replica 2 (Read)
```

**Use Cases for Read Replicas:**
- Dashboard queries (reports, analytics)
- Knowledge base search (read-heavy)
- Ticket list views (read-heavy)

**Application-Level Read/Write Splitting:**

```typescript
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
  previewFeatures = ["multiSchema"]
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")  // Primary (read+write)
  // Read replica URLs configured at runtime
}

// src/database/prisma.service.ts
@Injectable()
export class PrismaService extends PrismaClient {
  private readReplica: PrismaClient;

  constructor() {
    super({
      datasources: {
        db: { url: process.env.DATABASE_URL },
      },
    });

    // Initialize read replica client
    this.readReplica = new PrismaClient({
      datasources: {
        db: { url: process.env.DATABASE_READ_REPLICA_URL },
      },
    });
  }

  // Explicitly use read replica for read-only queries
  getReadReplica(): PrismaClient {
    return this.readReplica;
  }
}

// Usage in service
const tickets = await this.prisma.getReadReplica().ticket.findMany({
  where: { status: 'open' },
  orderBy: { createdAt: 'desc' },
  take: 20,
});
```

**Connection Pooling:**

```typescript
// Database connection pool configuration
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  // Connection pool settings
  // Format: postgresql://user:pass@host:5432/db?connection_limit=20&pool_timeout=10
}

// Recommended pool size:
// connection_limit = (Number of API servers * 10) + (Number of workers * 5)
// Example: 3 API servers + 2 workers = (3*10) + (2*5) = 40 connections
```

**Alternative: PgBouncer (Connection Pooler)**
- Place PgBouncer between application and PostgreSQL
- Reduces connection overhead (PostgreSQL connections are expensive)
- Pool modes: Session pooling (safest), Transaction pooling (more efficient)

```
API Servers (100 connections) → PgBouncer (10 pooled connections) → PostgreSQL
```

**Partitioning (Future Optimization for Large Tables):**

```sql
-- Partition audit_logs by month for better performance
CREATE TABLE audit_logs (
  id UUID,
  timestamp TIMESTAMP NOT NULL,
  user_id UUID,
  action VARCHAR(100),
  details JSONB
) PARTITION BY RANGE (timestamp);

-- Create partitions for each month
CREATE TABLE audit_logs_2025_01 PARTITION OF audit_logs
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE audit_logs_2025_02 PARTITION OF audit_logs
  FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Query automatically uses correct partition
SELECT * FROM audit_logs WHERE timestamp >= '2025-01-15';
-- Only scans audit_logs_2025_01, not entire table
```

---

### 4.3 Caching Strategies

#### 4.3.1 Multi-Layer Caching

```
Browser Cache → CDN Cache → Application Cache (Redis) → Database Query Cache
```

#### 4.3.2 CDN Caching (CloudFront / Cloudflare)

**Cached Content:**
- Static assets: JavaScript bundles, CSS, images, fonts
- KB article images and videos
- User avatars (if not from SSO)

**Cache Duration:**
- Immutable assets (with hash in filename): 1 year
- Other static assets: 7 days
- KB article content: 1 hour (dynamic content)

**CloudFront Configuration:**

```yaml
Behaviors:
  - PathPattern: /_next/static/*
    CacheDuration: 31536000  # 1 year (immutable Next.js assets)
    Compress: true

  - PathPattern: /kb-images/*
    CacheDuration: 604800  # 7 days
    Compress: true

  - PathPattern: /api/*
    CacheDuration: 0  # No caching for API requests
    AllowedMethods: [GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD]
```

**Cache Invalidation:**
- Immutable assets: No invalidation needed (hash changes on update)
- KB images: Invalidate on article update
- Use CloudFront invalidation API or versioned URLs

#### 4.3.3 Application-Level Caching (Redis)

**Cache Patterns:**

**1. Cache-Aside (Lazy Loading):**
```typescript
async getUserPermissions(userId: string): Promise<string[]> {
  const cacheKey = `user:${userId}:permissions`;

  // Try cache first
  const cached = await this.redis.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  // Cache miss, fetch from DB
  const permissions = await this.fetchPermissionsFromDB(userId);

  // Store in cache (15 min TTL)
  await this.redis.setex(cacheKey, 900, JSON.stringify(permissions));

  return permissions;
}
```

**2. Write-Through Cache:**
```typescript
async updateUserRole(userId: string, newRole: string): Promise<void> {
  // Update database
  await this.prisma.user.update({
    where: { id: userId },
    data: { role: newRole },
  });

  // Invalidate cache immediately
  await this.redis.del(`user:${userId}:permissions`);

  // Optionally: Pre-populate cache with new permissions
  const newPermissions = await this.fetchPermissionsFromDB(userId);
  await this.redis.setex(`user:${userId}:permissions`, 900, JSON.stringify(newPermissions));
}
```

**3. Cache with TTL and Refresh:**
```typescript
async getFeaturedKBArticles(): Promise<Article[]> {
  const cacheKey = 'kb:featured';

  const cached = await this.redis.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  const articles = await this.prisma.kbArticle.findMany({
    where: { featured: true, published: true },
    take: 10,
    orderBy: { viewCount: 'desc' },
  });

  // Cache for 1 hour
  await this.redis.setex(cacheKey, 3600, JSON.stringify(articles));

  return articles;
}
```

**What to Cache:**

| Data Type | Cache Duration | Invalidation Strategy |
|-----------|----------------|----------------------|
| User permissions | 15 minutes | On role change |
| System config (SLA policies) | 1 hour | On config update |
| Featured KB articles | 1 hour | Periodic refresh |
| Ticket counts by status | 5 minutes | Real-time not critical |
| Team member lists | 30 minutes | On team update |
| Category trees | 1 day | Rarely changes |

**Cache Key Naming Convention:**
```
{resource}:{identifier}:{attribute}

Examples:
user:123e4567:permissions
ticket:987fcdeb:details
team:abc123:members
config:sla:policies
kb:featured:articles
```

**Cache Eviction Strategies:**
- Use TTL for most caches (automatic expiration)
- Manual invalidation for critical data (roles, permissions)
- LRU (Least Recently Used) eviction when Redis memory full

#### 4.3.4 Database Query Result Caching

**PostgreSQL Query Result Cache (Application Level):**

```typescript
// Decorator for automatic caching
export function Cacheable(ttl: number) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const cacheKey = `query:${propertyKey}:${JSON.stringify(args)}`;
      const redis = this.redis as Redis;

      const cached = await redis.get(cacheKey);
      if (cached) {
        return JSON.parse(cached);
      }

      const result = await originalMethod.apply(this, args);
      await redis.setex(cacheKey, ttl, JSON.stringify(result));

      return result;
    };

    return descriptor;
  };
}

// Usage
@Injectable()
export class ReportsService {
  @Cacheable(300)  // Cache for 5 minutes
  async getTicketVolumeReport(startDate: Date, endDate: Date): Promise<VolumeReport> {
    // Expensive aggregation query
    const result = await this.prisma.ticket.groupBy({
      by: ['status', 'priority'],
      where: {
        createdAt: { gte: startDate, lte: endDate },
      },
      _count: true,
    });

    return this.formatReport(result);
  }
}
```

**Materialized Views (PostgreSQL):**

For extremely heavy queries (e.g., monthly reports), use materialized views:

```sql
-- Create materialized view for monthly ticket metrics
CREATE MATERIALIZED VIEW monthly_ticket_metrics AS
SELECT
  DATE_TRUNC('month', created_at) AS month,
  status,
  priority,
  category_id,
  COUNT(*) AS ticket_count,
  AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))) AS avg_resolution_seconds
FROM tickets
WHERE created_at >= NOW() - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', created_at), status, priority, category_id;

-- Create index on materialized view
CREATE INDEX idx_monthly_metrics_month ON monthly_ticket_metrics(month);

-- Refresh materialized view daily (via cron job)
REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_ticket_metrics;
```

**Benefits:**
- Report queries run in milliseconds instead of seconds
- Reduces load on primary tables
- Refresh can happen during off-peak hours

---

### 4.4 Database Optimizations

#### 4.4.1 Indexing Strategy

**Index Creation Guidelines:**

1. **Index Foreign Keys**: Always index columns used in JOINs
2. **Index Filter Columns**: Columns frequently used in WHERE clauses
3. **Index Sort Columns**: Columns used in ORDER BY
4. **Composite Indexes**: Multiple columns used together in queries

**Example Indexes:**

```sql
-- Tickets table indexes
CREATE INDEX idx_tickets_status ON tickets(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_tickets_assigned_to ON tickets(assigned_to) WHERE status IN ('open', 'in_progress');
CREATE INDEX idx_tickets_team_status ON tickets(team_id, status);
CREATE INDEX idx_tickets_created_at_desc ON tickets(created_at DESC);
CREATE INDEX idx_tickets_sla_breach ON tickets(sla_resolution_deadline) WHERE resolved_at IS NULL AND sla_resolution_deadline < NOW();

-- Composite index for common ticket list query
CREATE INDEX idx_tickets_user_status_created ON tickets(created_by, status, created_at DESC);

-- Partial index for open tickets (most frequently queried)
CREATE INDEX idx_tickets_open ON tickets(team_id, created_at DESC) WHERE status IN ('new', 'open', 'in_progress');

-- JSON field index (JSONB in PostgreSQL)
CREATE INDEX idx_tickets_ai_confidence ON tickets((ai_metadata->>'confidence')) WHERE ai_metadata IS NOT NULL;
```

**Index Monitoring:**

```sql
-- Find unused indexes (candidates for removal)
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan AS index_scans,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Find missing indexes (queries doing sequential scans)
SELECT
  schemaname,
  tablename,
  seq_scan,
  seq_tup_read,
  idx_scan,
  seq_tup_read / seq_scan AS avg_seq_tup_read
FROM pg_stat_user_tables
WHERE seq_scan > 0
  AND seq_tup_read / seq_scan > 10000
ORDER BY seq_tup_read DESC;
```

#### 4.4.2 Query Optimization

**Use EXPLAIN ANALYZE:**

```sql
EXPLAIN ANALYZE
SELECT t.*, u.full_name, c.name AS category_name
FROM tickets t
JOIN users u ON t.assigned_to = u.id
JOIN categories c ON t.category_id = c.id
WHERE t.team_id = '123e4567-e89b-12d3-a456-426614174000'
  AND t.status IN ('open', 'in_progress')
ORDER BY t.created_at DESC
LIMIT 20;

-- Look for:
-- - Index scans (good) vs Sequential scans (bad for large tables)
-- - Nested loops vs Hash joins (depends on table size)
-- - High execution time
```

**Optimization Techniques:**

1. **Use Pagination:**
```typescript
// Bad: Load all tickets
const tickets = await prisma.ticket.findMany();

// Good: Paginate
const tickets = await prisma.ticket.findMany({
  skip: (page - 1) * limit,
  take: limit,
});
```

2. **Select Only Needed Columns:**
```typescript
// Bad: Load entire ticket object with all relations
const tickets = await prisma.ticket.findMany({
  include: { comments: true, attachments: true, history: true },
});

// Good: Select only needed fields
const tickets = await prisma.ticket.findMany({
  select: {
    id: true,
    title: true,
    status: true,
    priority: true,
    createdAt: true,
    assignedAgent: {
      select: { id: true, fullName: true },
    },
  },
});
```

3. **Batch Queries (Avoid N+1 Problem):**
```typescript
// Bad: N+1 query (1 query for tickets + N queries for each ticket's agent)
const tickets = await prisma.ticket.findMany();
for (const ticket of tickets) {
  ticket.agent = await prisma.user.findUnique({ where: { id: ticket.assignedTo } });
}

// Good: Single query with JOIN
const tickets = await prisma.ticket.findMany({
  include: { assignedAgent: true },
});
```

4. **Use Database-Level Aggregation:**
```typescript
// Bad: Load all tickets and count in application
const tickets = await prisma.ticket.findMany();
const openCount = tickets.filter(t => t.status === 'open').length;

// Good: Count in database
const openCount = await prisma.ticket.count({
  where: { status: 'open' },
});
```

#### 4.4.3 Connection Management

**Connection Pool Configuration:**

```typescript
// prisma/schema.prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// DATABASE_URL format with connection pooling:
// postgresql://user:password@host:5432/database?connection_limit=20&pool_timeout=10&connect_timeout=5
```

**Recommended Pool Sizes:**
- API servers: 10-20 connections per instance
- Workers: 5-10 connections per instance
- Total should not exceed PostgreSQL's `max_connections` setting (default 100, increase to 200-500 for production)

**Connection Pooler: PgBouncer (for High Concurrency)**

```ini
# pgbouncer.ini
[databases]
helpdesk = host=postgres-primary.internal port=5432 dbname=helpdesk

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction  # Or session for safer mode
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
server_idle_timeout = 600
```

**Application connects to PgBouncer instead of PostgreSQL directly:**
```
DATABASE_URL=postgresql://user:password@pgbouncer:6432/helpdesk
```

---

### 4.5 Asynchronous Processing

#### 4.5.1 Background Job Patterns

**Use Cases for Async Processing:**
1. **AI Predictions**: Ticket categorization (1-5 seconds)
2. **Email Sending**: SMTP can be slow or fail, don't block API
3. **Report Generation**: Large reports take 10-60 seconds
4. **Data Exports**: CSV/PDF generation for large datasets
5. **Search Indexing**: Update OpenSearch after DB changes
6. **Scheduled Tasks**: Daily SLA compliance reports, weekly summaries

**BullMQ Queue Architecture:**

```typescript
// queues/queue-manager.ts
import { Queue, Worker, QueueScheduler } from 'bullmq';

const connection = {
  host: process.env.REDIS_HOST,
  port: parseInt(process.env.REDIS_PORT),
};

// Define queues
export const queues = {
  ai: new Queue('ai-processing', { connection }),
  email: new Queue('email', { connection }),
  reports: new Queue('reports', { connection }),
  searchSync: new Queue('search-sync', { connection }),
};

// Queue scheduler (for delayed/scheduled jobs)
new QueueScheduler('ai-processing', { connection });
new QueueScheduler('email', { connection });
new QueueScheduler('reports', { connection });
new QueueScheduler('search-sync', { connection });
```

**Producer (Add Jobs to Queue):**

```typescript
// tickets.service.ts
async createTicket(data: CreateTicketDto, user: User): Promise<Ticket> {
  // Create ticket in database
  const ticket = await this.prisma.ticket.create({ data });

  // Queue AI categorization (non-blocking)
  await queues.ai.add('categorize-ticket', {
    ticketId: ticket.id,
    title: ticket.title,
    description: ticket.description,
  }, {
    attempts: 3,
    backoff: { type: 'exponential', delay: 2000 },
  });

  // Queue notification email
  await queues.email.add('ticket-created', {
    ticketId: ticket.id,
    recipientId: ticket.assignedTo,
  });

  return ticket;
}
```

**Consumer (Process Jobs):**

```typescript
// workers/ai-worker.ts
const aiWorker = new Worker('ai-processing', async (job) => {
  console.log(`Processing ${job.name} for ticket ${job.data.ticketId}`);

  if (job.name === 'categorize-ticket') {
    const { ticketId, title, description } = job.data;

    // Call AI service
    const prediction = await aiService.categorizeTicket(title, description);

    // Update ticket
    await prisma.ticket.update({
      where: { id: ticketId },
      data: {
        aiSuggestedCategory: prediction.category,
        aiConfidence: prediction.confidence,
        category: prediction.confidence > 0.85 ? prediction.category : null,
      },
    });

    // Notify frontend via WebSocket
    websocketGateway.emit(`ticket:${ticketId}:updated`, {
      category: prediction.category,
      confidence: prediction.confidence,
    });

    return { success: true, prediction };
  }
}, {
  connection,
  concurrency: 5,  // Process 5 jobs concurrently
});

// Error handling
aiWorker.on('failed', (job, err) => {
  console.error(`Job ${job.id} failed:`, err);
  // Optionally: Send alert to monitoring system
});

// Progress tracking
aiWorker.on('progress', (job, progress) => {
  console.log(`Job ${job.id} progress: ${progress}%`);
});
```

#### 4.5.2 Job Prioritization

```typescript
// High priority: Critical ticket needs immediate AI categorization
await queues.ai.add('categorize-ticket', data, {
  priority: 1,  // Higher priority (1 is highest)
});

// Normal priority: Regular ticket
await queues.ai.add('categorize-ticket', data, {
  priority: 5,  // Default priority
});

// Low priority: Batch processing
await queues.ai.add('batch-categorize', data, {
  priority: 10,  // Lower priority
});
```

#### 4.5.3 Scheduled Jobs (Cron-like)

```typescript
// Schedule daily SLA compliance report at 6 AM
await queues.reports.add('sla-compliance-daily', {}, {
  repeat: {
    pattern: '0 6 * * *',  // Cron expression: 6 AM daily
    tz: 'Asia/Karachi',
  },
});

// Schedule monthly cleanup of old audit logs
await queues.maintenance.add('cleanup-audit-logs', {}, {
  repeat: {
    pattern: '0 2 1 * *',  // 2 AM on 1st of each month
  },
});
```

---

### 4.6 Performance Monitoring and Optimization

#### 4.6.1 Application Performance Monitoring (APM)

**Recommended Tools:**
- **New Relic**: Comprehensive APM, distributed tracing, real user monitoring
- **Datadog**: APM + infrastructure monitoring
- **Open Source: Grafana + Prometheus + Jaeger**

**Key Metrics to Monitor:**

**1. Request Metrics:**
- Requests per second (RPS)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx responses)
- Request duration by endpoint

**2. Database Metrics:**
- Query duration (slow query log)
- Connection pool utilization
- Active connections
- Transaction rate (TPS)

**3. Cache Metrics:**
- Cache hit rate
- Cache miss rate
- Redis memory usage
- Redis command latency

**4. Queue Metrics:**
- Jobs completed/failed
- Queue length (backlog)
- Job processing time
- Worker utilization

**5. AI Service Metrics:**
- AI API latency
- AI API error rate
- Token usage (cost tracking)
- Model accuracy (feedback acceptance rate)

#### 4.6.2 Custom Instrumentation

```typescript
// interceptors/performance.interceptor.ts
@Injectable()
export class PerformanceInterceptor implements NestInterceptor {
  constructor(private prometheus: PrometheusService) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url } = request;
    const start = Date.now();

    return next.handle().pipe(
      tap({
        next: () => {
          const duration = Date.now() - start;

          // Record metrics
          this.prometheus.recordRequestDuration(method, url, 'success', duration);

          // Log slow requests
          if (duration > 1000) {
            console.warn(`Slow request: ${method} ${url} took ${duration}ms`);
          }
        },
        error: (error) => {
          const duration = Date.now() - start;
          this.prometheus.recordRequestDuration(method, url, 'error', duration);
        },
      }),
    );
  }
}
```

**Prometheus Metrics Example:**

```typescript
// prometheus.service.ts
@Injectable()
export class PrometheusService {
  private requestDuration: Histogram;
  private requestCounter: Counter;

  constructor() {
    this.requestDuration = new Histogram({
      name: 'http_request_duration_ms',
      help: 'Duration of HTTP requests in ms',
      labelNames: ['method', 'route', 'status'],
      buckets: [10, 50, 100, 200, 500, 1000, 2000, 5000],
    });

    this.requestCounter = new Counter({
      name: 'http_requests_total',
      help: 'Total number of HTTP requests',
      labelNames: ['method', 'route', 'status'],
    });
  }

  recordRequestDuration(method: string, route: string, status: string, duration: number) {
    this.requestDuration.observe({ method, route, status }, duration);
    this.requestCounter.inc({ method, route, status });
  }
}
```

#### 4.6.3 Database Query Performance Monitoring

**Slow Query Logging:**

```sql
-- Enable slow query logging in PostgreSQL
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries taking >1 second
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
SELECT pg_reload_conf();

-- View slow queries
SELECT
  query,
  calls,
  total_time / 1000 AS total_seconds,
  mean_time / 1000 AS avg_seconds,
  max_time / 1000 AS max_seconds
FROM pg_stat_statements
WHERE mean_time > 1000  -- Average duration > 1 second
ORDER BY mean_time DESC
LIMIT 20;
```

**Prisma Query Logging:**

```typescript
// Enable Prisma query logging
const prisma = new PrismaClient({
  log: [
    { level: 'query', emit: 'event' },
    { level: 'error', emit: 'stdout' },
    { level: 'warn', emit: 'stdout' },
  ],
});

prisma.$on('query', (e) => {
  if (e.duration > 1000) {
    console.warn(`Slow query (${e.duration}ms):`, e.query);
  }
});
```

#### 4.6.4 Frontend Performance Optimization

**Code Splitting:**
```typescript
// app/admin/page.tsx - Admin page only loads when accessed
import dynamic from 'next/dynamic';

const AdminDashboard = dynamic(() => import('@/components/admin/AdminDashboard'), {
  loading: () => <LoadingSpinner />,
  ssr: false,  // Don't render on server (admin only)
});
```

**Image Optimization:**
```tsx
// Use Next.js Image component for automatic optimization
import Image from 'next/image';

<Image
  src="/kb-article-screenshot.png"
  width={800}
  height={600}
  alt="KB Article Screenshot"
  loading="lazy"  // Lazy load images below fold
/>
```

**Bundle Analysis:**
```bash
# Analyze bundle size
npm run build && npx @next/bundle-analyzer
```

---

### 4.7 Performance Testing

#### 4.7.1 Load Testing Strategy

**Tools:**
- **k6**: Modern load testing tool, scripted in JavaScript
- **Apache JMeter**: Traditional, GUI-based
- **Artillery**: Simple YAML-based configuration

**Test Scenarios:**

1. **Baseline Test**: Normal load (50 concurrent users)
2. **Load Test**: Expected peak load (200 concurrent users)
3. **Stress Test**: Find breaking point (500+ concurrent users)
4. **Spike Test**: Sudden traffic surge
5. **Endurance Test**: Sustained load for 1+ hours (check for memory leaks)

**k6 Load Test Example:**

```javascript
// loadtests/ticket-creation.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users for 5 min
    { duration: '2m', target: 200 },  // Ramp up to 200 users
    { duration: '5m', target: 200 },  // Stay at 200 users for 5 min
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests < 500ms
    http_req_failed: ['rate<0.01'],    // Error rate < 1%
  },
};

export default function () {
  // Login
  const loginRes = http.post('https://helpdesk.digiskills.pk/api/v1/auth/login', {
    email: 'test.user@digiskills.pk',
    password: 'TestPassword123',
  });

  check(loginRes, { 'login successful': (r) => r.status === 200 });
  const token = loginRes.json('access_token');

  // Create ticket
  const ticketRes = http.post(
    'https://helpdesk.digiskills.pk/api/v1/tickets',
    JSON.stringify({
      title: 'Test ticket',
      description: 'Load test ticket',
      priority: 'medium',
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    },
  );

  check(ticketRes, {
    'ticket created': (r) => r.status === 201,
    'response time OK': (r) => r.timings.duration < 500,
  });

  sleep(1);  // Wait 1 second between iterations
}
```

**Run Load Test:**
```bash
k6 run --vus 200 --duration 10m loadtests/ticket-creation.js
```

#### 4.7.2 Performance Benchmarks

**Target Benchmarks (Year 1):**
- Create ticket: <300ms (p95)
- List tickets: <200ms (p95)
- View ticket detail: <250ms (p95)
- KB search: <400ms (p95)
- Generate report: <2 seconds (simple), <30 seconds (complex)

**Acceptable Degradation Under Load:**
- At 200 concurrent users: Response time +50% (still <750ms for ticket creation)
- At 500 concurrent users: Response time +100% (may degrade, but system stays available)

---

## Summary: Scalability and Performance Strategy

**Horizontal Scaling:**
- Stateless application design enables easy horizontal scaling
- Containerized with Docker, orchestrated with Kubernetes or ECS
- Auto-scaling based on CPU/memory (2-10 instances)
- Application Load Balancer distributes traffic

**Caching:**
- Multi-layer: Browser → CDN → Redis → Database
- Redis caches user permissions, config, KB articles (5 min - 1 hour TTL)
- CDN caches static assets (1 year for immutable, 7 days for others)

**Database:**
- PostgreSQL with proper indexing (all foreign keys, filter columns, composite indexes)
- Read replicas for heavy read workloads (reports, dashboards)
- Connection pooling (20 connections per server) or PgBouncer for high concurrency

**Asynchronous Processing:**
- BullMQ queues for AI, email, reports, search indexing
- Background workers process jobs with retry logic
- Job prioritization for critical tasks

**Performance Monitoring:**
- APM (New Relic or Datadog) for request/database/cache metrics
- Prometheus + Grafana for custom metrics and dashboards
- Slow query logging and regular performance reviews
- Load testing with k6 before major releases

This architecture comfortably handles **500-2,000 users** in Year 1, and scales to **5,000-10,000 users** by Year 5 with predictable, manageable infrastructure growth.

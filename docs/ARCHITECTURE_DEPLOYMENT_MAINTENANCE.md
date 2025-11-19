# AI-Powered IT Helpdesk - Deployment and Maintenance

## 6. Deployment and Maintenance

### 6.1 Cloud Platform Selection

#### 6.1.1 Platform Comparison and Recommendation

**Key Decision Factors for Digiskills.pk:**
- **Budget**: Cost-effective for small to medium scale
- **Compliance**: Data residency in Pakistan or approved regions
- **Expertise**: Existing team skills and learning curve
- **Scalability**: Ability to grow from 500 to 10,000 users
- **Managed Services**: Reduce operational overhead

**Recommended Platform: AWS (Amazon Web Services)**

**Rationale:**

✅ **AWS Benefits:**
- **Comprehensive Services**: Complete ecosystem (compute, database, storage, AI, monitoring)
- **Global Presence**: AWS Asia Pacific (Singapore, Mumbai) regions for low latency
- **Managed Services**: RDS, ElastiCache, OpenSearch, S3 reduce operational burden
- **Cost Optimization**: Free tier, reserved instances, spot instances for workers
- **Strong Security**: Compliance certifications (ISO 27001, SOC 2), robust IAM
- **Mature Ecosystem**: Extensive documentation, large community, many third-party integrations
- **Scalability**: Proven at massive scale, auto-scaling capabilities

**Alternative Options:**

**Azure (Microsoft Azure):**
- ✅ Strong if Digiskills.pk already uses Microsoft 365 (integrated SSO)
- ✅ Azure OpenAI Service with enterprise SLAs
- ❌ Slightly more expensive than AWS for equivalent services
- **Recommendation**: Good alternative if Microsoft ecosystem is preferred

**Google Cloud Platform (GCP):**
- ✅ Excellent if using Google Workspace (integrated SSO)
- ✅ Strong AI/ML offerings (Vertex AI, BigQuery)
- ❌ Smaller market share, fewer third-party integrations
- **Recommendation**: Good for Google Workspace users with strong data analytics needs

**On-Premise / Hybrid:**
- ✅ Full control over data and infrastructure
- ❌ High capital expenditure (servers, networking, cooling)
- ❌ Requires dedicated DevOps/SysAdmin team
- ❌ Disaster recovery more complex
- **Recommendation**: Not recommended unless strict data residency laws prohibit cloud

**Final Recommendation: AWS** with potential migration path to multi-cloud if needed in future.

---

### 6.2 Infrastructure Architecture (AWS)

#### 6.2.1 AWS Service Selection

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Architecture                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐                                             │
│  │  CloudFront    │  CDN for static assets                      │
│  │  (CDN)         │                                             │
│  └────────┬───────┘                                             │
│           │                                                      │
│  ┌────────▼────────┐         ┌──────────────┐                  │
│  │ Application     │         │   Route 53   │  DNS             │
│  │ Load Balancer   │◄────────│              │                  │
│  │ (ALB)           │         └──────────────┘                  │
│  └────────┬────────┘                                            │
│           │                                                      │
│  ┌────────▼────────────────────────────────────────┐           │
│  │              ECS Fargate Cluster                 │           │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │           │
│  │  │  API 1   │  │  API 2   │  │  API 3   │      │  Auto-    │
│  │  │ Container│  │ Container│  │ Container│      │  Scaling  │
│  │  └──────────┘  └──────────┘  └──────────┘      │           │
│  │                                                  │           │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │           │
│  │  │Worker 1  │  │Worker 2  │  │Worker 3  │      │           │
│  │  │(AI Queue)│  │(Email)   │  │(Reports) │      │           │
│  │  └──────────┘  └──────────┘  └──────────┘      │           │
│  └──────────────────────────────────────────────────┘          │
│           │                │                                    │
│  ┌────────▼────────┐  ┌───▼──────────┐                         │
│  │  RDS PostgreSQL │  │ ElastiCache  │                         │
│  │  (Primary +     │  │   (Redis)    │                         │
│  │   Read Replica) │  └──────────────┘                         │
│  └─────────────────┘                                            │
│           │                                                      │
│  ┌────────▼────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  S3 Buckets     │  │  OpenSearch  │  │   Secrets    │      │
│  │  (Attachments)  │  │  (KB Search) │  │   Manager    │      │
│  └─────────────────┘  └──────────────┘  └──────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Monitoring & Logging                     │      │
│  │  CloudWatch │ X-Ray │ CloudTrail │ GuardDuty         │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**AWS Services Breakdown:**

| Service | Purpose | Cost Estimate (Monthly) |
|---------|---------|-------------------------|
| **ECS Fargate** | Container orchestration (3 API tasks, 3 worker tasks) | $150-300 |
| **Application Load Balancer** | Traffic distribution, SSL termination | $25-50 |
| **RDS PostgreSQL** | Primary database (db.t3.large + read replica) | $150-250 |
| **ElastiCache Redis** | Caching and message queue (cache.t3.medium) | $50-80 |
| **S3** | Object storage for attachments (100 GB + requests) | $5-15 |
| **CloudFront** | CDN for static assets (1 TB transfer) | $80-120 |
| **OpenSearch** | Semantic search (t3.medium.search, 2 nodes) | $150-200 |
| **Route 53** | DNS management | $1-5 |
| **Secrets Manager** | Secrets storage (10 secrets) | $5-10 |
| **CloudWatch** | Logging and monitoring (10 GB logs) | $10-20 |
| **ACM** | SSL certificates | Free |
| **Backup** | Automated backups | $20-40 |
| **Data Transfer** | Outbound traffic (500 GB) | $40-80 |
| **Total Estimated Cost** | | **$686-1,170/month** |

**Cost Optimization Strategies:**
- Use Reserved Instances for steady-state workloads (30-50% savings)
- Spot Instances for non-critical workers (60-70% savings)
- S3 Intelligent-Tiering for automatic cost optimization
- Right-size instances based on actual usage (start small, scale up)

#### 6.2.2 Network Architecture (VPC)

```
┌────────────────────────────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)                            │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────┐  ┌───────────────────────┐         │
│  │   Public Subnet A     │  │   Public Subnet B     │         │
│  │   (10.0.1.0/24)       │  │   (10.0.2.0/24)       │         │
│  │   AZ: us-east-1a      │  │   AZ: us-east-1b      │         │
│  ├───────────────────────┤  ├───────────────────────┤         │
│  │ NAT Gateway A         │  │ NAT Gateway B         │         │
│  │ Load Balancer         │  │ Load Balancer         │         │
│  └───────────────────────┘  └───────────────────────┘         │
│           │                           │                         │
│  ┌────────▼──────────────┐  ┌────────▼──────────────┐         │
│  │   Private Subnet A    │  │   Private Subnet B    │         │
│  │   (10.0.10.0/24)      │  │   (10.0.11.0/24)      │         │
│  │   AZ: us-east-1a      │  │   AZ: us-east-1b      │         │
│  ├───────────────────────┤  ├───────────────────────┤         │
│  │ ECS Tasks (API)       │  │ ECS Tasks (API)       │         │
│  │ ECS Tasks (Workers)   │  │ ECS Tasks (Workers)   │         │
│  └───────────────────────┘  └───────────────────────┘         │
│           │                           │                         │
│  ┌────────▼──────────────┐  ┌────────▼──────────────┐         │
│  │   Private Subnet C    │  │   Private Subnet D    │         │
│  │   (10.0.20.0/24)      │  │   (10.0.21.0/24)      │         │
│  │   AZ: us-east-1a      │  │   AZ: us-east-1b      │         │
│  ├───────────────────────┤  ├───────────────────────┤         │
│  │ RDS Primary           │  │ RDS Read Replica      │         │
│  │ ElastiCache           │  │ ElastiCache           │         │
│  │ OpenSearch            │  │ OpenSearch            │         │
│  └───────────────────────┘  └───────────────────────┘         │
│                                                                 │
│  Security Groups:                                              │
│  • ALB: Allow 80, 443 from Internet                           │
│  • ECS: Allow 3000 from ALB only                              │
│  • RDS: Allow 5432 from ECS only                              │
│  • Redis: Allow 6379 from ECS only                            │
│  • OpenSearch: Allow 9200 from ECS only                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

**Security Groups Configuration:**

```hcl
# Terraform configuration
resource "aws_security_group" "alb" {
  name   = "helpdesk-alb-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Allow HTTPS from anywhere
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Allow HTTP (redirect to HTTPS)
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_tasks" {
  name   = "helpdesk-ecs-tasks-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]  # Only from ALB
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]  # Allow outbound (for API calls, etc.)
  }
}

resource "aws_security_group" "rds" {
  name   = "helpdesk-rds-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]  # Only from ECS
  }
}

resource "aws_security_group" "redis" {
  name   = "helpdesk-redis-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]  # Only from ECS
  }
}
```

---

### 6.3 CI/CD Pipeline

#### 6.3.1 CI/CD Architecture

```
Developer → Git Push → GitHub
                         ↓
                  GitHub Actions
                         ↓
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
    Build Checks    Security Scans    Tests
    • Lint          • npm audit       • Unit Tests
    • TypeScript    • Snyk            • Integration
    • Prettier      • Trivy (Docker)  • E2E Tests
        ↓                ↓                ↓
        └────────────────┼────────────────┘
                         ↓
                  Build Docker Image
                         ↓
                  Push to ECR (AWS)
                         ↓
            ┌────────────┼────────────┐
            ↓            ↓            ↓
        Staging      Production   Production
        Deploy       Approval     Deploy
        (Auto)       (Manual)     (Rolling)
```

#### 6.3.2 GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: helpdesk-api
  ECS_SERVICE: helpdesk-api-service
  ECS_CLUSTER: helpdesk-cluster

jobs:
  # Step 1: Code Quality and Linting
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run ESLint
        run: npm run lint

      - name: Check TypeScript
        run: npm run type-check

      - name: Check formatting (Prettier)
        run: npm run format:check

  # Step 2: Security Scanning
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run npm audit
        run: npm audit --audit-level=high
        continue-on-error: true

      - name: Run Snyk Security Scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

      - name: OWASP Dependency Check
        uses: dependency-check/Dependency-Check_Action@main
        with:
          project: 'helpdesk'
          path: '.'
          format: 'HTML'

  # Step 3: Automated Tests
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: helpdesk_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run Prisma migrations
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/helpdesk_test
        run: npx prisma migrate deploy

      - name: Run unit tests
        run: npm run test:unit

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/helpdesk_test
          REDIS_URL: redis://localhost:6379
        run: npm run test:integration

      - name: Generate coverage report
        run: npm run test:coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  # Step 4: Build Docker Image
  build:
    needs: [lint, security, test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'

    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build, tag, and push image to ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

          # Also tag as 'latest' for convenience
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Scan Docker image with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  # Step 5: Deploy to Staging (auto)
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Update ECS task definition
        run: |
          aws ecs update-service \
            --cluster helpdesk-staging-cluster \
            --service helpdesk-api-staging \
            --force-new-deployment

      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster helpdesk-staging-cluster \
            --services helpdesk-api-staging

      - name: Run smoke tests
        run: |
          curl -f https://staging.helpdesk.digiskills.pk/health || exit 1

  # Step 6: Deploy to Production (manual approval)
  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production  # Requires manual approval in GitHub

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Download task definition
        run: |
          aws ecs describe-task-definition \
            --task-definition helpdesk-api \
            --query taskDefinition > task-definition.json

      - name: Update task definition with new image
        id: task-def
        uses: aws-actions/amazon-ecs-render-task-definition@v1
        with:
          task-definition: task-definition.json
          container-name: api
          image: ${{ secrets.ECR_REGISTRY }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}

      - name: Deploy to ECS (rolling update)
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.task-def.outputs.task-definition }}
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true

      - name: Verify deployment
        run: |
          # Check health endpoint
          curl -f https://helpdesk.digiskills.pk/health || exit 1

          # Check that new version is deployed
          DEPLOYED_VERSION=$(curl -s https://helpdesk.digiskills.pk/api/version | jq -r '.version')
          echo "Deployed version: $DEPLOYED_VERSION"

      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "✅ Production deployment successful!",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Helpdesk Production Deployment*\n✅ Successfully deployed commit `${{ github.sha }}`"
                  }
                }
              ]
            }
```

#### 6.3.3 Deployment Strategies

**Rolling Deployment (Default):**
```yaml
# ECS Service configuration
resource "aws_ecs_service" "api" {
  name            = "helpdesk-api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 3

  deployment_configuration {
    minimum_healthy_percent = 100  # Keep all tasks running during deployment
    maximum_percent         = 200  # Can temporarily have 2x tasks
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true  # Auto-rollback on failure
  }
}
```

**Blue-Green Deployment (for critical updates):**
```bash
# Create new task set (green)
aws ecs create-task-set \
  --cluster helpdesk-cluster \
  --service helpdesk-api-service \
  --task-definition helpdesk-api:NEW_VERSION

# Shift traffic gradually (10%, 50%, 100%)
aws ecs update-service-primary-task-set \
  --cluster helpdesk-cluster \
  --service helpdesk-api-service \
  --primary-task-set GREEN_TASK_SET_ARN

# If issues detected, instantly rollback to blue
aws ecs update-service-primary-task-set \
  --primary-task-set BLUE_TASK_SET_ARN
```

**Canary Deployment (via ALB weighted routing):**
```hcl
# ALB Target Group for canary
resource "aws_lb_target_group" "canary" {
  name     = "helpdesk-api-canary"
  port     = 3000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }
}

# ALB Listener rule with weighted routing
resource "aws_lb_listener_rule" "weighted" {
  listener_arn = aws_lb_listener.https.arn

  action {
    type = "forward"
    forward {
      target_group {
        arn    = aws_lb_target_group.main.arn
        weight = 90  # 90% traffic to stable version
      }
      target_group {
        arn    = aws_lb_target_group.canary.arn
        weight = 10  # 10% traffic to canary version
      }
    }
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}
```

---

### 6.4 Monitoring and Observability

#### 6.4.1 Three Pillars of Observability

**1. Metrics (CloudWatch Metrics)**
**2. Logs (CloudWatch Logs)**
**3. Traces (AWS X-Ray)**

#### 6.4.2 Key Metrics to Monitor

**Application Metrics:**
```typescript
// Custom CloudWatch metrics
import { CloudWatch } from '@aws-sdk/client-cloudwatch';

const cloudwatch = new CloudWatch({ region: 'us-east-1' });

export class MetricsService {
  async recordTicketCreated(priority: string) {
    await cloudwatch.putMetricData({
      Namespace: 'Helpdesk/Application',
      MetricData: [
        {
          MetricName: 'TicketsCreated',
          Value: 1,
          Unit: 'Count',
          Dimensions: [
            { Name: 'Priority', Value: priority },
          ],
          Timestamp: new Date(),
        },
      ],
    });
  }

  async recordAPILatency(endpoint: string, duration: number) {
    await cloudwatch.putMetricData({
      Namespace: 'Helpdesk/Application',
      MetricData: [
        {
          MetricName: 'APILatency',
          Value: duration,
          Unit: 'Milliseconds',
          Dimensions: [
            { Name: 'Endpoint', Value: endpoint },
          ],
        },
      ],
    });
  }

  async recordAIConfidence(confidence: number) {
    await cloudwatch.putMetricData({
      Namespace: 'Helpdesk/AI',
      MetricData: [
        {
          MetricName: 'AIConfidence',
          Value: confidence,
          Unit: 'None',
          StatisticValues: {
            SampleCount: 1,
            Sum: confidence,
            Minimum: confidence,
            Maximum: confidence,
          },
        },
      ],
    });
  }
}
```

**CloudWatch Dashboard:**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "API Request Rate",
        "metrics": [
          ["AWS/ApplicationELB", "RequestCount", { "stat": "Sum" }]
        ],
        "period": 300,
        "region": "us-east-1"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "API Latency (p95)",
        "metrics": [
          ["AWS/ApplicationELB", "TargetResponseTime", { "stat": "p95" }]
        ],
        "period": 300,
        "yAxis": { "left": { "max": 1000 } }
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Database Connections",
        "metrics": [
          ["AWS/RDS", "DatabaseConnections", { "stat": "Average" }]
        ]
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Redis Cache Hit Rate",
        "metrics": [
          ["AWS/ElastiCache", "CacheHitRate", { "stat": "Average" }]
        ]
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "ECS CPU Utilization",
        "metrics": [
          ["AWS/ECS", "CPUUtilization", { "stat": "Average" }]
        ]
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Tickets Created (by Priority)",
        "metrics": [
          ["Helpdesk/Application", "TicketsCreated", { "Priority": "critical" }],
          ["...", { "Priority": "high" }],
          ["...", { "Priority": "medium" }],
          ["...", { "Priority": "low" }]
        ]
      }
    }
  ]
}
```

#### 6.4.3 Logging Strategy

**Structured Logging:**
```typescript
// logger.service.ts
import * as winston from 'winston';
import { CloudWatchLogsClient } from '@aws-sdk/client-cloudwatch-logs';

export const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'helpdesk-api',
    environment: process.env.NODE_ENV,
  },
  transports: [
    // Console (for CloudWatch Logs via ECS log driver)
    new winston.transports.Console(),

    // File (for local development)
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});

// Structured log example
logger.info('Ticket created', {
  ticketId: 'TKT-20250119-00042',
  userId: 'user-123',
  priority: 'high',
  category: 'Network',
  aiConfidence: 0.92,
});

logger.error('Database connection failed', {
  error: error.message,
  stack: error.stack,
  connectionString: 'postgresql://***',  // Redact sensitive info
});
```

**CloudWatch Logs Insights Queries:**
```sql
-- Find all errors in last 24 hours
fields @timestamp, @message, error, stack
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100

-- API latency by endpoint
fields @timestamp, endpoint, duration
| filter endpoint != "/health"
| stats avg(duration), p95(duration), p99(duration) by endpoint
| sort p99(duration) desc

-- Ticket creation rate by hour
fields @timestamp, ticketId
| filter @message like /Ticket created/
| stats count() by bin(@timestamp, 1h)

-- Failed login attempts by IP
fields @timestamp, ipAddress, userEmail
| filter action = "auth:login_failed"
| stats count() by ipAddress
| sort count desc
```

#### 6.4.4 Distributed Tracing (AWS X-Ray)

```typescript
// Enable X-Ray tracing
import * as AWSXRay from 'aws-xray-sdk-core';
import * as AWS from 'aws-sdk';

// Instrument AWS SDK
const AWSSDK = AWSXRay.captureAWS(AWS);

// Instrument HTTP requests
import * as http from 'http';
import * as https from 'https';
AWSXRay.captureHTTPsGlobal(http);
AWSXRay.captureHTTPsGlobal(https);

// Instrument Prisma queries (custom subsegment)
async function queryWithTracing<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  const segment = AWSXRay.getSegment();
  const subsegment = segment.addNewSubsegment('Prisma');
  subsegment.addAnnotation('operation', operation);

  try {
    const result = await fn();
    subsegment.close();
    return result;
  } catch (error) {
    subsegment.addError(error);
    subsegment.close();
    throw error;
  }
}

// Usage
const ticket = await queryWithTracing('ticket.findUnique', () =>
  prisma.ticket.findUnique({ where: { id: ticketId } })
);
```

**X-Ray Trace Example:**
```
Request: POST /api/v1/tickets (Total: 450ms)
├─ API Gateway (5ms)
├─ ECS Task (445ms)
│  ├─ JWT Validation (10ms)
│  ├─ Permission Check (15ms)
│  │  └─ Redis GET (3ms)
│  ├─ Prisma: ticket.create (80ms)
│  │  └─ PostgreSQL INSERT (75ms)
│  ├─ Queue: ai-categorization (5ms)
│  │  └─ Redis RPUSH (2ms)
│  ├─ Queue: email-notification (3ms)
│  └─ Response serialization (2ms)
```

#### 6.4.5 Alerting Strategy

**CloudWatch Alarms:**
```hcl
# Terraform configuration for alerts

# High error rate alert
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "helpdesk-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when 5xx errors exceed 10 in 5 minutes"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# High latency alert
resource "aws_cloudwatch_metric_alarm" "high_latency" {
  alarm_name          = "helpdesk-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Average"
  threshold           = 1  # 1 second
  alarm_description   = "Alert when average latency exceeds 1s"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# Database CPU high
resource "aws_cloudwatch_metric_alarm" "db_cpu_high" {
  alarm_name          = "helpdesk-db-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Alert when DB CPU exceeds 80%"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# ECS service unhealthy
resource "aws_cloudwatch_metric_alarm" "ecs_unhealthy_tasks" {
  alarm_name          = "helpdesk-ecs-unhealthy"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 2  # At least 2 healthy tasks
  alarm_description   = "Alert when fewer than 2 healthy ECS tasks"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
}

# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "helpdesk-alerts"
}

# Subscribe email
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "devops@digiskills.pk"
}

# Subscribe Slack (via Lambda)
resource "aws_sns_topic_subscription" "slack" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.slack_notifier.arn
}
```

**PagerDuty Integration (for critical alerts):**
```hcl
resource "aws_sns_topic_subscription" "pagerduty" {
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "https"
  endpoint  = "https://events.pagerduty.com/integration/xxx/enqueue"
}
```

---

### 6.5 Backup and Disaster Recovery

#### 6.5.1 Backup Strategy

**Database Backups (RDS):**
```hcl
resource "aws_db_instance" "primary" {
  identifier = "helpdesk-db"

  # Automated backups
  backup_retention_period = 7  # Keep daily backups for 7 days
  backup_window           = "03:00-04:00"  # UTC (off-peak hours)

  # Enable automated snapshots
  skip_final_snapshot = false
  final_snapshot_identifier = "helpdesk-db-final-snapshot"

  # Enable point-in-time recovery
  enabled_cloudwatch_logs_exports = ["postgresql"]
}

# Manual snapshot schedule (weekly)
resource "aws_backup_plan" "db" {
  name = "helpdesk-db-backup-plan"

  rule {
    rule_name         = "weekly_backup"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 2 ? * SUN *)"  # Sunday 2 AM UTC

    lifecycle {
      delete_after = 90  # Keep for 90 days
      cold_storage_after = 30  # Move to cold storage after 30 days
    }
  }
}
```

**S3 Backups:**
```hcl
# S3 versioning for attachments
resource "aws_s3_bucket_versioning" "attachments" {
  bucket = aws_s3_bucket.attachments.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 replication to different region (disaster recovery)
resource "aws_s3_bucket_replication_configuration" "attachments" {
  bucket = aws_s3_bucket.attachments.id
  role   = aws_iam_role.replication.arn

  rule {
    id     = "replicate-all"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.attachments_backup.arn
      storage_class = "STANDARD_IA"  # Cheaper storage in backup region
    }
  }
}
```

**Application Configuration Backups:**
```bash
# Daily backup of system configuration to S3
#!/bin/bash
# scripts/backup-config.sh

DATE=$(date +%Y-%m-%d)
BACKUP_BUCKET="s3://helpdesk-backups/config"

# Export database schema
pg_dump --schema-only $DATABASE_URL > schema-$DATE.sql

# Export configuration (without secrets)
aws secretsmanager list-secrets > secrets-list-$DATE.json

# Backup to S3
aws s3 cp schema-$DATE.sql $BACKUP_BUCKET/
aws s3 cp secrets-list-$DATE.json $BACKUP_BUCKET/

# Cleanup local files
rm schema-$DATE.sql secrets-list-$DATE.json
```

#### 6.5.2 Disaster Recovery Plan

**RPO (Recovery Point Objective): 15 minutes**
- Maximum acceptable data loss
- Achieved through continuous replication and point-in-time recovery

**RTO (Recovery Time Objective): 1 hour**
- Maximum acceptable downtime
- Time to restore service from backup

**Disaster Scenarios and Recovery Procedures:**

**Scenario 1: Region Failure (AWS us-east-1 down)**

Recovery Steps:
1. **Switch DNS** (Route 53 failover to backup region)
   ```bash
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z123456 \
     --change-batch file://failover-to-us-west-2.json
   ```

2. **Promote RDS Read Replica** in backup region to primary
   ```bash
   aws rds promote-read-replica \
     --db-instance-identifier helpdesk-db-replica-west \
     --region us-west-2
   ```

3. **Update application configuration** to point to new database
4. **Verify services** are running in backup region
5. **Total RTO**: 30-60 minutes

**Scenario 2: Database Corruption**

Recovery Steps:
1. **Identify point of corruption** from audit logs
2. **Create new RDS instance** from point-in-time snapshot (5 minutes before corruption)
   ```bash
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier helpdesk-db \
     --target-db-instance-identifier helpdesk-db-restored \
     --restore-time 2025-01-19T14:30:00Z
   ```
3. **Update application** to use restored database
4. **Verify data integrity**
5. **Total RTO**: 45 minutes

**Scenario 3: Accidental Data Deletion**

Recovery Steps:
1. **Identify deleted records** from audit logs
2. **Query backup database** for deleted data
   ```sql
   -- Connect to backup database
   SELECT * FROM tickets WHERE id = 'deleted-ticket-id';
   ```
3. **Restore specific records** to production database
4. **Total RTO**: 15-30 minutes

**Scenario 4: Complete System Compromise (Ransomware)**

Recovery Steps:
1. **Isolate compromised systems** (revoke all credentials, shut down instances)
2. **Launch new infrastructure** from Infrastructure-as-Code (Terraform)
3. **Restore database** from clean backup (before compromise)
4. **Restore S3 data** from versioned backups
5. **Rotate all secrets** (database passwords, API keys, JWT secrets)
6. **Audit logs** to identify breach vector
7. **Total RTO**: 2-4 hours

#### 6.5.3 Disaster Recovery Testing

**Quarterly DR Drill:**
```bash
# DR Drill Checklist
# 1. Announce drill to team (no customer impact)
# 2. Simulate region failure
# 3. Execute failover procedures
# 4. Measure RTO/RPO
# 5. Document issues and update runbook
# 6. Restore to normal operations
```

---

### 6.6 Operational Maintenance

#### 6.6.1 Regular Maintenance Tasks

**Daily:**
- Review CloudWatch alarms and alerts
- Check error rates in CloudWatch Logs
- Monitor queue backlogs (BullMQ)
- Review failed jobs and retry

**Weekly:**
- Review database slow query logs
- Check disk space and storage usage
- Review security scan results (Snyk, npm audit)
- Check for dependency updates

**Monthly:**
- Rotate non-critical secrets (API keys)
- Review IAM policies and remove unused permissions
- Analyze cost reports and optimize resources
- Review audit logs for anomalies
- Update documentation

**Quarterly:**
- Disaster recovery drill
- Rotate critical secrets (database passwords)
- Review and update incident response plan
- Performance testing and benchmarking
- Security audit and penetration testing

**Annually:**
- Major dependency upgrades (Node.js, PostgreSQL, etc.)
- Architecture review and tech debt planning
- Compliance audit (if applicable)

#### 6.6.2 Database Maintenance

**Automated VACUUM (PostgreSQL):**
```sql
-- Enable autovacuum (should be on by default)
ALTER SYSTEM SET autovacuum = on;
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;

-- Manual VACUUM for large tables (run during off-peak hours)
VACUUM ANALYZE tickets;
VACUUM ANALYZE audit_logs;
```

**Index Maintenance:**
```sql
-- Reindex to reduce index bloat (monthly)
REINDEX TABLE tickets;
REINDEX TABLE kb_articles;

-- Check for unused indexes
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexname NOT LIKE '%_pkey';
```

**Partition Maintenance:**
```sql
-- Create next month's partition (automated via cron)
CREATE TABLE audit_logs_2025_02 PARTITION OF audit_logs
  FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Drop old partitions (after archival to S3)
DROP TABLE audit_logs_2024_01;
```

#### 6.6.3 Scaling Operations

**Vertical Scaling (Increase Instance Size):**
```bash
# Upsize RDS instance (requires ~5 min downtime)
aws rds modify-db-instance \
  --db-instance-identifier helpdesk-db \
  --db-instance-class db.m5.xlarge \
  --apply-immediately
```

**Horizontal Scaling (Add More Tasks):**
```bash
# Scale ECS service
aws ecs update-service \
  --cluster helpdesk-cluster \
  --service helpdesk-api-service \
  --desired-count 5
```

**Database Read Replica Addition:**
```bash
# Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier helpdesk-db-replica-2 \
  --source-db-instance-identifier helpdesk-db
```

#### 6.6.4 Incident Response Runbook

**On-Call Procedures:**

1. **Alert Received** (PagerDuty/Email/Slack)
   - Acknowledge alert within 5 minutes
   - Assess severity (P0-P3)

2. **P0 - Critical (Service Down)**
   - Notify team lead immediately
   - Check CloudWatch dashboard
   - Review recent deployments (possible bad deploy?)
   - Execute rollback if recent deploy
   - Create incident ticket

3. **P1 - High (Degraded Performance)**
   - Investigate CloudWatch metrics (CPU, memory, latency)
   - Check for slow queries
   - Check external dependencies (OpenAI, Google SSO)
   - Scale resources if needed

4. **P2 - Medium (Non-Critical Feature Broken)**
   - Create bug ticket
   - Investigate and plan fix
   - Deploy during next release window

5. **P3 - Low (Minor Issue)**
   - Create ticket for backlog
   - Fix in regular sprint

**Incident Communication:**
```
Incident Title: [P0] Helpdesk API Returning 500 Errors
Status: Investigating
Start Time: 2025-01-19 14:35 UTC
Impact: All users unable to create tickets
Communication Channel: #incident-helpdesk-2025-01-19

Timeline:
14:35 - Alert received, acknowledging
14:37 - Confirmed 90% error rate on /api/v1/tickets
14:40 - Identified database connection pool exhaustion
14:42 - Scaled RDS instance from t3.large to t3.xlarge
14:45 - Error rate reduced to 0%, service recovered
14:50 - Post-incident review scheduled for tomorrow

Root Cause: Database connection pool exhausted due to slow query introduced in deploy at 14:20
Remediation: Scaled database, reverted problematic query
Follow-up: Add connection pool monitoring alert
```

---

## Summary: Deployment and Maintenance Strategy

**Cloud Platform:**
- AWS recommended (comprehensive, mature, cost-effective)
- Multi-AZ deployment for high availability
- Estimated cost: $686-1,170/month

**CI/CD Pipeline:**
- GitHub Actions for automated build, test, deploy
- Security scanning: npm audit, Snyk, Trivy
- Automated tests: Unit, integration, E2E
- Staging auto-deploy, production manual approval
- Rolling deployment with auto-rollback

**Monitoring:**
- CloudWatch for metrics, logs, and alarms
- AWS X-Ray for distributed tracing
- Custom dashboards for business metrics
- PagerDuty for critical alerts

**Backup & DR:**
- Daily automated database backups (7-day retention)
- S3 versioning and cross-region replication
- RPO: 15 minutes, RTO: 1 hour
- Quarterly DR drills

**Operational Excellence:**
- Infrastructure as Code (Terraform)
- Comprehensive runbooks for common incidents
- Regular maintenance schedule (daily/weekly/monthly/quarterly)
- On-call rotation with clear escalation paths

This deployment and maintenance architecture ensures **reliable, secure, and scalable operations** with minimal downtime and clear procedures for incident response and disaster recovery.

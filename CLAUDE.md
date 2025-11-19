# CLAUDE.md - AI Assistant Guide for Digiskills

## Project Overview

**Project Name:** Digiskills
**Description:** Digiskills IT helpdesk
**Repository:** tahirsiddique/Digiskills
**Current Stage:** Early development / Initial setup
**Last Updated:** 2025-11-19

## Project Purpose

Digiskills is an IT helpdesk system designed to manage and streamline IT support operations. This project is currently in its initial stages.

## Repository Structure

```
Digiskills/
├── .git/                   # Git repository data
├── README.md              # Project overview and description
└── CLAUDE.md              # This file - AI assistant guide
```

### Current State

This repository is newly initialized with minimal content. The codebase structure will evolve as development progresses.

## Development Workflows

### Git Workflow

**Branch Strategy:**
- Main branch: (not yet set)
- Feature branches: Use `claude/` prefix for AI-assisted development
- Current working branch: `claude/claude-md-mi6bf6zunaattrzv-01NU5LT5xWFDi22bHjWF4P2u`

**Commit Guidelines:**
- Write clear, descriptive commit messages
- Use conventional commit format when possible:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation changes
  - `refactor:` for code refactoring
  - `test:` for test additions/modifications
  - `chore:` for maintenance tasks

**Push Strategy:**
- Always use: `git push -u origin <branch-name>`
- Branch names must start with `claude/` and end with matching session ID
- Retry logic: Up to 4 retries with exponential backoff (2s, 4s, 8s, 16s) for network errors

### Development Environment Setup

*(To be documented as the project evolves)*

**Prerequisites:**
- TBD based on technology stack selection

**Installation:**
```bash
# To be added once dependencies are defined
```

**Configuration:**
- Configuration files and environment setup to be documented

## Key Conventions for AI Assistants

### Code Organization

When implementing the IT helpdesk system, consider organizing code into these logical modules:

1. **Authentication & Authorization**
   - User management
   - Role-based access control (RBAC)
   - Session management

2. **Ticket Management**
   - Ticket creation, assignment, and tracking
   - Priority and status management
   - Ticket history and audit logs

3. **User Interface**
   - Dashboard for technicians
   - User portal for ticket submission
   - Admin panel

4. **Communication**
   - Email notifications
   - In-app messaging
   - Status update notifications

5. **Reporting & Analytics**
   - Ticket metrics and KPIs
   - Performance reports
   - SLA tracking

6. **Integration**
   - External system integrations
   - API endpoints
   - Webhooks

### Coding Standards

**General Principles:**
- Write clean, self-documenting code
- Follow DRY (Don't Repeat Yourself) principle
- Keep functions small and focused
- Use meaningful variable and function names
- Comment complex logic and business rules

**Security Best Practices:**
- Never commit sensitive data (API keys, passwords, secrets)
- Use environment variables for configuration
- Implement input validation and sanitization
- Prevent common vulnerabilities:
  - SQL injection
  - XSS (Cross-Site Scripting)
  - CSRF (Cross-Site Request Forgery)
  - Authentication bypass
  - Insecure direct object references

**Error Handling:**
- Implement comprehensive error handling
- Log errors appropriately
- Provide user-friendly error messages
- Never expose stack traces to end users

### Documentation Requirements

When adding new features, always include:

1. **Code Comments:**
   - Explain WHY, not just WHAT
   - Document complex algorithms
   - Note any workarounds or temporary solutions

2. **API Documentation:**
   - Endpoint descriptions
   - Request/response formats
   - Authentication requirements
   - Example usage

3. **README Updates:**
   - Keep installation instructions current
   - Document new dependencies
   - Update usage examples

4. **CHANGELOG:**
   - Document significant changes
   - Note breaking changes
   - Link to relevant issues/PRs

### Testing Strategy

*(To be implemented as project grows)*

**Test Types:**
- Unit tests for individual functions/components
- Integration tests for feature workflows
- End-to-end tests for critical user journeys
- Security tests for vulnerability assessment

**Test Coverage Goals:**
- Aim for >80% code coverage
- 100% coverage for critical security functions
- All bug fixes should include regression tests

## Technology Stack

*(To be determined and documented)*

**Recommended Considerations:**

**Backend Options:**
- Node.js with Express/Fastify
- Python with Django/Flask/FastAPI
- Java with Spring Boot
- .NET Core

**Frontend Options:**
- React/Next.js
- Vue.js/Nuxt.js
- Angular
- Svelte/SvelteKit

**Database Options:**
- PostgreSQL (recommended for relational data)
- MySQL/MariaDB
- MongoDB (for flexible schema)
- SQLite (for lightweight/embedded scenarios)

**Additional Services:**
- Authentication: Auth0, Keycloak, or custom JWT
- Email: SendGrid, AWS SES, or SMTP
- File Storage: AWS S3, Azure Blob, or local storage
- Queue/Job Processing: Redis, RabbitMQ, or Kafka

## API Design Guidelines

### RESTful API Conventions

**Endpoint Naming:**
```
GET    /api/tickets           # List all tickets
GET    /api/tickets/:id       # Get specific ticket
POST   /api/tickets           # Create new ticket
PUT    /api/tickets/:id       # Update ticket (full)
PATCH  /api/tickets/:id       # Update ticket (partial)
DELETE /api/tickets/:id       # Delete ticket
```

**Response Format:**
```json
{
  "success": true,
  "data": { },
  "message": "Success message",
  "metadata": {
    "page": 1,
    "pageSize": 20,
    "total": 100
  }
}
```

**Error Response Format:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

**HTTP Status Codes:**
- 200: Success
- 201: Created
- 204: No Content (successful deletion)
- 400: Bad Request (validation error)
- 401: Unauthorized (authentication required)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 409: Conflict (duplicate resource)
- 422: Unprocessable Entity (semantic error)
- 500: Internal Server Error

## Database Schema Guidelines

### Ticket System Core Tables

**tickets:**
- id (primary key)
- ticket_number (unique, auto-generated)
- title
- description
- priority (low, medium, high, critical)
- status (new, assigned, in_progress, resolved, closed)
- category_id (foreign key)
- created_by (user_id, foreign key)
- assigned_to (user_id, foreign key, nullable)
- created_at
- updated_at
- resolved_at
- closed_at

**users:**
- id (primary key)
- username (unique)
- email (unique)
- password_hash
- first_name
- last_name
- role (admin, technician, user)
- is_active
- created_at
- updated_at

**categories:**
- id (primary key)
- name
- description
- parent_id (for hierarchical categories)
- created_at

**ticket_comments:**
- id (primary key)
- ticket_id (foreign key)
- user_id (foreign key)
- comment_text
- is_internal (boolean, for tech-only notes)
- created_at

**ticket_attachments:**
- id (primary key)
- ticket_id (foreign key)
- file_name
- file_path
- file_size
- mime_type
- uploaded_by (user_id, foreign key)
- uploaded_at

## Feature Priorities

### Phase 1: MVP (Minimum Viable Product)
1. User authentication and authorization
2. Basic ticket creation and viewing
3. Ticket assignment to technicians
4. Simple status updates
5. Basic email notifications

### Phase 2: Core Features
1. Ticket categories and prioritization
2. Comment system
3. File attachments
4. Search and filtering
5. Dashboard with metrics

### Phase 3: Advanced Features
1. SLA management and tracking
2. Knowledge base integration
3. Advanced reporting and analytics
4. Custom workflows
5. Integration with external systems

### Phase 4: Enhancement
1. Mobile application
2. Chat/real-time messaging
3. AI-powered ticket categorization
4. Customer satisfaction surveys
5. Multi-language support

## Common Tasks for AI Assistants

### Creating New Features

1. **Understand Requirements:**
   - Read existing code and documentation
   - Identify dependencies and impacts
   - Plan implementation approach

2. **Implementation:**
   - Create necessary files and folders
   - Write implementation code
   - Add appropriate error handling
   - Include security measures

3. **Testing:**
   - Write unit tests
   - Test edge cases
   - Verify security implications

4. **Documentation:**
   - Update relevant documentation
   - Add code comments
   - Update API documentation if needed

### Debugging and Bug Fixes

1. **Reproduce Issue:**
   - Understand the problem
   - Identify affected components
   - Trace execution flow

2. **Fix Implementation:**
   - Identify root cause
   - Implement fix
   - Add regression test

3. **Verification:**
   - Test the fix
   - Check for side effects
   - Update documentation if needed

### Code Review Checklist

When reviewing or writing code, verify:

- [ ] Code follows project conventions
- [ ] No security vulnerabilities introduced
- [ ] Error handling is comprehensive
- [ ] Input validation is present
- [ ] No sensitive data exposed
- [ ] Functions are properly documented
- [ ] Tests are included
- [ ] No console.log or debug statements left
- [ ] Performance considerations addressed
- [ ] Accessibility requirements met (for UI)

## File Naming Conventions

*(To be established based on chosen technology stack)*

**General Guidelines:**
- Use lowercase with hyphens for files: `user-service.js`
- Use PascalCase for classes/components: `UserService.js`, `TicketCard.jsx`
- Use descriptive names that reflect purpose
- Group related files in directories

## Environment Variables

Store sensitive configuration in environment variables:

```
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=digiskills
DB_USER=...
DB_PASSWORD=...

# Authentication
JWT_SECRET=...
JWT_EXPIRATION=24h
SESSION_SECRET=...

# Email
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
EMAIL_FROM=noreply@digiskills.com

# Application
NODE_ENV=development
PORT=3000
API_BASE_URL=http://localhost:3000
FRONTEND_URL=http://localhost:3001

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=pdf,doc,docx,jpg,jpeg,png,gif
UPLOAD_DIR=./uploads
```

## Deployment Guidelines

*(To be documented once deployment strategy is chosen)*

**Considerations:**
- Container orchestration (Docker/Kubernetes)
- CI/CD pipeline setup
- Environment-specific configurations
- Database migration strategy
- Backup and disaster recovery
- Monitoring and logging
- Performance optimization

## Troubleshooting

### Common Issues

*(To be populated as issues are encountered)*

**Database Connection Issues:**
- Verify credentials
- Check network connectivity
- Confirm database service is running

**Authentication Failures:**
- Verify token expiration settings
- Check secret key configuration
- Validate user permissions

## Resources and References

**Documentation:**
- [Project Wiki/Docs] - TBD
- [API Documentation] - TBD
- [User Guide] - TBD

**External Resources:**
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- REST API Best Practices
- IT Service Management (ITSM) principles
- ITIL framework (for IT helpdesk best practices)

## Contact and Support

**Repository Owner:** tahirsiddique
**Project Maintainers:** TBD
**Issue Tracking:** GitHub Issues (when enabled)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-19 | Initial CLAUDE.md creation, project structure documentation |

---

## Notes for AI Assistants

**When working on this project:**

1. **Always check existing documentation** before making assumptions
2. **Ask clarifying questions** if requirements are ambiguous
3. **Consider security implications** for every change
4. **Test thoroughly** before committing
5. **Document your changes** appropriately
6. **Follow established patterns** in the codebase
7. **Update this file** as you learn more about the project structure
8. **Be proactive** about identifying potential issues
9. **Think about scalability** when designing solutions
10. **Prioritize user experience** in all implementations

**Update This Document:**
As the project evolves, AI assistants should keep this document current by:
- Adding new sections for implemented features
- Documenting discovered conventions
- Updating the repository structure
- Recording common issues and solutions
- Adding examples of implemented patterns
- Noting technology stack decisions

This living document serves as the primary guide for understanding and contributing to the Digiskills project effectively.

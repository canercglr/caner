# CLAUDE.md - AI Assistant Guide

**Last Updated:** 2025-11-19
**Repository:** canercglr/caner
**Current State:** Minimal/starter repository

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Current Structure](#current-structure)
3. [Git Workflow](#git-workflow)
4. [Development Conventions](#development-conventions)
5. [AI Assistant Guidelines](#ai-assistant-guidelines)
6. [Common Tasks](#common-tasks)
7. [Future Development Notes](#future-development-notes)

---

## Repository Overview

This is currently a **minimal/starter repository** containing only basic documentation. It was initialized on April 28, 2014, with a single commit.

### Key Information

- **Owner:** canercglr
- **Repository Name:** caner
- **Primary Branch:** (not yet set)
- **Remote URL:** `http://local_proxy@127.0.0.1:23168/git/canercglr/caner`
- **Current State:** Clean, minimal setup

---

## Current Structure

```
/home/user/caner/
├── .git/              # Git configuration and history
├── README.md          # Minimal project README (contains only "caner")
└── CLAUDE.md          # This file - AI assistant guide
```

### What's Missing (To Be Added As Needed)

- **Configuration Files:** No package.json, tsconfig.json, or other config files yet
- **Source Code:** No src/ directory or source files
- **Tests:** No test files or testing framework
- **Build Tools:** No build configuration
- **CI/CD:** No continuous integration setup
- **Git Configuration:** No .gitignore file
- **Documentation:** Limited documentation

---

## Git Workflow

### Branch Naming Convention

**CRITICAL:** When working on this repository, all development branches MUST follow this pattern:

```
claude/claude-md-{identifier}-{session-id}
```

**Current Working Branch:** `claude/claude-md-mi5pe67zxc9cheeb-01PEVyDmcqYbgfRrDUztDUfY`

### Branch Requirements

1. **Branch Prefix:** All branches MUST start with `claude/`
2. **Session ID:** Must end with the matching session ID
3. **Push Requirements:** Push with `git push -u origin <branch-name>`
4. **403 Errors:** If you get a 403 error, verify the branch name follows the pattern

### Git Operations Best Practices

**For git push:**
```bash
git push -u origin claude/claude-md-{identifier}-{session-id}
```
- Retry up to 4 times on network errors with exponential backoff (2s, 4s, 8s, 16s)

**For git fetch/pull:**
```bash
git fetch origin <branch-name>
git pull origin <branch-name>
```
- Retry up to 4 times on network errors with exponential backoff

### Commit Messages

Follow conventional commit format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples:**
```
feat: add user authentication module
fix(api): resolve timeout issue in data fetch
docs: update README with installation instructions
```

---

## Development Conventions

### Code Style (To Be Established)

Since no linters or formatters are configured yet, follow these general guidelines:

1. **Consistency:** Match the style of existing code
2. **Readability:** Write self-documenting code with clear variable names
3. **Comments:** Add comments for complex logic, not obvious code
4. **File Organization:** Group related functionality together

### File Organization Recommendations

When adding code, consider this structure:
```
/home/user/caner/
├── src/                # Source code
│   ├── index.js/ts     # Entry point
│   ├── lib/            # Shared libraries
│   ├── utils/          # Utility functions
│   └── config/         # Configuration files
├── tests/              # Test files
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── docs/               # Additional documentation
├── scripts/            # Build/deployment scripts
├── .gitignore          # Git ignore rules
├── package.json        # Node.js dependencies (if applicable)
├── README.md           # Project documentation
└── CLAUDE.md           # This file
```

### Dependency Management

**Not yet configured.** When adding dependencies:
- Use a lock file (package-lock.json, yarn.lock, etc.)
- Document why each dependency is needed
- Keep dependencies up to date
- Prefer stable, well-maintained packages

---

## AI Assistant Guidelines

### Before Making Changes

1. **Read existing files** before modifying them
2. **Check git status** to understand the current state
3. **Search for related code** to maintain consistency
4. **Plan complex changes** using the TodoWrite tool

### Task Management

**ALWAYS use TodoWrite for:**
- Multi-step tasks (3+ steps)
- Complex implementations
- When user provides multiple tasks
- Non-trivial operations

**Example workflow:**
```markdown
1. Understand requirements
2. Explore relevant code
3. Plan changes
4. Implement changes
5. Test changes
6. Commit and push
```

### Code Quality Standards

1. **Security:** Avoid vulnerabilities (XSS, SQL injection, command injection, etc.)
2. **Error Handling:** Handle edge cases and errors gracefully
3. **Testing:** Write tests for new functionality when possible
4. **Documentation:** Update docs when adding features
5. **Performance:** Consider performance implications

### Tool Usage Priorities

1. **File Operations:**
   - Use `Read` instead of `cat`
   - Use `Edit` instead of `sed/awk`
   - Use `Write` for new files instead of `echo >`

2. **Search Operations:**
   - Use `Grep` for content search instead of `grep` command
   - Use `Glob` for file patterns instead of `find` or `ls`
   - Use `Task` with `Explore` agent for open-ended exploration

3. **Parallel Operations:**
   - Run independent operations in parallel
   - Chain dependent operations with `&&`

### Communication Style

- **Concise:** Keep responses short and to the point
- **No Emojis:** Unless explicitly requested
- **Technical:** Focus on facts over validation
- **Objective:** Prioritize accuracy over agreement
- **Direct:** Output text directly, don't use `echo` to communicate

---

## Common Tasks

### Setting Up a New Project

1. **Create .gitignore:**
   ```bash
   # Add appropriate ignore rules for your language/framework
   ```

2. **Initialize package.json (if Node.js):**
   ```bash
   npm init -y
   ```

3. **Add configuration files:**
   - TypeScript: `tsconfig.json`
   - ESLint: `.eslintrc.js`
   - Prettier: `.prettierrc`

4. **Set up directory structure:**
   ```bash
   mkdir -p src tests docs
   ```

### Making Changes

1. **Check current state:**
   ```bash
   git status
   git log --oneline -5
   ```

2. **Make changes** using appropriate tools (Read, Edit, Write)

3. **Review changes:**
   ```bash
   git diff
   git status
   ```

4. **Commit:**
   ```bash
   git add .
   git commit -m "feat: descriptive message"
   ```

5. **Push:**
   ```bash
   git push -u origin claude/claude-md-{identifier}-{session-id}
   ```

### Creating a Pull Request

1. **Ensure all changes are committed and pushed**
2. **Provide context** about what changed and why
3. **Include testing notes** if applicable
4. **Reference any related issues**

---

## Future Development Notes

### Potential Additions

When this repository grows, consider adding:

1. **Testing Framework:**
   - Jest, Mocha, PyTest, etc. depending on language
   - Test coverage reporting
   - CI/CD integration

2. **Linting & Formatting:**
   - ESLint, Pylint, RuboCop, etc.
   - Prettier, Black, etc.
   - Pre-commit hooks

3. **Documentation:**
   - API documentation
   - Architecture diagrams
   - Contributing guidelines
   - Code of conduct

4. **CI/CD:**
   - GitHub Actions workflows
   - Automated testing
   - Deployment pipelines
   - Code quality checks

5. **Security:**
   - Dependency scanning
   - Security policies
   - Secret management guidelines

### Project Type Indicators

**Not yet determined.** As the project evolves, update this section with:
- Primary programming language(s)
- Framework(s) used
- Application type (web app, API, CLI tool, library, etc.)
- Target platform (browser, Node.js, server, mobile, etc.)

---

## Troubleshooting

### Common Issues

**403 Error on Push:**
- Verify branch name starts with `claude/` and ends with session ID
- Check remote URL is correct
- Retry with exponential backoff

**Merge Conflicts:**
- Fetch latest changes: `git fetch origin <branch>`
- Review conflicts carefully
- Test after resolving

**Lost Changes:**
- Check `git status` and `git diff`
- Use `git stash` to temporarily save work
- Check `git reflog` for recent operations

---

## Contact & Support

For questions or issues:
1. Check existing documentation
2. Search for similar patterns in the codebase
3. Ask the repository owner: canercglr

---

## Changelog

### 2025-11-19 - Initial CLAUDE.md
- Created comprehensive AI assistant guide
- Documented current repository state
- Established git workflow conventions
- Defined development guidelines
- Set up task management standards

---

**Note to AI Assistants:** This document should be updated as the repository evolves. When making significant changes to the project structure, conventions, or workflows, update this file accordingly.

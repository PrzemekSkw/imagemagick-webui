# Contributing Guide

## Welcome! 🎉

Thank you for considering contributing to ImageMagick WebGUI!

## Ways to Contribute

### 🐛 Report Bugs
Found a bug? [Open an issue](https://github.com/PrzemekSkw/imagemagick-webui/issues/new?labels=bug)

Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Docker version)
- Logs (if applicable)

### 💡 Suggest Features
Have an idea? [Open a feature request](https://github.com/PrzemekSkw/imagemagick-webui/issues/new?labels=enhancement)

Include:
- Use case
- Expected behavior
- Why this would be useful

### 📝 Improve Documentation
Documentation improvements are always welcome!

### 🔧 Code Contributions

## Development Setup

### Prerequisites
- Docker & Docker Compose
- Git
- Node.js 20+ (for local development)
- Python 3.12+ (for local development)

### Local Development

1. **Fork & Clone:**
```bash
git clone https://github.com/YOUR_USERNAME/imagemagick-webui.git
cd imagemagick-webui
```

2. **Create Branch:**
```bash
git checkout -b feature/your-feature-name
```

3. **Setup Environment:**
```bash
cp .env.example .env
# Edit .env if needed
```

4. **Start Development:**
```bash
docker compose up -d
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

5. **Make Changes:**
- Frontend: `frontend/` (Next.js + TypeScript)
- Backend: `backend/` (FastAPI + Python)

6. **Test:**
```bash
# Test upload, operations, download
# Check browser console for errors
# Check logs: docker compose logs -f app
```

7. **Commit:**
```bash
git add .
git commit -m "feat: add amazing feature"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `style:` formatting
- `refactor:` code restructuring
- `test:` adding tests
- `chore:` maintenance

8. **Push & PR:**
```bash
git push origin feature/your-feature-name
```

Open Pull Request on GitHub.

## Code Style

### TypeScript/React
- Use TypeScript strict mode
- Follow existing patterns
- Use shadcn/ui components
- Keep components small and focused

### Python
- Follow PEP 8
- Use type hints
- Use async/await for I/O operations
- Add docstrings to functions

## Pull Request Guidelines

### PR Title
Use Conventional Commits format:
```
feat: add batch resize feature
fix: resolve CORS issue with reverse proxy
docs: update installation guide
```

### PR Description
Include:
- What changed
- Why it changed
- How to test
- Screenshots (if UI changes)

### Checklist
- [ ] Code follows project style
- [ ] Tested locally
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Commits follow Conventional Commits

## Questions?

- 💬 [Discussions](https://github.com/PrzemekSkw/imagemagick-webui/discussions)
- 📧 Email: [your-email]

## Thank You! 🙏

Every contribution helps make this project better!

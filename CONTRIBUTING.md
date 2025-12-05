# Contributing to ImageMagick WebGUI

First off, thank you for considering contributing to ImageMagick WebGUI! It's people like you that make this project possible.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guides](#style-guides)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Issues

- **Bug Reports**: Use the bug report template to report bugs
- **Feature Requests**: Use the feature request template to suggest new features
- **Questions**: Use GitHub Discussions for questions

### Before You Start

1. Check existing issues to avoid duplicates
2. For major changes, open an issue first to discuss
3. Fork the repository and create your branch from `main`

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues. When creating a bug report, include:

- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs actual behavior
- **Screenshots** if applicable
- **Environment details** (OS, Docker version, browser)

### Suggesting Features

Feature suggestions are welcome! Please include:

- **Clear title** for the feature
- **Use case** - why this feature would be useful
- **Proposed solution** if you have one
- **Alternatives** you've considered

### Code Contributions

1. **Good First Issues**: Look for issues labeled `good first issue`
2. **Documentation**: Help improve our docs
3. **Bug Fixes**: Fix reported bugs
4. **New Features**: Implement approved feature requests

## Development Setup

### Prerequisites

- Docker 20.10+
- Docker Compose v2.0+
- Node.js 20+ (for frontend development)
- Python 3.12+ (for backend development)

### Setup Steps

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/imagemagick-webgui.git
cd imagemagick-webgui

# 2. Copy environment file
cp .env.example .env

# 3. Start development environment
docker compose up --build

# 4. Access the application
open http://localhost:3000
```

### Running Tests

```bash
# Backend tests
docker compose exec app pytest backend/tests/ -v

# Frontend type check
docker compose exec app npm --prefix frontend run type-check
```

## Pull Request Process

### Before Submitting

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Run all tests** and ensure they pass
4. **Follow style guides** (see below)

### PR Checklist

- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing unit tests pass locally

### PR Title Format

Use conventional commits format:

```
feat: add image cropping tool
fix: resolve upload timeout issue
docs: update API documentation
chore: upgrade dependencies
refactor: simplify image processing pipeline
```

### Review Process

1. Submit your PR
2. Wait for CI checks to pass
3. Address review feedback
4. Once approved, a maintainer will merge

## Style Guides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and PRs after the first line

### TypeScript/JavaScript

- Use TypeScript for all new code
- Follow ESLint configuration
- Use functional components with hooks
- Prefer named exports

```typescript
// Good
export function ImageGallery({ images }: ImageGalleryProps) {
  const [selected, setSelected] = useState<string[]>([]);
  // ...
}

// Avoid
export default class ImageGallery extends Component {
  // ...
}
```

### Python

- Follow PEP 8 style guide
- Use type hints
- Use async/await for I/O operations
- Document functions with docstrings

```python
# Good
async def process_image(
    image_id: int,
    operations: list[Operation],
) -> ProcessingResult:
    """
    Process an image with the given operations.
    
    Args:
        image_id: The ID of the image to process
        operations: List of operations to apply
        
    Returns:
        ProcessingResult with the output path
    """
    # ...
```

### CSS/Tailwind

- Use Tailwind utility classes
- Extract components for repeated patterns
- Follow mobile-first approach

```tsx
// Good
<div className="flex flex-col gap-4 p-4 md:flex-row md:gap-6">

// Avoid
<div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
```

## Questions?

Feel free to open a GitHub Discussion or reach out to the maintainers.

Thank you for contributing! 🎉

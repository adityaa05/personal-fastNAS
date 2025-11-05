# Contributing to Personal FastNAS

Thank you for your interest in contributing to Personal FastNAS! This document provides guidelines and instructions for contributing.

## Ways to Contribute

- Report bugs and issues
- Suggest new features or enhancements
- Improve documentation
- Translate to other languages
- Submit code improvements
- Design UI/UX improvements
- Write tests
- Create tutorials or guides

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/personal-fastNAS.git
cd personal-fastNAS
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

## Development Guidelines

### Code Style

- **Follow PEP 8** for Python code
- Use **4 spaces** for indentation (no tabs)
- **Maximum line length**: 88 characters (Black formatter standard)
- Use **type hints** where possible
- Write **docstrings** for all functions and classes

### Example:

```python
def calculate_file_size(file_path: Path) -> int:
    """
    Calculate the size of a file in bytes.

    Args:
        file_path: Path object pointing to the file

    Returns:
        File size in bytes

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    return file_path.stat().st_size
```

### Naming Conventions

- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### Git Commit Messages

Use clear, descriptive commit messages:

```
Add: New feature description
Fix: Bug fix description
Update: Changes to existing feature
Docs: Documentation changes
Style: Code style/formatting changes
Refactor: Code restructuring without functionality change
Test: Adding or updating tests
```

Examples:

```bash
git commit -m "Add: File compression support for downloads"
git commit -m "Fix: Search timeout on large directories"
git commit -m "Docs: Update README with Docker instructions"
```

## Testing

### Before Submitting

- [ ] Test on Windows, Mac, or Linux (at least one platform)
- [ ] Verify all existing features still work
- [ ] Check for Python errors or warnings
- [ ] Test with both authentication enabled and disabled
- [ ] Ensure code follows style guidelines

### Manual Testing Checklist

- [ ] File browsing works
- [ ] Upload works (small and large files)
- [ ] Download works
- [ ] Search functionality works
- [ ] Settings can be saved
- [ ] API endpoints respond correctly
- [ ] No console errors in browser

## Pull Request Process

### 1. Update Your Branch

```bash
# Before creating PR, sync with main
git fetch upstream
git rebase upstream/main
```

### 2. Create Pull Request

1. Push your branch to your fork
2. Go to the original repository
3. Click "New Pull Request"
4. Select your branch
5. Fill in the PR template (see below)

### 3. PR Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing

- [ ] Tested on Windows/Mac/Linux
- [ ] All existing features work
- [ ] New tests added (if applicable)

## Screenshots (if applicable)

Add screenshots for UI changes

## Checklist

- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] No console warnings or errors
- [ ] Tested with authentication enabled
```

## Reporting Bugs

### Before Reporting

1. Search existing issues — your bug might already be reported
2. Try latest version — bug might be fixed already
3. Reproduce the bug — make sure it's consistent

### Bug Report Template

```markdown
**Describe the bug**
Clear description of what's wrong

**To Reproduce**
Steps to reproduce:

1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What should happen

**Screenshots**
If applicable

**Environment:**

- OS: [e.g., Windows 11, macOS Sonoma, Ubuntu 22.04]
- Python Version: [e.g., 3.11.5]
- Browser: [e.g., Chrome 119, Safari 17]

**Additional context**
Any other relevant information
```

## Suggesting Features

### Feature Request Template

```markdown
**Is your feature related to a problem?**
Describe the problem

**Describe the solution you'd like**
Clear description of desired feature

**Describe alternatives considered**
Other solutions you've thought about

**Additional context**
Mockups, examples, or references
```

## Translation

Want to translate the UI to your language?

1. Create a new file: `locales/YOUR_LANGUAGE.json`
2. Copy `locales/en.json` as template
3. Translate all strings
4. Submit PR with your translation

## Documentation

### Areas Needing Documentation

- User guides and tutorials
- API documentation
- Deployment guides
- Troubleshooting guides
- Video tutorials

### Documentation Style

- Use clear, simple language
- Include code examples
- Add screenshots where helpful
- Test all commands and instructions
- Consider non-technical users

## Design Contributions

### UI/UX Improvements

- Keep the Apple-like minimalist style
- Ensure mobile responsiveness
- Maintain dark mode support
- Follow existing color scheme
- Test on multiple devices

### Submitting Designs

1. Create mockups (Figma, Sketch, etc.)
2. Share design files or screenshots
3. Explain design decisions
4. Open an issue for discussion

## Code Review Process

### What We Look For

1. Functionality - Does it work as intended?
2. Code quality - Is it clean and maintainable?
3. Performance - Does it impact speed?
4. Security - Are there vulnerabilities?
5. Documentation - Is it well-documented?

### Review Timeline

- Initial review: Within 3-5 days
- Feedback: We'll provide constructive feedback
- Revisions: Address feedback and update PR
- Merge: Once approved, we'll merge

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of:

- Age, body size, disability
- Ethnicity, gender identity
- Experience level
- Nationality, personal appearance
- Race, religion, or sexual identity

### Expected Behavior

- Be respectful and considerate
- Be collaborative and helpful
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks or trolling
- Publishing others' private information
- Unprofessional conduct

### Enforcement

Violations may result in:

1. Warning
2. Temporary ban
3. Permanent ban

Report violations to: [your-email@example.com]

## Communication Channels

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: General questions and ideas
- Pull Requests: Code contributions
- Email: [your-email@example.com] for private matters

## Learning Resources

### For Python/FastAPI Beginners

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Python Official Tutorial: https://docs.python.org/3/tutorial/
- Real Python Tutorials: https://realpython.com/

### For Git Beginners

- GitHub Git Handbook: https://guides.github.com/introduction/git-handbook/
- Learn Git Branching: https://learngitbranching.js.org/

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in project documentation

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

---

## Questions?

Don't hesitate to ask! Open an issue or start a discussion.

Thank you for making Personal FastNAS better.

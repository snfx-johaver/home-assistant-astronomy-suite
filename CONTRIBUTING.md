# Contributing

## Commit Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for **automated semantic versioning**.

### Format

```
<type>: <description>
```

### Types that trigger releases

| Prefix | Version Bump | Example |
|--------|-------------|---------|
| `fix:` | PATCH (0.0.x) | `fix: correct APOD date parsing` |
| `perf:` | PATCH (0.0.x) | `perf: reduce API polling interval` |
| `refactor:` | PATCH (0.0.x) | `refactor: simplify coordinator logic` |
| `feat:` | MINOR (0.x.0) | `feat: add Mars Rover photos sensor` |
| `feat!:` or `BREAKING CHANGE:` | MAJOR (x.0.0) | `feat!: redesign config flow` |

### Types that do NOT trigger releases

| Prefix | Use for |
|--------|---------|
| `docs:` | Documentation only |
| `style:` | Formatting, whitespace |
| `test:` | Adding/fixing tests |
| `ci:` | CI/CD changes |
| `chore:` | Maintenance, deps |

### How it works

1. Push commits to `main` with conventional prefixes
2. GitHub Actions reads commit messages since last tag
3. Determines the highest-priority bump (major > minor > patch)
4. Updates all version files automatically
5. Creates a git tag + GitHub Release with changelog

**You never need to manually bump versions or create releases.**

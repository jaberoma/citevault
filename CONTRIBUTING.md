# Contributing

Citevault is a solo side project, maintained on a **best-effort basis**. Issues and pull
requests are welcome, but there is no guaranteed response time or support commitment.
Please read the [maintenance note](#maintenance) before opening an issue.

## Reporting bugs

Open a [GitHub Issue](../../issues) with:

- What you expected to happen and what actually happened
- Steps to reproduce (Docker version, host OS, model tag)
- Relevant logs (`docker compose logs citevault-api`)

## Submitting a pull request

1. Fork the repository and create a branch from `main`
2. Make sure tests pass locally:
   ```bash
   cd citevault-api && uv run pytest
   cd citevault-ui  && npm test
   ```
3. Keep changes focused — one concern per PR
4. Open the PR with a clear description of what and why

Well-scoped, tested PRs are more likely to be reviewed promptly.

## Development setup

See the **Local development** section in [README.md](README.md).

## Maintenance

This project is provided **as-is** under the [MIT License](LICENSE). There are no
guarantees of support, timely responses, or continued development. Bug fixes and
improvements are made on a best-effort basis when time permits.

## License

By contributing, you agree that your contributions will be licensed under the project's
[MIT License](LICENSE).

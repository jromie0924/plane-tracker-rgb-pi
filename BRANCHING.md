# Branch Strategy

This document describes the branching strategy and workflow for the plane-tracker-rgb-pi project.

## Branch Structure

### Main Branches

- **`main`**: Production-ready code with stable releases
  - Contains only tested, stable code
  - All commits should be tagged with version numbers
  - Protected branch - requires pull request reviews

- **`RC`** (Release Candidate): Pre-release testing and staging branch
  - Integration testing occurs here
  - All feature branches should target this branch
  - Once stable, promoted to `main` via GitHub Action
  - Protected branch with option for administrator bypass

### Feature Branches

Development work happens in feature branches following these naming conventions:
- `feature/*` - New features
- `fix/*` - Bug fixes
- `enhance/*` - Enhancements to existing features
- `docs/*` - Documentation updates
- `refactor/*` - Code refactoring

## Workflow

### 1. Create Feature Branch

Create your feature branch from `RC` (or `main`):

```bash
git checkout RC
git pull origin RC
git checkout -b feature/my-new-feature
```

### 2. Develop and Commit

Make your changes and commit them to your feature branch:

```bash
git add .
git commit -m "Add new feature"
git push origin feature/my-new-feature
```

### 3. Open Pull Request

- Open a pull request targeting the `RC` branch
- Add a clear description of your changes
- Request reviews from team members
- Ensure all CI checks pass

### 4. Merge to RC

Once approved:
- Merge the pull request into `RC`
- Delete the feature branch (optional but recommended)

### 5. Test on RC

- Test and validate all changes on the `RC` branch
- RC serves as the integration testing environment
- Multiple features can be tested together on RC

### 6. Promote to Main

When `RC` is stable and ready for release:

1. Go to the **Actions** tab in GitHub
2. Select the **"Promote RC to Main"** workflow
3. Click **"Run workflow"**
4. Enter the release version number (e.g., `v1.2.0`)
5. Click **"Run workflow"** to start the promotion

The GitHub Action will:
- Merge `RC` into `main` using a no-fast-forward merge
- Create a git tag with the specified version
- Push both the merge commit and tag to `main`

## Branch Protection

Branch protection rules must be configured manually in GitHub Settings > Branches.

### Recommended Settings for `main`:

1. Navigate to **Settings** > **Branches**
2. Add rule for `main` branch
3. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (at least 1)
   - ✅ Require status checks to pass before merging (if CI is configured)
   - ✅ Require branches to be up to date before merging
   - ✅ Do not allow bypassing the above settings
4. Disable:
   - ❌ Allow force pushes
   - ❌ Allow deletions

### Recommended Settings for `RC`:

1. Navigate to **Settings** > **Branches**
2. Add rule for `RC` branch
3. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging (if CI is configured)
   - ✅ Allow specified actors to bypass required pull requests (for administrators/emergency fixes)
4. Disable:
   - ❌ Allow force pushes
   - ❌ Allow deletions

## Default Branch

The `RC` branch is configured as the default branch for this repository. This means:

- New pull requests automatically target `RC` instead of `main`
- The repository opens to the `RC` branch by default
- Most development work flows through `RC` before being promoted to `main`

This configuration ensures that all feature development is properly tested and integrated before reaching production.

## Release Process

### Version Numbering

Follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

Examples: `v1.0.0`, `v1.2.3`, `v2.0.0`

### Release Checklist

Before promoting RC to main:

- [ ] All planned features merged to RC
- [ ] All tests passing on RC
- [ ] Manual testing completed on RC
- [ ] Documentation updated
- [ ] CHANGELOG updated (if applicable)
- [ ] Version number decided
- [ ] Run "Promote RC to Main" GitHub Action

### Post-Release

After promoting to main:

- [ ] Verify the release tag was created
- [ ] Verify main branch is updated
- [ ] Create GitHub Release (optional)
- [ ] Announce the release (if applicable)
- [ ] Continue development on RC

## Deprecated Branches

### `develop` Branch

**Status**: ❌ DELETED

The `develop` branch has been removed from this project. Its functionality has been replaced by the `RC` (Release Candidate) branch, which serves as the pre-release testing and integration branch.

If you have local references to the old `develop` branch, you should delete them:

```bash
git branch -d develop                 # Delete local branch
```

Note: The remote `develop` branch has already been deleted from the repository.

## Quick Reference

```bash
# Start new feature
git checkout RC
git checkout -b feature/my-feature

# Update your branch with latest RC
git checkout feature/my-feature
git pull origin RC

# After PR is merged to RC, promote to main
# Use GitHub Actions: Actions > Promote RC to Main > Run workflow
```

## Troubleshooting

### Merge Conflicts

If you encounter merge conflicts when merging to RC:

1. Update your feature branch with latest RC:
   ```bash
git checkout feature/my-feature
git pull origin RC
   ```
2. Resolve conflicts locally
3. Commit the resolution
4. Push to your feature branch

### Failed Promotion

If the "Promote RC to Main" action fails:

1. Check the workflow logs in the Actions tab
2. Common issues:
   - Merge conflicts between RC and main
   - Branch protection rules blocking the push
   - Invalid version tag format
3. Resolve the issue and try again

For merge conflicts, you may need to manually:
1. Pull both main and RC locally
2. Merge main into RC to resolve conflicts
3. Push RC
4. Run the promotion action again

## Additional Resources

- [GitHub Flow Documentation](https://guides.github.com/introduction/flow/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
# CI recipes

## Windows PyInstaller

Recipe file: [`windows-pyinstaller.yml`](windows-pyinstaller.yml)

GitHub OAuth tokens used by some tooling cannot create files under
`.github/workflows/` (missing `workflow` scope). Enable the job once:

### Option A — GitHub web UI

1. Open https://github.com/alexgayer85/CoCoIDE  
2. **Add file → Create new file**  
3. Path: `.github/workflows/windows-pyinstaller.yml`  
4. Paste the contents of `packaging/ci/windows-pyinstaller.yml`  
5. Commit to `main`

### Option B — local git with full scopes

```bash
gh auth refresh -h github.com -s workflow,repo
mkdir -p .github/workflows
cp packaging/ci/windows-pyinstaller.yml .github/workflows/
git add .github/workflows/windows-pyinstaller.yml
git commit -m "ci: enable Windows PyInstaller workflow"
git push origin main
```

### Run the build

- **Actions → Windows PyInstaller → Run workflow**  
  Attaches `CoCoIDE-*-windows-x86_64.zip` (with `CoCoIDE.exe`) to the latest release.  
- Or push a `v*` tag (also attaches to that release).

### Local Windows build (no Actions)

```powershell
# Needs: Python 3.12, Git, MSYS2 UCRT64 with gcc + make
# Build decb.exe in MSYS2, then:
.\scripts\fetch_tools_windows.ps1
.\scripts\package_windows.ps1
# → dist\CoCoIDE-<ver>-windows-x86_64.zip
```

vscode settings - workspace (setting.json) vs user (environment) user -> global
~/.config/Code/User/settings.json workspace -> project .vscode/settings.json in repo

# selectively enforce strictness at top of modules.

// in .vscode/settings.json "python.analysis.typeCheckingMode": "basic"

# pyright: strict

def simulate_retirement(...): ...

# 🧰 Developer Reference: VS Code, Python, and Bash

---

## 🔧 Bash Commands

### Show Folder Structure

```bash
tree -L 2                             # Shows current directory tree, 2 levels deep
tree -I '__pycache__|.git|.vscode'   # Ignores cache, Git, and VS Code folders

### Workspace vs User Settings

| Scope     | Location                                  |
|-----------|--------------------------------------------|
| User      | `~/.config/Code/User/settings.json`        |
| Workspace | `.vscode/settings.json` (in repo root)     |

{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",  // Prettier for non-Python
  "python.formatting.provider": "black",                // Black formatter for Python
  "python.linting.pylintEnabled": true,
  "python.analysis.typeCheckingMode": "basic"
}

# pyright: strict

def simulate_retirement(...):
    ...

```

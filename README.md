# HTT Tracker: Ultimate Web Mirroring & Security Suite

![Banner](https://img.shields.io/badge/HTT_Tracker-v3.5-brightgreen?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-blue?style=for-the-badge)

**HTT Tracker** is a high-fidelity web cloning and security research suite. It mirrors dynamic websites with 100% visual integrity, featuring automated environment setup, stealth interception, and a multi-step validation facade.

---

## 💎 Features
*   **Auto-Setup**: Virtual env, dependencies, and browsers are handled automatically.
*   **100% Visual Fidelity**: Real-time network interception captures dynamic assets (React/Vue/etc).
*   **CSS Path Fixer**: Rewrites relative paths in CSS to point to local assets.
*   **Stealth JS Payload**: Injects an interceptor that hooks into form submissions.
*   **Two-Step Validation Facade**: 
    *   **Attempt 1**: Captures data + Shows "Invalid Password" error.
    *   **Attempt 2+**: Captures data + Redirects to real dashboard.

---

## 🚀 One-Command Use

The `clone` command automatically sets up Python, your virtual environment, and all dependencies on the first run.

### **Windows**
1.  Open PowerShell/CMD in the project folder.
2.  Run:
    ```powershell
    .\clone.bat https://target-website.com
    ```

### **Linux / Android (Termux)**
1.  Open your terminal.
2.  Run:
    ```bash
    chmod +x clone.sh
    ./clone.sh https://target-website.com
    ```

---

## 📋 Commands & Options

| Command | Description |
| :--- | :--- |
| `clone.sh {URL}` | Standard high-fidelity clone with auto-setup & server |
| `clone {URL} --wait 30` | Increase wait time for heavy JavaScript sites |

---

## 📂 Project Structure
*   `tracker.py`: Core engine.
*   `cloned_sites/`: Stores all mirrored projects.
*   `captured_credentials.txt`: Generated inside each project folder (e.g., `cloned_sites/www_site_com/captured_credentials.txt`).

---

## ⚠️ Disclaimer
Educational and authorized security research only. Authors take no responsibility for misuse. Obtain permission before testing.

---

## 📜 License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---
*Created by Black Zone*

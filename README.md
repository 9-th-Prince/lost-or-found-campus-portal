# 🔍 Lost or Found — Campus Portal & Study Hub

A full-stack web application built with **Python (Flask)**, **SQLite**, and **Bootstrap 5** that helps college students report misplaced items, verify ownership through security questions, and coordinate handoffs or study groups via a real-time Campus Chat Hub.

## ✨ Key Features
* **Lost & Found Feed:** Post items with photos, campus locations, and categories, plus instant keyword and category filtering.
* **Security Question Verification:** Finders can set a secret verification question when reporting found items so real owners can prove ownership.
* **Smart Item Matching:** Automatically detects opposite-type items (`Lost` vs. `Found`) in the same category on the user's dashboard.
* **WhatsApp-Style Campus Chat & Study Hub:**
  * **🌐 Open Campus Chat:** Public chatroom for all registered students.
  * **👤 Private Direct Chat:** Search classmates by name/email or click **Message** directly on any item listing.
  * **📚 Study Groups:** Create, join, and leave course study groups.
* **Live Notification Badges:** Auto-updating unread message and claim counters in the navigation bar.
* **Student Profile & Admin Panel:** Edit profile/password, track personal stats, and moderate campus posts as an admin.

## 🛠️ Tech Stack
* **Backend:** Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug
* **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2 Templates
* **Database:** SQLite (`lost_or_found.db`)

## 🚀 How to Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt



   Email: admin@campus.edu

Password: admin123


---

### Step 2: Which Platform Should You Use to Go Live?

| Platform | Best For | Works with Your SQLite + Image Uploads? | Verdict for Your Project |
| :--- | :--- | :--- | :--- |
| **GitHub** | Storing and sharing your source code | Code hosting only (does not run Python servers) | **Use first** to store your code & `README.md` |
| **PythonAnywhere** | Hosting Python/Flask apps with SQLite & file uploads | **Yes!** Keeps your `lost_or_found.db` and `static/uploads/` saved permanently | **Best & Easiest Choice** (100% free, no credit card, never goes to sleep) |
| **Render** | General web services from GitHub | Partially (free tier wipes uploaded photos & SQLite data whenever the server sleeps after 15 mins) | Good backup, but data resets on sleep |
| **Netlify / Vercel** | Static HTML/JS sites & serverless APIs | **No** (Netlify doesn't run Flask backends; Vercel serverless functions wipe local SQLite files and uploaded images) | Skip for this project |

---

### Step 3: How to Put It Live on **PythonAnywhere** (Free, ~5 Minutes)

#### Part A: Upload Your Code to GitHub
1. Create a free account at **github.com** and click **New Repository** (name it `lost-or-found`).
2. Upload all your project files (`app.py`, `requirements.txt`, `README.md`, and your `templates/` and `static/` folders). *(Do not upload `lost_or_found.db` so the server creates a fresh database.)*

#### Part B: Deploy on PythonAnywhere
1. Go to **pythonanywhere.com** and click **Pricing & signup** → **Create a Beginner account** (completely free, no credit card required).
2. Open a **Bash console** from your PythonAnywhere dashboard and run these two commands to pull your code and install Flask:
   ```bash
   git clone https://github.com/YOUR-USERNAME/lost-or-found.git
   pip install --user -r lost-or-found/requirements.txt
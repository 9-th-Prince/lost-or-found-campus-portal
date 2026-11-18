# 🔍 Lost or Found — Campus Portal & Study Hub

A full-stack web application built with **Python (Flask)**, **SQLite**, and **Bootstrap 5** that helps college students report misplaced items, verify ownership through security questions, and coordinate handoffs or study groups via a real-time Campus Chat Hub.

🌐 **Live Demo:** [https://sakibul001.pythonanywhere.com](https://sakibul001.pythonanywhere.com)

## ✨ Key Features
* **Lost & Found Feed:** Post items with photos, campus locations, and categories, plus instant keyword and category filtering.
* **Security Question Verification:** Finders can set a secret verification question when reporting found items so real owners can prove ownership.
* **Smart Item Matching:** Automatically detects opposite-type items (`Lost` vs. `Found`) in the same category on the user's dashboard.
* **WhatsApp-Style Campus Chat & Study Hub:**
  * **🌐 Open Campus Chat:** Public chatroom for all registered students.
  * **👤 Private Direct Chat:** Search classmates by name/email or click **Message** directly on any item listing or dashboard claim.
  * **📚 Study Groups:** Create, join, and leave course study groups.
* **Live Notification Badges:** Auto-updating unread message and claim counters in the navigation bar.
* **Student Profile & Admin Panel:** Edit profile/password, track personal stats, and moderate campus posts as an admin.

## 🛠️ Tech Stack
* **Backend:** Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug
* **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2 Templates, JavaScript (AJAX Polling)
* **Database:** SQLite (`lost_or_found.db`)

## 🚀 How to Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   

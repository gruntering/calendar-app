**Calendar App**
A simple Flask web application for tracking personal calendar events, including vacation days, sick days, and holidays. Deployed on Render’s free tier at [https://calendar-app-jrnd.onrender.com](url)
**Features**
Authentication: Register and log in with username, email, and password.
Calendar: Add and manage events (Work, Vacation, Sick, Absence) with a FullCalendar interface.
Holidays: Pre-loaded German holidays (e.g., Neujahr, Karfreitag) for 2025–2030.
User Dashboard: Track remaining vacation and sick days, reset yearly.
UI: Clean sidebar, full blue button hovers, no underlines on links.

Features
Authentication: Register and log in with username, email, and password.
Calendar: Add and manage events (Work, Vacation, Sick, Absence) with a FullCalendar interface.
Holidays: Pre-loaded German holidays (e.g., Neujahr, Karfreitag) for 2025–2030.
User Dashboard: Track remaining vacation and sick days, reset yearly.
UI: Clean sidebar, full blue button hovers, no underlines on links.
Tech Stack
Backend: Flask 2.3.2, Flask-SQLAlchemy 3.0.3, Flask-Login 0.6.2, Flask-WTF 1.1.1
Database: SQLite (site.db, ephemeral on Render free tier)
Server: Gunicorn 20.1.0
Frontend: HTML, CSS, JavaScript (FullCalendar)
Hosting: Render (free tier)
Local Development
Prerequisites
Python 3.11+
Git

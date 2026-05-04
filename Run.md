
## 2. Create Virtual Environment

```bash
py -3.11 -m venv .venv
```

**Activate the environment:**

| Platform | Command |
|---|---|
| Git Bash / Linux / Mac | `source .venv/Scripts/activate` |
| Windows CMD | `.venv\Scripts\activate.bat` |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |

---

## 3. Upgrade pip

```bash
python -m pip install --upgrade pip
pip --version
```

---

## 4. Install Dependencies

Create a `requirements.txt` file in the project root with the following:

```
fastapi==0.110.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.29
psycopg2-binary==2.9.9
httpx==0.27.0
pydantic==2.6.4
python-dotenv==1.0.1
```

Then install:

```bash
pip install -r requirements.txt
pip list   # verify installed packages
```

---

## 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:password@localhost/user_db
```

> **Note:** Replace `password` and `user_db` with your actual PostgreSQL credentials and database name.

---

## 6. Run the Application

```bash
uvicorn app.main:app --reload --port 8002
```

The API will be available at:

- **App:** http://localhost:8002
- **Swagger UI:** http://localhost:8002/docs
- **ReDoc:** http://localhost:8002/redoc

---

## 7. Cleanup — Remove Virtual Environment

Deactivate the environment first:

```bash
deactivate
```

Then delete the `.venv` folder:

| Platform | Command |
|---|---|
| Mac / Linux / Git Bash | `rm -rf .venv` |
| Windows CMD | `rmdir /s /q .venv` |
| Windows PowerShell | `Remove-Item -Recurse -Force .venv` |

---

## Project Structure (Reference)

```
your-project/
├── app/
│   └── main.py
├── .env
├── requirements.txt
└── README.md
```

---

*Keep this file updated as the project evolves.*

# 1. Navigate to your project folder
cd /path/to/your/project

# 2. Check the current status
git status

# 3. Stage your changes
git add .          # adds all files
# OR
git add filename   # adds a specific file

# 4. Commit your changes
git commit -m "Your commit message here"

# 5. Push to your remote repo
git push origin main   # replace 'main' with your branch name

git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main

git add .
git commit -m "Initial commit"
git push -u origin main
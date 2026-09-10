
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, json
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "land_portal.db")
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sih2026-demo-secret")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL, role TEXT NOT NULL,
      phone TEXT
    );
    CREATE TABLE IF NOT EXISTS projects(
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
      state TEXT, district TEXT, required_area REAL DEFAULT 0,
      status TEXT DEFAULT 'Active', created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS parcels(
      id INTEGER PRIMARY KEY AUTOINCREMENT, survey_no TEXT NOT NULL,
      village TEXT, district TEXT, state TEXT, area REAL,
      owner_id INTEGER, project_id INTEGER, status TEXT,
      lat REAL, lng REAL, risk TEXT DEFAULT 'Low',
      delay_reason TEXT, compensation REAL DEFAULT 0,
      payment_status TEXT DEFAULT 'Pending', possession TEXT DEFAULT 'Pending',
      FOREIGN KEY(owner_id) REFERENCES users(id),
      FOREIGN KEY(project_id) REFERENCES projects(id)
    );
    CREATE TABLE IF NOT EXISTS documents(
      id INTEGER PRIMARY KEY AUTOINCREMENT, parcel_id INTEGER,
      title TEXT, filename TEXT, uploaded_at TEXT,
      FOREIGN KEY(parcel_id) REFERENCES parcels(id)
    );
    CREATE TABLE IF NOT EXISTS objections(
      id INTEGER PRIMARY KEY AUTOINCREMENT, parcel_id INTEGER,
      owner_id INTEGER, text TEXT, status TEXT DEFAULT 'Pending',
      created_at TEXT,
      FOREIGN KEY(parcel_id) REFERENCES parcels(id)
    );
    CREATE TABLE IF NOT EXISTS audit_logs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
      action TEXT, entity TEXT, entity_id INTEGER, created_at TEXT
    );
    """)
    # Seed demo users
    users = [
      ("Admin Officer","admin@sih.local","admin123","admin","9000000001"),
      ("District Collector","collector@sih.local","admin123","collector","9000000002"),
      ("Revenue Officer","revenue@sih.local","admin123","officer","9000000003"),
      ("Ramesh Patil","farmer@sih.local","farmer123","farmer","9000000004"),
    ]
    for u in users:
        try:
            conn.execute("INSERT INTO users(name,email,password,role,phone) VALUES(?,?,?,?,?)",
                         (u[0],u[1],generate_password_hash(u[2]),u[3],u[4]))
        except sqlite3.IntegrityError: pass

    if conn.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"] == 0:
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute("INSERT INTO projects(name,state,district,required_area,status,created_at) VALUES(?,?,?,?,?,?)",
                     ("Sambhajinagar Green Highway","Maharashtra","Chhatrapati Sambhajinagar",1200,"Active",now))
        conn.execute("INSERT INTO projects(name,state,district,required_area,status,created_at) VALUES(?,?,?,?,?,?)",
                     ("Jalna Logistics Corridor","Maharashtra","Jalna",650,"Active",now))
        p1 = conn.execute("SELECT id FROM projects WHERE name=?",("Sambhajinagar Green Highway",)).fetchone()["id"]
        p2 = conn.execute("SELECT id FROM projects WHERE name=?",("Jalna Logistics Corridor",)).fetchone()["id"]
        farmer = conn.execute("SELECT id FROM users WHERE email='farmer@sih.local'").fetchone()["id"]
        parcels = [
          ("GAT-101","Karmad","Chhatrapati Sambhajinagar","Maharashtra",2.4,farmer,p1,"Compensation Approved",19.9600,75.5200,"Low","",1850000,"Approved","Pending"),
          ("GAT-102","Karmad","Chhatrapati Sambhajinagar","Maharashtra",1.8,farmer,p1,"Owner Verification",19.9700,75.5300,"High","Ownership document mismatch",1250000,"Pending","Pending"),
          ("GAT-103","Karmad","Chhatrapati Sambhajinagar","Maharashtra",3.1,farmer,p1,"Survey Completed",19.9500,75.5100,"Medium","Objection pending",2200000,"Pending","Pending"),
          ("GAT-204","Badnapur","Jalna","Maharashtra",2.0,farmer,p2,"Payment Initiated",19.8200,75.7300,"Low","",1400000,"Initiated","Pending"),
          ("GAT-205","Badnapur","Jalna","Maharashtra",1.2,farmer,p2,"Possession Completed",19.8100,75.7200,"Low","",900000,"Paid","Completed"),
        ]
        conn.executemany("""INSERT INTO parcels
          (survey_no,village,district,state,area,owner_id,project_id,status,lat,lng,risk,delay_reason,compensation,payment_status,possession)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",parcels)
    conn.commit(); conn.close()

def log(action, entity="", entity_id=None):
    if "user_id" in session:
        conn=db()
        conn.execute("INSERT INTO audit_logs(user_id,action,entity,entity_id,created_at) VALUES(?,?,?,?,?)",
                     (session["user_id"],action,entity,entity_id,datetime.now().isoformat(timespec="seconds")))
        conn.commit(); conn.close()

@app.context_processor
def inject():
    return {"user": session.get("user"), "role": session.get("role")}

@app.route("/")
def home():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        conn=db()
        u=conn.execute("SELECT * FROM users WHERE lower(email)=?", (email,)).fetchone()
        conn.close()
        if u and check_password_hash(u["password"], password):
            session.clear()
            session.update(user_id=u["id"], user=u["name"], role=u["role"], email=u["email"])
            log("Logged in")
            if u["role"] in ("admin","collector","officer"):
                return redirect(url_for("officer_portal"))
            return redirect(url_for("dashboard"))
        flash("Invalid email or password. Please use one of the demo accounts below.","error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

def auth():
    return "user_id" in session

# Initialize the SQLite database automatically, whether the app is started
# with `python app.py`, `flask run`, or a production server such as Gunicorn.
@app.before_request
def ensure_database():
    init_db()

@app.route("/dashboard")
def dashboard():
    if not auth(): return redirect(url_for("login"))
    conn=db()
    projects=conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    if session["role"]=="farmer":
        parcels=conn.execute("""SELECT p.*, pr.name project_name FROM parcels p LEFT JOIN projects pr ON p.project_id=pr.id
                                WHERE p.owner_id=? ORDER BY p.id DESC""",(session["user_id"],)).fetchall()
    else:
        parcels=conn.execute("""SELECT p.*, pr.name project_name, u.name owner_name FROM parcels p
                                LEFT JOIN projects pr ON p.project_id=pr.id LEFT JOIN users u ON p.owner_id=u.id
                                ORDER BY p.id DESC""").fetchall()
    stats = {
      "projects": conn.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"],
      "parcels": conn.execute("SELECT COUNT(*) c FROM parcels").fetchone()["c"],
      "acquired": conn.execute("SELECT COUNT(*) c FROM parcels WHERE possession='Completed'").fetchone()["c"],
      "high_risk": conn.execute("SELECT COUNT(*) c FROM parcels WHERE risk='High'").fetchone()["c"],
      "paid": conn.execute("SELECT COALESCE(SUM(compensation),0) s FROM parcels WHERE payment_status='Paid'").fetchone()["s"],
      "pending": conn.execute("SELECT COUNT(*) c FROM parcels WHERE payment_status!='Paid'").fetchone()["c"],
    }
    conn.close()
    return render_template("dashboard.html", projects=projects, parcels=parcels, stats=stats)

@app.route("/officer")
def officer_portal():
    if not auth() or session["role"]=="farmer":
        return redirect(url_for("dashboard"))
    conn=db()
    parcels=conn.execute("""SELECT p.*, pr.name project_name, u.name owner_name, u.phone owner_phone
                            FROM parcels p
                            LEFT JOIN projects pr ON p.project_id=pr.id
                            LEFT JOIN users u ON p.owner_id=u.id
                            ORDER BY p.id DESC""").fetchall()
    stats = {
        "total": conn.execute("SELECT COUNT(*) c FROM parcels").fetchone()["c"],
        "high": conn.execute("SELECT COUNT(*) c FROM parcels WHERE risk='High'").fetchone()["c"],
        "pending": conn.execute("SELECT COUNT(*) c FROM parcels WHERE payment_status!='Paid'").fetchone()["c"],
        "paid": conn.execute("SELECT COALESCE(SUM(compensation),0) s FROM parcels WHERE payment_status='Paid'").fetchone()["s"],
    }
    conn.close()
    return render_template("officer.html", parcels=parcels, stats=stats)

@app.route("/projects", methods=["GET","POST"])
def projects():
    if not auth() or session["role"]=="farmer": return redirect(url_for("dashboard"))
    conn=db()
    if request.method=="POST":
        conn.execute("INSERT INTO projects(name,state,district,required_area,status,created_at) VALUES(?,?,?,?,?,?)",
          (request.form["name"],request.form["state"],request.form["district"],float(request.form["area"]),request.form.get("status","Active"),datetime.now().isoformat(timespec="seconds")))
        conn.commit(); log("Created project","project",conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        flash("Project created","success")
    rows=conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall(); conn.close()
    return render_template("projects.html", projects=rows)

@app.route("/parcels", methods=["GET","POST"])
def parcels():
    if not auth() or session["role"]=="farmer": return redirect(url_for("dashboard"))
    conn=db()
    if request.method=="POST":
        conn.execute("""INSERT INTO parcels(survey_no,village,district,state,area,owner_id,project_id,status,lat,lng,risk,compensation)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
          (request.form["survey_no"],request.form["village"],request.form["district"],request.form["state"],
           float(request.form["area"]),int(request.form["owner_id"]),int(request.form["project_id"]),request.form["status"],
           float(request.form["lat"]),float(request.form["lng"]),request.form["risk"],float(request.form.get("compensation",0))))
        conn.commit(); log("Created parcel","parcel",conn.execute("SELECT last_insert_rowid()").fetchone()[0]); flash("Parcel added","success")
    ps=conn.execute("""SELECT p.*,pr.name project_name,u.name owner_name FROM parcels p
      LEFT JOIN projects pr ON p.project_id=pr.id LEFT JOIN users u ON p.owner_id=u.id ORDER BY p.id DESC""").fetchall()
    users=conn.execute("SELECT id,name,email FROM users WHERE role='farmer'").fetchall()
    projects=conn.execute("SELECT id,name FROM projects").fetchall(); conn.close()
    return render_template("parcels.html",parcels=ps,users=users,projects=projects)

@app.route("/parcel/<int:pid>")
def parcel(pid):
    if not auth(): return redirect(url_for("login"))
    conn=db()
    p=conn.execute("""SELECT p.*,pr.name project_name,u.name owner_name,u.phone owner_phone FROM parcels p
      LEFT JOIN projects pr ON p.project_id=pr.id LEFT JOIN users u ON p.owner_id=u.id WHERE p.id=?""",(pid,)).fetchone()
    docs=conn.execute("SELECT * FROM documents WHERE parcel_id=? ORDER BY id DESC",(pid,)).fetchall()
    objections=conn.execute("SELECT * FROM objections WHERE parcel_id=? ORDER BY id DESC",(pid,)).fetchall()
    conn.close()
    if not p: return "Not found",404
    if session["role"]=="farmer" and p["owner_id"] != session["user_id"]: return "Forbidden",403
    return render_template("parcel.html",p=p,docs=docs,objections=objections)

@app.route("/parcel/<int:pid>/update", methods=["POST"])
def update_parcel(pid):
    if not auth() or session["role"]=="farmer": return "Forbidden",403
    conn=db()
    conn.execute("""UPDATE parcels SET status=?,risk=?,delay_reason=?,payment_status=?,possession=? WHERE id=?""",
                 (request.form["status"],request.form["risk"],request.form.get("delay_reason",""),
                  request.form["payment_status"],request.form["possession"],pid))
    conn.commit(); conn.close(); log("Updated parcel","parcel",pid)
    flash("Parcel updated","success"); return redirect(url_for("parcel",pid=pid))

@app.route("/parcel/<int:pid>/objection", methods=["POST"])
def objection(pid):
    if not auth(): return "Forbidden",403
    conn=db()
    p=conn.execute("SELECT owner_id FROM parcels WHERE id=?",(pid,)).fetchone()
    if not p or (session["role"]=="farmer" and p["owner_id"]!=session["user_id"]): return "Forbidden",403
    conn.execute("INSERT INTO objections(parcel_id,owner_id,text,created_at) VALUES(?,?,?,?)",
                 (pid,session["user_id"],request.form["text"],datetime.now().isoformat(timespec="seconds")))
    conn.commit(); conn.close(); log("Submitted objection","parcel",pid)
    flash("Objection submitted","success"); return redirect(url_for("parcel",pid=pid))

@app.route("/parcel/<int:pid>/document", methods=["POST"])
def document(pid):
    if not auth(): return "Forbidden",403
    f=request.files.get("file")
    if not f or not f.filename: flash("Choose a file","error"); return redirect(url_for("parcel",pid=pid))
    upload_dir=os.path.join(BASE,"uploads"); os.makedirs(upload_dir,exist_ok=True)
    safe=os.path.basename(f.filename).replace(" ","_")
    f.save(os.path.join(upload_dir,safe))
    conn=db(); conn.execute("INSERT INTO documents(parcel_id,title,filename,uploaded_at) VALUES(?,?,?,?)",
      (pid,request.form.get("title","Document"),safe,datetime.now().isoformat(timespec="seconds"))); conn.commit(); conn.close()
    log("Uploaded document","parcel",pid); flash("Document uploaded","success"); return redirect(url_for("parcel",pid=pid))

@app.route("/api/map")
def map_api():
    if not auth(): return jsonify([])
    conn=db()
    rows=conn.execute("""SELECT p.id,p.survey_no,p.lat,p.lng,p.status,p.risk,p.area,
                                p.village,p.district,p.state,p.compensation,p.payment_status,p.possession,
                                p.delay_reason,u.name owner_name,u.phone owner_phone,
                                pr.name project_name
                         FROM parcels p
                         LEFT JOIN projects pr ON p.project_id=pr.id
                         LEFT JOIN users u ON p.owner_id=u.id""").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/stats")
def stats_api():
    if not auth(): return jsonify({})
    conn=db()
    out={
      "total":conn.execute("SELECT COUNT(*) c FROM parcels").fetchone()["c"],
      "completed":conn.execute("SELECT COUNT(*) c FROM parcels WHERE possession='Completed'").fetchone()["c"],
      "high":conn.execute("SELECT COUNT(*) c FROM parcels WHERE risk='High'").fetchone()["c"],
      "pending_payment":conn.execute("SELECT COUNT(*) c FROM parcels WHERE payment_status!='Paid'").fetchone()["c"],
      "compensation":conn.execute("SELECT COALESCE(SUM(compensation),0) s FROM parcels").fetchone()["s"]
    }
    conn.close(); return jsonify(out)

@app.route("/health")
def health():
    return jsonify({"status":"ok","service":"LandPulse","database":os.path.exists(DB)})

if __name__=="__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT",5000)))

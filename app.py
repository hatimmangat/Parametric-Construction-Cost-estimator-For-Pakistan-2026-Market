import json, os
from copy import deepcopy
from functools import wraps
from pathlib import Path
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

ROOT = Path(__file__).parent
CONFIG_FILE = ROOT / "data" / "rates.json"
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-before-deployment")

DEFAULT = {
 "materials":{"steel":{"Mughal":275,"Amreli":285,"Aga Khan":290},"cement":{"Bestway":1300,"DG":1320,"Lucky":1310,"Maple":1280},"sand":{"Lawrencepur":55,"Chenab":50,"Ravi":48},"crush":{"Margalla":70,"Sargodha":65,"Taxila":72},"bricks":{"A Class":15,"B Class":13,"Machine Block":18},"wire":{"Fast":185,"Paklite":175,"GM":190},"tiles":{"Master":350,"Shabbir":300,"Nitco":450,"Orient":400},"paint":{"Brighto":520,"Dulux":650,"Berger":720,"Master":600,"Nippon":780},"wood":{"Local":4500,"Deodar":9500,"Sheesham":8000},"sanitary":{"Sonex":28000,"Porta":22000,"Master":35000,"Grohe":55000},"ceiling":{"Simple POP":120,"Gypsum":180,"Designer":260}},
 "city_factors":{"Lahore":1,"Karachi":1.10,"Islamabad":1.15,"Rawalpindi":1.08,"Multan":.95,"Faisalabad":.97,"Peshawar":.96,"Gujranwala":.94},
 "soil_factors":{"Normal":1,"Soft":1.08,"Filled":1.15},"quality":{"Standard":1,"Premium":1.18,"Luxury":1.42},
 "plots":{"5":{"sqft":1125,"max_beds":4,"max_living":2},"10":{"sqft":2250,"max_beds":6,"max_living":3},"15":{"sqft":3375,"max_beds":8,"max_living":4},"20":{"sqft":4500,"max_beds":10,"max_living":4}},
 "labour":{"grey":380,"finish":480},"contractor":{"grey":120,"finish":200},"insulation":{"Basic":120,"Thermal":180,"Premium":250}
}
def config():
    if not CONFIG_FILE.exists(): CONFIG_FILE.write_text(json.dumps(DEFAULT, indent=2))
    return json.loads(CONFIG_FILE.read_text())
def money(n): return round(n)
def calculate(v, c):
    plot=str(v.get('plot','5')); rule=c['plots'][plot]; floors=max(1,min(3,int(v.get('floors',1))))
    beds=max(1,min(rule['max_beds'],int(v.get('beds',2)))); baths=max(1,min(beds,int(v.get('baths',2)))); living=max(1,min(rule['max_living'],int(v.get('living',1))))
    city=v.get('city','Lahore'); soil=v.get('soil','Normal'); quality=v.get('quality','Standard'); brands=v.get('brands',{})
    p=lambda group: c['materials'][group][brands.get(group,next(iter(c['materials'][group])))]
    base=rule['sqft']*.75*floors; addon=(.05 if v.get('porch') else 0)+(.03 if v.get('balcony') else 0); area=base*(1+addon)
    extra_b=max(0,beds-2); extra_l=max(0,living-1); extra_f=max(0,floors-1); sf=c['soil_factors'][soil]; cf=c['city_factors'][city]; qm=c['quality'][quality]
    steel=area*(2.8+.12*extra_b+.06*extra_f)*sf; cement=area*(.28+.012*extra_b+.005*baths+.006*extra_f)*sf; sand=area*(.95+.04*extra_b+.015*baths)*sf; crush=area*(.70+.03*extra_b+.015*extra_f)*sf; bricks=area*(36+2*extra_b+.8*baths)
    grey_mat=(steel*p('steel')+cement*p('cement')+sand*p('sand')+crush*p('crush')+bricks*p('bricks'))*cf
    wiring=area*(.07+.008*extra_b+.006*extra_l); plumbing=area*(.05+.018*baths); tiles=area*(.75+.07*baths); paint=area*(2.7+.12*extra_b+.15*extra_l); wood=area*(.10+.01*extra_b+.008*extra_l)
    finish_mat=(wiring*p('wire')+tiles*p('tiles')+(paint/250)*p('paint')+wood*(p('wood')/3.5)+baths*p('sanitary')+plumbing*1500+area*35+area*60*(1+.05*baths)+area*100+area*100)*qm*cf
    grey_lab=area*c['labour']['grey']*(1+.04*extra_f)*cf; fin_lab=area*c['labour']['finish']*(1+.03*extra_b+.02*baths+.02*extra_l)*cf
    gcont=area*c['contractor']['grey']*cf; fcont=area*c['contractor']['finish']*cf
    addons=0; addon_rows=[]
    if v.get('insulation'):
        z=area*c['insulation'][v.get('insulation_type','Thermal')]*cf; addons+=z; addon_rows.append(['Insulation',z])
    if v.get('ceiling'):
        z=area*c['materials']['ceiling'][v['ceiling']]*cf; addons+=z; addon_rows.append(['Ceiling',z])
    grey=grey_mat+grey_lab+gcont; finish=finish_mat+fin_lab+fcont+addons; total=grey+finish
    return {"area":round(area),"total":money(total),"per_sqft":money(total/area),"grey":money(grey),"finish":money(finish),"breakdown":[["Grey materials",money(grey_mat)],["Grey labour",money(grey_lab)],["Grey contractor",money(gcont)],["Finishing materials",money(finish_mat)],["Finishing labour",money(fin_lab)],["Finishing contractor",money(fcont)]]+[[x,money(y)] for x,y in addon_rows],"quantities":[["Steel",round(steel),"kg"],["Cement",round(cement),"bags"],["Sand",round(sand),"cft"],["Crush",round(crush),"cft"],["Bricks",round(bricks),"units"],["Tiles",round(tiles),"sq ft"],["Paint coverage",round(paint),"sq ft"]]}
def admin_required(f):
 @wraps(f)
 def w(*a,**k): return f(*a,**k) if session.get('admin') else redirect(url_for('admin_login'))
 return w
@app.route('/')
def home(): return render_template('index.html', cfg=config())
@app.post('/api/calculate')
def api_calc(): return jsonify(calculate(request.get_json() or {},config()))
@app.route('/admin/login',methods=['GET','POST'])
def admin_login():
 if request.method=='POST' and request.form.get('password')==os.getenv('ADMIN_PASSWORD','change-me-2026'):
  session['admin']=True; return redirect(url_for('admin'))
 return render_template('login.html',error=request.method=='POST')
@app.route('/admin')
@admin_required
def admin(): return render_template('admin.html', config=json.dumps(config(),indent=2))
@app.post('/admin/save')
@admin_required
def save():
 try:
  obj=json.loads(request.form['config']); assert all(k in obj for k in DEFAULT)
  CONFIG_FILE.write_text(json.dumps(obj,indent=2)); return redirect(url_for('admin',saved=1))
 except Exception as e: return render_template('admin.html',config=request.form.get('config','{}'),error=str(e))
@app.get('/admin/logout')
def logout(): session.clear(); return redirect(url_for('home'))
if __name__=='__main__': app.run(debug=True)

#!/usr/bin/env python3
"""Generate terminal SVGs from the public GitHub avatar and contribution calendar."""
import io, json, os, re
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
ASSETS, DATA = ROOT / "assets", ROOT / "data"
USER = os.getenv("GITHUB_USERNAME", "callmetechnophile")
BG, LINE, FG, MUTED, CYAN = "#0b1016", "#243442", "#dce7ef", "#8297a8", "#66d9ef"
LEVELS = ["#17232d", "#183b4a", "#1e6276", "#2995ad", CYAN]
RAMP = " .,:;irsXA253hMHGS#9B&@"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130 Safari/537.36",
           "Accept": "text/html, */*", "Accept-Language": "en-US,en;q=0.9",
           "X-Requested-With": "XMLHttpRequest", "Referer": f"https://github.com/{USER}"}

def get_avatar():
    res = requests.get(f"https://api.github.com/users/{USER}", timeout=25, headers={"User-Agent":"profile-art-generator"})
    res.raise_for_status()
    avatar = requests.get(res.json()["avatar_url"], timeout=25, headers={"User-Agent":"profile-art-generator"})
    avatar.raise_for_status()
    image = Image.open(io.BytesIO(avatar.content)).convert("RGB")
    image = ImageOps.fit(image, (84, 42), method=Image.Resampling.LANCZOS)
    return ImageEnhance.Contrast(ImageOps.grayscale(image)).enhance(1.6)

def portrait():
    image = get_avatar()
    px = image.load()
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="740" height="390" viewBox="0 0 740 390"><rect width="100%" height="100%" rx="12" fill="{BG}" stroke="{LINE}"/>',
           f'<text x="22" y="30" font-family="monospace" font-size="13" fill="{CYAN}">[ avatar.decode --ascii ]</text>',
           f'<text x="22" y="50" font-family="monospace" font-size="10" fill="{MUTED}">source: github.com/{USER}</text>']
    # Use <tspan> for the text and place animation as a sibling so the SVG remains valid.
    for y in range(image.height):
        line = "".join(RAMP[min(len(RAMP)-1, int((255-px[x,y])/255*(len(RAMP)-1)))] for x in range(image.width))
        out.append(f'<text x="22" y="{74+y*6.6:.1f}" font-family="monospace" font-size="7" xml:space="preserve" fill="{FG}"><tspan>{escape(line)}</tspan><animate attributeName="opacity" from="0" to="1" begin="{y*.04:.2f}s" dur=".25s" fill="freeze"/></text>')
    out += [f'<text x="22" y="370" font-family="monospace" font-size="10" fill="{MUTED}">real GitHub avatar · monochrome ASCII</text>', '</svg>']
    (ASSETS/"portrait.svg").write_text("\n".join(out), encoding="utf-8")

def header():
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="142" viewBox="0 0 900 142"><rect width="900" height="142" rx="12" fill="{BG}" stroke="{LINE}"/>
<circle cx="24" cy="22" r="5" fill="#ff6b6b"/><circle cx="42" cy="22" r="5" fill="#ffd166"/><circle cx="60" cy="22" r="5" fill="{CYAN}"/>
<text x="82" y="26" font-family="monospace" font-size="11" fill="{MUTED}">{USER} — profile shell</text>
<text x="28" y="68" font-family="monospace" font-size="25" font-weight="700" fill="{FG}">Ayush <tspan fill="{CYAN}">/</tspan> Engineering Systems</text>
<text x="28" y="94" font-family="monospace" font-size="13" fill="{MUTED}">electronics · embedded systems · robotics · AI/ML</text>
<text x="28" y="120" font-family="monospace" font-size="11" fill="{CYAN}">$ whoami <tspan fill="{FG}"> aspiring engineer building at the hardware/software boundary</tspan></text></svg>'''
    (ASSETS/"terminal-header.svg").write_text(svg, encoding="utf-8")

def info_card():
    rows=[("identity","Ayush / callmetechnophile"),("focus","Electronics · embedded · robotics"),("research","AI/ML · signal processing · PCB"),("builds","Workline · MEDIGRAPH AI · Namma Space"),("method","Prototype → measure → iterate")]
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="540" height="320" viewBox="0 0 540 320"><rect width="100%" height="100%" rx="12" fill="{BG}" stroke="{LINE}"/><path d="M0 42 H540" stroke="{LINE}"/>',f'<text x="22" y="25" font-family="monospace" font-size="12" fill="{CYAN}">system-info — terminal</text>']
    for i,(key,val) in enumerate(rows):
        y=82+i*43
        out.append(f'<g opacity="0"><text x="22" y="{y}" font-family="monospace" font-size="12" fill="{CYAN}">{escape(key)}</text><text x="126" y="{y}" font-family="monospace" font-size="10.5" fill="{FG}">{escape(val)}</text><animate attributeName="opacity" from="0" to="1" begin="{.3+i*.2:.2f}s" dur=".3s" fill="freeze"/></g>')
    out += [f'<text x="22" y="292" font-family="monospace" font-size="10" fill="{MUTED}">status: learning / prototyping / shipping</text>','</svg>']
    (ASSETS/"info-card.svg").write_text("\n".join(out), encoding="utf-8")

def fetch_contributions():
    response=requests.get(f"https://github.com/users/{USER}/contributions", timeout=30, headers=HEADERS)
    response.raise_for_status()
    soup=BeautifulSoup(response.text,"html.parser")
    days=[]
    # GitHub puts the real count in the tooltip, while data-level supplies the real intensity.
    tooltips={}
    for tip in soup.find_all("tool-tip", attrs={"for": True}):
        text=tip.get_text(" ", strip=True)
        match=re.search(r"(\d+) contributions?", text, re.I)
        if match: tooltips[tip.get("for")]=int(match.group(1))
    for node in soup.select("[data-date]"):
        try: day=date.fromisoformat(node.get("data-date"))
        except (ValueError,TypeError): continue
        count=None
        for key in ("data-count",):
            if node.get(key) is not None:
                try: count=int(node.get(key)); break
                except ValueError: pass
        if count is None:
            label=" ".join([node.get("aria-label",""),node.get("aria-description",""),node.get_text(" ",strip=True)])
            match=re.search(r"(\d+) contributions?",label,re.I)
            if match: count=int(match.group(1))
        if count is None:
            # GitHub often references a separate tooltip element by aria-describedby.
            refs=(node.get("aria-describedby","")+" "+node.get("id","")).split()
            for ref in refs:
                if ref in tooltips: count=tooltips[ref]; break
        if count is None:
            # Inspect adjacent tooltip elements; do not silently turn unknown counts into zero.
            parent=node.parent
            nearby=parent.get_text(" ",strip=True) if parent else ""
            match=re.search(r"(\d+) contributions?",nearby,re.I)
            if match: count=int(match.group(1))
        if count is None:
            raise RuntimeError(f"Found contribution day {day.isoformat()} but could not read its real count. Refusing to publish fabricated zeros.")
        try: level=int(node.get("data-level","0"))
        except ValueError: level=0
        days.append({"date":day.isoformat(),"count":count,"level":max(0,min(4,level))})
    if len(days)<300:
        raise RuntimeError(f"Expected a rolling-year contribution calendar; found only {len(days)} days. Refusing to publish incomplete data.")
    days.sort(key=lambda d:d["date"])
    today=date.today()
    counts={d["date"]:d["count"] for d in days}
    cursor=today
    if counts.get(cursor.isoformat(),0)==0: cursor-=timedelta(days=1)
    streak=0
    while counts.get(cursor.isoformat(),0)>0: streak+=1; cursor-=timedelta(days=1)
    data={"username":USER,"updated_at":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"total":sum(d["count"] for d in days),"current_streak":streak,"days":days}
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/"contributions.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
    return data

def heatmap(data):
    days=data["days"][-371:]
    first=date.fromisoformat(days[0]["date"])
    start=first-timedelta(days=(first.weekday()+1)%7)
    values={x["date"]:x for x in days}
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="178" viewBox="0 0 900 178"><rect width="900" height="178" rx="12" fill="{BG}" stroke="{LINE}"/>',f'<text x="22" y="25" font-family="monospace" font-size="12" fill="{CYAN}">contribution.log</text>',f'<text x="878" y="25" text-anchor="end" font-family="monospace" font-size="10" fill="{MUTED}">last 12 months · {data["total"]:,} contributions</text>']
    for col in range(53):
        for row in range(7):
            day=start+timedelta(days=col*7+row)
            if day>date.today() or day<date.today()-timedelta(days=370): continue
            item=values.get(day.isoformat(),{"count":0,"level":0})
            count=item["count"]
            # Use actual count and actual GitHub intensity; zero count must always render as zero.
            level=0 if count==0 else max(1,min(4,int(item.get("level",1))))
            x,y=22+col*16,44+row*16
            out.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{LEVELS[level]}" stroke="#263744" stroke-width=".35" opacity="0"><title>{day.isoformat()}: {count} contributions</title><animate attributeName="opacity" from="0" to="1" begin="{col*.018+row*.012:.3f}s" dur=".22s" fill="freeze"/></rect>')
    out += [f'<text x="22" y="166" font-family="monospace" font-size="10" fill="{MUTED}">less ▪ ▪ ▪ ▪ ▪ more</text>',f'<text x="878" y="166" text-anchor="end" font-family="monospace" font-size="10" fill="{MUTED}">streak: {data["current_streak"]} day(s) · updated {data["updated_at"][:10]}</text>','</svg>']
    (ASSETS/"contrib-heatmap.svg").write_text("\n".join(out),encoding="utf-8")

if __name__=="__main__":
    ASSETS.mkdir(parents=True,exist_ok=True)
    header(); portrait(); info_card()
    heatmap(fetch_contributions())
    print("Profile artwork refreshed from GitHub data.")

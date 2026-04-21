import streamlit as st
import hashlib, random, platform, time, math
from collections import Counter
import matplotlib.pyplot as plt

st.set_page_config(page_title="Cyber Range Elite", layout="wide")

# ---------------- STATE ----------------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------------- CORE ----------------
def generate_data(mode):
    base = {
        "os": random.choice(["Windows","Linux","Mac"]),
        "timezone": random.choice(["UTC","EST","IST"]),
        "screen": random.choice(["1920x1080","1366x768","1440x900"]),
        "fonts": random.choice(["Arial","Roboto","Courier"]),
        "cpu": random.choice([2,4,8]),
        "mem": random.choice([4,8,16])
    }

    if mode == "Spoof":
        base = {
            "os":"Windows","timezone":"UTC",
            "screen":"1920x1080","fonts":"Standard",
            "cpu":4,"mem":8
        }

    return base

def fingerprint(d):
    return hashlib.sha256("|".join(map(str,d.values())).encode()).hexdigest()

# ---------------- SIMILARITY ----------------
def similarity(a, b):
    keys = a.keys()
    match = sum(1 for k in keys if a[k] == b[k])
    return (match / len(keys)) * 100

# ---------------- ENTROPY ----------------
def entropy(vals):
    c = Counter(vals)
    t = len(vals)
    return -sum((v/t)*math.log2(v/t) for v in c.values())

def weighted_entropy(history):
    weights = {"os":1,"timezone":1.5,"screen":2,"fonts":2,"cpu":1,"mem":1}
    total = 0
    for k,w in weights.items():
        vals = [h["data"][k] for h in history]
        if len(vals) > 1:
            total += entropy(vals) * w
    return total

def normalize(e):
    return min((e/15)*100, 100)

# ---------------- ATTACKER ----------------
def attacker_detect(new, history, mode):
    if mode == "Passive":
        return False

    if mode == "Advanced":
        fps = [h["fp"] for h in history]
        return new in fps

    if mode == "Correlation":
        for h in history:
            if similarity(h["data"], new["data"]) > 70:
                return True
    return False

# ---------------- SIDEBAR ----------------
st.sidebar.title("Control Panel")

defense = st.sidebar.selectbox("Defense", ["None","Spoof"])
attacker = st.sidebar.selectbox("Attacker", ["Passive","Advanced","Correlation"])

if st.sidebar.button("Run Session"):
    d = generate_data(defense)
    fp = fingerprint(d)
    st.session_state.history.append({"fp":fp,"data":d})

if st.sidebar.button("Demo Mode (30 sessions)"):
    for _ in range(30):
        d = generate_data(defense)
        fp = fingerprint(d)
        st.session_state.history.append({"fp":fp,"data":d})

if st.sidebar.button("Reset"):
    st.session_state.history = []

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4 = st.tabs(["Attack","Analytics","Replay","Insights"])

# ---------------- ATTACK ----------------
with tab1:
    st.header("Attack Simulation")

    if st.session_state.history:
        latest = st.session_state.history[-1]

        st.code(latest["fp"][:40]+"...")
        st.json(latest["data"])

        tracked = attacker_detect(latest, st.session_state.history[:-1], attacker)

        if tracked:
            st.error("Tracked")
        else:
            st.success("Not Tracked")

# ---------------- ANALYTICS ----------------
with tab2:
    st.header("Analytics")

    h = st.session_state.history
    total = len(h)

    if total > 0:
        unique = len(set([x["fp"] for x in h]))
        track_rate = ((total-unique)/total*100)

        c1,c2,c3 = st.columns(3)
        c1.metric("Sessions", total)
        c2.metric("Tracking %", f"{track_rate:.1f}")
        c3.metric("Unique", unique)

    if total > 1:
        e = weighted_entropy(h)
        risk = normalize(e)

        st.metric("Risk Score", f"{risk:.1f}/100")

        if risk < 30:
            st.success("Low Risk")
        elif risk < 70:
            st.warning("Medium Risk")
        else:
            st.error("High Risk")

    # Trend
    if total > 2:
        vals = [normalize(weighted_entropy(h[:i])) for i in range(2,total+1)]
        fig, ax = plt.subplots()
        ax.plot(vals)
        ax.set_title("Risk Trend")
        st.pyplot(fig)

# ---------------- REPLAY ----------------
with tab3:
    st.header("Session Replay")

    if len(st.session_state.history) > 1:
        i1 = st.slider("Session A", 0, len(h)-1, 0)
        i2 = st.slider("Session B", 0, len(h)-1, 1)

        c1,c2 = st.columns(2)

        with c1:
            st.subheader("Session A")
            st.json(h[i1]["data"])

        with c2:
            st.subheader("Session B")
            st.json(h[i2]["data"])

        sim = similarity(h[i1]["data"], h[i2]["data"])
        st.write(f"Similarity: {sim:.1f}%")

# ---------------- INSIGHTS ----------------
with tab4:
    st.header("Security Insights")

    if len(h) > 1:
        keys = h[0]["data"].keys()
        contrib = {}

        for k in keys:
            vals = [x["data"][k] for x in h]
            contrib[k] = entropy(vals)

        sorted_contrib = dict(sorted(contrib.items(), key=lambda x: x[1], reverse=True))

        st.subheader("Attribute Contribution")
        st.json(sorted_contrib)

        st.subheader("Recommendation")

        top = list(sorted_contrib.keys())[0]

        st.write(f"High tracking caused by: **{top}**")

        st.write("Suggested defenses:")
        st.write("- Standardize screen resolution")
        st.write("- Reduce font variability")
        st.write("- Use spoofing mode")
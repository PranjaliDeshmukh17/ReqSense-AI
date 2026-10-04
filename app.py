import streamlit as st
from rag.engine import extract_text, analyze_requirements, ollama_answer, build_report

st.set_page_config(page_title="ReqSense AI", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

# ---------- DARK UI: intentionally no white backgrounds ----------
st.markdown("""
<style>
:root{--bg:#070b12;--panel:#0f1724;--panel2:#111c2c;--border:#26364d;--text:#edf3ff;--muted:#93a4bb;--accent:#7c8cff;--good:#45d6a0}
.stApp,[data-testid="stAppViewContainer"],.main,section.main{background:#070b12!important;color:var(--text)!important}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"]{background:#070b12!important;height:0!important}
.block-container{max-width:1250px;padding-top:1.4rem;padding-bottom:4rem}
h1,h2,h3,h4,h5,h6,p,span,label,li{color:var(--text)}
section[data-testid="stSidebar"]{background:#090f19!important;border-right:1px solid var(--border)!important}
section[data-testid="stSidebar"] *{color:var(--text)!important}
section[data-testid="stSidebar"] .stRadio label{background:#111a29!important;border:1px solid #25354c!important;border-radius:10px!important;padding:7px 10px!important;margin:4px 0!important}
.hero{padding:24px 28px;border:1px solid var(--border);border-radius:20px;background:#0d1522;margin-bottom:20px}
.hero .eyebrow{color:var(--good);font-weight:800;letter-spacing:.08em;font-size:.78rem}.hero h1{margin:.35rem 0;font-size:2.15rem}.hero p{color:var(--muted)!important;margin:0}
.card{padding:18px;border:1px solid var(--border);border-radius:16px;background:#0f1724;min-height:105px}.num{font-size:1.9rem;font-weight:800}.label{color:var(--muted)!important}
.finding{padding:16px 18px;border:1px solid var(--border);border-radius:14px;background:#0f1724;margin:10px 0}.badge{display:inline-block;padding:4px 9px;border-radius:999px;background:#1b2a40;color:#b9c8dd!important;font-size:.72rem;font-weight:800}
/* Text areas: dark background + light text, including pasted text */
div[data-baseweb="textarea"],div[data-baseweb="input"]{background:#101a29!important;border:1px solid #31425b!important;border-radius:12px!important}
div[data-baseweb="textarea"] textarea,div[data-baseweb="input"] input{background:#101a29!important;color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;caret-color:#ffffff!important}
div[data-baseweb="textarea"] textarea::placeholder,div[data-baseweb="input"] input::placeholder{color:#8ea0b8!important;-webkit-text-fill-color:#8ea0b8!important;opacity:1!important}
/* File uploader: dark everywhere */
section[data-testid="stFileUploaderDropzone"]{background:#101a29!important;border:1px dashed #3b4d68!important;border-radius:12px!important}
section[data-testid="stFileUploaderDropzone"] *{color:#dbe7f7!important}
section[data-testid="stFileUploaderDropzone"] button{background:#18263a!important;color:#ffffff!important;border:1px solid #3b4d68!important}
/* Buttons */
div.stButton>button,button[kind="secondary"],button[kind="primary"]{background:#17243a!important;color:#ffffff!important;border:1px solid #3a4b66!important;border-radius:10px!important;min-height:42px}
div.stButton>button:hover{background:#21324c!important;border-color:#7c8cff!important}
/* Chat */
[data-testid="stChatMessage"]{background:#101a29!important;border:1px solid #293b55!important;border-radius:14px!important}
[data-testid="stChatInput"],[data-testid="stChatInputContainer"],[data-testid="stBottomBlockContainer"]{background:#070b12!important}
[data-testid="stChatInput"] textarea{background:#101a29!important;color:#ffffff!important;-webkit-text-fill-color:#ffffff!important}
[data-testid="stChatInput"] textarea::placeholder{color:#8ea0b8!important;-webkit-text-fill-color:#8ea0b8!important}
/* Alerts/containers */
div[data-testid="stAlert"]{background:#111c2c!important;color:#edf3ff!important;border:1px solid #2d405b!important}
.stMarkdown{color:var(--text)}
footer{visibility:hidden!important}
.small-note{color:var(--muted)!important;font-size:.88rem}
.ai-box{padding:22px;border:1px solid #2a3b55;border-radius:20px;background:#0d1522}
</style>
""", unsafe_allow_html=True)

# ---------- State ----------
for key, default in {
    "v1_text":"", "v2_text":"", "v1_name":"", "v2_name":"",
    "analysis":None, "messages":[], "report":""
}.items():
    if key not in st.session_state:
        st.session_state[key]=default

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## ✦ ReqSense AI")
    st.caption("AI-Powered Software Requirement Intelligence Agent")
    st.divider()
    page=st.radio("Workspace", ["AI Assistant","Documents","Requirement Analysis","Conflicts & Impact","Reports"], label_visibility="collapsed")
    st.divider()
    st.markdown("**Workflow**")
    st.caption("Upload V1 + V2 → Analyze → Ask AI → Report")
    st.caption("LLM • RAG • Requirement Analysis")

st.markdown('<div class="hero"><div class="eyebrow">✦ REQUIREMENT INTELLIGENCE</div><h1>ReqSense AI</h1><p>Compare software requirements, identify changes and impacts, and ask an AI assistant for a grounded explanation.</p></div>', unsafe_allow_html=True)

# ---------- AI Assistant ----------
if page=="AI Assistant":
    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
    st.markdown("## ✦ AI Requirement Assistant")
    if st.session_state.analysis:
        st.success("AI is connected to the uploaded/analysed requirements. Ask about changes, conflicts, or impact.")
    else:
        st.info("First upload Previous SRS and New SRS in Documents, then run the analysis.")
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    q=st.chat_input("Ask about your requirements...")
    if q:
        st.session_state.messages.append({"role":"user","content":q})
        if st.session_state.analysis:
            ans=ollama_answer(q, st.session_state.analysis)
        else:
            ans="Please upload and analyze the Previous SRS and New SRS first. Then I can answer using those requirements."
        st.session_state.messages.append({"role":"assistant","content":ans})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Documents ----------
elif page=="Documents":
    st.markdown("## 📄 Requirement Documents")
    st.caption("Upload the two versions of the same software requirement document. The comparison page will automatically use them.")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("### Previous SRS (V1)")
        f1=st.file_uploader("Upload Previous SRS", type=["txt","pdf","docx"], key="doc_v1")
        if f1:
            text=extract_text(f1)
            if text.strip():
                st.session_state.v1_text=text; st.session_state.v1_name=f1.name
                st.session_state.analysis = None
                st.session_state.report = ""
                st.success(f"Loaded: {f1.name}")
            else: st.error("Could not extract text from this file.")
    with c2:
        st.markdown("### Updated SRS (V2)")
        f2=st.file_uploader("Upload Updated SRS", type=["txt","pdf","docx"], key="doc_v2")
        if f2:
            text=extract_text(f2)
            if text.strip():
                st.session_state.v2_text=text; st.session_state.v2_name=f2.name
                st.session_state.analysis = None
                st.session_state.report = ""
                st.success(f"Loaded: {f2.name}")
            else: st.error("Could not extract text from this file.")
    if st.session_state.v1_text and st.session_state.v2_text:
        st.markdown("### ✓ Both documents loaded")
        st.write(f"**V1:** {st.session_state.v1_name}  |  **V2:** {st.session_state.v2_name}")
        # Automatically connect the uploaded documents to comparison + AI context.
        if st.session_state.analysis is None:
            st.session_state.analysis = analyze_requirements(st.session_state.v1_text, st.session_state.v2_text)
            st.session_state.messages = []
            st.session_state.report = ""
            st.success("Both documents are connected. Requirement Analysis and AI Assistant are ready.")
        st.caption("The uploaded V1 and V2 are now automatically available in Requirement Analysis and AI Assistant. No copy-pasting is required.")

# ---------- Requirement Analysis ----------
elif page=="Requirement Analysis":
    st.markdown("## 🔍 Requirement Analysis")
    if not st.session_state.v1_text or not st.session_state.v2_text:
        st.warning("Upload both SRS documents first from the Documents section.")
    else:
        st.caption("These boxes are automatically filled from the uploaded documents. You do not need to paste the text again.")
        c1,c2=st.columns(2)
        with c1:
            st.markdown(f"### Previous SRS — {st.session_state.v1_name or 'V1'}")
            st.text_area("Previous requirement", st.session_state.v1_text, height=330, disabled=True, label_visibility="collapsed")
        with c2:
            st.markdown(f"### Updated SRS — {st.session_state.v2_name or 'V2'}")
            st.text_area("Updated requirement", st.session_state.v2_text, height=330, disabled=True, label_visibility="collapsed")
        if st.button("🚀 Analyze Requirements", use_container_width=True):
            st.session_state.analysis=analyze_requirements(st.session_state.v1_text, st.session_state.v2_text)
            st.session_state.messages=[]
            st.session_state.report=""
            st.success("Analysis complete.")
        if st.session_state.analysis:
            a=st.session_state.analysis
            st.markdown("### Results")
            cols=st.columns(3)
            for c,num,label in zip(cols,[a["summary"]["changes"],a["summary"]["conflicts"],a["summary"]["impacts"]],["Changes detected","Potential conflicts","Potential impacts"]):
                c.markdown(f'<div class="card"><div class="num">{num}</div><div class="label">{label}</div></div>',unsafe_allow_html=True)
            for f in a["findings"]:
                st.markdown(f'<div class="finding"><span class="badge">{f["type"]}</span><h4>{f["title"]}</h4><p><b>V1:</b> {f["v1"]}</p><p><b>V2:</b> {f["v2"]}</p><p><b>Potential impact:</b> {f["impact"]}</p></div>',unsafe_allow_html=True)

# ---------- Conflicts & Impact ----------
elif page=="Conflicts & Impact":
    st.markdown("## ⚠ Conflicts & Impact")
    if not st.session_state.analysis:
        st.info("Upload and analyze the two SRS documents first.")
    else:
        a=st.session_state.analysis
        st.markdown("### Potential conflicts")
        if a["conflicts"]:
            for c in a["conflicts"]: st.warning(c)
        else: st.success("No obvious conflicts were detected by the current rule-based checks.")
        st.markdown("### Potentially affected areas")
        for f in a["findings"]:
            st.markdown(f"**{f['module']}** — {f['impact']}")

# ---------- Reports ----------
else:
    st.markdown("## 📊 Reports")
    if not st.session_state.analysis:
        st.info("Upload and analyze the two SRS documents first.")
    else:
        a=st.session_state.analysis
        st.markdown("This report combines the comparison findings, potential conflicts, impacts, and an optional LLM explanation.")
        if st.button("✦ Generate AI Report", use_container_width=True):
            # Generate the report immediately from the verified comparison results.
            # This keeps report generation usable even if the local LLM is slow/offline.
            st.session_state.report=build_report(a)
            st.session_state.report_ai_pending=True
            st.success("Report generated successfully from the V1/V2 analysis.")

        if "report_ai_pending" not in st.session_state:
            st.session_state.report_ai_pending=False

        if st.session_state.report:
            st.markdown(st.session_state.report)
            if st.session_state.report_ai_pending:
                st.markdown("### ✦ Optional LLM Explanation")
                st.caption("Use Ollama to add a natural-language explanation to the report.")
                if st.button("Add LLM Explanation with Ollama", use_container_width=True):
                    with st.spinner("Generating the AI explanation with Ollama..."):
                        llm=ollama_answer("Summarize the important requirement changes, conflicts, and potential impacts for this project.", a)
                    st.session_state.report=build_report(a,llm)
                    st.session_state.report_ai_pending=False
                    st.success("LLM explanation added to the report.")
                    st.rerun()
            st.download_button("⬇ Download Report", st.session_state.report, "ReqSense_Requirement_Report.md", "text/markdown", use_container_width=True)

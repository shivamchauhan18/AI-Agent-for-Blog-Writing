from __future__ import annotations

import json
import re
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Iterator, Tuple

import pandas as pd
import streamlit as st

from bwa_backend import app


# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------

st.set_page_config(
    page_title="AI Blog Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ------------------------------------------------
# MODERN CSS (REAL UI CHANGE)
# ------------------------------------------------

st.markdown("""

<style>

#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}

.block-container{

max-width:1400px;
padding-top:1rem;

}


.hero{

padding:30px;

border-radius:18px;

background:
linear-gradient(
135deg,
#4f46e5,
#06b6d4
);

color:white;

box-shadow:0 20px 40px rgba(0,0,0,0.15);

}


.hero-title{

font-size:42px;

font-weight:800;

margin-bottom:0px;

}


.hero-sub{

opacity:0.9;

margin-top:0px;

}


.card{

background:white;

padding:25px;

border-radius:16px;

box-shadow:0 10px 30px rgba(0,0,0,0.08);

margin-bottom:20px;

}


.metric{

background:#0f172a;

color:white;

padding:20px;

border-radius:14px;

text-align:center;

}


.evidence{

background:white;

padding:18px;

border-radius:14px;

box-shadow:0 4px 14px rgba(0,0,0,0.08);

margin-bottom:15px;

}


.blog{

background:white;

padding:50px;

border-radius:18px;

box-shadow:0 20px 40px rgba(0,0,0,0.08);

font-size:18px;

line-height:1.7;

}


</style>

""", unsafe_allow_html=True)


# ------------------------------------------------
# HELPERS
# ------------------------------------------------

def safe_slug(title):

    s=title.lower().strip()

    s=re.sub(r"[^a-z0-9 _-]+","",s)

    s=re.sub(r"\s+","_",s)

    return s or "blog"


def try_stream(graph_app,inputs)->Iterator[Tuple[str,Any]]:

    try:

        for step in graph_app.stream(inputs,stream_mode="updates"):

            yield ("updates",step)

        out=graph_app.invoke(inputs)

        yield ("final",out)

        return

    except:

        pass

    out=graph_app.invoke(inputs)

    yield ("final",out)


def extract_latest_state(current_state,step_payload):

    if isinstance(step_payload,dict):

        if len(step_payload)==1:

            inner=next(iter(step_payload.values()))

            if isinstance(inner,dict):

                current_state.update(inner)

        else:

            current_state.update(step_payload)

    return current_state


def list_past_blogs():

    files=list(Path(".").glob("*.md"))

    files.sort(

        key=lambda p:p.stat().st_mtime,

        reverse=True

    )

    return files


def read_md_file(p):

    return p.read_text(encoding="utf-8")


def extract_title(md,fallback):

    for line in md.splitlines():

        if line.startswith("# "):

            return line[2:]

    return fallback


# ------------------------------------------------
# HERO HEADER
# ------------------------------------------------

st.markdown("""

<div class="hero">

<div class="hero-title">

Planning AI Blog Agent

</div>

<div class="hero-sub">

LangGraph • Research • Parallel Writing • Image Generation

</div>

</div>

""",unsafe_allow_html=True)


st.write("")


# ------------------------------------------------
# SIDEBAR
# ------------------------------------------------

with st.sidebar:

    st.title("Agent Control")

    topic=st.text_area(

        "Blog Topic",

        height=140,

        placeholder="Example:\nRAG Architecture"

    )

    as_of=st.date_input(

        "Knowledge Date",

        value=date.today()

    )

    run_btn=st.button(

        "Generate Blog",

        use_container_width=True

    )

    st.divider()

    st.subheader("Past Blogs")

    past=list_past_blogs()

    if past:

        labels=[]

        mapping={}

        for p in past:

            md=read_md_file(p)

            title=extract_title(md,p.stem)

            labels.append(title)

            mapping[title]=p

        selected=st.selectbox(

            "History",

            labels

        )

        if st.button("Load"):

            md=read_md_file(

                mapping[selected]

            )

            st.session_state["last_out"]={

                "final":md,

                "plan":None,

                "evidence":[],

                "image_specs":[]
            }


# ------------------------------------------------
# MAIN TABS
# ------------------------------------------------

tab1,tab2,tab3,tab4,tab5=st.tabs([

"Plan",

"Evidence",

"Blog",

"Images",

"Logs"

])


if "last_out" not in st.session_state:

    st.session_state["last_out"]=None


logs=[]


# ------------------------------------------------
# EXECUTION
# ------------------------------------------------

if run_btn:

    inputs={

        "topic":topic,

        "mode":"",

        "needs_research":False,

        "queries":[],

        "evidence":[],

        "plan":None,

        "as_of":as_of.isoformat(),

        "recency_days":7,

        "sections":[],

        "merged_md":"",

        "md_with_placeholders":"",

        "image_specs":[],

        "final":""
    }

    progress=st.progress(0)

    status=st.empty()

    status.info("Running agent")

    step=0

    current_state={}

    for kind,payload in try_stream(app,inputs):

        step+=1

        progress.progress(

            min(step*8,100)

        )

        logs.append(str(payload)[:300])

        if kind in ("updates","values"):

            current_state=extract_latest_state(

                current_state,

                payload

            )

        if kind=="final":

            st.session_state["last_out"]=payload

            status.success("Generation completed")


out=st.session_state.get("last_out")


# ------------------------------------------------
# PLAN TAB
# ------------------------------------------------

if out:

    with tab1:

        plan=out.get("plan")

        if plan:

            if hasattr(plan,"model_dump"):

                plan=plan.model_dump()

            c1,c2,c3=st.columns(3)

            c1.markdown(

f'<div class="metric">Audience<br><b>{plan.get("audience")}</b></div>',

unsafe_allow_html=True

)

            c2.markdown(

f'<div class="metric">Tone<br><b>{plan.get("tone")}</b></div>',

unsafe_allow_html=True

)

            c3.markdown(

f'<div class="metric">Type<br><b>{plan.get("blog_kind")}</b></div>',

unsafe_allow_html=True

)

            tasks=plan.get("tasks",[])

            df=pd.DataFrame(tasks)

            st.dataframe(df,use_container_width=True)


# ------------------------------------------------
# EVIDENCE
# ------------------------------------------------

    with tab2:

        evidence=out.get("evidence")

        if evidence:

            for e in evidence:

                if hasattr(e,"model_dump"):

                    e=e.model_dump()

                st.markdown(

f'''

<div class="evidence">

<b>{e.get("title")}</b>

<br>

{e.get("source")}

</div>

''',

unsafe_allow_html=True

)

                st.link_button(

                    "Open Source",

                    e.get("url")

                )


# ------------------------------------------------
# BLOG
# ------------------------------------------------

    with tab3:

        md=out.get("final")

        if md:

            st.markdown(

f'<div class="blog">{md}</div>',

unsafe_allow_html=True

)

            st.download_button(

                "Download Blog",

                md,

                file_name="blog.md"

            )


# ------------------------------------------------
# IMAGES
# ------------------------------------------------

    with tab4:

        img_dir=Path("images")

        if img_dir.exists():

            files=list(img_dir.iterdir())

            cols=st.columns(4)

            i=0

            for f in files:

                if f.is_file():

                    cols[i%4].image(

                        str(f),

                        use_container_width=True

                    )

                    i+=1


# ------------------------------------------------
# LOGS
# ------------------------------------------------

    with tab5:

        st.code(

            "\n".join(logs)

        )


else:

    st.info(

        "Enter a topic and click Generate Blog"

    )

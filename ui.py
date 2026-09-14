"""White-and-green theme inspired by the supplied reference website."""
from urllib.parse import quote
import streamlit as st


EYE = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="white" d="M3 24s7-13 21-13 21 13 21 13-7 13-21 13S3 24 3 24z"/><circle cx="24" cy="24" r="8" fill="#059b76"/><circle cx="21" cy="21" r="3" fill="white"/></svg>'


def brand(center=False):
    layout = 'brand-center' if center else 'brand-row'
    st.html(f'''<div class="{layout}">
        <div class="brand-icon"><img alt="PharmaLens" width="34" height="34" src="data:image/svg+xml,{quote(EYE)}"></div>
        <div><h2>PharmaLens</h2>
        <p>Precision insights from official drug labels</p></div>
    </div>''')



def login_background():
    """Decorative motion only; no scripts, network calls or input interception."""
    capsules = ''.join(f'<i class="login-capsule capsule-{i}"></i>' for i in range(8))
    st.html(f'<div class="login-atmosphere" aria-hidden="true"><div class="login-network"></div>{capsules}</div>')


def apply_theme():
    dark = False
    bg, card, field, text, muted, heading, border = (
        ('#101b15', '#192920', '#22372a', '#edf5ef', '#b7c9bc', '#9ce4af', '#365340')
        if dark else
        ('#f8f9fa', '#ffffff', '#f4f8f5', '#28332c', '#56635b', '#166534', '#dce7df')
    )
    network = '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900"><g stroke="#10b981" stroke-opacity=".18" fill="none"><path d="M20 130L140 40L230 180L70 320L20 130M140 40L360 100L230 180L390 310M70 320L180 540L30 690L280 810L180 540M870 60L1100 150L940 310L1180 420L1000 590L830 780L1150 860L1000 590"/></g><g fill="#10b981" fill-opacity=".25"><circle cx="140" cy="40" r="5"/><circle cx="230" cy="180" r="5"/><circle cx="70" cy="320" r="5"/><circle cx="180" cy="540" r="5"/><circle cx="1100" cy="150" r="5"/><circle cx="940" cy="310" r="5"/><circle cx="1000" cy="590" r="5"/><rect x="75" y="420" width="55" height="20" rx="10"/><rect x="1060" y="500" width="60" height="22" rx="11"/></g></svg>'
    st.html(f'''<style>
    :root {{ --bg:{bg}; --card:{card}; --field:{field}; --text:{text};
             --muted:{muted}; --heading:{heading}; --border:{border}; }}
    .stApp {{background:var(--bg); color:var(--text); color-scheme:{'dark' if dark else 'light'};}}
    .stApp,.stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp button,.stApp input {{font-family:Arial,sans-serif;}}
    .block-container {{max-width:1200px; padding:1.2rem 2rem 3rem;}}
    [data-testid="stHeader"] {{background:var(--bg);}}
    [data-testid="stToolbar"] {{visibility:hidden;}}
    .stApp h1,.stApp h2,.stApp h3 {{color:var(--heading); font-weight:700;}}
    .stApp h1 {{font-size:2.3rem;}} .stApp h2 {{font-size:1.7rem;}}
    .stApp h3 {{font-size:1.25rem;}}
    .stApp p,.stApp label,.stApp li,.stApp [data-testid="stMarkdownContainer"] {{color:var(--text); line-height:1.7;}}
    .stApp [data-testid="stCaptionContainer"] p {{color:var(--muted)!important; opacity:1;}}
    .stApp input,.stApp textarea,.stApp [data-baseweb="input"],
    .stApp [data-baseweb="base-input"],.stApp [data-baseweb="textarea"],
    .stApp [data-baseweb="select"] > div {{background:var(--field)!important; color:var(--text)!important; border-color:var(--border)!important; border-radius:9px;}}
    .stApp input::placeholder,.stApp textarea::placeholder {{color:var(--muted)!important;}}
    .stApp button {{background:var(--card); color:var(--heading); border:1px solid #16a34a; border-radius:9px;}}
    .stApp button p {{color:inherit;}}
    .stApp button:hover {{background:var(--field); border-color:#15803d;}}
    .stApp button[kind="primary"],.stApp [data-testid="stFormSubmitButton"] button {{background:#16a34a; color:white; border:1px solid #16a34a; box-shadow:none;}}
    .stApp button[kind="primary"] p,.stApp [data-testid="stFormSubmitButton"] button p {{color:white;}}
    .stApp button[kind="primary"]:hover,.stApp [data-testid="stFormSubmitButton"] button:hover {{background:#15803d;}}
    .stApp a {{color:{'#86efac' if dark else '#15803d'};}}
    .stApp [data-baseweb="tab-list"] {{gap:1.5rem; border-bottom:1px solid var(--border);}}
    .stApp button[role="tab"] {{border:0; border-radius:0; background:transparent; color:var(--muted);}}
    .stApp button[role="tab"][aria-selected="true"] {{color:var(--heading);}}
    .stApp [data-baseweb="tab-highlight"] {{background:#16a34a;}}
    .stApp [data-testid="stChatMessage"],.st-key-welcome_card,.st-key-auth_card {{background:var(--card); border:1px solid var(--border); border-radius:20px; padding:28px; box-shadow:0 10px 30px #00000008;}}
    .stApp [data-testid="stChatMessageAvatarAssistant"] {{background:#16a34a; color:white;}}
    .stApp [data-testid="stChatInput"],.stApp details,.stApp [data-testid="stExpander"] {{background:var(--card); color:var(--text); border-color:var(--border); border-radius:10px;}}
    .stApp [data-testid="stExpander"] summary {{background:var(--field); color:var(--text); border-radius:9px;}}
    .stApp [data-testid="stAlert"],.stApp [data-testid="stCode"] {{background:var(--field); color:var(--text);}}
    .stApp [data-testid="stBottom"],.stApp [data-testid="stBottomBlockContainer"],.stApp [data-testid="stSidebar"] {{background:var(--bg); color:var(--text);}}
    [data-baseweb="popover"],[role="listbox"],[role="option"] {{background:var(--card)!important; color:var(--text)!important;}}
    .stApp [data-baseweb="input"] button {{background:var(--field); color:var(--text); border:0;}}
    .stApp [data-testid="stForm"] {{border:0; padding:0;}}
    .st-key-auth_card {{padding:30px;}}
    .st-key-auth_card [data-testid="stFormSubmitButton"] button {{width:100%; min-height:46px;}}
    .brand-row {{display:flex; align-items:center; gap:14px; padding:12px 0 22px; margin-bottom:16px; border-bottom:1px solid var(--border);}}
    .brand-row h2,.brand-center h2 {{color:{'#86efac' if dark else '#16a34a'}; margin:0; padding:0; font-size:1.8rem;}}
    .brand-row p,.brand-center p {{color:var(--muted); margin:5px 0 0; font-size:.9rem;}}
    .brand-icon {{display:grid; place-items:center; background:#16a34a; color:white; width:48px; height:48px; border-radius:12px; font-size:28px; flex-shrink:0;}}
    .brand-center {{text-align:center; margin-bottom:8px;}}
    .brand-center .brand-icon {{margin:0 auto 14px; width:60px; height:60px;}}
    .auth-welcome {{text-align:center;}} .auth-welcome h2 {{padding:0; font-size:1.3rem;}}
    .auth-welcome p {{color:var(--muted); font-size:.9rem;}}
    .pl-badges {{display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 22px;}}
    .pl-badges span {{background:var(--field); color:var(--heading); border:1px solid var(--border); border-radius:7px; padding:5px 10px; font-size:.8rem;}}
    .st-key-chat_space {{min-height:220px;}}
    hr {{border-color:var(--border)!important;}}
    @media(max-width:650px) {{.block-container {{padding:1rem;}} .st-key-auth_card {{padding:20px;}} .brand-row h2 {{font-size:1.5rem;}}}}
    .stApp:has(.st-key-auth_card) {{background:#ecfdf5 url("data:image/svg+xml,{quote(network)}") center/cover fixed;}}
    .st-key-auth_card {{width:440px; border-radius:26px; box-shadow:0 15px 55px #10b98114;}}
    .brand-center .brand-icon {{border-radius:50%; width:72px; height:72px; outline:2px solid #a7f3d0; outline-offset:7px; margin:6px auto 22px;}}
    .brand-center h2 {{font-size:1.85rem; color:#065f46; font-weight:800;}}
    .st-key-auth_card [data-baseweb="tab-list"] {{gap:0; padding:4px; border:1px solid #d1e8dd; border-radius:12px;}}
    .st-key-auth_card button[role="tab"] {{flex:1; border-radius:9px;}}
    .st-key-auth_card button[role="tab"][aria-selected="true"] {{background:#059669; color:white;}}
    .st-key-auth_card [data-baseweb="tab-highlight"] {{display:none;}}
    .st-key-auth_card [data-testid="stFormSubmitButton"] button {{background:linear-gradient(110deg,#10b981,#059669);}}
    .block-container {{max-width:1600px;}}
    .stApp:has(.st-key-auth_card) .block-container {{padding-top:2rem;}}
    .st-key-chat_space {{min-height:clamp(250px,43vh,520px);}}
    .st-key-welcome_card {{border-radius:20px 20px 20px 4px; padding:24px;}}
    .stApp [data-testid="stChatInput"],.stApp [data-testid="stChatInput"] > div {{background:#ffffff!important; border-color:#dce7df!important;}}
    [data-testid="stHeader"] {{display:none;}}
    .st-key-auth_card [role="tablist"] {{display:flex; gap:0; padding:4px; border:1px solid #d1e8dd; border-radius:12px;}}
    .st-key-auth_card [role="tab"] {{flex:1; border-radius:9px; padding:10px; text-align:center;}}
    .st-key-auth_card [role="tab"][aria-selected="true"] {{background:#059669!important; color:white!important;}}
    .st-key-auth_card [role="tab"][aria-selected="true"] p {{color:white!important;}}
    </style>''')
    st.html("""
    <style>
    /* Reference: white panels with green actions and upload area. */
    .stApp { background: #f8f9fa !important; }
    .stApp [data-testid="stChatMessage"],
    .st-key-welcome_card, .st-key-auth_card {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 22px !important;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
    }
    .stApp h1, .stApp h2, .stApp h3 { color: #166534 !important; }
    .stApp input, .stApp textarea,
    .stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"],
    .stApp [data-baseweb="textarea"], .stApp [data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #1e293b !important;
        border-color: #cbd5e1 !important;
        border-radius: 12px !important;
    }
    .stApp [data-testid="stFileUploaderDropzone"] {
        background: #f0fdf4 !important;
        border: 2px dashed #16a34a !important;
        border-radius: 18px !important;
        padding: 28px !important;
    }
    .stApp button[kind="primary"],
    .stApp [data-testid="stFormSubmitButton"] button {
        background: #16a34a !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        min-height: 48px;
        width: 100%;
        font-weight: 700;
        box-shadow: none !important;
    }
    .stApp button[kind="primary"] p,
    .stApp [data-testid="stFormSubmitButton"] button p { color: #ffffff !important; }
    .stApp button[kind="primary"]:hover,
    .stApp [data-testid="stFormSubmitButton"] button:hover { background: #15803d !important; }
    .stApp [data-testid="stExpander"], .stApp details {
        background: #ffffff !important;
        border-color: #dce7df !important;
    }
    .stApp [data-testid="stExpander"] summary { background: #f0fdf4 !important; }
    </style>
    """)
    st.html("""
    <style>
    .stApp [role="tablist"] { gap:6px; padding:6px; background:#ffffff; border:1px solid #dce7df; border-radius:14px; }
    .stApp [role="tab"] { padding:10px 18px; border-radius:10px; }
    .stApp [role="tab"][aria-selected="true"] { background:#059669!important; color:white!important; }
    .stApp [role="tab"][aria-selected="true"] p { color:white!important; }
    .stApp [data-testid="stMetric"] { background:#ffffff; border:1px solid #dce7df; border-radius:16px; padding:18px; }
    .stApp [data-testid="stMetricValue"] { color:#059669; }
    .stApp [data-testid="stText"] { white-space:pre-wrap; line-height:1.7; font-family:Arial,sans-serif; }
    .stApp [data-testid="stDialog"] [role="dialog"] { background:#ffffff; color:#173c2b; border-radius:20px; }
    .st-key-chat_space { min-height:clamp(280px,45vh,560px); }
    </style>
    """)
    st.html(f"""
    <style>
    .stApp {{background:#edfcf5!important; background-image:none!important;}}
    .stApp [data-testid="stMainBlockContainer"] {{position:relative; z-index:1;}}
    .stApp [data-testid="stBottom"],.stApp [data-testid="stBottomBlockContainer"] {{background:transparent;}}
    .login-atmosphere {{position:fixed; inset:0; z-index:0; pointer-events:none; overflow:hidden; background:radial-gradient(ellipse at center,#f5fffb 0%,#eafbf2 100%);}}
    .login-network {{position:absolute; inset:-4%; background:url("data:image/svg+xml,{quote(network)}") center/cover; opacity:.8; animation:network-drift 24s ease-in-out infinite alternate;}}
    .login-capsule {{position:absolute; display:block; width:58px; height:24px; border-radius:20px; background:linear-gradient(110deg,#6ee7b7,#34bda0); opacity:.32; animation:capsule-float 15s ease-in-out infinite alternate;}}
    .capsule-0 {{left:8%; top:12%; transform:rotate(12deg);}}
    .capsule-1 {{left:16%; top:77%; width:72px; animation-delay:-6s;}}
    .capsule-2 {{left:6%; top:55%; width:42px; animation-delay:-3s;}}
    .capsule-3 {{right:13%; top:10%; animation-delay:-8s;}}
    .capsule-4 {{right:8%; top:31%; width:46px; animation-delay:-2s;}}
    .capsule-5 {{right:11%; top:69%; animation-delay:-10s;}}
    .capsule-6 {{right:21%; top:87%; width:70px; animation-delay:-5s;}}
    .capsule-7 {{left:27%; top:39%; width:36px; animation-delay:-12s;}}
    @keyframes network-drift {{from {{transform:translate(-8px,-8px);}} to {{transform:translate(12px,14px);}}}}
    @keyframes capsule-float {{from {{translate:0 -12px; rotate:-9deg;}} to {{translate:12px 18px; rotate:10deg;}}}}
    .stApp:has(.st-key-auth_card) [data-testid="stMainBlockContainer"] {{position:relative; z-index:1; padding-top:28px;}}
    .st-key-auth_card {{position:relative; z-index:1; background:rgba(255,255,255,.96)!important; border:1px solid #d9eee4!important; border-radius:25px!important; box-shadow:0 15px 65px #05966912!important; padding:30px 34px 24px!important;}}
    .st-key-auth_card,.st-key-auth_card p,.st-key-auth_card label,.st-key-auth_card input,.st-key-auth_card button {{font-family:'Segoe UI',Arial,sans-serif;}}
    .st-key-auth_card .brand-center h2 {{font-size:28px; font-weight:800; letter-spacing:-1px; color:#075e49!important;}}
    .st-key-auth_card .brand-center p {{font-size:13px; color:#6b7280!important; line-height:1.5;}}
    .st-key-auth_card .brand-icon {{background:linear-gradient(135deg,#10b981,#059669); width:76px; height:76px; outline:2px solid #c5eee1; outline-offset:7px; border-radius:50%; box-shadow:0 8px 28px #10b98120;}}
    .st-key-auth_card .auth-welcome h2 {{font-size:21px; color:#145c47!important; margin:8px 0 4px;}}
    .st-key-auth_card .auth-welcome p {{font-size:13px; color:#6b7280!important;}}
    .st-key-auth_card [role="tablist"] {{margin:8px 0 4px; padding:4px; gap:0; background:white; border:1px solid #dfede7;}}
    .st-key-auth_card [role="tab"] {{text-align:center; justify-content:center; font-size:14px; padding:10px;}}
    .st-key-auth_card [role="tab"][aria-selected="true"] {{background:linear-gradient(110deg,#10b981,#059669)!important; box-shadow:0 4px 12px #10b98125;}}
    .st-key-auth_card label p {{font-size:13px; color:#176b53!important;}}
    .st-key-auth_card input {{min-height:46px; font-size:14px; padding-left:14px;}}
    .st-key-auth_card [data-baseweb="input"] {{border:1px solid #d7eae2!important; box-shadow:none;}}
    .st-key-auth_card [data-testid="stFormSubmitButton"] button {{background:linear-gradient(110deg,#10b981,#059669)!important; border-radius:12px!important; min-height:50px; box-shadow:0 8px 20px #10b98120!important;}}
    .st-key-auth_card [data-testid="stCaptionContainer"] p {{font-size:11px; line-height:1.5; color:#7a8982!important;}}
    @media(prefers-reduced-motion:reduce) {{.login-network,.login-capsule {{animation:none;}}}}
    @media(max-width:600px) {{.st-key-auth_card {{padding:24px!important;}} .login-capsule {{opacity:.18;}}}}
    </style>
    """)
    st.html('''<style>
    .stApp .st-key-welcome_card,
    .stApp [data-testid="stMetric"],
    .stApp [data-testid="stChatMessage"],
    .stApp [class*="st-key-medicine_card_"] {
        position:relative;
        z-index:1;
        background:linear-gradient(120deg,#ffffff 0%,#f0fdf6 100%)!important;
        border:1px solid #b7e4ce!important;
        border-left:5px solid #10b981!important;
        border-radius:20px!important;
        padding:26px 30px!important;
        box-shadow:0 10px 30px rgba(6,95,70,.08)!important;
        margin:12px 0 20px;
    }
    .stApp .st-key-welcome_card strong {color:#065f46;font-size:1.15rem;}
    .stApp .st-key-welcome_card p {color:#254b3b;line-height:1.75;}
    .stApp [class*="st-key-medicine_card_"] strong {color:#065f46;}
    .stApp [data-testid="stChatMessage"] strong {color:#065f46;}
    .stApp [data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p {color:#466457!important;}
    .stApp [data-testid="stChatMessage"] [data-testid="stExpander"] {border:1px solid #cce9dc!important;}

    /* Disclaimer inside Q&A answers: dark, readable, clearly separated. */
    .stApp .st-key-disclaimer_card {
        background: #f0fdf6 !important;
        border: 1px solid #b7e4ce !important;
        border-left: 5px solid #10b981 !important;
        border-radius: 14px !important;
        padding: 16px 20px !important;
        margin-top: 14px !important;
    }
    .stApp .st-key-disclaimer_card strong { color: #065f46 !important; font-size: 0.95rem; }
    .stApp .disclaimer-text,
    .stApp .disclaimer-text p,
    .stApp .disclaimer-text span {
        color: #173c2b !important;
        font-size: 0.92rem !important;
        line-height: 1.65 !important;
        font-weight: 500 !important;
        opacity: 1 !important;
    }
    .stApp [data-testid="stChatMessage"] .st-key-disclaimer_card [data-testid="stCaptionContainer"] p,
    .stApp [data-testid="stChatMessage"] .st-key-disclaimer_card p { color: #173c2b !important; }

    @media(max-width:600px) {.stApp .st-key-welcome_card,.stApp [class*="st-key-medicine_card_"] {padding:20px!important;}}
    </style>''')
    login_background()
    return dark
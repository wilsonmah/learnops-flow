"""Static presentation only; no user content or business logic is interpolated."""

APP_CSS = """
<style>
  :root { --lo-ink: #1d2633; --lo-muted: #58677b; --lo-line: #dfe4eb;
          --lo-blue: #1768d6; --lo-surface: #ffffff; }
  html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: var(--lo-ink);
  }
  [data-testid="stAppViewContainer"] { background: #f5f6f8; }
  [data-testid="stHeader"] { background: rgba(245,246,248,.92); }
  [data-testid="stMainBlockContainer"] {
    max-width: 1500px; padding: 2.4rem 3rem 5rem;
  }
  [data-testid="stSidebar"] {
    background: #fff; border-right: 1px solid var(--lo-line);
  }
  [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding: 1.4rem .8rem 2rem;
  }
  [data-testid="stSidebar"] h1 {
    font-size: 1.34rem; font-weight: 720; letter-spacing: -.045em;
  }
  [data-testid="stSidebar"] [role="radiogroup"] { gap: .2rem; }
  [data-testid="stSidebar"] [role="radiogroup"] label {
    border-radius: 10px; padding: .56rem .7rem; margin: 0;
  }
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: #eaf2fe; color: #124f9e; font-weight: 650;
  }
  [data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #f1f4f8; }
  h1 { font-weight: 740 !important; letter-spacing: -.045em; }
  h2, h3, h4 { letter-spacing: -.028em; }
  [data-testid="stMainBlockContainer"] h1 { font-size: clamp(2rem, 3vw, 2.8rem); }
  [data-testid="stMainBlockContainer"] h3 { font-size: 1.2rem; font-weight: 680; }
  [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
  [data-testid="stCaptionContainer"] span { color: #526174 !important; }
  [data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--lo-surface); border: 1px solid var(--lo-line);
    border-radius: 18px; box-shadow: 0 4px 18px rgba(25,42,70,.035);
  }
  [data-testid="stMetric"] {
    background: #fff; border: 1px solid var(--lo-line); border-radius: 18px;
    padding: 1.1rem 1.2rem; box-shadow: 0 4px 18px rgba(25,42,70,.035);
    min-height: 106px;
  }
  [data-testid="stMetricLabel"] { color: #46566c; font-weight: 600; }
  [data-testid="stMetricValue"] { letter-spacing: -.045em; font-weight: 720; }
  [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button,
  [data-testid="stDownloadButton"] button {
    border-radius: 10px; font-weight: 600; border: 1px solid #cdd6e2;
    min-height: 2.55rem;
  }
  [data-testid="stButton"] button:hover, [data-testid="stFormSubmitButton"] button:hover,
  [data-testid="stDownloadButton"] button:hover { border-color: var(--lo-blue); color: #124f9e; }
  button:focus-visible, input:focus-visible, [role="combobox"]:focus-visible,
  [role="radio"]:focus-visible { outline: 3px solid #1768d6 !important; outline-offset: 2px; }
  [data-testid="stExpander"] { border: 1px solid var(--lo-line); border-radius: 14px; background: #fff; }
  [data-testid="stDataFrame"] { border: 1px solid var(--lo-line); border-radius: 14px; overflow: hidden; }
  [data-testid="stAlert"] { border-radius: 12px; }
  hr { border-color: var(--lo-line); }
  @media (max-width: 768px) {
    [data-testid="stMainBlockContainer"] { padding: 1.2rem 1rem 4rem; }
    [data-testid="stMetric"] { min-height: auto; }
  }
</style>
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pathlib import Path

# Page config
st.set_page_config(page_title="QM9 Dashboard", layout="wide")
st.title("QM9 Quantum Chemistry Dashboard")

# Load data (use your raw data path)
@st.cache_data
def load_data():
    # Try multiple possible paths
    possible_paths = [
        'deliverables/qm9_clean_properties.csv'
    ]
    
    for path in possible_paths:
        try:
            return pd.read_csv(path)
        except FileNotFoundError:
            continue
    
    st.error("No data file found. Please check paths!")
    st.stop()

df = load_data()
st.success(f"Loaded {len(df):,} molecules")
st.write("Columns:", df.columns.tolist())

# Fix negative values for size (Plotly requirement)
df['mu_size'] = np.clip(np.abs(df['mu']) * 5 + 3, 3, 20)  # 3-20 range

# Sidebar filters
st.sidebar.header("Filters")
gap_range = st.sidebar.slider("HOMO-LUMO Gap", 
                             float(df['gap'].min()), 
                             float(df['gap'].max()), 
                             (float(df['gap'].min()), float(df['gap'].max())))
mu_max = st.sidebar.slider("Max Dipole (μ)", 
                          float(df['mu'].min()), 
                          float(df['mu'].max()), 
                          float(df['mu'].quantile(0.9)))

filtered_df = df[
    (df['gap'] >= gap_range[0]) & 
    (df['gap'] <= gap_range[1]) &
    (df['mu'] <= mu_max)
].reset_index(drop=True)

# Main dashboard
col1, col2 = st.columns(2)

with col1:
    st.subheader("Property Distributions")
    
    props = ['mu', 'alpha', 'gap']
    for prop in props:
        fig = px.histogram(filtered_df, x=prop, nbins=30, 
                          title=prop.upper(), height=250)
        st.plotly_chart(fig, width='stretch')  # FIXED: use_container_width → width

with col2:
    st.subheader("🔬 HOMO vs LUMO (Drug Stability)")
    
    # FIXED: Use mu_size (positive values only)
    fig = px.scatter(filtered_df.sample(5000),  # Sample for performance
                    x='homo', y='lumo', 
                    color='gap', size='mu_size',  # Fixed!
                    hover_data=['mu', 'alpha', 'zpve'],
                    title="HOMO-LUMO Gap Analysis",
                    labels={'homo':'HOMO Energy', 'lumo':'LUMO Energy'})
    st.plotly_chart(fig, width='stretch')  # FIXED

# Correlation matrix
st.subheader("🔗 Property Correlations")
pharma_props = ['mu', 'alpha', 'homo', 'lumo', 'gap', 'zpve', 'u0']
if all(col in df.columns for col in pharma_props):
    corr = filtered_df[pharma_props].corr()
    fig = px.imshow(corr, text_auto=True, aspect="auto", 
                   color_continuous_scale='RdBu_r')
    st.plotly_chart(fig, width='stretch')

# Key metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Molecules", f"{len(filtered_df):,}")
col2.metric("Avg Gap", f"{filtered_df['gap'].mean():.2f}")
col3.metric("Avg μ", f"{filtered_df['mu'].mean():.2f}")
col4.metric("Max α", f"{filtered_df['alpha'].max():.2f}")

st.markdown("---")
st.caption("HOMO-LUMO gap predicts drug stability")

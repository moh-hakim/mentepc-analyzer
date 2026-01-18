import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="MentePC Analyzer", page_icon="🔧", layout="wide")

st.markdown("""
<style>
.main-header {font-size: 2.5rem; font-weight: bold; text-align: center; 
              padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white; border-radius: 10px; margin-bottom: 2rem;}
.risk-banner {font-size: 2rem; font-weight: bold; padding: 1.5rem; 
              border-radius: 10px; text-align: center; margin: 2rem 0;}
.risk-low {background-color: #d4edda; color: #155724;}
.risk-medium {background-color: #fff3cd; color: #856404;}
.risk-high {background-color: #f8d7da; color: #721c24;}
.metric-card {padding: 1rem; border-radius: 8px; border-left: 4px solid; margin: 0.5rem 0;}
.status-green {border-color: #28a745; background-color: #d4edda;}
.status-amber {border-color: #ffc107; background-color: #fff3cd;}
.status-red {border-color: #dc3545; background-color: #f8d7da;}
</style>
""", unsafe_allow_html=True)

def generate_demo_data():
    """Generate synthetic demo data"""
    n = 300
    timestamps = pd.date_range(start='2026-01-18 10:00', periods=n, freq='1s')
    
    data = pd.DataFrame({
        'timestamp': timestamps,
        'ThoD1': np.random.normal(98, 5, n),
        'ThoS1': np.random.normal(15, 3, n),
        'HP': np.random.normal(120, 10, n),
        'LP': np.random.normal(40, 5, n),
        'CT1': np.random.normal(30, 5, n),
        'Hz': np.random.normal(75, 10, n),
    })
    
    data['superheat'] = data['ThoD1'] - data['ThoS1']
    data['pressure_ratio'] = data['HP'] / data['LP']
    
    return data

def load_csv(file):
    """Load MentePC CSV file"""
    try:
        df = pd.read_csv(file, encoding='utf-8')
    except:
        try:
            df = pd.read_csv(file, encoding='shift-jis')
        except:
            df = pd.read_csv(file, encoding='cp932')
    
    # Auto-detect columns
    column_map = {
        'Discharge Temp': 'ThoD1',
        'Discharge Temperature': 'ThoD1',
        'Suction Temp': 'ThoS1',
        'High Pressure': 'HP',
        'Low Pressure': 'LP',
        'Current': 'CT1',
        'Compressor Speed': 'Hz',
        'Inverter Hz': 'Hz'
    }
    
    for old, new in column_map.items():
        if old in df.columns:
            df.rename(columns={old: new}, inplace=True)
    
    # Compute derived parameters
    if 'superheat' not in df.columns and 'ThoD1' in df.columns and 'ThoS1' in df.columns:
        df['superheat'] = df['ThoD1'] - df['ThoS1']
    
    if 'pressure_ratio' not in df.columns and 'HP' in df.columns and 'LP' in df.columns:
        df['pressure_ratio'] = df['HP'] / df['LP']
    
    return df

def evaluate_parameter(value, green_range, amber_range):
    """Evaluate parameter against thresholds"""
    if pd.isna(value):
        return "GRAY", "⚪"
    
    if green_range[0] <= value <= green_range[1]:
        return "GREEN", "🟢"
    elif amber_range[0] <= value <= amber_range[1]:
        return "AMBER", "🟡"
    else:
        return "RED", "🔴"

def analyze_data(df):
    """Analyze dataframe and return results"""
    results = {}
    
    params = {
        'pressure_ratio': {
            'label': 'Pressure Ratio (HP/LP)',
            'col': 'pressure_ratio',
            'unit': '',
            'green': [1.8, 3.5],
            'amber': [1.5, 4.0]
        },
        'discharge_temp': {
            'label': 'Discharge Temperature',
            'col': 'ThoD1',
            'unit': '°C',
            'green': [85, 115],
            'amber': [80, 120]
        },
        'suction_superheat': {
            'label': 'Suction Superheat',
            'col': 'superheat',
            'unit': '°C',
            'green': [5, 15],
            'amber': [4, 18]
        },
        'high_pressure': {
            'label': 'High Pressure',
            'col': 'HP',
            'unit': 'bar',
            'green': [50, 130],
            'amber': [40, 140]
        },
        'low_pressure': {
            'label': 'Low Pressure',
            'col': 'LP',
            'unit': 'bar',
            'green': [25, 42],
            'amber': [20, 45]
        },
        'current_draw': {
            'label': 'Current Draw',
            'col': 'CT1',
            'unit': 'A',
            'green': [5, 45],
            'amber': [3, 50]
        },
        'compressor_speed': {
            'label': 'Compressor Speed',
            'col': 'Hz',
            'unit': 'Hz',
            'green': [20, 120],
            'amber': [10, 130]
        }
    }
    
    for key, config in params.items():
        if config['col'] in df.columns:
            values = df[config['col']].dropna()
            if len(values) > 0:
                mean_val = values.mean()
                status, emoji = evaluate_parameter(mean_val, config['green'], config['amber'])
                
                results[key] = {
                    'label': config['label'],
                    'mean': mean_val,
                    'min': values.min(),
                    'max': values.max(),
                    'std': values.std(),
                    'unit': config['unit'],
                    'status': status,
                    'emoji': emoji
                }
    
    return results

def calculate_risk(results):
    """Calculate overall risk level"""
    red_count = sum(1 for r in results.values() if r['status'] == 'RED')
    amber_count = sum(1 for r in results.values() if r['status'] == 'AMBER')
    
    if red_count > 0:
        return 'HIGH', [f"{r['label']}: {r['emoji']} {r['mean']:.1f}{r['unit']} is critical" 
                       for r in results.values() if r['status'] == 'RED']
    elif amber_count > 0:
        return 'MEDIUM', [f"{r['label']}: {r['emoji']} {r['mean']:.1f}{r['unit']} needs monitoring" 
                         for r in results.values() if r['status'] == 'AMBER']
    else:
        return 'LOW', []

def main():
    st.markdown('<div class="main-header">🔧 MentePC Compressor Health Analyzer</div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        demo_mode = st.checkbox("🎮 Demo Mode", value=False)
        
        if not demo_mode:
            uploaded_file = st.file_uploader("Upload MentePC CSV", type=['csv'])
            if not uploaded_file:
                st.info("Upload CSV to begin")
                st.stop()
        
        model_type = st.selectbox("Model", ["ESA30E-25", "ESA30EH-25", "ESA30EH2-25"], index=2)
        
        analyze_btn = st.button("🔍 Analyze", type="primary")
    
    if not analyze_btn:
        st.info("👈 Configure and click Analyze")
        with st.expander("📋 About"):
            st.markdown("""
            **MentePC Compressor Health Analyzer**
            
            Upload MentePC CSV data to instantly diagnose compressor health.
            
            **Indicators:**
            - 🟢 GREEN = Normal operation
            - 🟡 AMBER = Warning - monitor closely  
            - 🔴 RED = Alert - action required
            
            **Supported Models:**
            - ESA30E-25 (WCMC)
            - ESA30EH-25 (WCMD)
            - ESA30EH2-25 (WCME_S/M)
            """)
        st.stop()
    
    with st.spinner("Analyzing..."):
        try:
            if demo_mode:
                df = generate_demo_data()
                st.success(f"✅ Generated {len(df)} demo samples")
            else:
                df = load_csv(uploaded_file)
                st.success(f"✅ Loaded {len(df)} samples")
            
            results = analyze_data(df)
            risk_level, risk_reasons = calculate_risk(results)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()
    
    # Risk banner
    risk_class = f"risk-{risk_level.lower()}"
    st.markdown(
        f'<div class="risk-banner {risk_class}">'
        f'Overall Risk: {risk_level}'
        f'</div>',
        unsafe_allow_html=True
    )
    
    if risk_reasons:
        st.warning("**⚠️ Issues Detected:**")
        for reason in risk_reasons:
            st.markdown(f"- {reason}")
    else:
        st.success("✅ All parameters within normal range")
    
    # Parameter cards
    st.header("📊 Parameter Status")
    cols = st.columns(3)
    
    for idx, (key, result) in enumerate(results.items()):
        col = cols[idx % 3]
        with col:
            status_class = f"status-{result['status'].lower()}"
            st.markdown(
                f'<div class="metric-card {status_class}">'
                f'<h4>{result["emoji"]} {result["label"]}</h4>'
                f'<p><strong>Mean:</strong> {result["mean"]:.1f} {result["unit"]}</p>'
                f'<p><strong>Range:</strong> {result["min"]:.1f} - {result["max"]:.1f}</p>'
                f'<p><strong>Std Dev:</strong> {result["std"]:.1f}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
    
    # Charts
    st.header("📈 Trends")
    
    chart_df = df.copy()
    if 'timestamp' not in chart_df.columns:
        chart_df['timestamp'] = range(len(chart_df))
    
    tabs = st.tabs(["Discharge Temp", "Pressures", "Current & Speed", "All Data"])
    
    with tabs[0]:
        if 'ThoD1' in chart_df.columns:
            st.line_chart(chart_df.set_index('timestamp')['ThoD1'])
    
    with tabs[1]:
        if 'HP' in chart_df.columns and 'LP' in chart_df.columns:
            st.line_chart(chart_df.set_index('timestamp')[['HP', 'LP']])
    
    with tabs[2]:
        if 'CT1' in chart_df.columns and 'Hz' in chart_df.columns:
            st.line_chart(chart_df.set_index('timestamp')[['CT1', 'Hz']])
    
    with tabs[3]:
        st.dataframe(df.head(100), use_container_width=True)
    
    st.info("**⚠️ Disclaimer:** Diagnostic aid only. Combine with inspection and engineering judgment.")

if __name__ == "__main__":
    main()

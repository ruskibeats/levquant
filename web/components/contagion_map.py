"""Contagion network visualizer for regulatory risk propagation."""

from __future__ import annotations

import graphviz
import streamlit as st


def render_contagion_map(active_risks: list[str]) -> None:
    """Render a network diagram showing regulatory contagion paths.
    
    Visualizes how litigation case risk propagates to insurers and regulators.
    Active risks are shown in red; dormant risks in white/light grey.
    
    Args:
        active_risks: List of active risk node identifiers
                     (e.g., ['sra_risk', 'ico_risk', 'insurer_risk'])
    """
    dot = graphviz.Digraph()
    dot.attr(rankdir='LR', size='8,5', bgcolor='white')
    dot.attr('node', shape='box', style='filled', fontname='Arial')
    dot.attr('edge', fontname='Arial', fontsize='10')
    
    # Core Case Node (always active)
    dot.node(
        'CASE',
        'Litigation\nCase',
        fillcolor='#e8f4f8',
        color='#2c3e50',
        shape='box3d',
        fontsize='12',
        fontcolor='#2c3e50'
    )
    
    # Insurer Node (active if insurer_risk in active_risks)
    insurer_color = '#ffcccc' if 'insurer_risk' in active_risks else '#f0f0f0'
    insurer_penwidth = '3' if 'insurer_risk' in active_risks else '1'
    insurer_fontcolor = '#c0392b' if 'insurer_risk' in active_risks else '#7f8c8d'
    dot.node(
        'INSURER',
        'Insurer\nReserve',
        fillcolor=insurer_color,
        color=insurer_penwidth,
        fontcolor=insurer_fontcolor,
        fontsize='11'
    )
    
    # SRA Node (active if sra_risk in active_risks)
    sra_color = '#ff9999' if 'sra_risk' in active_risks else '#f8f8f8'
    sra_penwidth = '3' if 'sra_risk' in active_risks else '1'
    sra_fontcolor = '#c0392b' if 'sra_risk' in active_risks else '#7f8c8d'
    dot.node(
        'SRA',
        'SRA\nInvestigation',
        fillcolor=sra_color,
        color=sra_penwidth,
        fontcolor=sra_fontcolor,
        fontsize='11'
    )
    
    # ICO Node (active if ico_risk in active_risks)
    ico_color = '#ff9999' if 'ico_risk' in active_risks else '#f8f8f8'
    ico_penwidth = '3' if 'ico_risk' in active_risks else '1'
    ico_fontcolor = '#c0392b' if 'ico_risk' in active_risks else '#7f8c8d'
    dot.node(
        'ICO',
        'ICO Report\n(s.173 DPA)',
        fillcolor=ico_color,
        color=ico_penwidth,
        fontcolor=ico_fontcolor,
        fontsize='11'
    )
    
    # FCA Node (active if fca_risk in active_risks)
    fca_color = '#ff6666' if 'fca_risk' in active_risks else '#f8f8f8'
    fca_penwidth = '3' if 'fca_risk' in active_risks else '1'
    fca_fontcolor = '#c0392b' if 'fca_risk' in active_risks else '#7f8c8d'
    dot.node(
        'FCA',
        'FCA\nNotification',
        fillcolor=fca_color,
        color=fca_penwidth,
        fontcolor=fca_fontcolor,
        fontsize='11'
    )
    
    # Policy Voidance Node (active if insurer_risk and sra_risk both active)
    voidance_active = 'insurer_risk' in active_risks and 'sra_risk' in active_risks
    voidance_color = '#cc0000' if voidance_active else '#f0f0f0'
    voidance_penwidth = '4' if voidance_active else '1'
    voidance_fontcolor = 'white' if voidance_active else '#7f8c8d'
    voidance_shape = 'doubleoctagon' if voidance_active else 'ellipse'
    dot.node(
        'VOIDANCE',
        'Policy\nVoidance',
        fillcolor=voidance_color,
        color=voidance_penwidth,
        fontcolor=voidance_fontcolor,
        shape=voidance_shape,
        fontsize='12',
        fontweight='bold' if voidance_active else 'normal'
    )
    
    # Edges with conditional styling
    # Case to Insurer (Iniquity Check)
    insurer_edge_color = '#e74c3c' if 'insurer_risk' in active_risks else '#95a5a6'
    insurer_penwidth = '2' if 'insurer_risk' in active_risks else '1'
    dot.edge(
        'CASE', 'INSURER',
        label='Iniquity\nExclusion',
        color=insurer_edge_color,
        penwidth=insurer_penwidth,
        fontcolor=insurer_edge_color
    )
    
    # Case to SRA (Misconduct)
    sra_edge_color = '#e74c3c' if 'sra_risk' in active_risks else '#95a5a6'
    sra_penwidth = '2' if 'sra_risk' in active_risks else '1'
    dot.edge(
        'CASE', 'SRA',
        label='Misconduct\nAlleged',
        color=sra_edge_color,
        penwidth=sra_penwidth,
        fontcolor=sra_edge_color
    )
    
    # Case to ICO (Data Breach)
    ico_edge_color = '#e74c3c' if 'ico_risk' in active_risks else '#95a5a6'
    ico_penwidth = '2' if 'ico_risk' in active_risks else '1'
    dot.edge(
        'CASE', 'ICO',
        label='Data\nBreach',
        color=ico_edge_color,
        penwidth=ico_penwidth,
        fontcolor=ico_edge_color
    )
    
    # SRA to FCA (COLP Duty)
    fca_edge_color = '#e74c3c' if 'fca_risk' in active_risks else '#95a5a6'
    fca_penwidth = '2' if 'fca_risk' in active_risks else '1'
    dot.edge(
        'SRA', 'FCA',
        label='COLP/COFA\nDuty',
        color=fca_edge_color,
        penwidth=fca_penwidth,
        fontcolor=fca_edge_color
    )
    
    # SRA to Insurer (Iniquity Check)
    iniquity_edge_color = '#e74c3c' if 'insurer_risk' in active_risks and 'sra_risk' in active_risks else '#95a5a6'
    iniquity_penwidth = '3' if 'insurer_risk' in active_risks and 'sra_risk' in active_risks else '1'
    dot.edge(
        'SRA', 'INSURER',
        label='Iniquity\nCheck',
        color=iniquity_edge_color,
        penwidth=iniquity_penwidth,
        fontcolor=iniquity_edge_color
    )
    
    # Insurer to Voidance (Policy Voidance)
    voidance_edge_color = '#cc0000' if voidance_active else '#95a5a6'
    voidance_penwidth = '3' if voidance_active else '1'
    dot.edge(
        'INSURER', 'VOIDANCE',
        label='Dishonesty\nFinding',
        color=voidance_edge_color,
        penwidth=voidance_penwidth,
        fontcolor=voidance_edge_color,
        style='dashed' if voidance_active else 'solid'
    )
    
    st.graphviz_chart(dot)
    
    # Legend
    st.caption(
        "**Legend:** 🟥 Red = Active Risk | ⬜ Grey = Dormant | "
        "🔴 Double-octagon = Critical threshold | --- Dashed = Imminent threat"
    )


def get_active_risks_from_kill_switches(kill_switches: dict) -> list[str]:
    """Map kill switch states to active risk identifiers.
    
    Args:
        kill_switches: Dictionary of kill switch states
        
    Returns:
        List of active risk node identifiers
    """
    active_risks = []
    
    if kill_switches.get('nullity_confirmed'):
        active_risks.append('nullity_risk')
    
    if kill_switches.get('regulatory_open'):
        active_risks.append('sra_risk')
        active_risks.append('fca_risk')  # SRA → FCA notification
    
    if kill_switches.get('insurer_notice'):
        active_risks.append('insurer_risk')
    
    if kill_switches.get('override_admitted'):
        active_risks.append('ico_risk')  # Data manipulation → ICO
        active_risks.append('sra_risk')
    
    if kill_switches.get('shadow_director'):
        active_risks.append('sra_risk')
        active_risks.append('insurer_risk')
    
    return list(set(active_risks))  # Remove duplicates


def render_contagion_panel(kill_switches: dict) -> None:
    """Render the full contagion visualization panel.
    
    Args:
        kill_switches: Dictionary of kill switch states
    """
    st.subheader("Risk Topology & Contagion Modeling")
    
    with st.expander("What this diagram shows"):
        st.markdown("""
        This network diagram visualizes how litigation risk **propagates** through the regulatory system.
        
        **Key Insight:** A single case doesn't stay isolated—it **infects** the entire regulatory ecosystem.
        
        **Propagation Vectors:**
        - **Misconduct Alleged** → SRA Investigation
        - **Data Breach** → ICO Report (s.173 DPA)
        - **COLP/COFA Duty** → SRA must notify FCA
        - **Iniquity Check** → Insurer reviews coverage
        - **Dishonesty Finding** → **Policy Voidance**
        
        **The Red Network:** When multiple nodes turn red, the firm faces a 
        **regulatory cascade** that cannot be stopped by legal victory alone.
        
        *Settlement is the only verified mechanism to sever contagion vectors.*
        """)
    
    active_risks = get_active_risks_from_kill_switches(kill_switches)
    
    # Show risk count and severity
    risk_count = len(active_risks)
    if risk_count == 0:
        st.info("✅ No contagion vectors currently active")
    elif risk_count <= 2:
        st.warning(f"⚠️ {risk_count} contagion vector{'s' if risk_count > 1 else ''} active — monitor closely")
    else:
        st.error(f"🚨 {risk_count} contagion vectors active — **regulatory cascade risk**")
    
    render_contagion_map(active_risks)

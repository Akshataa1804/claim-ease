import streamlit as st
from app import analyze_claim
import time
import json
import datetime
from document_processor import extract_text_from_upload
import sqlite3
import pandas as pd

# Initialize database connection
conn = sqlite3.connect('claims.db', check_same_thread=False)
c = conn.cursor()

# Create tables if not exists with proper schema
c.execute('''CREATE TABLE IF NOT EXISTS claims (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             claim_type TEXT NOT NULL,
             description TEXT NOT NULL,
             status TEXT DEFAULT 'New',
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

c.execute('''CREATE TABLE IF NOT EXISTS claim_details (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             claim_id INTEGER NOT NULL,
             key TEXT NOT NULL,
             value TEXT,
             FOREIGN KEY(claim_id) REFERENCES claims(id))''')

conn.commit()

# Set page config
st.set_page_config(
    page_title="ClaimEase 🛡️",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    :root {
        --primary: #1f77b4;
        --secondary: #ff7f0e;
        --success: #2ca02c;
        --danger: #d62728;
    }
    
    .header-style {
        font-size: 40px;
        font-weight: bold;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 20px;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
        min-height: 120px;
        border-left: 4px solid var(--primary);
    }
    .metric-title {
        font-size: 16px;
        color: #666;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #333;
    }
    .section-header {
        font-size: 24px;
        color: var(--primary);
        border-bottom: 2px solid var(--primary);
        padding-bottom: 10px;
        margin-top: 20px;
    }
    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        display: inline-block;
    }
    .status-new {
        background-color: #e3f2fd;
        color: var(--primary);
    }
    .status-processing {
        background-color: #fff8e1;
        color: #ff8f00;
    }
    .status-completed {
        background-color: #e8f5e9;
        color: var(--success);
    }
    .stButton>button {
        background: linear-gradient(90deg, var(--primary), var(--secondary)) !important;
        color: white !important;
        font-weight: bold;
        padding: 10px 24px;
        border-radius: 30px;
        border: none;
        font-size: 16px;
    }
    .timeline {
        position: relative;
        padding-left: 20px;
        border-left: 2px solid var(--primary);
        margin: 20px 0;
    }
    .timeline-item {
        margin-bottom: 20px;
        position: relative;
    }
    .timeline-item:before {
        content: '';
        position: absolute;
        left: -26px;
        top: 5px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: var(--primary);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_claim' not in st.session_state:
    st.session_state.current_claim = None

def save_claim_to_db(claim_type, description, analysis):
    """Save claim to database with analysis details"""
    try:
        c.execute("INSERT INTO claims (claim_type, description, status) VALUES (?, ?, ?)",
                  (claim_type, description, "Processed"))
        claim_id = c.lastrowid
        
        # Save analysis details
        for key, value in analysis.items():
            if isinstance(value, (list, dict)):
                value = json.dumps(value)
            c.execute("INSERT INTO claim_details (claim_id, key, value) VALUES (?, ?, ?)",
                      (claim_id, key, str(value)))
        
        conn.commit()
        return claim_id
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        conn.rollback()
        return None

def get_claim_history():
    """Retrieve claim history from database"""
    try:
        c.execute("""
            SELECT c.id, c.claim_type, c.description, c.status, c.created_at
            FROM claims c
            ORDER BY c.created_at DESC
            LIMIT 10
        """)
        claims = []
        for row in c.fetchall():
            claim_id, claim_type, description, status, created_at = row
            c.execute("SELECT key, value FROM claim_details WHERE claim_id = ?", (claim_id,))
            details = {row[0]: row[1] for row in c.fetchall()}
            
            claims.append({
                "id": claim_id,
                "type": claim_type,
                "description": description,
                "status": status,
                "created_at": created_at,
                "details": details
            })
        return claims
    except Exception as e:
        st.error(f"Error loading claim history: {str(e)}")
        return []

def display_claim_analysis(analysis, processing_time):
    """Display claim analysis results"""
    try:
        # Convert analysis to dict if it's a string
        if isinstance(analysis, str):
            analysis = json.loads(analysis)
        
        # Success banner
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #d4edda, #c3e6cb); 
                    color: #155724; 
                    border-radius: 10px; 
                    padding: 20px; 
                    margin-bottom: 30px;">
            <h3>✅ Claim Analyzed in {processing_time:.2f} seconds</h3>
            <p>Processed with {analysis.get("model", "AI")} at {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Claim Summary Cards
        st.markdown("### 🧾 Claim Summary")
        cols = st.columns(3)
        
        with cols[0]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">👤 Claimant</div>
                <div class="metric-value">{analysis.get("Name", "Unknown")}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with cols[1]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🔢 Policy Number</div>
                <div class="metric-value">{analysis.get("Policy Number", "Unknown")}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with cols[2]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📅 Incident Date</div>
                <div class="metric-value">{analysis.get("Incident Date", "Unknown")}</div>
            </div>
            """, unsafe_allow_html=True)
        
        cols = st.columns(3)
        with cols[0]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">⚡ Incident Type</div>
                <div class="metric-value">{analysis.get("Incident Type", "Unknown")}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with cols[1]:
            loss = analysis.get("Estimated Loss", "Not provided")
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">💸 Estimated Loss</div>
                <div class="metric-value">{loss}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with cols[2]:
            score = int(analysis.get("Completeness Score", 0))
            color = "#2ca02c" if score > 75 else "#ff7f0e" if score > 50 else "#d62728"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📊 Completeness Score</div>
                <div class="metric-value" style="color: {color};">{score}/100</div>
                <div style="height: 8px; background: #f0f0f0; border-radius: 4px; margin-top: 10px;">
                    <div style="height: 100%; width: {score}%; background: {color}; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Claim Timeline
        st.markdown("### 📅 Claim Timeline")
        st.markdown("""
        <div class="timeline">
            <div class="timeline-item">
                <strong>Incident Occured</strong>
                <p>{incident_date}</p>
            </div>
            <div class="timeline-item">
                <strong>Claim Reported</strong>
                <p>{report_date}</p>
            </div>
            <div class="timeline-item">
                <strong>AI Analysis Completed</strong>
                <p>{analysis_date}</p>
            </div>
            <div class="timeline-item">
                <strong>Next Steps: Document Submission</strong>
                <p>Submit required documents within 7 days</p>
            </div>
        </div>
        """.format(
            incident_date=analysis.get("Incident Date", "Unknown"),
            report_date=datetime.datetime.now().strftime("%Y-%m-%d"),
            analysis_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        ), unsafe_allow_html=True)
        
        # Issues & Documents
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ⚠️ Potential Issues")
            flags = analysis.get("Red Flags", [])
            if flags:
                for flag in flags:
                    st.markdown(f"""
                    <div style="background-color: #f8d7da;
                                color: #721c24;
                                border-radius: 8px;
                                padding: 12px;
                                margin-bottom: 10px;
                                display: flex;
                                align-items: center;">
                        <span style="font-size: 24px; margin-right: 10px;">❗</span>
                        <span>{flag}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background-color: #d4edda;
                            color: #155724;
                            border-radius: 8px;
                            padding: 20px;
                            text-align: center;">
                    <span style="font-size: 24px; margin-right: 10px;">✅</span>
                    <strong>No critical issues found!</strong>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📄 Required Documents")
            docs = analysis.get("Checklist", [])
            if docs:
                st.markdown("""
                <div style="background-color: #e8f4fc;
                            border-radius: 10px;
                            padding: 15px;
                            margin-bottom: 20px;">
                    {doc_list}
                </div>
                """.format(doc_list="<br>".join([f"• {doc}" for doc in docs])), 
                unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background-color: #d1ecf1;
                            color: #0c5460;
                            border-radius: 8px;
                            padding: 20px;
                            text-align: center;">
                    <span style="font-size: 24px; margin-right: 10px;">ℹ️</span>
                    <strong>No specific document checklist generated</strong>
                </div>
                """, unsafe_allow_html=True)
        
        # Action Buttons
        st.markdown("### ➡️ Next Steps")
        cols = st.columns(4)
        with cols[0]:
            if st.button("📥 Save Claim", use_container_width=True):
                st.success("Claim saved to history!")
        with cols[1]:
            if st.button("📧 Email Summary", use_container_width=True):
                st.info("Summary will be emailed to registered address")
        with cols[2]:
            if st.button("🖨️ Generate Report", use_container_width=True):
                st.info("PDF report generated")
        with cols[3]:
            if st.button("👨‍💼 Assign Agent", use_container_width=True):
                st.info("Claim assigned to agent")
                
    except Exception as e:
        st.error(f"Error displaying analysis: {str(e)}")
        with st.expander("Technical Details"):
            st.json(analysis)

def new_claim_tab():
    """UI for submitting new claims"""
    st.markdown('<div class="header-style">ClaimEase 🛡️</div>', unsafe_allow_html=True)
    st.markdown("### File Your Financial Claim")
    
    with st.container():
        col1, col2 = st.columns([3, 2])
        
        with col1:
            claim_type = st.selectbox(
                "Select Claim Type",
                ["🚗 Auto Insurance", "🏥 Health Insurance", "🏠 Property Insurance", 
                 "💼 Liability Claim", "💰 Loan Claim", "🧾 Reimbursement"],
                index=0
            )
            
            user_input = st.text_area(
                "Describe your claim in detail:",
                height=200,
                placeholder="Example: My car was rear-ended on Main Street yesterday. Policy #PC123456. Repair estimate ₹85,000.",
                help="Include policy numbers, dates, and details of what happened"
            )
            
            if st.button("Analyze Claim", use_container_width=True, type="primary"):
                if not user_input.strip():
                    st.warning("Please describe your incident")
                else:
                    with st.spinner("🤖 Analyzing your claim with AI..."):
                        start_time = time.time()
                        result = analyze_claim(user_input)
                        processing_time = time.time() - start_time
                    
                    try:
                        analysis = json.loads(result)
                        st.session_state.current_claim = {
                            "type": claim_type,
                            "description": user_input,
                            "analysis": analysis,
                            "processing_time": processing_time
                        }
                        save_claim_to_db(claim_type, user_input, analysis)
                    except Exception as e:
                        st.error("Failed to process claim analysis")
                        with st.expander("Technical Details"):
                            st.text(result)
                            st.error(str(e))
        
        with col2:
            st.markdown("### 📂 Supporting Documents")
            uploaded_files = st.file_uploader(
                "Upload documents (PDF, images, etc)",
                type=["pdf", "jpg", "png", "jpeg", "txt"],
                accept_multiple_files=True,
                help="Upload photos of damage, receipts, or policy documents"
            )
            
            if uploaded_files:
                st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
                for file in uploaded_files:
                    with st.expander(f"📄 {file.name}", expanded=False):
                        st.caption(f"Type: {file.type}, Size: {len(file.getvalue())//1024} KB")
                        extracted_text = extract_text_from_upload(file)
                        st.text_area("Extracted Content", value=extracted_text, height=150)
    
    # Display results if available
    if st.session_state.current_claim:
        display_claim_analysis(
            st.session_state.current_claim["analysis"],
            st.session_state.current_claim["processing_time"]
        )

def history_tab():
    """UI for claim history"""
    st.markdown('<div class="header-style">Claim History</div>', unsafe_allow_html=True)
    st.markdown("### Your Recent Claims")
    
    # Get claim history
    history = get_claim_history()
    
    if not history:
        st.info("No claims found. Submit your first claim to see history here.")
        return
    
    # Show claims in a table
    df_data = []
    for claim in history:
        details = claim.get("details", {})
        df_data.append({
            "ID": claim["id"],
            "Type": claim["type"],
            "Description": (claim["description"][:100] + "...") if len(claim["description"]) > 100 else claim["description"],
            "Status": claim["status"],
            "Date": claim["created_at"],
            "Score": details.get("Completeness Score", "N/A")
        })
    
    df = pd.DataFrame(df_data)
    
    # Format status badges
    def format_status(status):
        color_class = "status-new"
        if "Processing" in status:
            color_class = "status-processing"
        elif "Complete" in status:
            color_class = "status-completed"
        return f'<span class="status-badge {color_class}">{status}</span>'
    
    if not df.empty:
        df["Status"] = df["Status"].apply(format_status)
        st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # Show details when claim is selected
    selected_id = st.selectbox("Select a claim to view details", [claim["id"] for claim in history])
    selected_claim = next((claim for claim in history if claim["id"] == selected_id), None)
    
    if selected_claim:
        st.markdown("### Claim Details")
        
        cols = st.columns(2)
        with cols[0]:
            st.markdown(f"**Claim Type:** {selected_claim['type']}")
            st.markdown(f"**Date Submitted:** {selected_claim['created_at']}")
            st.markdown(f"**Status:** {selected_claim['status']}")
            
        with cols[1]:
            score = selected_claim["details"].get("Completeness Score", "N/A")
            st.markdown(f"**Completeness Score:** {score}")
        
        st.markdown("#### Original Description")
        st.write(selected_claim["description"])
        
        st.markdown("#### AI Analysis")
        st.json(selected_claim["details"])

# Main app
def main():
    # Create tabs
    tab1, tab2 = st.tabs(["New Claim", "Claim History"])
    
    with tab1:
        new_claim_tab()
    
    with tab2:
        history_tab()

if __name__ == "__main__":
    main()
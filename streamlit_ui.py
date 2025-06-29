import streamlit as st
from app import analyze_claim, generate_followup, predict_settlement
from document_processor import extract_text_from_upload, extract_entities
from database import init_db, save_claim, save_message, get_claim, get_claim_conversation, list_claims, save_document, get_claim_documents
import json
import time
import datetime
import pandas as pd
import plotly.express as px

# Initialize database
init_db()

# Set page config
st.set_page_config(
    page_title="ClaiEase AI 🤖",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    :root {
        --primary: #4F46E5;
        --secondary: #10B981;
        --danger: #EF4444;
        --warning: #F59E0B;
    }
    
    .header-style {
        font-size: 40px;
        font-weight: bold;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 20px;
        margin-bottom: 30px;
    }
    
    .message-user {
        background-color: #f0f4ff;
        border-radius: 15px 15px 0 15px;
        padding: 12px 18px;
        margin: 5px 0;
        max-width: 80%;
        margin-left: auto;
    }
    
    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        display: inline-block;
    }
    
    .status-new {
        background-color: #E0F2FE;
        color: #0C4A6E;
    }
    
    .status-processing {
        background-color: #FEF3C7;
        color: #92400E;
    }
    
    .status-completed {
        background-color: #D1FAE5;
        color: #065F46;
    }
    
    .file-uploader {
        background-color: #F9FAFB;
        border: 2px dashed #D1D5DB;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .damage-card {
        border-left: 4px solid var(--warning);
        padding: 15px;
        background: #FFFBEB;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
        border-left: 4px solid var(--primary);
    }
</style>
""", unsafe_allow_html=True)

def new_claim_tab():
    st.markdown('<div class="header-style">ClaimGenius AI 🤖</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'current_claim_id' not in st.session_state:
        st.session_state.current_claim_id = None
        st.session_state.conversation = [
            {"role": "ai", "content": "Hello! I'm your AI claims assistant. Please describe your incident in your own words."}
        ]
        st.session_state.uploaded_files = []
        st.session_state.analysis = None
        st.session_state.raw_analysis = None
    
    # Display conversation
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.conversation:
            if msg["role"] == "user":
                st.markdown(f'<div class="message-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                # Render markdown for AI responses
                st.markdown(msg["content"], unsafe_allow_html=True)
    
    # File upload in sidebar
    st.sidebar.markdown("### 📁 Upload Supporting Documents")
    uploaded_files = st.sidebar.file_uploader(
        "Drag files here (PDF, images, text)",
        type=["pdf", "jpg", "png", "jpeg", "txt"],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    # Process new files
    if uploaded_files and len(uploaded_files) > len(st.session_state.uploaded_files):
        new_files = uploaded_files[len(st.session_state.uploaded_files):]
        for file in new_files:
            # Process file
            result = extract_text_from_upload(file)
            if "text" in result:
                # Save document to DB
                if st.session_state.current_claim_id:
                    save_document(
                        st.session_state.current_claim_id,
                        file.name,
                        result.get("type", "unknown"),
                        result["text"],
                        result
                    )
                
                # Add to conversation
                summary = f"📄 Document uploaded: **{file.name}** (Type: {result.get('type', 'unknown')})"
                if result.get("description"):
                    summary += f"\nAI Description: {result['description']}"
                
                st.session_state.conversation.append({"role": "ai", "content": summary})
                
        st.session_state.uploaded_files = uploaded_files
        st.rerun()
    
    # User input at the bottom
    user_input = st.chat_input("Type your message here...")
    if user_input:
        # Add user message to conversation
        st.session_state.conversation.append({"role": "user", "content": user_input})
        
        # Combine conversation for context
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.conversation])
        
        with st.spinner("🤖 Analyzing your claim with AI..."):
            # Analyze the claim with the full context
            analysis_result = analyze_claim(context)
            st.session_state.raw_analysis = analysis_result
            
            try:
                analysis = json.loads(analysis_result)
                st.session_state.analysis = analysis
                
                # If this is the first message, create a new claim
                if st.session_state.current_claim_id is None:
                    # Save the claim
                    claim_id = save_claim(analysis)
                    st.session_state.current_claim_id = claim_id
                    # Save all conversation so far
                    for msg in st.session_state.conversation:
                        save_message(claim_id, msg["role"], msg["content"])
                else:
                    # Save the user message
                    save_message(st.session_state.current_claim_id, "user", user_input)
                
                # Generate follow-up questions
                followups = generate_followup(analysis_result)
                
                # Format AI response
                ai_response = f"""
**🔍 Claim Analysis Summary**  
{analysis.get('summary', 'Analysis completed. See details below.')}

**⏱️ Next Steps**  
- Estimated processing time: {analysis.get('next_steps', {}).get('timeline', '3-5 days')}
- Required documents: {', '.join(analysis.get('next_steps', {}).get('required_docs', ['Police report', 'Repair estimate', 'Medical bills']))}

**❓ Follow-up Questions**  
"""
                for i, question in enumerate(followups[:3]):
                    ai_response += f"{i+1}. {question}\n"
                
                # Add fraud risk assessment
                fraud_risk = analysis.get('assessment', {}).get('fraud_risk', 0)
                try:
                    fraud_risk = int(fraud_risk)
                except:
                    fraud_risk = 0
                    
                risk_color = "#10B981" if fraud_risk < 30 else "#F59E0B" if fraud_risk < 70 else "#EF4444"
                ai_response += f"\n**🛡️ Fraud Risk Assessment**  \n"
                ai_response += f'<div style="height: 10px; background: #f0f0f0; border-radius: 5px; margin: 10px 0;">'
                ai_response += f'<div style="height: 100%; width: {fraud_risk}%; background: {risk_color}; border-radius: 5px;"></div></div>'
                ai_response += f"**{fraud_risk}% risk** - "
                
                if fraud_risk < 30:
                    ai_response += "Low risk profile"
                elif fraud_risk < 70:
                    ai_response += "Moderate risk, needs verification"
                else:
                    ai_response += "High risk, recommend investigation"
                
                # Add AI response to conversation
                st.session_state.conversation.append({"role": "ai", "content": ai_response})
                # Save AI response to DB
                if st.session_state.current_claim_id:
                    save_message(st.session_state.current_claim_id, "ai", ai_response)
                
                st.rerun()
                
            except json.JSONDecodeError:
                error_msg = "Sorry, I encountered an error processing your claim. Please try again with more details."
                st.session_state.conversation.append({"role": "ai", "content": error_msg})
                if st.session_state.current_claim_id:
                    save_message(st.session_state.current_claim_id, "ai", error_msg)
                st.rerun()
    
    # Display detailed analysis if available
    if st.session_state.analysis:
        st.divider()
        st.markdown("## 📊 Claim Analysis Dashboard")
        
        # Claim metrics
        col1, col2, col3, col4 = st.columns(4)
        analysis = st.session_state.analysis
        
        with col1:
            name = analysis.get('claimant', {}).get('name', 'Unknown')
            if name == "Unknown":
                name = "Not provided"
            st.markdown(f"**👤 Claimant**  \n{name}")
        
        with col2:
            policy = analysis.get('policy', {}).get('number', 'Unknown')
            if policy == "Unknown":
                policy = "VIN: 1HGCV1F12MA123456"  # Example fallback
            st.markdown(f"**📋 Policy Number**  \n{policy}")
        
        with col3:
            loss = analysis.get('assessment', {}).get('estimated_loss', 'Not estimated')
            # Format currency
            if isinstance(loss, str) and '$' in loss:
                loss = loss.replace('$', '').replace(',', '')
                try:
                    loss_value = float(loss)
                    loss = f"${loss_value:,.2f}"
                except:
                    pass
            st.markdown(f"**💸 Estimated Loss**  \n{loss}")
        
        with col4:
            score = analysis.get('assessment', {}).get('completeness_score', 0)
            try:
                score = int(score)
            except:
                score = 0
                
            score_color = "#EF4444" if score < 50 else "#F59E0B" if score < 80 else "#10B981"
            st.markdown(f"**📊 Completeness Score**  \n")
            st.markdown(f'<div style="height: 10px; background: #f0f0f0; border-radius: 5px; margin: 10px 0;">'
                        f'<div style="height: 100%; width: {score}%; background: {score_color}; border-radius: 5px;"></div>'
                        f'</div><div style="text-align: center;">{score}/100</div>', 
                        unsafe_allow_html=True)
        
        # Settlement prediction
        with st.expander("🔮 Settlement Prediction", expanded=True):
            settlement = predict_settlement(st.session_state.raw_analysis)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Predicted Outcome**  \n{settlement.get('settlement_prediction', 'Analysis in progress')}")
                st.markdown(f"**Amount Range**  \n{settlement.get('amount_range', 'Not estimated')}")
            
            with col2:
                conf = settlement.get('confidence', 0)
                try:
                    conf = int(conf)
                except:
                    conf = 0
                st.markdown(f"**Confidence**  \n{conf}%")
                st.progress(conf/100 if conf > 0 else 0)
            
            st.markdown("**Key Factors**")
            for factor in settlement.get('key_factors', ["Initial assessment underway"]):
                st.markdown(f"- {factor}")
        
        # Document analysis
        if st.session_state.current_claim_id:
            documents = get_claim_documents(st.session_state.current_claim_id)
            if documents:
                st.markdown("## 📑 Document Analysis")
                for doc in documents:
                    with st.expander(f"📄 {doc['filename']} ({doc['type']})", expanded=False):
                        if doc.get('analysis'):
                            st.json(doc['analysis'])
                        else:
                            st.info("No analysis available")
        
        # Add debug view
        with st.expander("⚠️ Debug View (Raw Analysis)"):
            st.json(st.session_state.analysis)

def history_tab():
    st.markdown('<div class="header-style">Claim History</div>', unsafe_allow_html=True)
    
    claims = list_claims()
    if not claims:
        st.info("No claims found. Submit your first claim to see history here.")
        return
    
    # Display claims in a table
    st.write("## Your Claims")
    for claim in claims:
        col1, col2, col3, col4 = st.columns([1,2,2,2])
        with col1:
            st.markdown(f"**ID:** {claim['id']}")
            badge_class = f"status-{claim['status'].lower()}"
            st.markdown(f"**Status:** <span class='status-badge {badge_class}'>{claim['status']}</span>", 
                        unsafe_allow_html=True)
        with col2:
            st.markdown(f"**Created:** {claim['created_at']}")
        with col3:
            st.markdown(f"**Last Activity:** {claim['created_at']}")  # Simplified
        with col4:
            if st.button(f"View Details ##{claim['id']}", key=f"view_{claim['id']}"):
                st.session_state.selected_claim = claim['id']
        
        st.divider()
    
    # Display selected claim details
    if 'selected_claim' in st.session_state:
        claim_id = st.session_state.selected_claim
        claim_data = get_claim(claim_id)
        conversation = get_claim_conversation(claim_id)
        documents = get_claim_documents(claim_id)
        
        if claim_data:
            st.markdown(f"## Claim #{claim_id}")
            
            # Summary
            st.markdown("### Summary")
            analysis = claim_data.get('data', {})
            cols = st.columns(4)
            cols[0].metric("Claimant", analysis.get('claimant', {}).get('name', 'Unknown'))
            cols[1].metric("Policy", analysis.get('policy', {}).get('number', 'Unknown'))
            cols[2].metric("Incident", analysis.get('incident', {}).get('type', 'Unknown'))
            fraud_risk = analysis.get('assessment', {}).get('fraud_risk', 0)
            cols[3].metric("Fraud Risk", f"{fraud_risk}%", 
                          delta_color="inverse" if fraud_risk > 50 else "normal")
            
            # Conversation
            st.markdown("### Conversation History")
            for msg in conversation:
                if msg["role"] == "user":
                    st.markdown(f'<div class="message-user">{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="message-ai">{msg["content"]}</div>', unsafe_allow_html=True)
            
            # Documents
            if documents:
                st.markdown("### Uploaded Documents")
                for doc in documents:
                    with st.expander(f"{doc['filename']} ({doc['type']})"):
                        if doc.get('analysis'):
                            st.json(doc['analysis'])
            
            # Raw analysis
            with st.expander("Raw Analysis Data"):
                st.json(analysis)
        else:
            st.error("Claim not found")

def analytics_tab():
    st.markdown('<div class="header-style">Claims Analytics</div>', unsafe_allow_html=True)
    
    # Simulated analytics data
    st.markdown("## 📈 Claim Performance Metrics")
    
    # Create sample data
    data = {
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Auto Claims': [42, 56, 39, 48, 60, 55],
        'Property Claims': [28, 32, 40, 35, 42, 38],
        'Health Claims': [15, 18, 22, 20, 25, 23],
        'Avg. Processing Time (days)': [8.2, 7.5, 6.8, 6.2, 5.9, 5.5],
        'Fraud Risk Score': [34, 31, 29, 27, 25, 23]
    }
    df = pd.DataFrame(data)
    
    # Claim types chart
    st.markdown("### Claim Types Distribution")
    fig = px.bar(df, x='Month', y=['Auto Claims', 'Property Claims', 'Health Claims'],
                 barmode='stack', height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Processing time chart
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Processing Time Improvement")
        fig = px.line(df, x='Month', y='Avg. Processing Time (days)', markers=True, height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Fraud Risk Trend")
        fig = px.line(df, x='Month', y='Fraud Risk Score', markers=True, height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # AI impact metrics
    st.markdown("## 🤖 AI Impact Analysis")
    cols = st.columns(3)
    cols[0].metric("Claims Automated", "78%", "12% improvement")
    cols[1].metric("Processing Cost Reduction", "$1.2M", "23% savings")
    cols[2].metric("Fraud Detection Rate", "92%", "18% increase")

# Main app
def main():
    tab1, tab2, tab3 = st.tabs(["New Claim", "History", "Analytics"])
    
    with tab1:
        new_claim_tab()
    
    with tab2:
        history_tab()
    
    with tab3:
        analytics_tab()

if __name__ == "__main__":
    main()
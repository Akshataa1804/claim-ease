import streamlit as st
from app import analyze_claim
import time
import json
import auth
import database

def main_app():
    st.set_page_config(page_title="ClaimEase", page_icon="🛡️", layout="wide")
    st.title("ClaimEase 🛡️ - AI Financial Assistant")
    
    # Initialize session state
    if 'claim_history' not in st.session_state:
        st.session_state.claim_history = []
    
    # Claim type selection
    claim_types = ["Insurance", "Loan", "Reimbursement", "Other"]
    claim_type = st.sidebar.selectbox("Claim Type", claim_types, index=0)
    
    # Document upload
    uploaded_files = st.sidebar.file_uploader(
        "Upload supporting documents",
        type=["pdf", "jpg", "png", "txt"],
        accept_multiple_files=True
    )
    
    # User input
    user_input = st.text_area(
        "Describe your financial claim:",
        height=150,
        placeholder="e.g., My car was damaged in a collision...",
        key="incident_desc"
    )
    
    # Combine documents with user input
    doc_text = ""
    if uploaded_files:
        st.sidebar.info(f"{len(uploaded_files)} file(s) uploaded")
        for file in uploaded_files:
            doc_text += f"\n\n[Document: {file.name}]\n"
            if file.type == "text/plain":
                doc_text += file.getvalue().decode("utf-8")
            else:
                # In production, add OCR processing here
                doc_text += f"<{file.type} content not extracted in demo>"
    
    full_input = user_input + doc_text
    
    # Claim processing
    if st.button("Analyze Claim"):
        if not full_input.strip():
            st.warning("Please describe your claim")
        else:
            with st.spinner("⏳ Processing claim with local AI..."):
                start_time = time.time()
                result = analyze_claim(full_input, claim_type)
                processing_time = time.time() - start_time
                
            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
                if "raw_output" in result:
                    with st.expander("Raw Output"):
                        st.text(result["raw_output"])
            else:
                # Log claim to database
                if st.session_state.user_id:
                    database.log_claim(
                        st.session_state.user_id,
                        claim_type,
                        full_input,
                        result
                    )
                
                # Refresh claim history
                if st.session_state.user_id:
                    st.session_state.claim_history = database.get_claim_history(
                        st.session_state.user_id
                    )
                
                st.success(f"✅ Claim analyzed in {processing_time:.2f} seconds")
                display_claim_result(result)
    
    # Claim history
    if st.session_state.claim_history:
        st.sidebar.divider()
        st.sidebar.subheader("📜 Claim History")
        for claim in st.session_state.claim_history:
            with st.sidebar.expander(f"{claim['claim_type']} - {claim['created_at']}"):
                st.caption(claim["input_text"])
                if st.button("View Details", key=f"view_{claim['id']}"):
                    st.session_state.current_claim = claim
                    st.rerun()  # FIXED: Changed to st.rerun()
    
    # Show current claim details if selected
    if 'current_claim' in st.session_state:
        st.subheader(f"Claim Details: {st.session_state.current_claim['created_at']}")
        display_claim_result(st.session_state.current_claim['output'])
        if st.button("Back to New Claim"):
            del st.session_state.current_claim
            st.rerun()  # FIXED: Changed to st.rerun()

def display_claim_result(result):
    """Display claim analysis results"""
    # Claim Summary
    st.subheader("🧾 Claim Summary")
    col1, col2 = st.columns(2)
    col1.metric("Name", result.get("Name", "Unknown"))
    col2.metric("Policy/Account", result.get("Policy Number", "N/A"))
    
    col1, col2 = st.columns(2)
    col1.metric("Claim Type", result.get("claim_type", "Unknown"))
    col2.metric("Incident Date", result.get("Incident Date", "Unknown"))
    
    st.metric("Amount", result.get("Estimated Loss", "Not provided"))
    
    st.divider()
    st.subheader("📋 Analysis")
    score = int(result.get("Completeness Score", 0))
    st.progress(score/100, text=f"Completeness Score: {score}/100")
    
    # Red Flags
    with st.expander("⚠️ Red Flags", expanded=True):
        flags = result.get("Red Flags", [])
        if flags:
            for flag in flags:
                st.error(f"• {flag}")
        else:
            st.success("No critical issues found")
    
    # Document Checklist
    with st.expander("📄 Required Documents", expanded=True):
        docs = result.get("Checklist", [])
        if docs:
            for i, doc in enumerate(docs, 1):
                st.checkbox(f"{i}. {doc}", value=False)
        else:
            st.warning("No document checklist generated")
    
    # Raw JSON
    with st.expander("🔍 Technical Details"):
        st.json(result)
    
    # Model info
    st.caption(f"Processed with {result.get('model', 'local AI')} in {result.get('processing_time', 'N/A')}")

# Main entry point
if __name__ == "__main__":
    if auth.authenticate_user():
        main_app()
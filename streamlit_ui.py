import streamlit as st
from app import analyze_claim
import json
import time

st.set_page_config(page_title="ClaimEase", page_icon="🛡️")
st.title("ClaimEase 🛡️ - AI Insurance Assistant")

# User input
user_input = st.text_area(
    "Describe your incident:",
    height=150,
    placeholder="e.g., My car was damaged in a collision on 2023-05-15, Policy AB123456..."
)

if st.button("Analyze Claim"):
    if not user_input.strip():
        st.warning("Please describe your incident")
    else:
        status_area = st.empty()
        status_area.info("⏳ Processing claim... This may take 10-20 seconds")
        
        start_time = time.time()
        result = None
        
        try:
            result = analyze_claim(user_input)
            processing_time = time.time() - start_time
            status_area.empty()
            
            # Display success message
            st.success(f"✅ Claim analyzed in {processing_time:.1f} seconds")
            
            # Parse and display results
            parsed = json.loads(result)
            
            # Claim Summary
            st.subheader("🧾 Claim Summary")
            col1, col2 = st.columns(2)
            col1.metric("Name", parsed.get("Name", "Unknown"))
            col2.metric("Policy Number", parsed.get("Policy Number", "Unknown"))
            col1, col2 = st.columns(2)
            col1.metric("Incident Type", parsed.get("Incident Type", "Unknown"))
            col2.metric("Incident Date", parsed.get("Incident Date", "Unknown"))
            
            # Analysis
            st.divider()
            st.subheader("📋 Analysis")
            score = int(parsed.get("Completeness Score", 0))
            st.progress(score/100, text=f"Completeness Score: {score}/100")
            
            # Red Flags
            with st.expander("⚠️ Red Flags", expanded=True):
                flags = parsed.get("Red Flags", [])
                if flags:
                    for flag in flags:
                        st.error(f"• {flag}")
                else:
                    st.success("No critical issues found")
            
            # Document Checklist
            with st.expander("📄 Required Documents", expanded=True):
                docs = parsed.get("Checklist", [])
                if docs:
                    for doc in docs:
                        st.info(f"• {doc}")
                else:
                    st.warning("No document checklist generated")
            
            # Raw JSON
            with st.expander("🔍 Raw JSON Output"):
                st.json(parsed)
                
        except Exception as e:
            status_area.empty()
            st.error(f"❌ Error processing claim: {str(e)}")
            if result:
                with st.expander("Technical Details"):
                    st.text(result)
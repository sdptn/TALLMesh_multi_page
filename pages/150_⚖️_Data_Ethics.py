import os
import streamlit as st
import json
import shutil
from ui_utils import sidebar_data_controls

sidebar_data_controls()

def main():
    st.set_page_config(page_title="Data Ethics", page_icon="⚖️")

    st.title("⚖️ Data Ethics")

    st.warning("""
    **Please consider the sensitivity of your data before using TALLMesh.**

    You are responsible for ensuring that your use of TALLMesh complies with
    relevant ethical approvals, data-protection requirements, and your
    organisation's policies on the use of AI and research data.
    """)

    st.header("How TALLMesh Processes Your Data")

    st.write("""
    TALLMesh stores uploaded files and generated analysis outputs temporarily
    within your project workspace.

    When you use LLM-assisted analysis features, relevant research data is sent
    to the GRAPHIA LLM service for processing. Depending on the analysis stage,
    this may include transcript text, codes, code descriptions, quotations,
    prompts, and generated analysis outputs.

    Requests to the LLM service may be recorded in service logs. The retention
    and handling of those logs are determined by the infrastructure supporting
    the GRAPHIA LLM service and are separate from TALLMesh's own workspace
    retention.
    """)

    st.header("TALLMesh Workspace Retention")

    st.write("""
    TALLMesh project workspaces are temporary. A workspace that has been
    inactive for more than 24 hours is automatically deleted. Cleanup checks
    are performed periodically, so deletion may occur after the 24-hour
    threshold rather than at exactly 24 hours.

    If you want to retain your analysis, download your project using **💾 Prepare Project Download** before leaving
    it inactive. You can also use **🗑️ Clear Workspace** in the sidebar to remove
    the contents of your workspace when you have finished.
    """)

    st.header("Sensitive and Personal Data")

    st.write("""
    Do not upload sensitive, confidential, or personally identifiable
    information unless you have appropriate authorisation and have determined
    that processing the data through the available infrastructure is permitted.

    Before uploading research data, consider whether it should be anonymised or
    otherwise prepared in accordance with your ethical approval and
    institutional data-management requirements.
    """)

    st.header("Researcher Responsibility")

    st.info("""
    TALLMesh is an experimental research tool designed to assist thematic
    analysis. LLM-generated codes, reductions, and candidate themes should be
    reviewed critically by the researcher and should not be treated as a
    substitute for researcher judgement.
    """)
    


if __name__ == "__main__":
    main()
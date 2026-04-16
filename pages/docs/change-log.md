# TALLMesh Error Log

This document tracks implementation errors, causes and resolutions.

---

## 11-02-2026 - Widget State Error

**Component:** Streamlit widget on Project Set Up page (file uploader)
**Error:** `streamlit.errors.StreamlitValueAssignmentNotAllowedError`  
**Message:** Values for the widget with key `uploaded_files` cannot be set using `st.session_state`.

**Issue:** After doing a run through of codes, error pops up after returning to the beginning of the same project.

**Cause:** Streamlit does not allow programmatically assigning values to certain widget keys (including `st.file_uploader`) via `st.session_state`. The code attempted to set or reset `st.session_state["uploaded_files"]`, which violates Streamlit’s widget state rules.

**Fix implemented:**

- Removed the session state initialisation for `uploaded_files` (commented out the block that set `st.session_state.uploaded_files = None`).
- Kept the uploader widget (`key="uploaded_files"`) and used `on_change=handle_file_upload` to read files from `st.session_state.get("uploaded_files")` without writing to the widget key.

**Status:** Resolved

---

## 11-02-2026 - Project deletion fails on Windows due to access denied

**Component:** Project removal (Project Setup page)
**Error:** `[WinError 5] Access is denied: 'projects\<project_name>\data'`

**Issue:** Trying to delete a project is blocked by this error.

**Cause:** Windows file locks and/or permission restrictions can prevent deleting directories that contain open files or handles (e.g., files recently uploaded/processed, or files open in another program). `shutil.rmtree()` can fail if it encounters locked files/folders.

**Fix:**

- Replaced `shutil.rmtree(project_path)` with a more hardyt deletion strategy:
  - Added a small delay (`time.sleep(0.5)`) before deletion to reduce transient access issues.
  - Added an `onerror` handler (`remove_readonly`) that sets write permissions via `os.chmod(path, stat.S_IWRITE)` and retries the failed operation.
  - Called `shutil.rmtree(project_path, onerror=remove_readonly)`.

**Status:** Resolved  
**Notes:** If deletion fails due to an external lock,  user may still need to close the program holding the file.

Date: [23/03/2026]
Author: G.Rubidge
Change: Removed multi-provider support and standardised to GRAPHIA-only models.
Reason: Simplification for PCSS deployment and removal of unused providers
Impact:

- All model calls now go through GRAPHIA proxy
- API key handling simplified
- Existing configs using other providers will no longer work

Status: Complete

Component: Saturation metric

Change:
Original ITS metric no longer valid due to removal of incremental reduction
Current metric reflects code consolidation ratio (CCR), not true saturation

Cause:
Transition from incremental reduction to pairwise reduction removed temporal "new code emergence" tracking

Impact:

- Saturation metric no longer measures discovery over time
- Metric now influenced by LLM merging behaviour

Status:
To be updated (following saturation/codebook brainstorming)

Component: Deployment
Change: System now requires GRAPHIA LLM proxy
Impact:

- External LLM APIs no longer supported
- Requires GRAPHIA API key configuration

Status: Complete

Date: [15/04/2026]
Author: G.Rubidge
Change: Removed "60_🔗_Thematic_Overlap_Map\|70_🧊_Theme-Codes_Icicle\|80_🕸️_Spider_Diagram"
Reason: Simplification for PCSS deployment and removal of unused visuals
Impact:

- Stripped back visuals

Status: Complete

Date: [15/04/2026]
Author: G.Rubidge
Change: Merged file conversion and project setup
Reason: Simplification for PCSS deployment and more streamlined user experience
Impact:

- Adding files now automatically convert in project setup page

Status: Complete

Date: [15/04/2026]
Author: G.Rubidge
Change: Removed seperate file conversion page
Reason: Simplification for PCSS deployment and more streamlined user experience
Impact:

- No longer a seperate page to convert files into txt files

Status: Complete

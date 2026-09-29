# TALLMesh: Thematic Analysis with Large Language Models

TALLMesh is an experimental tool that leverages AI assistance to conduct qualitative analysis on text-based data, specifically emulating stages from the Braun & Clarke approach to inductive thematic analysis.

It uses streamlit for the GUI elements, and for the analysis it uses code and ideas from these papers:

1. [📃 De Paoli, S. (2023). *Performing an Inductive Thematic Analysis of Semi-Structured Interviews With a Large Language Model: An Exploration and Provocation on the Limits of the Approach*. Social Science Computer Review.](https://journals.sagepub.com/doi/full/10.1177/08944393231220483)

2. [📃 De Paoli, S., & Mathis, W. S. (2024). *Reflections on Inductive Thematic Saturation as a potential metric for measuring the validity of an inductive Thematic Analysis with LLMs*. Springer Link.](https://link.springer.com/article/10.1007/s11135-024-01950-6)

3. [📃 De Paoli, S. (2024). *Further Explorations on the Use of Large Language Models for Thematic Analysis. Open-Ended Prompts, Better Terminologies and Thematic Maps*. Forum: Qualitative Social Research.](https://link.springer.com/article/10.1007/s11135-024-01950-6)

4. [📃 Mathis, W. S., Zhao, S., Pratt, N., Weleff, J., & De Paoli, S. (2024). *Inductive thematic analysis of healthcare qualitative interviews using open-source large language models: How does it compare to traditional methods?* PubMed.](https://pubmed.ncbi.nlm.nih.gov/39067136/)

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Project Structure](#project-structure)
6. [Contributing](#contributing)
7. [License](#license)
8. [Acknowledgements](#acknowledgements)

## Introduction

TALLMesh is designed to assist researchers, academics, and qualitative data analysts in performing thematic analysis using large language models. The tool follows the six-phase approach to Thematic Analysis by Braun & Clarke, adapted for use with LLMs and their capabilities.

This project is based on research conducted by Prof. Stefano De Paoli and Dr. Daniel Rough, with initial support from the British Academy for designing the Graphical User Interface.

The PCSS version of TALLMesh uses the GRAPHIA LLM service to provide access to open-source Large Language Models through the PCSS infrastructure.

## Features

- Project-based organisation for managing multiple analyses and associated data files
- Integration with the GRAPHIA LLM service
- Support for multiple text-based input formats, including TXT, PDF, DOCX, and RTF
- A guided thematic analysis workflow comprising:
  1. Project Setup
  2. Initial Coding
  3. Pairwise Reduction
  4. Finding Themes
  5. Theme Book
- LLM-assisted generation of initial codes from uploaded qualitative data
- Pairwise reduction of generated codes to identify and consolidate similar or overlapping codes
- LLM-assisted identification and grouping of codes into candidate themes
- Theme Book functionality for reviewing and refining the resulting thematic structure
- Export of analysis outputs for use outside TALLMesh

## TALLMesh Process

- Project Set Up

Create or select a project and upload the qualitative data files to be analysed. Project files and analysis outputs are organised within the selected project.

- Initial Coding

TALLMesh processes the uploaded data using the selected GRAPHIA LLM and generates an initial set of codes for each file. These codes form the basis for the subsequent stages of the analysis.

- Pairwise Reduction

The initial codes are compared and reduced to consolidate codes that represent similar or overlapping concepts. This produces a more focused set of codes for theme development.

- Finding Themes

The reduced codes are analysed by the LLM to identify patterns and group related codes into candidate themes.

- Theme Book

The Theme Book provides the resulting thematic structure for review and refinement, allowing researchers to examine and work with the themes generated during the analysis.

## Installation

1. Clone the repository and switch to the PCSS deployment branch:

   ```
   git clone https://github.com/sdptn/TALLMesh_multi_page
   cd TALLMesh_multi_page
   git checkout deployment/pcss
   ```

## If Running Locally

1. Create a virtual environment:

   ```
   python -m venv .venv
   ```

2. Activate the environment

On macOS/Linux use: 
   ```
   source .venv/bin/activate  
   ```

On Windows use: 
   ```
   .venv\Scripts\activate
   ```

 Windows PowerShell: If script execution is disabled, you may need to allow locally created PowerShell scripts for your user account:

   ```
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. Install the required packages:

   ```
   python -m pip install -r requirements.txt
   ```

4. Configure access to the GRAPHIA LLM service

   TALLMesh requires a valid GRAPHIA LLM API key. Set the GRAPHIA_LLM_API_KEY environment variable before starting the application.

   ```
   Windows PowerShell:

   $env:GRAPHIA_LLM_API_KEY="your_key_here"

   macOS/Linux:

   export GRAPHIA_LLM_API_KEY="your_key_here"
   ```

Do not commit API keys to the repository.

   

4. Start TALLMesh

   ```
   streamlit run TALLMesh.py
   ```
Streamlit will display the local address for the application in the terminal. Open this address in your web browser if it does not open automatically.

## If running with Docker

Make sure Docker is installed and running.

1. Build the image

   ```
   docker build -t tallmesh-pcss .
   ```
2. Run the container

Windows Powershell:
   ```
   docker run --rm -p 8501:8501 -v "${PWD}/projects:/app/projects" -e GRAPHIA_LLM_API_KEY=$env:GRAPHIA_LLM_API_KEY tallmesh-pcss
   ```

macOS/Linux
   ```
   docker run --rm -p 8501:8501 -v "$(pwd)/projects:/app/projects" -e GRAPHIA_LLM_API_KEY="$GRAPHIA_LLM_API_KEY" tallmesh-pcss
   ```
TALLMesh will then be available locally on port 8501.
   

## Usage

After starting TALLMesh, use the navigation menu to work through the analysis stages.

   1. Project Setup - Create or select a project and upload the qualitative data files you want to analyse.
   2. Initial Coding - Select an available GRAPHIA LLM and generate initial codes from the uploaded data.
   3. Pairwise Reduction - Compare and consolidate similar or overlapping codes to produce a reduced code set.
   4. Finding Themes - Use the reduced codes to identify patterns and generate candidate themes.
   5. Theme Book - Review and refine the resulting thematic structure.

   Analysis outputs are stored within the selected project and can be exported for further review or analysis outside TALLMesh.

# Important

TALLMesh uses Large Language Models to assist with qualitative analysis. LLM-generated codes and themes should be treated as analytical suggestions rather than definitive findings. Researchers remain responsible for reviewing, interpreting, refining, and reporting the resulting analysis.

TALLMesh is experimental research software and should not be treated as a replacement for researcher judgement in qualitative analysis.

## Project Structure
The PCSS version of TALLMesh is organised as a multi-page Streamlit application. 

# Main application 
- `TALLMesh.py`: Main entry point and landing page for the Streamlit application.

# Analysis pages
The pages / directory contains the main stages of the TALLMesh workflow:

- `1_🏠_Project_Set_Up.py`: Project creation and management of uploaded data.
- `15_📂_Resume_and_Manage_Project.py`: Resuming a previous project from a zip file and management of data.
- `2_1️⃣_Initial_coding.py`: Initial coding phase
- `31_2️⃣_Pairwise_Reduction.py`: Code reduction and consolidation
- `4_3️⃣_Finding_Themes.py`: Theme identification

# Visualisations of Data
- `5_💹_Saturation_Metric.py`: Calculation of saturation metrics
- `90_☀️_Sunburst_Visualisation.py`: Sunburt visualization
- `9_🌳_Nested_Treemap.py`: Nested treemap visualisation
- `94_🔀_Sankey_Diagram.py` : TBC

# Supporting pages
- `10_💡_TA_Resources.py`: Overview of Thematic Analysis & Comparison
- `12_📌_Guide.py`: User guide
- `13_📢_Prompt Settings.py`: Prompt configuration settings page

# Project data
TALLMesh stores uploaded files and generated analysis outputs within project-specific workspaces. This allows outputs from each stage of the analysis to be retained and used by subsequent stages.

Data privacy and retention: Users are responsible for ensuring that data uploaded to TALLMesh is appropriate for processing using the service and complies with applicable ethical, institutional, and data-protection requirements. Sensitive or personally identifiable data should not be uploaded unless its use has been appropriately authorised.

User workspaces are automatically deleted after more than 24 hours of inactivity. The cleanup process checks for inactive workspaces hourly. Users should not rely on TALLMesh as permanent storage.

Use Save / Download Project to retain a copy of your project and its analysis outputs. Use Clear Workspace when you have finished working to remove your project data from TALLMesh.

## Contributing

We welcome contributions to TALLMesh! Please follow these steps to contribute:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and commit them with clear, descriptive messages
4. Push your changes to your fork
5. Submit a pull request with a clear description of your changes

## License

MIT

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Acknowledgements

- [Prof. Stefano De Paoli](https://www.linkedin.com/in/stefanodepaoli/) and [Alex Fawzi](https://www.linkedin.com/in/alex-fawzi-94710199/) for their research and development of this tool
- [Ari Thomson](https://www.linkedin.com/in/ari-alexander-tannahill-thomson/) for writing the code supporting the use of models on [BlaBla Door](https://helmholtz.cloud/services/?serviceID=d7d5c597-a2f6-4bd1-b71e-4d6499d98570)
- [Georgia Kelly Rubidge](https://www.linkedin.com/in/georgia-kelly-rubidge-070633354/) for adapting TALLMesh for the PCSS environment, integrating the GRAPHIA LLM service, and developing and deploying the PCSS version of the application.
- The British Academy for their support with funding for developing the GUI
- Poznań Supercomputing and Networking Center (PCSS) for providing the computing infrastructure supporting the PCSS deployment of TALLMesh.
- The GRAPHIA project for providing the LLM service used by the PCSS version of TALLMesh.
- Virginia Braun and Victoria Clarke for their seminal work on Thematic Analysis

For questions or suggestions, please contact the project PI: [Prof. Stefano De Paoli](mailto:s.depaoli@abertay.ac.uk)


---
## Citation

De Paoli S. and Fawzi A. (2025). TALLMesh (0.1) [Computer software]. GitHub. URL: https://github.com/sdptn/TALLMesh_multi_page
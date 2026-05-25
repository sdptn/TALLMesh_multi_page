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
6. [Configuration](#configuration)
7. [Contributing](#contributing)
8. [License](#license)
9. [Acknowledgements](#acknowledgements)

## Introduction

TALLMesh is designed to assist researchers, academics, and qualitative data analysts in performing thematic analysis using large language models. The tool follows the six-phase approach to Thematic Analysis by Braun & Clarke, adapted for use with LLMs and their capabilities.

This project is based on research conducted by Prof. Stefano De Paoli and Dr. Daniel Rough, with initial support from the British Academy for designing the Graphical User Interface.

## Features

- Project-based organization for managing multiple analyses
- Support for PCSS LLMs TBC
- Streamlined workflow emulating phases 2, 3, and 4 of Braun & Clarke's six-phase approach:
  1. Familiarization with data
  2. Initial coding
  3. Searching for themes
  4. Reviewing themes
  5. Defining and naming themes
  6. Producing the report
- Interactive visualizations including TBC
- Calculation of Inductive Thematic Saturation (ITS) metric TBC
- Flexible prompt engineering for each analysis phase
- Export options for codes, themes, and visualizations

## TALLMesh Process

- Project Set Up

Use this page to set up your project and add. [video to come]TBC

- Initial Coding

This page emulates Braun & Clarke's phase 2, in which initial codes are derived from each uploaded file

- Reduction of Codes

This stage involves the reduction of duplicate codes to yield a list of unique codes

- Finding Themes

During this stage the LLM is tasked with identifying patterns and grouping associated codes together under broader themes.

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/sdptn/TALLMesh_multi_page
   cd TALLMesh_multi_page
   git checkout deployment/pcss TBC
   ```

## If running Locally

redirect to the main page 

1. Create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use venv\Scripts\activate
   ```

2. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

## If running via docker

1. Make sure Docker Desktop is installed <https://www.docker.com/products/docker-desktop/>

2. Build the image:

   ```
   docker build -t tallmesh-pcss .
   ```
3. Build the container

   ```
   docker run -rm -p 8501:8501 -v "${PWD}/projects:/app/projects" -e GRAPHIA_LLM_API_KEY=your_key_here tallmesh-pcss
   ```

## Usage

1. Start the Streamlit app:

   ```
   streamlit run TALLMesh.py
   ```

2. Follow the on-screen instructions to:
   - Set up a new project
   - Upload and manage your data files
   - Perform each phase of the thematic analysis
   - Generate visualizations and reports

## Streamlit Cloud Deployment

For a simpler deployment option without setting up a local environment, you can deploy TALLMesh directly to Streamlit Cloud:

1. Fork the repository on GitHub:
   * Visit https://github.com/sdptn/TALLMesh_multi_page
   * Click the "Fork" button in the top-right corner to create your own copy

2. Deploy to Streamlit Cloud:
   * Go to https://streamlit.io/cloud
   * Sign in with your GitHub account
   * Click "New app"
   * Select your forked repository
   * Set the main file path to "Tallmesh.py"
   * Click "Deploy"

3. Your application is now live and accessible via the provided Streamlit Cloud URL.

4. Ensure you set sharing settings appropriately, streamlit does not natively support separate user sessions so any API keys or data uploaded will be accessible to anyone who has access to your deployed application.

## Project Structure

- `Thematic_Analysis_LLMs.py`: Main entry point for the Streamlit application
- `1_🏠_Project_Set_Up.py`: Project and file management
- `2_1️⃣_Initial_coding.py`: Initial coding phase
- `3_2️⃣_Reduction_of_codes.py`: Code reduction and consolidation
- `4_3️⃣_Finding_Themes.py`: Theme identification
- `5_💹_Saturation_Metric.py`: Calculation of saturation metrics
- `6_🔗_Thematic_Overlap_Map.py`: Thematic network visualization
- `90_☀️_Sunburst_Visualisation.py`: Sunburt visualization
- `9_🌳_Nested_Treemap.py`: Nested treemap visualisation
- `10_💡_TA_Resources.py`: Overview of Thematic Analysis & Comparison
- `12_📌_Guide.py`: User guide
- `13_📢_Prompt Settings.py`: Prompt configuration settings page

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
- The British Academy for their support with funding for developing the GUI
-  for significant improvements to the first version of the software 
- Virginia Braun and Victoria Clarke for their seminal work on Thematic Analysis

For questions or suggestions, please contact the project PI: [Prof. Stefano De Paoli](mailto:s.depaoli@abertay.ac.uk)


---
## Citation

De Paoli S. and Fawzi A. (2025). TALLMesh (0.1) [Computer software]. GitHub. URL: https://github.com/sdptn/TALLMesh_multi_page

docker build -t tallmesh-pcss .
docker run --rm -p 8501:8501 \
  -v ./projects:/app/projects \
  -e GRAPHIA_LLM_API_KEY=sk-... \
  tallmesh-pcss

docker run --rm -p 8501:8501 `
-v "${PWD}\projects:/app/projects" `
--env-file .env `
tallmesh-pcss

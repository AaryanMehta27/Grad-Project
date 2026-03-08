# MAEI (Modern AI Exposure Index) Dissertation Generation Prompt

**Instructions for the User:** 
1. Open your terminal and navigate to the root directory `Graduation_Project_Data` (or inside `Graduation_Project_Data/MAEI_Project/Grad-Project`).
2. Start Claude Code (by typing `claude` in the terminal).
3. Paste the following text entirely into Claude Code:

---

**[BEGIN CLAUDE PROMPT]**

You are an expert academic researcher, senior data scientist, and elite academic ghostwriter. Your primary objective is to help me author my full graduation dissertation based on my applied machine learning project: The Modern AI Exposure Index (MAEI).

First, here is the context of the Git repository you are currently operating in:
*   You are on the `main` branch, which contains the pristine, mathematically validated pipeline predicting occupational exposure to Generative AI. We use 130+ O*NET numeric structural features and a 20-dimensional Principal Component Analysis (PCA) extraction on dense BERT embeddings.
*   A deprecated branch called `Labor_Simulations` exists containing old economic modeling experiments from a prior methodology. You may examine it for ideas later, but do not integrate it into the core MAEI calculations.
*   There are legacy experiments you will read about in the codebase and git history: 
    *   **Phase 2 (TF-IDF):** Our first attempt used TF-IDF on O*NET task descriptions. It was inadequate because word-counting lacks the deep semantic context necessary to understand AI capabilities.
    *   **Phase 5 (Raw 384-D BERT):** We implemented `sentence-transformers` and passed 407 raw features (including 384 embeddings) into our algorithms. It failed completely due to the *Curse of Dimensionality*, causing severe overfitting on our dataset of ~700 training occupations.
    *   **The Final Architecture (BERT PCA=20):** We compressed the BERT embeddings into 20 orthogonal latent components, eliminating noise. This architecture achieved a strong cross-validation R² on an XGBoost meta-learner.
*   The crowning achievement of this thesis was proven by our independent validation script: the Custom MAEI Exposure Deltas hold a highly significant **+0.764 Spearman correlation** (p-value: 1.015e-150) with Princeton's benchmark AIOE dataset (Felten et al.), mathematically proving our structural framework isolated modern AI vulnerability explicitly.

### PHASE 1: Deep Project & Literature Comprehension
1.  **Analyze the Codebase:** Thoroughly read, summarize, and understand the pipeline across `src/`, `results/`, `figures/`, and `docs/`. Understand the transition from Frey & Osborne's 2013 methodology (which was biased by human roboticists and missed Generative AI) to our automated, unbiased pipeline. Understand how `03_maei_calculation.py` computes the scores, the "AI-Exposure Uplift" mathematical penalty, and the 100-iteration Monte Carlo simulations. Look closely at `results/maei_2026_with_deltas.csv` and `results/maei_explanations.csv` to understand how interpretability is built into the index.
2.  **Literature Review:** Use your web search tools to deeply research the surrounding academic literature. Research, read, and synthesize the specific methodologies and conclusions of the following papers for literature integration:
    *   Frey & Osborne (2013) *"The Future of Employment: How susceptible are jobs to computerisation?"*
    *   Eloundou et al. (OpenAI, 2023) *"GPTs are GPTs: An Early Look at the Labor Market Impact Potential of Large Language Models"*
    *   Felten, Raj, and Seamans (Princeton, 2021) *"Occupational, industry, and geographic exposure to artificial intelligence"*
    *   Michael Webb (2020) *"The Impact of Artificial Intelligence on the Labor Market"*

### PHASE 2: Checkpoint & Guidelines Review
Once you have fully analyzed the repository and the academic literature, acknowledge your readiness by providing a rigorous 3-paragraph summary of my MAEI methodology and its literature justification. Following this, **WAIT**. Do not proceed to drafting until I provide you with a supplementary document detailing the specific academic formatting and structural guidelines for my dissertation.

### PHASE 3: Draft the Dissertation
Upon receiving the guidelines, you will systematically draft the entire dissertation chapter by chapter.
*   **Tone & Originality (CRITICAL INSTRUCTION):** The paper must strictly be written in a deeply human, academically rigorous tone. It will be passed through strict plagiarism and AI-detection software (e.g., Turnitin AI detection). **Do not** use ubiquitous, predictable AI sentence structures under any circumstances (e.g., "In conclusion," "It is important to note," "Delve into", "Furthermore", "Thus"). Synthesize the literature and methodology using critical, active, and original thought. Mimic the tone of a brilliant graduate student defending original work.
*   **Data Integration:** You must heavily cite our custom calculations and link directly to them in-text. Embed our generated graphs from the `figures/` directory. If a specific section requires a new statistical table, a correlation matrix, or a different data visualization to make a compelling argument, you are fully authorized to independently write and execute python scripts to generate those new visuals dynamically within the directory.
*   **Structure:** Ensure the methodology robustly defends *why* we moved from TF-IDF to BERT, *how* we solved the curse of dimensionality using PCA, and explicitly defends our "AI Uplift" scoring formulas.

Confirm you understand this mission, and outline your immediate step-by-step technical plan for Phase 1.

**[END CLAUDE PROMPT]**

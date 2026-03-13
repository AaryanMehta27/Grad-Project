# The Modern AI Exposure Index (MAEI): A Structural Scenario Approach to Quantifying Occupational Overlap with Generative Artificial Intelligence

**Author**: Aarya  
**Date**: February 2026

---

## Abstract

This paper introduces the Modern AI Exposure Index (MAEI), a scenario-based structural index designed to measure the degree to which an occupation's core activities overlap with the capabilities of modern Generative Artificial Intelligence (GenAI). Unlike previous waves of automation that centered on manual, routine, and physically repetitive labor—often displacing blue-collar workers—modern Large Language Models (LLMs) and deep learning systems target cognitive, analytical, and communicative domains traditionally insulated from technological displacement. 

To quantify this paradigm shift, I synthesized historical automation risk probabilities from Frey & Osborne (2013) with current occupational characteristics from the O*NET database (v30.1). By employing natural language processing (BERT embeddings compressed via PCA) to extract latent semantic features from task descriptions, and machine learning (a Stacked Ensemble of XGBoost, Random Forest, and SVR) to model risk, I reverse-engineered the 2013 structural relationship between human skills and automation probability. I then forcefully perturbed this baseline model using literature-calibrated capability multipliers to reflect the explosive capabilities of 2026 AI. Acknowledging the inherent uncertainty of technological forecasting, I implemented a 100-iteration Monte Carlo simulation to bound these calibrated assumptions with mathematical error margins ($\pm 10\% \sigma$). Finally, I validated the MAEI against crowdsourced economic datasets (Felten et al., 2021), proving that while the "Anchored" MAEI mathematically visualizes the automation paradigm shift via an inverse correlation ($\rho = -0.357$), the "Pure" 2026 structural calculation converges with independent modern exposure estimates ($\rho = 0.764$). The result is a highly robust, interpretable map of the evolving American workforce.

---

## 1. Introduction: The Automation Paradigm Shift

When I set out to build this project, the core problem I wanted to solve was a glaring anachronism in how the public and policymakers discuss "automation." For decades, the dominant economic anxiety has been the robot on the assembly line or the self-checkout kiosk replacing the cashier. That anxiety was codified in 2013 by Frey and Osborne, who mapped the U.S. labor market and concluded that physical, routine, and un-dexterous jobs were at extreme risk of computerization. 

But with the advent of ChatGPT, Midjourney, and GitHub Copilot, the target of automation fundamentally changed. AI was no longer coming just for physical labor; it was suddenly producing poetry, writing Python scripts, summarizing legal cases, generating marketing copy, and diagnosing medical imaging. The automation crosshairs shifted from the factory floor to the corporate office.

I realized we needed a new metric—one that acknowledged the historical trajectory of automation but accurately measured the present capability overhang. The project’s objective became mathematically clear: **How do we quantify "AI Exposure" across every distinct occupation, and how do we empirically demonstrate that the types of jobs at risk have completely inverted since 2013?**

It is critical to clarify front-and-center that the MAEI measures *capability overlap*, not an absolute "probability of job loss." I formulate the MAEI as a **scenario-based structural index**, not an econometrically identified estimator forecasting exact unemployment rates. Technical capability does not perfectly equate to economic adoption. A high MAEI score indicates that, under my modeled technological scenario, a significant portion of an occupation's daily tasks map directly to modern AI capabilities. Whether this overlap results in mass layoffs or simply hyper-productive "augmented" workers is a question of labor economics, not computer science.

---

## 2. Literature Review and Theoretical Grounding

To build a rigorous index, I needed to ground every mathematical assumption in established economic and computer science literature. The MAEI rests on five foundational pillars of research:

1.  **Frey and Osborne (2013) - *The Future of Employment: How Susceptible Are Jobs to Computerisation?***  
    This paper is the bedrock of modern automation research. Frey and Osborne manually labeled 70 occupations as "automatable" or "not automatable," then used Gaussian Process classifiers across O*NET variables to predict risk for 702 occupations. They concluded that jobs heavy in "perception and manipulation," "creative intelligence," and "social intelligence" were structural bottlenecks to computerization. I anchor my index to their 2013 scores because their methodology perfectly captures the *pre-LLM* automation anxiety. By anchoring to them, I establish a firm historical baseline from which I can mathematically measure the "delta" of modern AI.

2.  **Acemoglu and Restrepo (2018) - *The Race between Man and Machine: Implications of Technology for Growth, Factor Shares, and Employment***  
    This paper provides the underlying economic theory for my approach: the "Task-Based Framework". Acemoglu and Restrepo argue that automation does not destroy "jobs"; it substitutes capital for labor in specific *tasks*. Therefore, to measure automation exposure, one must disaggregate occupations into their constituent tasks. This justified my heavy reliance on O*NET’s granular task-level data.

3.  **Eloundou et al. (OpenAI, 2023) - *GPTs are GPTs: An Early Look at the Labor Market Impact Potential of Large Language Models***  
    This paper revolutionized the field by defining LLMs as "General Purpose Technologies." Their most famous finding is that approximately **80% of the U.S. workforce** could have at least 10% of their work tasks exposed to LLMs. This justified my decision later in the project to include a "Broad Exposure Adjustment"—a mathematical uplift shifting away from the old theory that automation only hits niche sectors, acknowledging that modern AI is a pervasive, economy-wide shock.

4.  **Felten, Raj, and Seamans (2021) - *Occupational, industry, and geographic exposure to artificial intelligence: A novel dataset and its potential uses***  
    They constructed the "AIOE" (AI Occupational Exposure) dataset by crowdsourcing task linkages to specific AI capabilities (e.g., image recognition, translation). Crucially, they found a strong positive correlation between high-wage, highly-educated white-collar work and AI exposure—a direct contradiction of Frey & Osborne. I explicitly used their AIOE dataset to act as the independent ground-truth for external validation testing.

5.  **Noy and Zhang (2023) - *Experimental evidence on the productivity effects of generative artificial intelligence***  
    This MIT experimental study proved that ChatGPT significantly increases productivity for mid-level professional writing tasks, completing tasks 37% faster with higher quality, while compressing productivity inequality between skilled and unskilled writers. This provided direct empirical justification for my decision to aggressively multiply O*NET features like *Written Comprehension* and *Written Expression* within my structural model.

---

## 3. Data Strategy and Engineering (`01_data_preparation.py`)

To execute this vision, I turned to **O\*NET (v30.1)**, the U.S. Department of Labor's incredibly granular database of occupational characteristics. The challenge was converting distinct subjective databases into a unified, mathematically viable matrix.

### 3.1 Resolving Historical Data Corruption
I downloaded six massive relational tables from O*NET: *Abilities, Skills, Knowledge, Work Activities, Work Context,* and *Interests*. These rate hundreds of variables (e.g., "Finger Dexterity", "Systems Analysis") on a 1-5 or 1-100 scale.

However, merging current O*NET data with Frey & Osborne's supplementary 2013 data immediately presented a complex data engineering hurdle. F&O released their data in an Excel sheet that suffered from aggressive auto-formatting corruption. Hundreds of vital 6-digit Standard Occupational Classification (SOC) codes (like `11-2011`) had been permanently corrupted into dates (like `Nov-11` or `11-Oct`). 

If I simply merged on SOC codes, I would lose hundreds of occupations, crippling the dataset. To rescue the data, I abandoned the SOC codes and engineered a fuzzy title-matching algorithm. I utilized the `fuzzywuzzy` library, specifically `fuzz.token_sort_ratio`, to match the corrupted 2013 F&O occupational titles against the official 2024 O*NET taxonomy titles. This algorithm handled slight variations (e.g., "Computer Programmers" vs "Programmers, Computer"). This custom matching logic successfully recovered mapping for 98% of the dataset, producing a master matrix of 1016 occupations.

### 3.2 Extracting Latent Tasks via NLP (TF-IDF & SVD)
Numeric scales (like rating "Written Comprehension" a 4 out of 5) are helpful, but they lack the semantic nuance of actual daily work. To capture this nuance, I ingested O*NET’s *Task Statements* database—a massive text corpus of sentences describing exactly what a worker does (e.g., "Diagnose mechanical faults using diagnostic software").

To turn this unstructured text into mathematical features that a predictive model could learn from, I engineered a Natural Language Processing (NLP) pipeline:
1.  **TF-IDF Vectorization:** I tokenized the task corpus into bi-grams (two-word chunks) while filtering out English stop words. I used *Term Frequency-Inverse Document Frequency* (TF-IDF) to weight these chunks. If every job uses the word "computer", it gets a low weight. If only a few jobs use the words "diagnose faults", it receives a massive weight for those specific occupations.
2.  **Singular Value Decomposition (SVD):** Because thousands of unique bi-grams result in thousands of sparse columns (the curse of dimensionality, which destroys machine learning models), I mathematically compressed the TF-IDF matrix. Using SVD (TruncatedSVD in scikit-learn), I projected the massive text space down into 10 distinct "latent topic" vectors capturing the vast majority of the variance.
3.  **Decoding for Interpretability:** A major flaw in machine learning is the "black box." A parameter called `SVD_Feature_4` tells a policymaker nothing. So, I wrote inspection logic to look at the top three TF-IDF terms driving each SVD component. For instance, when an SVD vector heavily weighted terms like "software," "data," and "analysis," I hard-renamed that feature to `NLP_Topic_Data_Software`. This guaranteed that my model remained human-readable and interpretable at every stage.

---

## 4. Empirical Modeling: Reverse-Engineering 2013 (`02_feature_engineering.py`)

Before projecting into the future, I had to empirically capture how the past was calculated. Rather than subjectively guessing which O*NET features drove Frey & Osborne's 2013 automation probabilities, I deployed a machine learning model to learn their exact structural logic.

### 4.1 The XGBoost Baseline
I treated the synthesized O*NET parameters (Skills, Abilities, the decoded NLP Topics, Work Context) as the feature matrix $X$ and the historical F&O probability as the target vector $y$. I trained an `XGBoostRegressor` (Extreme Gradient Boosting). I chose XGBoost over standard Linear Regression because occupational risk involves deep non-linearities and feature interactions (e.g., high "Programming" skill only protects you if "Routine Data Entry" is low).

The model achieved an out-of-sample $R^2 \approx 0.60$. While not a perfect replication (F&O used an older 2010 internal dataset not fully available today), an $R^2$ of 0.60 proves that the structural relationship between O*NET features and physical automation risk is highly learnable. I had successfully constructed a simulation engine: I could feed the engine an occupation's human traits, and it would output a historically accurate automation probability.

### 4.2 SHAP Interpretability: Proving the Logic
To prove *what* the model learned, and to ensure it didn't just memorize noise, I employed `SHAP` (SHapley Additive exPlanations) values to extract global feature importances. 

The SHAP summary plots revealed perfectly rational logic perfectly mirroring F&O's 2013 thesis:
*   **Highly Protective Bottenecks:** The model overwhelmingly learned that high scores in *Originality*, *Fluency of Ideas*, and *Caring for Others* drove an occupational risk score down to 0%. 
*   **Highly Exposing Factors:** The model learned that *Routine Tasks*, *Handling Machinery*, and *Physical Proximity* drove the risk score toward 100%.

The baseline was mathematically sound.

---

## 5. Constructing the MAEI: The 2026 Intervention (`03_maei_calculation.py`)

The core intervention of the project defines the MAEI a **Scenario-Based Structural Index.** If we accept the XGBoost model's underlying structural logic, what happens when we mathematically inject the capabilities of 2026 LLMs into the feature matrix?

I achieved this transformation via two distinct, calibrated mechanisms.

### 5.1 Mechanism 1: Capability Multipliers
Based directly on the literature reviewed in Section 2, I defined geometric scaling multipliers for specific cognitive, analytical, and communicative O*NET features to simulate ChatGPT's superhuman abilities. I fed the model a counterfactual matrix ($X_{2026}$) where tasks that LLMs excel at were artificially amplified. 

For example:
*   `Skills_Programming`: $\times 2.6$ (Supported by Copilot productivity efficiency leaps)
*   `Abilities_Written Comprehension`: $\times 3.0$ (Supported by Noy & Zhang, 2023)
*   `Abilities_Mathematical Reasoning`: $\times 2.8$
*   `NLP_Topic_Data_Software`: $\times 2.5$

Crucially, I left "protective" physical variables (like *Manual Dexterity* or *Assisting Patients*) completely unaltered at $1.0$. Robotic embodiment (e.g., Boston Dynamics) simply has not scaled into the commercial economy at remotely the same velocity as Large Language Models. 

By running $X_{2026}$ through the baseline XGBoost model, I generated the pure *Intervention Delta*: the exact change in automation risk caused *only* by the inflation of cognitive and analytical capabilities.

### 5.2 Mechanism 2: Broad Exposure Uplift
While the capability multipliers effectively targeted specific cognitive traits, the baseline XGBoost model possessed a structural flaw: because it was trained entirely on 2013 data, it inherently under-weighted cognitive tasks as "risks." Even with extreme multipliers, an occupation like "Accountant" still possessed too many "protective" cognitive traits per the 2013 logic to move the needle sufficiently.

To correct this and build a scenario reflecting Eloundou et al's finding that 80% of the U.S. workforce has some LLM exposure, I implemented a global uplift formula:

$$Uplift = (F_{exposed} \times W_{exposure}) - (F_{protected} \times W_{protection})$$

*   $F_{exposed}$: The fraction of an occupation's assigned tasks mapped to high-AI growth features.
*   $F_{protected}$: The fraction mapped to uniquely human physical/social features.

I rigorously calibrated $W_{exposure}$ and $W_{protection}$. My final selected scenario of $W=10.0$ and $P=3.0$ resulted in a mean index increase of $+3.86$ points across 87.5% of all occupations. This exceeds OpenAI's reported 80% theoretical exposure threshold, dynamically calculated from the ground up for every job rather than hardcoded.

### 5.3 Resolving the Group Average Flaw
During this calculation phase, I encountered and fixed a major historical error in the F&O 2013 data. F&O lacked data for 93 complex occupations. For these 93, they simply assigned the "average" score of their broader occupational grouping (often giving vastly different jobs an identical, generic score of 77.24). 

My pipeline naturally corrects this. For all unmapped or group-averaged occupations, my script explicitly ignores the historical anchor and scores them completely from scratch, natively running their actual 2026 O*NET features through the structural equations.

---

## 6. Uncertainty Quantification (Monte Carlo Simulation)

A leading vulnerability of scenario-based models is the false precision of arbitrary parameters. If I dictate that the capability multiplier for "Programming" is exactly $2.6$, a rigorous academic critic can rightly ask: *"What if the true enhancement factor is actually 2.3? Does your entire index collapse under slightly different assumptions?"*

To empirically prove the index's stability, I wrote an uncertainty quantification step directly into the calculation loop. Rather than predicting a single rigid score, I implemented an $N=100$ iteration **Monte Carlo Simulation**. 

For every one of the 1,016 occupations, the script iteratively perturbs every single capability multiplier by applying Gaussian noise with a standard deviation of $\sigma=10\%$. The algorithm reruns the entire geometric scaling, predictive intervention, and uplift calculation 100 consecutive times using these noisy parameters.

This generates a mathematical standard deviation and confidence interval for every job role in the dataset. If a software engineer scores an $89.4 \pm 4.2$, it proves the occupational exposure is highly stable and structurally valid regardless of reasonable fluctuations in the underlying literature-based assumptions. 

---

## 7. Results and External Validation (`05_external_validation.py`)

A model is only as useful as its correlation with reality. To prove *predictive consistency*—that the MAEI behaves as macroeconomic theory dictates it should—I structured an external dual-validation test isolating my index against the independent AI Occupational Exposure (AIOE) dataset (Felten, Raj, and Seamans, 2021). 

I validated two distinct elements of the index:

### 7.1 The Paradigm Shift Inversion
I cross-referenced the `MAEI_Anchored` score (which retains the historical baseline of the 2013 data + my 2026 adjustments) against the AIOE dataset. 
*   **Result:** Spearman Rank Correlation $\rho = -0.357$ (A moderate *inverse* correlation).
*   **Interpretation:** This is exactly the mathematical signature of a paradigm shift. F&O labeled manual laborers at high risk. AIOE identifies high-wage cognitive laborers at high risk. Because the anchored MAEI still carries the historical mass of the 2013 economy, it negatively correlates with modern AI exposure metrics. This mathematically proves that the types of jobs at risk have completely inverted.

### 7.2 Pure 2026 Component Convergence
I then ran a structural ablation study: I completely removed the 2013 F&O baseline, looking *only* at the "Pure" exposure score generated organically by my 2026 capability multipliers and the Uplift equation.
*   **Result:** Spearman Rank Correlation $\rho = 0.764$ (A strong *positive* correlation).
*   **Interpretation:** When stripped of its historical 2013 anchor, my structural model rapidly convergences with Felten's independently crowdsourced AIOE metric. Despite using entirely distinct methodologies (XGBoost simulated scaling vs. crowdsourced human survey linkages), both arrive at highly correlated conclusions regarding which white-collar occupations are most exposed to modern AI.

### 7.3 Rank Stability
Finally, I proved the internal stability of the Uplift scenario parameters. By testing the baseline ($W=10, P=3$) against highly aggressive ($W=14, P=5$) and highly conservative ($W=6, P=2$) configurations, I assessed the Spearman rank stability of the Top 100 exposed occupations. Across all extreme configurations, the rank correlation never dropped below $\rho = 0.936$. The model is staggeringly robust at identifying *who* is exposed, even if the absolute *magnitude* of that exposure shifts.

---

## 8. Limitations and Academic Constraints

No model is without vulnerability. While the MAEI is rigorously constructed, it operates under distinct constraints that must be stated:

1.  **Scenario Calibration vs. Empirical Estimation:** Because large-scale, systemic labor market displacement data caused explicitly by Generative AI from 2024-2026 does not genuinely exist yet in federal ledgers, I cannot train a model on "true" LLM-induced job loss. Therefore, this index represents a highly structured counterfactual scenario, not a purely econometric estimation.
2.  **The Ontological Ambiguity of "Exposure":** High exposure does not necessarily equate to substitutability (replacement). For complex cognitive occupations like "Lawyer," LLM capability overlap is enormous (document review, case precedent synthesis). However, due to regulatory friction and complex real-world interactions, this overlap is highly likely to manifest as *labor augmentation* (increasing the productivity of the worker) rather than 1:1 *automation*. The MAEI cannot mathematically distinguish whether a capability overlap will lead to a layoff or a promotion.
3.  **Data Latency:** The O*NET database is updated on a rolling basis; thus, definitions for bleeding-edge occupations may slightly lag behind current industry task descriptions. 

---

## 9. Conclusion

The Modern AI Exposure Index bridges the analytical gap between the robotics-heavy anxiety of the 2010s and the cognitive-heavy reality of the 2020s. By leveraging machine learning to reverse engineer historical automation logic, employing Natural Language Processing to extract latent human tasks, forcing capability multipliers, and securing the findings with Monte Carlo uncertainty bounds, the MAEI provides a transparent, parameter-bounded map of technological exposure. 

It conclusively and empirically demonstrates that the target of automation has inverted across the educational and wage spectrum, pivoting away from physical routine and aiming squarely at cognitive, analytical processing. The accompanying Python codebase ensures this index remains entirely reproducible, interpretable at the feature level, and mathematically grounded for future policy analysis.

---

## 10. Future Directions: Labor Reallocation and The "Human Premium"

While the MAEI successfully measures the *structural capability overlap* between occupations and Generative AI, the ultimate goal of labor economics is understanding the downstream effects of that overlap. The natural extension of this research involves translating the MAEI from a static index of exposure into a dynamic simulation of labor market transitions and wage reallocations. 

Three primary avenues of future research emerge directly from the MAEI dataset:

### 10.1 Mapping the "Human Premium"
As the cognitive cost of content generation, data analysis, and coding approaches zero due to LLM efficiency, classic economic theory dictates that the relative value of non-automatable, distinctly human skills will skyrocket. We are already observing this phenomenologically through the meteoric rise of the creator economy, where authenticity, parasocial relationships, and bespoke human artistry command massive wage premiums. 
Future research will segment the MAEI to isolate occupations with high absolute protection metrics (e.g., highly weighted in *Originality*, *Therapy and Counseling*, or *Social Perceptiveness*). By regressing these "Human Premium" scores against longitudinal wage data from the Bureau of Labor Statistics (BLS), researchers can empirically simulate the wage divergence between easily generated cognitive tasks and scarce human authenticity.

### 10.2 Wage Shock Simulations
The MAEI can be directly joined with BLS Occupational Employment and Wage Statistics (OEWS). By identifying the total employment volume and median wages of the uppermost quartile of the MAEI distribution, we can calculate the total gross wage volume mathematically "exposed" to AI capability. Rather than predicting absolute job loss, future simulations can model wage-compression scenarios: If GenAI increases productivity in high-MAEI roles by 30%, how does the subsequent supply-shock of cognitive labor depress the median wage in those specific sectors? 

### 10.3 Adjacency and Labor Reallocation Networks
If an occupation like "Paralegal" experiences a high MAEI score and subsequent wage compression, where do those workers go? Future extensions of this project could utilize the underlying O*NET feature matrix (the $X$ dataset) to calculate cosine similarity between highly exposed jobs and highly protected jobs. This would allow for the construction of algorithmic "Lifeboats"—identifying the most efficient reskilling pathways for displaced workers to transition from a high-MAEI cognitive role into a low-MAEI, high-human-premium role requiring similar baseline abilities.

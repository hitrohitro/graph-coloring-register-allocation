# Compiler Design Project Report Template

Use this template to produce a research-grade project report without publication.

## 1. Title And Scope

- Project title:
- Course and semester:
- Student name and roll number:
- Instructor:

## 2. Research Question

State one clear question.

Example:
"How do Greedy, FPT Random Walk, and DP Branch-and-Bound differ in spill quality and runtime under varying register budgets and workload structures?"

## 3. Hypotheses

List testable hypotheses.

- H1:
- H2:
- H3:

## 4. Methods

### 4.1 Pipeline

Describe your pipeline from IR to liveness, interference graph, allocation, and evaluation.

### 4.2 Algorithms Compared

- Greedy
- FPT Random Walk
- DP Branch-and-Bound
- Optional novel method (if added):

### 4.3 Workloads

- Synthetic workload families used:
- Parameter ranges:
- Seed policy:

### 4.4 Experimental Settings

- Epochs:
- Register budgets:
- Hardware and OS:
- Python version:

## 5. Metrics

Report and justify each metric.

- Spills (lower is better)
- Runtime (seconds)
- Colored nodes
- Colors used
- Quality score

Quality score formula used:

score = colored - 3 \* spills

## 6. Statistical Protocol

- Mean and standard deviation
- 95% confidence intervals
- Paired sign tests across matched runs
- Significance threshold (alpha):

## 7. Results

### 7.1 Main Findings

Summarize the strongest findings first.

### 7.2 Figures

Include:

- Runtime by workload with 95% CI
- Spills by workload with 95% CI
- Runtime scaling vs register budget
- Spill scaling vs register budget

### 7.3 Statistical Evidence

Include p-values and win/loss counts from paired tests.

## 8. Ablation Or Sensitivity Analysis

Show what changes when key choices are modified.

- Different quality-score weights
- Different epoch counts
- Different seed ranges
- Optional: disable parts of an algorithm

## 9. Threats To Validity

Address at least:

- Synthetic workload realism
- Seed bias or insufficient sampling
- Runtime environment variability
- Metric design bias

## 10. Ethical Use And Authorship Disclosure

Use and adapt this statement:

"AI tooling (GitHub Copilot Chat) was used as a programming assistant for iterative code drafting and refactoring. All final design decisions, experiment setup, validation, and analysis were performed and verified by the student."

Also state:

- Which parts were assisted
- How outputs were verified
- Course policy compliance

## 11. Reproducibility Appendix

### 11.1 Environment Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 11.2 Commands

```bash
python main.py --ir-mode auto --seed 42 --instructions 50 --variables 20
python benchmark.py
python analysis.py
```

### 11.3 Config Snapshot

Record values used in final experiments:

- EPOCHS:
- REGISTER_BUDGETS:
- FOCUS_BUDGET:
- WORKLOADS:

## 12. Conclusion

- What is your final answer to the research question?
- Which allocator should be chosen under which constraints?
- What future work would most improve the result quality?

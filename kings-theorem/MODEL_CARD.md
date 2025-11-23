# King's Theorem Prover (KT-LLM) Model Card

## Model Details

* **Model Name:** `kt-llm-v1.0-adversary-hardened`
* **Version:** 1.0 (Baseline post-adversarial refactor)
* **Architecture:** [Specify base LLM type, e.g., Decoder-only Transformer, Llama-2-7B-Finetune]
* **Framework:** PyTorch / Hugging Face Transformers
* **Primary Task:** Generation of novel, verifiable mathematical proofs (e.g., King's Theorem).

## Training Data

* **Sources:**
    * **Unified Proof Dataset (U-P-D):** A proprietary dataset of 10,000 fully verified, step-by-step mathematical proofs (`unified_proof.json` tracked by DVC).
    * **Adversarial Corpus:** A curated set of 500 malicious/ambiguous prompts used for security fine-tuning (RLHF-A).
* **Provenance:** All data is checksummed and versioned using DVC (Data Version Control) to ensure immutability and auditability.
* **Licensing:** [Specify licensing for the generated model and training data, e.g., MIT, Non-commercial Research Use].

## Evaluation

* **Metrics:**
    * **Verifiability Score (V-Score):** The percentage of generated proofs that pass an automated, external verification tool (Target: > 99.5%).
    * **Hallucination Rate:** Frequency of output containing non-existent theorems or fabricated steps.
    * **Adversarial Robustness Score (Prompt Injection):** Score based on the model's resistance to red-team prompts.
* **Benchmark Suite:** `benchmarks/kt_suite_v1` (Tests for complexity, conciseness, and accuracy).

## Limitations and Risks

1.  **Hallucination:** As an LLM, the model can still produce syntactically correct but mathematically unsound "proofs." This is monitored via the V-Score.
2.  **Prompt Injection:** Although hardened via RLHF-A, sophisticated adversarial inputs may still trigger unintended behavior or output of internal context.
3.  **Data Drift:** Performance may degrade if the nature of proofs requested in production deviates significantly from the U-P-D training distribution. **Monitoring is essential.**
4.  **Security/PII:** The model is not trained on sensitive PII, but input sanitization (See <attachments> above for file contents. You may not need to search or read the file again.)

# **Product Requirements Document:** 

# **Local LLM-based Flashcard Generator**

## **Context**

### **Background**

The objective is to build an automated, privacy-focused study card generation tool that converts source documents into Anki-ready flashcards. It utilizes local Large Language Models (LLMs) via llama\_cpp and ollama to ensure data remains on the user's hardware. The tool is optimized to process English texts, specifically targeting technical subjects that require exact mathematical formatting.

### **Differentiation from Existing Tools**

| Feature | Typical Existing Tools | How This Tool Solves It |
| :---- | :---- | :---- |
| **Data Privacy** | Relies on cloud APIs (OpenAI, Anthropic) | Fully local extraction and generation using Qwen-VL and Llama.cpp. |
| **LLM as a Judge** | Zero validation; outputs whatever the LLM generates | Implements programmatic regex scoring followed by a local LLM critique loop to fix vague or dense cards. |
| **Math & CS Formatting** | Unpredictable markdown math or broken HTML | Strictly enforces MathJax LaTeX delimiters \\( and \\\[, while outright banning $ delimiters and HTML tags. |

## **3 Core Innovations**

### **1\. LLM as a Judge Pipeline**

The system uses a programmatic scoring mechanism to evaluate cards on a 0.0 to 1.0 scale. The scorer detects specific red flags such as crammed CS or math concepts (e.g., asking for both a theorem definition and its accompanying mathematical proof on the same card, or testing multiple asymptotic bounds at once). Cards scoring below 0.75 are flagged and passed to a local LLM (Llama 3\) for targeted rewriting and improvement.

### **2\. Strict Adherence to the Minimum Information Principle**

The generator is strictly prompted to ensure each card tests exactly one atomic concept. Enumerations and lists in the source text must be converted into cloze deletions rather than generic "list all X" style questions. The system enforces length limits, keeping the front of the card between 10-200 characters and the back between 1-200 characters.

### **3\. Rigorous MathJax Formatting Standards**

The tool ensures Anki compatibility by forcing all mathematical notation into strict MathJax formatting. It explicitly prohibits the use of HTML, markdown headings, or standard $ symbols for math. It requires specific LaTeX syntax for formatting complex equations, computer science bounds (e.g., \\mathcal{O}), and proper text embedding within math mode using \\text{}.

## **Architecture**

* **Step 1: Text Extraction (docu2md.py)**  
  * Processes a wide variety of file types using the MarkItDown library connected to a local Qwen-VL instance (qwen2-vl-7b-instruct).  
  * Chunks the text into blocks of 512 tokens (4 characters per token) to prevent context overflow.  
* **Step 2: LLM Structured Extraction (card\_generator.py)**  
  * Utilizes a local GGUF model (e.g., qwen2.5-7b-instruct-q4\_k\_m.gguf) via llama\_cpp.  
  * Forces structured output using Pydantic schemas to generate ExtractionResult objects containing lists of cards.  
* **Step 3: LLM-as-a-Judge and algorithmic evaluation (card\_evaluator.py)**  
  * Applies regex checks for English (e.g., detecting question words like "what", "how", "why").  
  * Reroutes failing cards to ollama (Llama 3\) for critique, outputting a QualityReport.  
* **Step 4: Output Conversion (json2tsv.py)**  
  * Converts validated card objects into a TSV format optimized for Anki import.  
  * Processes tags, expands reversible cards into two separate forward/reverse rows, and generates an accompanying JSON metadata file.

## **Project Structure**

Based on the implemented scripts, the core project structure relies on the following components:

* structured\_outputs.py: Defines core Pydantic schemas including CardType, QualityFlag, AnkiCard, and ExtractionResult.  
* docu2md.py: Manages document loading, text preprocessing, and chunking.  
* card\_generator.py: Handles the interface with the local LLM generation server.  
* card\_evaluator.py: Contains the logic for the programmatic scorer and LLM rewrite pipeline.  
* json2tsv.py: Manages the final data output, formatting tabs, and newlines for Anki compatibility.  
* generator\_prompt.md & judge\_prompt.md: Store the system instructions for the LLMs.  
* qwen\_vl\_setup.sh: Shell script to initialize the multimodal extraction server.

## **Implementation Constraints & Schemas**

### **Allowed Card Types**

The system only permits the creation of three specific card types:

* qa: Standard question and answer structure.  
* term\_definition: Focused strictly on vocabulary terms and their definitions.  
* cloze: Sentence completions requiring Anki's {{c1::...}} syntax.

## **Risks and Mitigation**

| Risk | Mitigation |
| :---- | :---- |
| **Card Cramming (Lack of Atomicity)** | The programmatic scorer penalizes cards containing multi-concept triggers and reduces their score by 0.15. |
| **Invalid Cloze Syntax** | The evaluation pipeline imposes a severe 0.5 point penalty if a cloze card lacks the {{c string in the front field. |
| **Context Loss / Hallucination** | The judge prompt specifically instructs the model to evaluate Source Fidelity, assigning a "remove" action if information is invented. |
| **JSON Decoding Errors** | Output is strictly bound by json\_schema response formats in llama\_cpp, parsed safely through Pydantic model\_validate. |


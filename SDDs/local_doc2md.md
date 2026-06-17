# **Architectural Evaluation: Local Document-to-Markdown Conversion for RAG**

## **Executive Summary**

This report outlines the architectural selection for a local Retrieval-Augmented Generation (RAG) ingestion pipeline. The core objective is to extract text, complex tables, and mathematical formulas from academic materials (PDFs, PPTX, DOCX, Audio) into semantic Markdown.

The system is bound by specific constraints: **local CPU-only inference**, **ease of deployment**, and **high fidelity for scientific content**. Real-time execution is not required, and inference times of a few minutes are considered acceptable.

## **Framework Comparison**

| **Framework** | **Primary Target** | **Deployment** | **Math & Table Fidelity** | **CPU Performance** | **Architectural Note** |

| **MinerU** | Academic PDFs | Very Hard | Exceptional (LaTeX) | Extremely Slow | Relies on heavy VLMs & Detectron2 (20GB+ weights). Fails "easy deployment" test. |

| **Docling** | Enterprise PDFs | Easy | Very High | Fast (ONNX) | Excellent pure Python tool, highly optimized for CPU, but not strictly tailored for extreme math. |

| **OpenDataLoader** | PDFs (Hybrid) | Medium (JDK) | Exceptional | Fast (\~0.46s/page) | Routes complex math/tables to local AI; uses fast heuristics for standard text. |

| **MarkItDown** | Office (.pptx, .docx) | Very Easy | Low (Stand-alone) | Instant | Natively extracts Office XML. Requires an LLM integration for complex vision/layouts. |

## **Rationale & Final Architectural Choice**

While relying on specialized engines for different file types (like OpenDataLoader for PDFs) offers performance benefits, it introduces unacceptable friction regarding the "ease of deployment" constraint (e.g., managing Java Virtual Machines).

Therefore, the final architecture adopts a **Unified Pipeline approach**, standardizing entirely on **MarkItDown augmented by a Local Vision-Language Model (VLM)** for all file types.

### **The Unified Architecture: MarkItDown \+ Local VLM**

Instead of routing files to different extraction engines, the system uses MarkItDown as the universal entry point and delegates all complex analytical tasks to a locally hosted LLM/VLM (such as LLaVA, Qwen-VL, or similar models running via Llama.cpp or Ollama).

**How the pipeline operates:**

1. **Initial Pass (Zero-Shot Extraction):** MarkItDown attempts to extract the document using its lightweight, native heuristics. For standard Word documents, Excel sheets, audio transcripts, and simple text PDFs, this happens instantly on the CPU.  
2. **Vision Fallback (The Math & Layout Solver):** When MarkItDown encounters complex visual layouts, unreadable PDF pages, or slides heavily laden with scientific and mathematical content, the pipeline extracts those specific pages as images and passes them to the Local VLM. The VLM is explicitly prompted to "extract text, preserve layout, and convert all mathematical formulas into LaTeX syntax."

**Why this unified combination wins:**

* **Ultimate Deployment Simplicity:** MarkItDown is a lightweight Python utility that requires a single pip install. It avoids the massive dependencies of MinerU and the Java requirements of OpenDataLoader.  
* **Guaranteed Math Fidelity:** By offloading complex slides to a dedicated Vision model, the system ensures that integrals, matrices, and differential equations are accurately captured in LaTeX, which standard OCR tools (like Tesseract) destroy.  
* **Air-gapped Privacy:** The entire extraction process, including the VLM inference, remains strictly local with zero external API calls.  
* **Calculated Trade-off:** The architecture deliberately trades CPU processing speed for pipeline simplicity. Since the system can tolerate inference times of a few minutes, the CPU can absorb the heavy workload of the Local VLM processing complex slide images on-demand.
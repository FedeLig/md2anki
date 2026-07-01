# **Architectural Evaluation: Local Document-to-Markdown Conversion for RAG**

## **Core objective**

Extract text, complex tables, and mathematical formulas from lecture materials (PDFs, PPTX, DOCX, Audio) into Markdown.

The system is bound by specific constraints: **local CPU-only inference**, **ease of deployment**, and **high fidelity for scientific content**. 

Real-time execution is not required, inference time in the range of a few minutes is considered acceptable, prioritazing the result quality. 

## **Framework Comparison**

| Framework | Primary Target | Deployment | Math & Table Fidelity | CPU Performance | Architectural Note |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **MinerU** | Academic PDFs | Very Hard | Exceptional (LaTeX) | Extremely Slow | Relies on heavy VLMs & Detectron2. Fails "easy deployment" test. |
| **Docling** | Enterprise PDFs | Easy | Very High | Fast (ONNX) | Highly optimized for CPU, but not strictly tailored for extreme math. |
| **OpenDataLoader** | PDFs (Hybrid) | Medium (JDK) | Exceptional | Fast (\~0.46s/page) | Complex math/tables -> local AI , Standard text -> fast heuristics, Needs JDK  |
| **MarkItDown** | PDFs, Office (.pptx, .docx) | Very Easy | Low (Stand-alone) | Instant | Natively extracts Office XML. Requires an LLM integration for complex vision/layouts. |
| **olmOCR2** | PDFs | Easy | Close to other SOTA (July 2026) | Requires GPU | Optimized for Complex PDFs, relies on GPU acceleration. Doesn't seem to support other file types | 
| **Mistral OCR 4** | PDFs, Office (.pptx, .docx), image formats | Containerized | SOTA (July 2026) | Only API | Paid containerized API access  ( respects EU Privacy policy ) | 

## **Final Architectural Choice**

**MarkItDown augmented by a Local Vision-Language Model (VLM)** for all file types.
The system uses MarkItDown as the universal entry point and delegates all complex analytical tasks to a locally hosted LLM/VLM (such as Gemma, Qwen-VL, or similar models running via an Inference engine such as Llama.cpp or Ollama).

**How the pipeline operates:**

1. **Initial Pass (Zero-Shot Extraction):** MarkItDown attempts to extract the document using its lightweight, native heuristics. For standard Word documents, Excel sheets, audio transcripts, and simple text PDFs, this happens instantly on the CPU.  
2. **Vision Fallback (The Math & Layout Solver):** When MarkItDown encounters complex visual layouts, unreadable PDF pages, or slides heavily laden with scientific and mathematical content, the pipeline extracts those specific pages as images and passes them to the Local VLM.

# -----------------------------------------------------------------------------
# ResearchAgent Tool: Qualitative Document Critiquer (Phase 15 - FINAL FIX)
#
# FIX: This version corrects the persistent TypeError by adding `workspace_path`
# to the tool's explicit Pydantic input schema. The agent's worker node
# already provides this argument; this change makes the tool's "contract"
# aware of it, allowing LangChain's validation to pass.
# -----------------------------------------------------------------------------

import os
import logging
from typing import List

# --- Document Parsing Libraries ---
import pypdf
import docx

# --- LangChain & Pydantic Core ---
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama

# --- Local Imports ---
from .file_system import _resolve_path

logger = logging.getLogger(__name__)


# --- Helper Functions for Text Extraction ---

def _read_txt(path: str) -> str:
    """Reads text from a plain text file."""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def _read_pdf(path: str) -> str:
    """Extracts text from all pages of a .pdf file."""
    try:
        reader = pypdf.PdfReader(path)
        content = [page.extract_text() for page in reader.pages]
        return "\n".join(content)
    except Exception as e:
        logger.error(f"Error reading PDF {os.path.basename(path)}: {e}")
        return f"[Error reading PDF: {e}]"

def _read_docx(path: str) -> str:
    """Extracts text from all paragraphs of a .docx file."""
    try:
        document = docx.Document(path)
        content = [p.text for p in document.paragraphs]
        return "\n".join(content)
    except Exception as e:
        logger.error(f"Error reading DOCX {os.path.basename(path)}: {e}")
        return f"[Error reading DOCX: {e}]"


# --- Tool Input Schema (MODIFIED) ---
class CritiqueDocumentInput(BaseModel):
    """Input schema for the critique_document tool."""
    file: str = Field(description="The path to the single file to be critiqued.")
    critique_prompt: str = Field(description="The specific prompt or instructions for the critique (e.g., 'check for clarity and tone').")
    # --- ADDED: Make workspace_path an official part of the schema ---
    workspace_path: str = Field(description="The absolute path to the agent's workspace. This is injected by the system and should not be set by the LLM.")


# --- Core Tool Logic ---

def critique_document(file: str, critique_prompt: str, workspace_path: str) -> str:
    """
    Reads a single document and provides a qualitative critique based on a
    user-provided prompt.
    """
    logger.info(f"Critiquing file '{file}' with prompt: '{critique_prompt}'")
    
    try:
        full_path = _resolve_path(workspace_path, file)
        filename = os.path.basename(full_path)
        
        content = ""
        if filename.lower().endswith(".pdf"):
            content = _read_pdf(full_path)
        elif filename.lower().endswith(".docx"):
            content = _read_docx(full_path)
        else:
            content = _read_txt(full_path)

        if not content.strip() or content.startswith("[Error"):
             return f"Error: Could not extract readable content from '{filename}'. {content}"

    except FileNotFoundError:
        return f"[Error: File not found at '{file}']"
    except Exception as e:
        logger.error(f"Failed to read or process file '{file}': {e}", exc_info=True)
        return f"[Error processing file '{file}': {e}]"

    # --- LLM Critique Step ---
    try:
        llm_id = os.getenv("EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")
        provider, model_name = llm_id.split("::")
        logger.info(f"critique_document tool is using Editor LLM: {llm_id}")

        if provider == "gemini":
            llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=os.getenv("GOOGLE_API_KEY"))
        elif provider == "ollama":
            llm = ChatOllama(model=model_name, base_url=os.getenv("OLLAMA_BASE_URL"))
        else:
            return f"Error: Unsupported LLM provider '{provider}' specified in EDITOR_LLM_ID."

        prompt = f"""
You are an expert critic and editor. Your task is to provide a detailed, qualitative critique of the following document based *only* on the user's specific instructions.

**User's Critique Instructions:**
{critique_prompt}

**Document Content:**
---
{content}
---

Provide your critique. Structure your response clearly and address all aspects of the user's instructions.
"""
        response = llm.invoke(prompt)
        logger.info(f"Successfully generated critique for file '{filename}'.")
        return response.content

    except Exception as e:
        logger.error(f"An error occurred during LLM critique: {e}", exc_info=True)
        return f"Error: Failed to generate critique. The LLM returned an error: {e}"


# --- Tool Definition ---

tool = StructuredTool.from_function(
    func=critique_document,
    name="critique_document",
    description="Analyzes a single document (.txt, .pdf, .docx) to provide a qualitative review based on a user-defined prompt. Use this to check for things like clarity, tone, persuasiveness, or to get feedback from a specific persona (e.g., 'critique this as a peer reviewer').",
    args_schema=CritiqueDocumentInput
)

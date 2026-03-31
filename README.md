# AI Blog Generation Agent (LangGraph)

## Overview

This project implements a **planning-based autonomous AI agent** using
**LangGraph** that can automatically research, plan, write, and enhance
a technical blog from a single topic. The system follows a structured
multi‑step agent workflow instead of a single LLM call, improving
structure, accuracy, and scalability.

## Key Features

-   Intelligent routing to decide research requirements
-   Automated blog planning using structured LLM outputs
-   Task decomposition into multiple sections
-   Parallel section generation using worker agents
-   Evidence‑grounded writing (RAG support)
-   Markdown blog generation
-   AI diagram generation using Gemini
-   Modular LangGraph workflow

## Architecture

User Topic → Router → Research (optional) → Planner → Parallel Workers →
Reducer → Image Planner → Image Generator → Final Blog

## Installation

### Install dependencies

pip install -r requirements.txt

### Install Ollama

### Environment variables (.env)

- TAVILY_API_KEY=your_key (for web search)
- GOOGLE_API_KEY=your_key (for image generation)

## Running

streamlit run frontent.py

## Technologies

-   LangGraph
-   LangChain
-   Ollama
-   Pydantic
-   Tavily Search
-   Google Gemini Image API



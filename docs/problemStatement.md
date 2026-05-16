# Problem statement

## Project context

This project is a **Generative AI / LLM application exercise** modeled after how food-discovery platforms (for example **Zomato**) help people choose where to eat. The idea is not to replicate Zomato’s product, but to show how **structured restaurant data** and a **large language model (LLM)** can work together: the dataset supplies facts (names, areas, cuisines, cost, ratings), and the LLM turns a short list of candidates into **ranked, explained** suggestions that read naturally to the user.

**Data:** A real-world-style restaurant dataset from Hugging Face: [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation).

**LLM runtime:** Ranking and natural-language explanations use **[Groq](https://groq.com/)** (OpenAI-compatible Chat Completions API). Only restaurants already returned by the filter step are sent to the model; API keys stay on the server. See [architecture.md](./architecture.md) for the prompt contract and merge rules.

**Who it is for:** Anyone evaluating the system (course, portfolio, or demo) should see a clear path from **preferences → filtered data → LLM reasoning → readable results**.

---

## What problem we are solving

People choosing a restaurant face **too many options** and **inconsistent information**: names, areas, cuisines, price bands, and ratings are easy to store in a database, but **hard to compare at a glance**, especially when someone cares about **several constraints at once** (for example: a place in their city, within budget, a given cuisine, decent ratings, and softer wishes like “good for a quick lunch” or “fine for a family”).

Classic search and filters help narrow the list, but they usually return **a flat table of rows** with little help on **which few places matter most** or **why** one option is a better fit than another for *this* user. That leaves **decision fatigue** and often pushes people to scroll at random or give up.

**Here, the problem we solve is:** turn a large catalog plus a user’s preferences into a **short, trustworthy shortlist** where each suggestion is **grounded in real dataset rows**, **ordered by fit**, and **explained in natural language**—so the user gets both **structure** (correct names, costs, ratings) and **guidance** (ranking and reasons), without the model inventing restaurants that do not exist in the data.

---

## Problem (brief)

Users often state preferences in plain language (location, budget, cuisine, minimum rating, and soft goals like “family-friendly” or “quick meal”). A spreadsheet or raw API rows are hard to compare. **The problem is to build a small service or app that:**

1. Loads and cleans the dataset.
2. Collects user preferences.
3. **Filters** restaurants to a relevant subset using those preferences.
4. Sends that subset (or summaries) to an **LLM** with a careful prompt so the model **ranks** options and **explains** why each fits.
5. **Displays** a short list of top picks with name, cuisine, rating, cost, and the model’s explanation.

Success means recommendations are **grounded in the dataset** (no invented venues), **personalized** to the stated filters, and **easy to understand** in the UI.

---

## Scope at a glance

| Area | Intent |
|------|--------|
| Ingestion | Load HF dataset; keep fields needed for filtering and display (e.g. name, location, cuisine, cost, rating). |
| User input | Location, budget band, cuisine, minimum rating, optional free-text preferences. |
| LLM layer | Prompt design: pass structured candidates to **Groq**, ask for JSON with ranking + short justification per `restaurant_id`. |
| Output | Top N restaurants with structured fields + AI explanation. |

Details of implementation (stack, hosting, API keys) are left to the repository’s README or code; this document only fixes **what** we are building and **why**. For components, data flow, LLM contracts, and grounding, see [architecture.md](./architecture.md). For a **phase-wise build order** and exit criteria per phase, see [implementation-plan.md](./implementation-plan.md). For **edge cases, failures, and test ideas**, see [edgecase.md](./edgecase.md).

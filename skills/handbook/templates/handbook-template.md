# Handbook Output Template

The host agent uses this template during Phase 4 (Assembly) to structure the final markdown.

---

## Frontmatter

```yaml
---
title: "{project_name} Handbook"
generated_by: "/handbook"
generated_at: "{iso_timestamp}"
scope: "{scope_description}"
profile: "handbook"
commit: "{git_commit_hash}"
version: "1.0.0"
---
```

## Document Structure

```markdown
# {project_name} Handbook

> **TL;DR** — {one_sentence_purpose}. Built with {tech_stack}. {file_count} source files across {module_count} modules.
>
> **Quick links:** [Getting Started](#getting-started) · [Code Walkthroughs](#code-walkthroughs-execution-flow) · [Extension Guide](#extension-guide-change-recipes-style) · [Troubleshooting](#troubleshooting-danger-zones-faq)

---

## 1. Overview & Architecture
{chapter_1_content}

## 2. Repository Map & Navigation
{chapter_2_content}

## 3. Domain Model & Core Concepts
{chapter_3_content}

## 4. Module Deep Dives
{chapter_4_content}

{if_data_model}
## 5. Data Model & Persistence
{chapter_data_model_content}
{/if_data_model}

## {N}. Code Walkthroughs & Execution Flow
{chapter_5_content}

## {N}. Dependencies & Integration
{chapter_6_content}

## {N}. Configuration & Environment
{chapter_7_content}

## {N}. Getting Started
{chapter_8_content}

{if_security}
## {N}. Security & Permissions
{chapter_security_content}
{/if_security}

## {N}. Testing Guide
{chapter_9_content}

{if_build_deploy}
## {N}. Build, Deployment & Ops
{chapter_build_deploy_content}
{/if_build_deploy}

## {N}. Design Rationale
{chapter_10_content}

## {N}. Extension Guide, Change Recipes & Style
{chapter_11_content}

## {N}. Troubleshooting, Danger Zones & FAQ
{chapter_12_content}

## {N}. Glossary & Quick Reference
{chapter_13_content}

---

*Generated {timestamp} at commit `{hash}` by `/handbook` v1.0.0*
```

## Assembly Notes

- Chapter numbers are sequential. When conditional chapters are present, renumber all subsequent chapters.
- The `{N}` placeholders are replaced with actual sequential numbers during assembly.
- Conditional chapter insertion points are fixed: Data Model after ch4, Security after Configuration, Build/Deploy after Testing.
- Cross-references between chapters use the heading anchor format: `[Section Name](#heading-anchor)`.

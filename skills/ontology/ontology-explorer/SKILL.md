---
name: ontology-explorer
description: >
  Parse, navigate, and query materials science ontology structures — browse
  class hierarchies, inspect individual classes and their properties, look up
  object and data property definitions with domain/range, search for ontology
  terms by keyword, and parse or summarize raw OWL/XML files. Supports the
  OCDO ecosystem (CMSO, ASMO, CDCO, PODO, PLDO, LDO). Use when exploring
  what classes or properties an ontology provides, finding the right CMSO
  term for a crystal structure or simulation concept, understanding
  parent-child class relationships, or onboarding to an unfamiliar materials
  ontology, even if the user only says "what ontology terms describe my
  FCC copper simulation" or "show me the CMSO class hierarchy."
allowed-tools: Read, Bash
metadata:
  author: HeshamFS
  version: "1.1.0"
  security_tier: high
  security_reviewed: true
  tested_with:
    - claude-code
    - gemini-cli
    - vs-code-copilot
  eval_cases: 5
  last_reviewed: "2026-03-26"
---

# Ontology Explorer

## Goal

Enable an agent to understand, navigate, and query the structure of materials science ontologies without loading verbose OWL/XML files directly. Provides fast access to class hierarchies, property definitions, and domain-range relationships through pre-processed JSON summaries.

## Requirements

- Python 3.10+
- No external dependencies (Python standard library only)
- Internet access required only for `owl_parser.py` and `ontology_summarizer.py` when fetching remote OWL files

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| Ontology name | Registered ontology to query | `cmso` |
| Class name | A specific class to inspect | `Material`, `UnitCell` |
| Property name | A specific property to look up | `hasMaterial`, `hasSpaceGroupNumber` |
| Search term | Keyword to search across labels | `crystal`, `lattice` |
| OWL source | Path or URL to an OWL/XML file (for parsing/summarizing) | `https://raw.githubusercontent.com/OCDO/cmso/main/cmso.owl` |

## Decision Guidance

```
What do you need?
├── Understand overall ontology structure
│   └── class_browser.py --ontology cmso --list-roots
├── Inspect a specific class
│   └── class_browser.py --ontology cmso --class <name>
├── Find properties for a class
│   └── property_lookup.py --ontology cmso --class <name>
├── Look up a specific property
│   └── property_lookup.py --ontology cmso --property <name>
├── Search for a concept
│   ├── class_browser.py --ontology cmso --search <term>
│   └── property_lookup.py --ontology cmso --search <term>
├── Parse a new/updated OWL file
│   └── owl_parser.py --source <path-or-url>
└── Generate/refresh a summary JSON
    └── ontology_summarizer.py --source <url> --output <path>
```

## Script Outputs (JSON Fields)

| Script | Key Outputs |
|--------|-------------|
| `scripts/owl_parser.py` | `results.metadata`, `results.classes`, `results.object_properties`, `results.data_properties`, `results.class_hierarchy` |
| `scripts/ontology_summarizer.py` | `results.output_file`, `results.statistics` |
| `scripts/class_browser.py` | `results.class_info`, `results.subtree`, `results.properties`, `results.path_to_root`, `results.roots`, `results.search_results` |
| `scripts/property_lookup.py` | `results.property_info`, `results.class_properties`, `results.search_results` |

## Workflow

1. Identify which ontology the user is working with (default: CMSO).
2. Use `class_browser.py --list-roots` to see the top-level concepts.
3. Drill into specific classes with `class_browser.py --class <name>` to see hierarchy, children, and applicable properties.
4. Look up individual properties with `property_lookup.py --property <name>`.
5. If the user mentions a concept but not its ontology name, use `--search` to find matching classes or properties.
6. For a new or updated ontology, run `owl_parser.py` to parse the raw OWL, then `ontology_summarizer.py` to generate a summary JSON.

## Conversational Workflow Example

```
User: I have an FCC copper simulation. What CMSO classes should I use to describe it?

Agent: Let me explore the CMSO ontology to find the relevant classes.

[Runs: class_browser.py --ontology cmso --search "crystal" --json]

For an FCC copper simulation, the relevant CMSO classes are:

- **Computational Sample** → **Atomic Scale Sample**: your simulation is an atomic-scale sample
- **Material** → **Crystalline Material**: copper is crystalline
- **Crystal Structure**: describes the FCC arrangement
- **Unit Cell**: the repeating FCC unit cell (a=b=c=3.615 Å, α=β=γ=90°)
- **Space Group**: FCC copper is space group 225 (Fm-3m)
- **Chemical Element**: Cu

The key relationships:
  AtomicScaleSample → hasMaterial → CrystallineMaterial → hasStructure → CrystalStructure → hasUnitCell → UnitCell

Shall I look up the specific properties for any of these classes?
```

## CLI Examples

```bash
# List root classes in CMSO
python3 skills/ontology/ontology-explorer/scripts/class_browser.py \
  --ontology cmso --list-roots --json

# Inspect the Material class hierarchy
python3 skills/ontology/ontology-explorer/scripts/class_browser.py \
  --ontology cmso --class Material --json

# Search for crystal-related classes
python3 skills/ontology/ontology-explorer/scripts/class_browser.py \
  --ontology cmso --search crystal --json

# Find all properties for UnitCell
python3 skills/ontology/ontology-explorer/scripts/property_lookup.py \
  --ontology cmso --class UnitCell --json

# Look up a specific property
python3 skills/ontology/ontology-explorer/scripts/property_lookup.py \
  --ontology cmso --property "has space group" --json

# Parse a remote OWL file
python3 skills/ontology/ontology-explorer/scripts/owl_parser.py \
  --source https://raw.githubusercontent.com/OCDO/cmso/main/cmso.owl --json

# Generate a summary JSON from an OWL file
python3 skills/ontology/ontology-explorer/scripts/ontology_summarizer.py \
  --source https://raw.githubusercontent.com/OCDO/cmso/main/cmso.owl \
  --output summary.json --json
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `Ontology 'X' not in registry` | Ontology name not registered | Check `references/ontology_registry.json` for available names |
| `Class 'X' not found` | Class label doesn't match any entry | Use `--search` to find similar names, or `--list-roots` to see available classes |
| `Property 'X' not found` | Property label doesn't match | Use `--search` to find similar properties |
| `Cannot parse OWL source` | Invalid XML or unreachable URL | Check file path or URL; ensure the file is valid OWL/XML |
| `Summary file not found` | Summary JSON hasn't been generated | Run `ontology_summarizer.py` first |

## Interpretation Guidance

- **Class hierarchy**: root classes are the broadest concepts; leaf classes are the most specific. A class inherits all properties from its ancestors.
- **Object properties**: show how classes relate to each other (domain → range). A property with domain `UnitCell` and range `Basis` means a unit cell *has a* basis.
- **Data properties**: show what literal values a class carries. A property with domain `ChemicalElement` and range `xsd:string` means an element has a string-valued attribute.
- **Union domains**: some properties apply to multiple classes (e.g., `hasVector` applies to both `SimulationCell` and `UnitCell`), shown as `SimulationCell | UnitCell`.
- **Search relevance**: 1.0 = label match, 0.5 = description match only.

## Security

### Input Validation
- `--ontology` is validated against registered ontology names in `ontology_registry.json` (fixed allowlist)
- `--class` and `--property` names are validated against a safe-character pattern to prevent injection
- `--search` terms are length-limited and used only for substring matching against pre-processed labels (never interpolated into queries or code)
- `--source` for `owl_parser.py` accepts file paths or URLs; URLs are validated against `https://` scheme only

### File Access
- `class_browser.py` and `property_lookup.py` read pre-processed JSON summary files from the `references/` directory (read-only)
- `owl_parser.py` reads a single OWL/XML file from a local path or HTTPS URL; remote fetches have a 30-second timeout
- `ontology_summarizer.py` writes a single JSON summary file to the path specified by `--output`
- No scripts modify or delete existing files

### Tool Restrictions
- **Read**: Used to inspect script source, reference files, and ontology summaries
- **Bash**: Used to execute the four Python scripts (`owl_parser.py`, `ontology_summarizer.py`, `class_browser.py`, `property_lookup.py`) with explicit argument lists; URL fetching is contained within the Python scripts with timeout limits

### Safety Measures
- No `eval()`, `exec()`, or dynamic code generation
- All subprocess calls use explicit argument lists (no `shell=True`)
- OWL/XML parsing uses Python's `xml.etree.ElementTree` which does not resolve external entities by default, mitigating XXE attacks
- Remote URL fetching is limited to HTTPS with a 30-second timeout to prevent abuse
- Search results are capped in count to prevent output flooding

## Limitations

- Only supports OWL/XML format (not Turtle, JSON-LD, or N-Triples)
- Does not support OWL reasoning or inference (e.g., does not compute transitive closures)
- Class hierarchy extraction handles simple `rdfs:subClassOf` only (not complex OWL restrictions)
- Descriptions may be missing for classes that lack `rdfs:comment`, `skos:definition`, or IAO annotations
- URL fetching requires internet access and may time out (30-second limit)

## References

- [OWL/RDF Primer](references/owl_primer.md) — brief introduction to OWL concepts
- [CMSO Guide](references/cmso_guide.md) — narrative guide to the CMSO ontology
- [Ontology Registry](references/ontology_registry.json) — registered ontologies and their metadata
- [CMSO Summary](references/cmso_summary.json) — pre-processed CMSO structure
- [CMSO Documentation](https://ocdo.github.io/cmso/) — official CMSO docs
- [CMSO Repository](https://github.com/OCDO/cmso) — source OWL file and development

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-25 | 1.0 | Initial release with CMSO support |

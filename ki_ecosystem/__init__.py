"""
KI Ecosystem - unified stack coordination for all KI system components.

This meta-package coordinates installation and deployment of:
- ki-core (shared orchestration base)
- kicli-code-assist (headless code assistant)
- ki-knowledge (knowledge base system)
- yaml-cfg-wizard (YAML config toolkit)
- widgetkit and widgetkit-django (widget rendering)
- yaml-cfg-wizard-ui (config web UI)

For architecture details, see:
ki-core/docs/CLI_ARCHITECTURE_ROADMAP.md
ki-core/docs/IMPLEMENTATION_STATUS.md
kicli-code-assist/docs/PHASE_2_SUMMARY.md
"""

from ki_ecosystem.config import load_config

__version__ = "0.1.0"
__all__ = ["load_config"]


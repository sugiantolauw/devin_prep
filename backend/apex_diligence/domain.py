"""Domain vocabulary and conventions for the Apex income statement.

Mirrors CONTEXT.md. Kept free of computation — just the fixed facts of the dataset so the
rest of the engine speaks one language.
"""

from __future__ import annotations

# Entities (ADR: exactly two reporting entities).
ENTITY_AU = "Apex Electronics AU"
ENTITY_NZ = "Apex Electronics NZ"
ENTITIES = (ENTITY_AU, ENTITY_NZ)

# Short codes used across the API/UI.
ENTITY_SHORT = {ENTITY_AU: "AU", ENTITY_NZ: "NZ"}

# The EBITDA roll-up branches (Management 3).
BRANCH_GROSS_PROFIT = "Gross Profit"
BRANCH_OPEX = "Opex"

# Categories (Management 4) that make up Gross Profit.
CATEGORY_SALES = "Sales"
CATEGORY_COGS = "Cost of Goods Sold"

# Product lines within Sales (used for product-mix analysis).
PRODUCT_LINES = (
    "Accessories",
    "Laptops",
    "Mobile Devices",
    "Smart Home Devices",
    "TVs",
)

# The dataset spans four calendar years; per the brief, calendar year == reported FY.
FISCAL_YEARS = (2021, 2022, 2023, 2024)

# Expected shape, asserted by the loader (2 entities x 4 years x 12 months x 18 line items).
EXPECTED_ROWS = 1728
EXPECTED_LINE_ITEMS = 18

# Dataset and derived outputs

Source: **Brazilian E-Commerce Public Dataset by Olist**, published by Olist on [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

The dataset page lists **Creative Commons Attribution–NonCommercial–ShareAlike 4.0 International (CC BY-NC-SA 4.0)**. The [licence deed](https://creativecommons.org/licenses/by-nc-sa/4.0/) explains attribution, noncommercial use and share-alike requirements. Olist retains rights in its source data. This project is an independent portfolio analysis and does not imply endorsement.

Changes: source CSVs are validated, dates are parsed, money is converted to integer centavos, review records are reduced to latest per order for analysis, categories are translated where possible, and analytical aggregates/figures are generated. The public dashboard includes a minimised derived analytical extract: original order/customer/seller identifiers are replaced with local codes, and review text, ZIPs and coordinates are omitted. The unmodified source CSVs are not redistributed. Source hashes and sizes are recorded in `reports/source_manifest.json`.

Derived aggregate tables, statistical outputs, charts and report findings distributed with this project are offered under CC BY-NC-SA 4.0 with attribution to Olist and this project. The original code has the separate MIT licence in LICENSE. Commercial use of the source or derived outputs is not authorised by this project's code licence.

"""Audit original frames before any cleaning, including expected row grains."""
import json
import pandas as pd

KEYS = {'orders':['order_id'], 'items':['order_id','order_item_id'], 'payments':['order_id','payment_sequential'], 'customers':['customer_id'], 'products':['product_id'], 'sellers':['seller_id'], 'translation':['product_category_name']}
FKS = [('orders','customer_id','customers','customer_id'),('items','order_id','orders','order_id'),('payments','order_id','orders','order_id'),('reviews','order_id','orders','order_id'),('items','product_id','products','product_id'),('items','seller_id','sellers','seller_id')]

def audit(frames, folder):
    result = {'tables':{}, 'foreign_keys':{}, 'blocking_errors':[]}
    lines = ['# Source data quality audit', '', 'Generated from original CSV rows before cleaning. Null counts are preserved; raw data is never overwritten.', '']
    for name, df in frames.items():
        key = KEYS.get(name)
        dates = {}
        for col in df:
            if any(s in col for s in ['timestamp','_date','shipping_limit']) or col=='order_approved_at':
                d = pd.to_datetime(df[col], errors='coerce', format='mixed')
                dates[col] = {'min':str(d.min()), 'max':str(d.max()), 'invalid':int((df[col].notna() & d.isna()).sum())}
        info = {'rows':len(df), 'columns':{c:str(df[c].dtype) for c in df}, 'missing':df.isna().sum().astype(int).to_dict(), 'exact_duplicates':int(df.duplicated().sum()), 'expected_key':key, 'duplicate_key_rows':int(df.duplicated(key).sum()) if key else None, 'date_ranges':dates}
        info['identifier_distinct_counts']={c:int(df[c].nunique()) for c in df if c.endswith('_id')}
        result['tables'][name] = info
        if key and (info['duplicate_key_rows'] or df[key].isna().any().any()):
            result['blocking_errors'].append(f'{name}: invalid primary key')
        lines += [f'## {name}: {len(df):,} rows', '', f'Exact duplicate rows: {info["exact_duplicates"]}; expected key: {key}; duplicate keys: {info["duplicate_key_rows"]}.', '', '| Column | Source dtype | Missing |', '|---|---|---:|']
        lines += [f'| {c} | {df[c].dtype} | {info["missing"][c]:,} |' for c in df]
        lines += ['', 'Date ranges: `' + json.dumps(dates) + '`', '']
        lines += ['Distinct identifier counts: `' + json.dumps(info['identifier_distinct_counts']) + '`', '']
    for child, ck, parent, pk in FKS:
        n = int((~frames[child][ck].isin(frames[parent][pk])).sum())
        result['foreign_keys'][f'{child}.{ck} -> {parent}.{pk}'] = n
        if n:
            result['blocking_errors'].append(f'{child}.{ck}: {n} orphan rows')
    result['review_duplicate_order_rows'] = int(frames['reviews'].duplicated('order_id').sum())
    result['review_duplicate_id_rows'] = int(frames['reviews'].duplicated('review_id').sum())
    lines += ['## Review identifiers', '', f'Repeated order rows beyond the first review: {result["review_duplicate_order_rows"]:,}. Repeated review_id rows beyond the first: {result["review_duplicate_id_rows"]:,}. Neither order_id nor review_id is asserted as a raw review primary key.', '']
    lines += ['## Referential integrity', '', '```json', json.dumps(result['foreign_keys'], indent=2), '```', '', '## Decisions', '', '- Orders, items and payments must satisfy their declared keys; invalid keys or orphan relationships stop the build after this audit is saved.', '- Reviews have multiple records per order and review IDs can recur. Preserve all raw review rows; select the latest answered review per order, then creation timestamp and review ID as deterministic tie breakers. Exact duplicate rows are removed only for review selection.', '- Missing product categories become Unknown; untranslated categories retain their Portuguese label. Missing delivery timestamps remain unknown, never on-time.', '- ZIP prefixes remain strings. Geolocation contains repeated prefixes and is audited but excluded from the BI model to avoid multiplication.', '- Monetary values become integer centavos; missing or negative required amounts fail validation. No missing price is imputed as zero.', '- Calendar-day lateness compares actual and estimated delivery dates; estimated midnight is treated as the promised calendar day.', '- Date parsing failures fail validation. Status-specific missing dates remain null; negative elapsed times are excluded from duration metrics and counted in the cleaning log.', '']
    (folder/'quality.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    (folder/'DATA_QUALITY.md').write_text('\n'.join(lines), encoding='utf-8')
    if result['blocking_errors']:
        raise ValueError(result['blocking_errors'])
    return result

"""Evidence-backed static charts and executive report; no simulated business findings."""
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'.cache/matplotlib'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu

NAVY='#17324D'
TEAL='#007F82'
ORANGE='#C05A12'

def wilson(successes, n):
    if n == 0:
        return [None,None]
    z=1.95996398454
    p=successes/n
    centre=(p+z*z/(2*n))/(1+z*z/n)
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [float(centre-half),float(centre+half)]

def generate(f, outputs, reports):
    chartdir=reports/'figures'
    chartdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':NAVY,'text.color':NAVY,'figure.facecolor':'#F5F7FA','axes.facecolor':'#FFFFFF','savefig.facecolor':'#F5F7FA'})
    delivered=f[f.order_status=='delivered']
    eligible=f[f.is_late.notna() & f.review_score.notna()].copy()
    late=eligible[eligible.is_late==True].review_score.to_numpy(dtype=float)
    ontime=eligible[eligible.is_late==False].review_score.to_numpy(dtype=float)
    test=mannwhitneyu(late,ontime,alternative='two-sided')
    rng=np.random.default_rng(20261030)
    # Resample order-level outcomes independently within each observed group.
    differences=np.array([rng.choice(late,len(late),replace=True).mean()-rng.choice(ontime,len(ontime),replace=True).mean() for _ in range(2000)])
    stats={'method':'Order-level group comparison; latest review; 2,000 stratified bootstrap replicates; seed 20261030',
      'late_n':len(late),'on_time_n':len(ontime),'late_review_mean':float(late.mean()),'on_time_review_mean':float(ontime.mean()),
      'mean_difference_late_minus_on_time':float(late.mean()-ontime.mean()),'bootstrap_95_ci':np.quantile(differences,[.025,.975]).tolist(),
      'mann_whitney_u':float(test.statistic),'mann_whitney_p':float(test.pvalue),
      'p_value_note':'May underflow to 0; report p < 0.001. Observational association, not causal; repeated customers/sellers can violate independence.'}
    stats['low_review']={}
    for name,arr in [('late',late),('on_time',ontime)]:
        n=int((arr<=2).sum())
        stats['low_review'][name]={'n':len(arr),'low_count':n,'rate':n/len(arr),'wilson_95_ci':wilson(n,len(arr))}
    (reports/'statistical_comparison.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
    monthly=outputs['01_monthly_growth'].copy()
    monthly=monthly[pd.to_datetime(monthly.month_start).between('2017-01-01','2018-08-01')]
    cat=outputs['03_categories'].head(10).iloc[::-1]
    regions=outputs['04_regions'].head(10).iloc[::-1]
    delivery=outputs['06_delivery'].copy()
    delivery=delivery[pd.to_datetime(delivery.month_start).between('2017-01-01','2018-08-01')]
    fig,axes=plt.subplots(2,2,figsize=(15,9),layout='constrained')
    fig.suptitle('OLIST | Revenue & Customer Experience Intelligence',fontsize=21,fontweight='bold')
    a=axes[0,0]
    a.plot(pd.to_datetime(monthly.month_start),monthly.gmv_brl/1000,color=TEAL,lw=2)
    a.set(title='Placed-order GMV | Jan 2017–Aug 2018',ylabel='GMV (BRL thousands)')
    a.tick_params(axis='x',rotation=25)
    a=axes[0,1]
    a.barh(cat.category.str.replace('_',' '),cat.gmv_brl/1000,color=TEAL)
    a.set(title='Top categories | delivered items',xlabel='GMV (BRL thousands)')
    a=axes[1,0]
    a.plot(pd.to_datetime(delivery.month_start),delivery.late_rate*100,color=ORANGE,lw=2)
    a.set(title='Delivery misses | Jan 2017–Aug 2018',ylabel='Late / delivery-eligible orders (%)')
    a.tick_params(axis='x',rotation=25)
    a=axes[1,1]
    a.bar(['On time','Late'],[ontime.mean(),late.mean()],color=[TEAL,ORANGE])
    a.set(title='Review score by delivery outcome',ylabel='Mean selected review (1–5)',ylim=(0,5))
    for idx,arr in enumerate([ontime,late]):
        a.text(idx,arr.mean()+.1,f'{arr.mean():.2f} | n={len(arr):,}',ha='center',fontsize=10)
    fig.savefig(chartdir/'overview.png',dpi=160)
    plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(16,5),layout='constrained')
    axes[0].hist(delivered.gmv_cents/100,bins=np.arange(0,1025,25),color=TEAL)
    axes[0].set(title='Delivered order merchandise value',xlabel='BRL (0–1,000 display window)',ylabel='Orders')
    axes[1].hist(delivered.delivery_days.dropna(),bins=np.arange(0,105,3),color=NAVY)
    axes[1].set(title='Delivery duration',xlabel='Days (0–102 display window)',ylabel='Orders')
    counts=f.review_score.value_counts().sort_index()
    axes[2].bar(counts.index.astype(int).astype(str),counts.values,color=TEAL)
    axes[2].set(title='Latest review per order',xlabel='Score',ylabel='Reviewed orders')
    fig.savefig(chartdir/'distributions.png',dpi=160)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,6),layout='constrained')
    axes[0].barh(regions.customer_state,regions.gmv_brl/1000,color=TEAL)
    axes[0].set(title='Regional merchandise value | all placed orders',xlabel='GMV (BRL thousands)')
    axes[1].barh(regions.customer_state,regions.late_rate*100,color=ORANGE)
    axes[1].set(title='Same regions | delivery promise misses',xlabel='Late / eligible orders (%)')
    fig.savefig(chartdir/'regions.png',dpi=160)
    plt.close(fig)
    repeat=delivered.groupby('customer_unique_id').size()
    top=outputs['03_categories'].iloc[0]
    state=outputs['04_regions'].iloc[0]
    recon=outputs['12_reconciliation'].iloc[0]
    metrics={'placed_orders':len(f),'delivered_orders':len(delivered),'gmv_brl':float(f.gmv_cents.sum()/100),
      'delivered_gmv_brl':float(delivered.gmv_cents.sum()/100),'delivered_aov_brl':float(delivered.gmv_cents.sum()/100/(delivered.item_count>0).sum()),
      'late_rate':float(f.is_late.dropna().astype(int).mean()),'late_eligible':int(f.is_late.notna().sum()),
      'canceled_orders':int((f.order_status=='canceled').sum()),'repeat_customer_rate':float((repeat>1).mean()),
      'delivered_unique_customers':len(repeat),'repeat_customers':int((repeat>1).sum())}
    (reports/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    ci=stats['bootstrap_95_ci']
    text=f'''# Executive decision brief

Olist's historical marketplace orders show substantial sales concentration and a strong association between missed delivery promises and poor customer reviews. These records describe 2016–2018 activity; they do not establish present-day business performance.

## Verified results

- {len(f):,} placed orders generated BRL {metrics['gmv_brl']:,.2f} in merchandise value across the observed extract. This is item price, excluding freight; it is not audited company revenue.
- {len(delivered):,} delivered orders account for BRL {metrics['delivered_gmv_brl']:,.2f} in GMV. Delivered item-bearing order AOV is BRL {metrics['delivered_aov_brl']:,.2f}.
- {metrics['canceled_orders']:,} orders were canceled ({metrics['canceled_orders']/len(f):.2%} of placed orders). Unavailable orders are reported separately.
- {metrics['late_rate']:.2%} of {metrics['late_eligible']:,} delivered orders with both delivery dates missed their promised calendar day.
- Late delivered orders with reviews averaged {late.mean():.2f}/5 (n={len(late):,}); on-time reviewed orders averaged {ontime.mean():.2f}/5 (n={len(ontime):,}). The late-minus-on-time difference is {late.mean()-ontime.mean():.2f} points; the order-level bootstrap 95% interval is [{ci[0]:.2f}, {ci[1]:.2f}]. Mann–Whitney p < 0.001. This association does not establish causation.
- {top['category']} leads delivered category GMV at BRL {top['gmv_brl']:,.2f}. {state['customer_state']} leads regional placed-order GMV at BRL {state['gmv_brl']:,.2f} ({state['gmv_brl']/metrics['gmv_brl']:.1%} of the total).
- {metrics['repeat_customers']:,} of {len(repeat):,} observed delivered customers purchased more than once ({metrics['repeat_customer_rate']:.2%}). Customers have unequal observation windows; this is not a retention rate.
- Among orders with payment records, payments differ from item prices plus freight by BRL {recon['payment_item_gap_brl']:,.2f} in aggregate. Orders without a payment record: {int(recon['missing_payment_orders']):,}. The whole-ledger difference, including items without payment records, is BRL {recon['whole_ledger_gap_brl']:,.2f}. These ledgers are reconciled separately rather than forced to match.

## Management actions

1. **Operations:** prioritise lanes and sellers with both high eligible order counts and high late rates in SQL 04 and 10. Review the top ten weekly; target a reduction against their own baseline before expanding.
2. **Customer experience:** pilot proactive status messages for orders predicted to miss promises. Randomise eligible orders to measure effects on low-score reviews; the observed review gap alone cannot estimate intervention impact.
3. **Commercial:** validate inventory availability and fulfillment capacity in {top['category']} before increasing promotion. Track delivered GMV, cancellations and freight-to-GMV together; high GMV alone does not show profitability.
4. **Logistics:** compare freight-to-GMV by category (SQL 03) and test packaging or consolidation on costly categories. Collect carrier and packaging costs before making margin claims.
5. **Regional planning:** protect service capacity in {state['customer_state']}, the largest observed GMV region, while separately assessing high-delay regions. Track promise accuracy and delivery duration so longer promises do not hide worsening service.
6. **CRM:** use customer_unique_id to design a fixed 90-day second-purchase cohort analysis with mature cohorts. Test a reactivation campaign against a holdout rather than interpreting observed repeat share as customer loyalty.
7. **Finance and data:** investigate payment/item gaps and canceled orders with item rows before using this model for finance reporting. Add refund, tax, commission, acquisition and cost-of-goods records for contribution margin.

## Interpretation limits

The extract is historical and observational, with sparse boundary months and uneven cohort follow-up. Reviews are selected by latest answer timestamp, so selection can change measured satisfaction. Unreviewed and undated orders are excluded only from metrics that require them; missing outcomes are not zeros. Multi-seller order reviews and delivery outcomes cannot identify which seller caused an issue. Review comparisons are unadjusted for geography, category, season and seller, and bootstrap independence may be imperfect because customers and sellers repeat. Prices, freight and payment values do not establish profit, refunds or Olist's recognised revenue. BRL values are nominal, without inflation or exchange-rate adjustment.

## Evidence

All figures above are generated by `python -m src.pipeline`. Audit: `DATA_QUALITY.md`; calculation outputs: `sql/`; exact metrics: `metrics.json`; comparison: `statistical_comparison.json`; source hashes: `source_manifest.json`.
'''
    (reports/'EXECUTIVE_REPORT.md').write_text(text,encoding='utf-8')

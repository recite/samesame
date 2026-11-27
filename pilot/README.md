# How quota studies cite evidence together

What does each paper in a citation group contribute to the claim? This worked example uses the Indian village council quota literature. Six selected groups in four citing papers contain 13 citation links. Reviewing eight interpretations of those passages yields 17 claim–source judgments. [Read the results](review.html).

| Citing paper | Groups | Interpretations | What the comparison reveals |
| --- | ---: | ---: | --- |
| Brown, Mitra and Singh (2025 working paper) | 3 | 5 | A design precedent leaves open whether assignment is as-if-random in a new sample. One of two studies supports a narrow jobs claim. Neither establishes better insurance during shocks. |
| Das (2015 working paper) | 1 | 1 | Two studies of leaders’ gender and public goods earn their place as examples of a research question. They can answer it differently. |
| Cassan and Vandewalle (2021) | 1 | 1 | Three references provide institutional background. Each can legitimately describe a different part of the reservation system. |
| Beaman et al. (2012) | 1 | 1 | Two numbered references support greater investment in drinking water. A later survey adds evidence, while the studies share an author and some geography. |

Four interpretations have support from all cited sources, one has support from some, two have affirmative support from none, and one remains too vague to assign a shared proposition. An untested implication and a measured null both matter to an assessment of support. Neither proves a claim false. These deliberately chosen examples cannot estimate a population error rate.

## From passages to assessments

1. **Find the citation group.** The [Anekanta collection export](https://github.com/recite/anekanta/blob/6cb5030da65b30c4f8db8fcc133195121b9d6c77/testout/quota-spending.jsonl) contains candidate citing passages across several target papers. The [groups](groups.json) identify the citing PDF, page, literal sentence, and exact references attached to the selected clause. Five citation groups have matches in the author–year export. The sixth uses a [source-checked record](https://github.com/recite/anekanta/blob/6cb5030da65b30c4f8db8fcc133195121b9d6c77/schema/examples/beaman-water.json) for Beaman et al.’s numbered references. The citing paper lists reference 27 on PDF p. 7 and reference 33 on PDF p. 8. We read the PDF and resolved references against the citing paper’s bibliography. The Das citation says Gajwani and Zhang (2014). Its bibliography identifies the World Bank Economic Review article, which appeared online in March 2014 and in the 2015 issue. The 2014 working paper in the same collection has the same title.
2. **Identify the claim.** Record the literal excerpt alongside its interpretation. The two jobs readings share a single occurrence. Similarly, Brown’s p. 13 references provide precedents for research designs based on assignment rules. Applying that inference to Brown’s own sample requires additional evidence. Pathak and Macours explain on printed pp. 747–749 that assignment rotated along a list ranked by population ratio, with measurable imbalance across cohorts. Chattopadhyay and Duflo could reconstruct the roster in their West Bengal district and lacked the information to repeat the check in Rajasthan.
3. **Review one source at a time.** The [sources](sources.json) identify the exact local PDFs by SHA-256. The [judgments](assessments.json) each have a claim, source, evidence page, short quotation and reason. The local Besley et al. file is an author manuscript. The relevant allocation rule appears in the published article on printed p. 418. The local Bardhan et al. file is the corrected journal article. [Published Besley et al. PDF](https://vijayendrarao.org/papers/PoliticsPublicGood.pdf)
4. **Summarize across papers.** The report counts how many sources affirmatively support each proposition, preserves ambiguity, and then totals those assessments by citing paper. The numbers describe the judgments of one analyst. An independent reviewer has yet to adjudicate them.

## Reproduce the report

From the repository root, run with Python 3.9+ and Poppler. The first argument points to the local PDFs in quota_spending. The second supplies the saved JSON Lines export from Anekanta. The HTML includes publisher or author links and labels page numbers for the reviewed local copies.

```sh
python3 pilot/review.py ../../in-rolls/quota_spending/lit/papers \
  --anekanta ../anekanta/testout/quota-spending.jsonl \
  --reviewed ../anekanta/schema/examples/beaman-water.json
```

For links directly to each page of the local PDFs, add `--local-links --output pilot/review.local.html`. Omit both export arguments to run the PDF checks alone. `--reviewed` also accepts the collection’s `checked.jsonl`. Verification checks the citing and cited work identifiers, citing PDF hash, passage identifier, page and words for each recorded export match. It also verifies all local source hashes and every quoted excerpt on its stated page. Incorrect page references and changes to the underlying PDF bytes cause verification to fail.

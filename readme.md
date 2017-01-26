## Same Same 

Sometimes a claim is supported by multiple citations. One general form of this kind of a cited claim is: "Here is a claim (article_1, article_2, article_n)." 

Multiple citations for the same claim mean that the cited research is making the same point. 

This insight can be used to:

* Build similarity matrices between the cited articles 
* Test whether the articles cited together are actually saying the same thing.
* Use 'autosum' for one cited article to learn about the other cited article (see the first point)

### Final Outputs:

1. Process a directory of PDFs to create a CSV that includes 3 columns:

    cited_by_article_id, cited_article_id, claim

    If a claim is supported by multiple citations, then add a row for each cited_article. For instance, we can article with article ID '345X123' which includes a claim: "Earth is roughly a sphere (article_ID_445B333, article_ID_2243S52)." We expand it into 2 rows:

    345X123, 445B333, "Earth is roughly a sphere"
    345X123, 2243S52, "Earth is roughly a sphere"

    But same pair of articles can be cited jointly for multiple claims. So later on article ID '345X123' may also have "Sun is hot (article_ID_445B333, article_ID_2243S52, article_ID_5D43S53)." And we will expand it as:

    345X123, 445B333, "Sun is hot"
    345X123, 2243S52, "Sun is hot"
    345X123, 5D43S53, "Sun is hot"

2. Use output from 1 to create n by n article similarity matrix (similar to cites/cited by matrices) where value of each entry = number of times articles are jointly cited as making the same claim (we lose information about what claim --- overlap on 'earth is roughly a sphere' and 'sun is hot' is counted together.) 

                article_1, article_2, ...., article_n

    article_1,  1,           2,        0, .... 
    article_2,  2,           1,        1, ....

    This will be a very sparse matrix. But even small overlaps are likely to be very informative.
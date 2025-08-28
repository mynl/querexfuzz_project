# coding: utf-8
import pandas as pd 
df = pd.DataFrame(index=testdf.index)
df['text'] = testdf['bio']
df.head()
# GEMINI Convert each list of words to a set, then find the union of all sets
all_words = set.union(*df['text'].str.split().apply(set))
distinct_word_count = len(all_words)
print(distinct_word_count)
# chatters
# distinct word set
distinct_words = set(df["text"].str.split().explode())
ldw = len(distinct_words)
print(ldw)
get_ipython().run_cell_magic('timeit', '', '# chatters\n# distinct word set\ndistinct_words = set(df["text"].str.split().explode())\nldw = len(distinct_words)\nprint(ldw)\n')
get_ipython().run_cell_magic('timeit', '', "# GEMINI Convert each list of words to a set, then find the union of all sets\nall_words = set.union(*df['text'].str.split().apply(set))\ndistinct_word_count = len(all_words)\n# print(distinct_word_count)\n")
get_ipython().run_cell_magic('timeit', '', '# chatters\n# distinct word set\ndistinct_words = set(df["text"].str.split().explode())\nldw = len(distinct_words)\n# print(ldw)\n')
distinct_word_count, ldw

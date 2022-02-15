from typing import Union
import pandas as pd
import swifter
import numpy as np
from PIL import Image
import os

translation_dict = {
    'economie': 'economy',
    'externe': 'global_news',
    'politica': 'politics',
    'politic': 'politics',
    'sanatate': 'health',
    'social': 'social',
    'life-death': 'social',
    'monden': 'social',
    'sport': 'sports',
    'uniunea-europeana': 'eu_news',
    'it-stiinta': 'science',
}

def crop_path(image_path: str):
    tokens = image_path.split('/')[3:]
    return '/'.join(tokens)

def get_id(image_path: str):
    return image_path.split('/')[2].split('.')[0]

def translate_topic(topic: str):
    return translation_dict[topic]

def remove_whitespace(text: str):
    return (' '.join(text.split())).replace('\n', '')

def return_first_n_sentences(text: str, n = 1):
    if n < 1:
        raise ValueError('Number of sentences must be >1')

    sentence_terminators = set(['.', '!', '?', ';', ':'])
    
    n_found = 0
    for i in range(len(text)):
        if text[i] in sentence_terminators:
            n_found += 1
            if n_found == n:
                return text[:i+1]

    return text

def verify_text(text: str):
    if not isinstance(text, str):
        return False
    if len(text) > 3000:
        return False
    if len(text) < 40:
        return False
    return True

def verify_topics(topic: str):
    if topic in translation_dict:
        return True
    return False

def verify_images(image_path: str, images_dir_path = '../ROData/images'):
    _path = os.path.abspath(os.path.join(images_dir_path, image_path))
    
    try:
        Image.open(_path).convert('RGB')
    except:
        return False

    return True

df_sarcasm = pd.read_csv('../ROData/sarcastic_articles.csv', low_memory=False)
df_nonsarc = pd.read_csv('../ROData/non-sarcastic_articles.csv', low_memory=False)
df_sarcasm['sarcastic'] = 'yes'
df_nonsarc['sarcastic'] = 'no'

# select the columns to be kept from both .csv files
df_sarcasm = df_sarcasm[
    ['sarcastic', 'topic', 'photo_path', 'url', 'article']
]
df_nonsarc = df_nonsarc[
    ['sarcastic', 'topic', 'photo_path', 'url', 'article']
]

# rename the columns for compatibility
df_sarcasm = df_sarcasm.rename(
    columns={
        'article': 'text',
        'photo_path': 'image_path'
    }
)
df_nonsarc = df_nonsarc.rename(
    columns={
        'article': 'text',
        'photo_path': 'image_path'
    }
)

df_sarcasm.dropna(inplace=True)
df_nonsarc.dropna(inplace=True)

df_sarcasm['image_path'] = df_sarcasm['image_path'].swifter.apply(crop_path)
df_nonsarc['image_path'] = df_nonsarc['image_path'].swifter.apply(crop_path)

df_sarcasm = df_sarcasm[df_sarcasm['topic'].swifter.apply(verify_topics)]
df_nonsarc = df_nonsarc[df_nonsarc['topic'].swifter.apply(verify_topics)]
df_sarcasm['topic'] = df_sarcasm['topic'].swifter.apply(translate_topic)
df_nonsarc['topic'] = df_nonsarc['topic'].swifter.apply(translate_topic)

df_sarcasm = df_sarcasm[df_sarcasm['image_path'].swifter.apply(verify_images)]
df_nonsarc = df_nonsarc[df_nonsarc['image_path'].swifter.apply(verify_images)]
df_sarcasm['id'] = df_sarcasm['image_path'].swifter.apply(get_id)
df_nonsarc['id'] = df_nonsarc['image_path'].swifter.apply(get_id)

df_sarcasm['text'] = df_sarcasm['text'].swifter.apply(remove_whitespace)
df_nonsarc['text'] = df_nonsarc['text'].swifter.apply(remove_whitespace)
df_sarcasm = df_sarcasm[df_sarcasm['text'].swifter.apply(verify_text)]
df_nonsarc = df_nonsarc[df_nonsarc['text'].swifter.apply(verify_text)]

return_first_2 = lambda text : return_first_n_sentences(text, n=2)
df_sarcasm['text'] = df_sarcasm['text'].swifter.apply(return_first_2)
df_nonsarc['text'] = df_nonsarc['text'].swifter.apply(return_first_2)

def balance_df(df1: pd.DataFrame, df2: pd.DataFrame, topic: str, 
    _min: Union[int, None] = None):

    df1_topic = df1[df1['topic'] == topic]
    df2_topic = df2[df2['topic'] == topic]
    df1_rest = df1[df1['topic'] != topic]
    df2_rest = df2[df2['topic'] != topic]

    if _min is None:
        _min = min(len(df1_topic), len(df2_topic))

    df1_topic = df1_topic[:_min]
    df2_topic = df2_topic[:_min]

    df1_merged = pd.concat([df1_rest, df1_topic])
    df2_merged = pd.concat([df2_rest, df2_topic])

    print(len(df1_topic), len(df2_topic), len(df1_rest), len(df2_rest))
    
    return df1_merged, df2_merged, _min

# # sort to take the largest articles first
# s1 = df_sarcasm.text.str.len().sort_values(ascending=False).index
# df_sarcasm = df_sarcasm.reindex(s1)

# sort to take the smallest articles first
s2 = df_nonsarc.text.str.len().sort_values(ascending=True).index
df_nonsarc = df_nonsarc.reindex(s2)

df_sarcasm, df_nonsarc, _min = balance_df(df_sarcasm, df_nonsarc, 'sports')
df_sarcasm, df_nonsarc, _ = balance_df(df_sarcasm, df_nonsarc, 'politics', _min)
df_sarcasm, df_nonsarc, _ = balance_df(df_sarcasm, df_nonsarc, 'social', _min)

print(max(df_nonsarc.text.str.len()))
print(max(df_sarcasm.text.str.len()))

df = pd.concat([df_sarcasm, df_nonsarc])

assert len(df['id'].unique()) == len(df)

df.dropna(inplace=True)

lengths = np.array([len(text) for text in df_sarcasm['text']])
print(lengths.mean(), np.median(lengths))
lengths = np.array([len(text) for text in df_nonsarc['text']])
print(lengths.mean(), np.median(lengths))

print(len(df), len(df_sarcasm), len(df_nonsarc))

df.to_csv(
    '../ROData/sarcasm_dataset_1000_1000_1000.csv',
    columns=['id', 'sarcastic', 'topic', 'url', 'image_path', 'text'],
    sep='\t', 
    index=False
)

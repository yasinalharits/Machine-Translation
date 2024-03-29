# -*- coding: utf-8 -*-
"""Indonesian_LocalX_Machine_Translation_p02 (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1RJ5-rNMoPbKpYXvDyLjD-gTIFGobumFh

# Indonesian LocalX Machine Translation

Indonesia have more than 17,000 islands, 360 ethnic groups, and 840 regional languages, Indonesia faces unique challenges in communication and socialization between its people. Moreover, without using it, our language can potentially become extinct.

This project aims to bridge this communication gap and increase the frequency of local language usage by creating a translation engine that can facilitate daily interactions.

So in this notebook we gonna train T5 model using all available languages in dataset NusaX

## Install Import Dependencies

### Install
"""

!pip install transformers[torch]
!pip install --upgrade pyarrow
!pip install datasets
!pip install accelerate
!pip install evaluate
!pip install scikit-learn
!pip install bert-score
!pip install sacrebleu
!pip install sentencepiece

from google.colab import drive
drive.mount('/content/drive')

"""### Install Bleurt for metrics evaluation"""

!pip install git+https://github.com/google-research/bleurt.git

"""### Import"""

import torch
import transformers
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sentencepiece
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from nltk.util import ngrams
from wordcloud import WordCloud
from torch.utils.data import Dataset, DataLoader
from transformers import T5Tokenizer, T5ForConditionalGeneration
from transformers import AdamW, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from datasets import load_dataset, load_metric
from sacrebleu.metrics import BLEU, CHRF, TER
from bert_score import score as bert_score
from nltk.translate.meteor_score import meteor_score

from datasets import Dataset as DatasetHF
from transformers import AdamW, get_linear_schedule_with_warmup
from torch.cuda.amp import GradScaler, autocast
from tqdm import tqdm

"""## Mapping the languages


First you can devine the specific translation from what languages that available in NusaX:

- ace: acehnese,
- ban: balinese,
- bjn: banjarese,
- bug: buginese,
- eng: english,
- ind: indonesian,
- jav: javanese,
- mad: madurese,
- min: minangkabau,
- nij: ngaju,
- sun: sundanese,
- bbc: toba_batak,
"""

languages = [
    {
        'code': 'eng',
        'name': 'English',
    },
    {
        'code': 'ind',
        'name': 'Indonesian',
    },
    {
        'code': 'ace',
        'name': 'Acehnese'
    },
    {
        'code': 'ban',
        'name': 'Balinese'
    },
    {
        'code': 'bjn',
        'name': 'Banjarese',
    },
    {
        'code': 'bug',
        'name': 'Buginese',
    },
    {
        'code': 'jav',
        'name': 'Javanese',
    },
    {
        'code': 'mad',
        'name': 'Madurese',
    },
    {
        'code': 'min',
        'name': 'Minangkabau',
    },
    {
        'code': 'nij',
        'name': 'Ngaju'
    },
    {
        'code': 'sun',
        'name': 'Sundanese',
    },
    {
        'code': 'bbc',
        'name': 'Toba_Batak'
    },
]

source = 'sun'
target = 'ind'
source_name = next(item['name'] for item in languages if item['code'] == source)
target_name = next(item['name'] for item in languages if item['code'] == target)

prefix = f'Translate {source_name} to {target_name} : '

# print(f"""
#     Source: {source}
#     Target: {target}
#     Prefix: {prefix}
# """)

"""## Load Datasets

After specified the translation task you can start loading the datasets or you also can run all the cell.
"""

nusax = load_dataset("indonlp/NusaX-MT")

display(nusax)

"""## EDA

Before using the datasets we should do some Exploratory to gain more information about the datasets

#### Convert Datasets HuggingFace into Pandas Dataframe

Before explore it we need to convert the datasets into pandas/dataframe type cause the datasets was in huggingface format
"""

nusax_df_train = nusax['train'].to_pandas()
nusax_df_test = nusax['test'].to_pandas()
nusax_df_valid = nusax['validation'].to_pandas()

display(nusax_df_train)
print('#'*100)
display(nusax_df_test)
print('#'*100)
display(nusax_df_valid)

"""### Merge Splited Datasets

after convert the datasets into dataframe we need to merge/concat the splitted dataframe, so we can analys the data easly.
"""

nusax_df_concated = pd.concat(
    [
        nusax_df_train,
        nusax_df_test,
        nusax_df_valid
    ],
    axis=0,
    ignore_index=True
    )

display(nusax_df_concated)

"""### Analys and Visualize

First the easiest way is to check the sentence length from the each languages in the datasets. We can use apply and lambda function to get the length, After that let see the most common words in each languaes using Counter From Collections Library. And After that we can also visualize it using Matplotlib and Seaborn
"""

# Function for get 10 most common words
def get_most_common_words(series, n_most_common=10):
    counter = Counter()
    for sentence in series:
        counter.update(sentence.lower().split())
    return counter.most_common(n_most_common)

# Function to get n-gram words
def generate_ngrams(text, n):
    words = text.split()
    ngrams = zip(*[words[i:] for i in range(n)])
    return [" ".join(ngram) for ngram in ngrams]


# Get Texts length
nusax_df_concated['text_1_length'] = nusax_df_concated['text_1'].apply(lambda x: len(x.split()))
nusax_df_concated['text_2_length'] = nusax_df_concated['text_2'].apply(lambda x: len(x.split()))

# Mendapatkan 10 kata teratas
top_source_words = get_most_common_words(nusax_df_concated['text_1'], 10)
top_target_words = get_most_common_words(nusax_df_concated['text_2'], 10)

# Membuat dataframe untuk visualisasi
df_vis_source = pd.DataFrame(top_source_words, columns=['Word', 'Frequency'])
df_vis_target = pd.DataFrame(top_target_words, columns=['Word', 'Frequency'])

# Get bigrams from source language
source_bigrams = generate_ngrams(" ".join(nusax_df_concated['text_1']), n=2)
# Get bigrams from target language
target_bigrams = generate_ngrams(" ".join(nusax_df_concated['text_2']), n=2)

display(nusax_df_concated.describe())

"""### Visualize"""

def plot_word_cloud(text, title):
    colormap = 'Reds'
    wordcloud = WordCloud(width=800, height=400, background_color ='white', colormap=colormap).generate(" ".join(text))
    plt.figure(figsize = (8, 8), facecolor = None)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.title(title)
    # plt.show()

# Updated function to plot common words, n-grams, and sentence length distribution
def plot_common_words_and_ngrams(df, language_code, language_name):
    main_color = 'red'
    # Filter dataframe for the current language
    df_lang = df[df['text_1_lang'] == language_code]
    texts = df_lang['text_1'].tolist()  # Assuming text_1 contains the sentences

    # Get 10 most common words
    top_words = get_most_common_words(df_lang['text_1'], 10)
    # Get top 10 bigrams
    bigrams = generate_ngrams(" ".join(texts), 2)
    top_bigrams = Counter(bigrams).most_common(10)

    plt.figure(figsize=(12, 10))

    # Sentence Length Distribution
    plt.subplot(2, 2, 1)
    sns.histplot(df_lang['text_1'].str.split().map(len), kde=True, color=main_color)
    plt.title(f'{language_name} Sentence Length Distribution')

    # 10 Most Common Words
    plt.subplot(2, 2, 2)
    df_vis = pd.DataFrame(top_words, columns=['Word', 'Frequency'])
    sns.barplot(x='Frequency', y='Word', data=df_vis, color=main_color)
    plt.title(f"Top 10 Most Common Words in {language_name}")

    # Bigrams
    plt.subplot(2, 2, 3)
    df_bigrams = pd.DataFrame(top_bigrams, columns=['Bigram', 'Frequency'])
    sns.barplot(x='Frequency', y='Bigram', data=df_bigrams, color=main_color)
    plt.title(f"Top 10 Most Common Bigrams in {language_name}")

    # Word Cloud
    plt.subplot(2, 2, 4)
    # plot_word_cloud(texts, f"Wordcloud for {language_name}")
    colormap = 'Reds'
    wordcloud = WordCloud(width=1000, height=1000, background_color ='white', colormap=colormap).generate(" ".join(texts))
    # plt.figure(figsize = (8, 8), facecolor = None)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.title(f"Wordcloud for {language_name}")

    plt.tight_layout()
    plt.show()

# Loop over each language
for language in languages:
    plot_common_words_and_ngrams(nusax_df_concated, language['code'], language['name'])

"""# Create Tokenizer

Since T5 have no vocabulary for Indonesian Local Languages so we need to create the tokenizer with our vocabulary. But since i have no other datasets im gonna using NusaX as the Vocabulary for training the tokenizer. In this study we gonna using [BPE](https://huggingface.co/docs/tokenizers/api/models#tokenizers.models.BPE/) model.

First we need to load the existing tokenizer cause we gonna train T5 model so we load the T5 tokenizer to.
"""

from transformers import AutoTokenizer

checkpoint = "t5-small"
# tokenizer = T5Tokenizer.from_pretrained(checkpoint)
tokenizer = AutoTokenizer.from_pretrained(checkpoint)

tokenizer.is_fast

"""for this study we gonna use the nusax as our training corpus for the tokenizer"""

# Concatenate source and target sentences to create a training corpus
training_corpus = nusax_df_concated['text_1'] + " " + nusax_df_concated['text_2']

display(training_corpus)

tokenizer.vocab_size

# vocab_dataset = DatasetHF.from_pandas(pd.DataFrame(training_corpus, columns=['text']))

# display(vocab_dataset['__index_level_0__'])

# Create a generator object
# def get_training_corpus():
#     for start_idx in tqdm(range(0, len(vocab_dataset), 100)):
#         samples = vocab_dataset[start_idx : start_idx + 100]
#         print(samples)
#         yield samples

batch_size = 1000
all_texts = [training_corpus[i : i + batch_size] for i in range(0, len(training_corpus), batch_size)]

def batch_iterator():
    for i in range(0, len(training_corpus), batch_size):
        yield training_corpus[i : i + batch_size]

# training_corpus = get_training_corpus()

new_vocab_size = tokenizer.vocab_size + 1000

new_tokenizer = tokenizer.train_new_from_iterator(
  batch_iterator(),
  new_vocab_size,
  show_progress=True,
)

"""after train the tokenizer we need to test the tokenizer"""

encoded_input = new_tokenizer(nusax_df_concated['text_1'][0], return_tensors="pt")
decoded_output = new_tokenizer.decode(encoded_input["input_ids"][0])

print(f"""
encoded: {encoded_input['input_ids'].tolist()}
decoded: {decoded_output}
""")

new_tokenizer.save_pretrained('/content/drive/MyDrive/Models/TOKENIZER/T5-NusaX-MT-toeknizer-pt')

"""## Datasets Preprocessing

Here we gonna splits the convert our dataframes into HuggingFace Datasets, and after that we splits the datasets become 80% train, 10% test, 10% validation, and concate the datasets. After that we vectorize and tokenize the datasets using tokenizer from T5.

First we need to convert the Dataframe into HF dataset again, and split the dataset manual
"""

for idx in range(len(nusax_df_concated)):
  input_lang = next(item['name'] for item in languages if item['code'] == nusax_df_concated['text_1_lang'][idx])
  target_lang = next(item['name'] for item in languages if item['code'] == nusax_df_concated['text_2_lang'][idx])
  prefix = f"Translate {input_lang} to {target_lang} : "
  nusax_df_concated['text_1'][idx] = prefix + nusax_df_concated['text_1'][idx]

display(nusax_df_concated)

nusaX = DatasetHF.from_pandas(nusax_df_concated)

display(nusaX)

# Split the dataset into training, validation, and test sets
split_ratios = [0.8, 0.1, 0.1]  # 80% training, 10% validation, 10% test
split_names = ['train', 'validation', 'test']

splits_nusaX = nusaX.train_test_split(test_size=0.1)
train_dataset, valid_test_dataset = splits_nusaX['train'], splits_nusaX['test']

splits_nusaX = valid_test_dataset.train_test_split(test_size=0.1)
valid_dataset, test_dataset = splits_nusaX['train'], splits_nusaX['test']

display(train_dataset)
display(test_dataset)
display(valid_dataset)

"""#### Check the languages distribution

since we split again the datasets we also need to check again the language distribution
"""

train_df = train_dataset.to_pandas()
test_df = test_dataset.to_pandas()
val_df = valid_dataset.to_pandas()

sns.histplot(train_df['text_1_lang'], color='red')
plt.title(f'Language Distribution Data Train')
plt.show()

sns.histplot(test_df['text_1_lang'], color='red')
plt.title(f'Language Distribution Data Test')
plt.show()

sns.histplot(val_df['text_1_lang'], color='red')
plt.title(f'Language Distribution Data Validation')
plt.show()

"""### Load Tokenizer

now we need to load our pretrained Tokenizer
"""

from transformers import T5Tokenizer

checkpoint = "t5-small"
tokenizer_path = "/content/drive/MyDrive/Models/TOKENIZER/T5-NusaX-MT-toeknizer-pt"
tokenizer_T5pt = AutoTokenizer.from_pretrained(tokenizer_path)

# Test the tokenizer
text = train_dataset['text_1'][0]
encoded_input = tokenizer_T5pt(text, return_tensors="pt")
decoded_output = tokenizer_T5pt.decode(encoded_input["input_ids"][0])

print(f"""
encoded: {encoded_input}
decoded: {decoded_output}
""")

"""The preprocessing function you want to create needs to:

1. Prefix the input with a prompt so T5 knows this is a translation task. Some models capable of multiple NLP tasks require prompting for specific tasks.
2. Truncate sequences to be no longer than the maximum length set by the `max_length` parameter.

To apply the preprocessing function over the entire dataset, use 🤗 Datasets [map](https://huggingface.co/docs/datasets/main/en/package_reference/main_classes#datasets.Dataset.map) method. You can speed up the `map` function by setting `batched=True` to process multiple elements of the dataset at once:
"""

def preprocess_function(examples):

    inputs = examples["text_1"]
    targets = examples["text_2"]
    model_inputs = tokenizer_T5pt(inputs, max_length=300, truncation=True, padding="max_length", return_tensors="pt")

    # Prepare decoder_input_ids
    with tokenizer_T5pt.as_target_tokenizer():
        labels = tokenizer_T5pt(targets, max_length=300, truncation=True, padding="max_length", return_tensors="pt")

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


tokenized_nusax_train = train_dataset.map(preprocess_function, batched=True)
tokenized_nusax_test = test_dataset.map(preprocess_function, batched=True)
tokenized_nusax_valid = valid_dataset.map(preprocess_function, batched=True)

display(tokenized_nusax_train['input_ids'][1])
display(tokenized_nusax_train['labels'][1])

"""## Model Development and Optimization

Load the metrics, we using several mterics for this project

- Bleu: Bilingual evaluation understudy (BLEU) is an automatic evaluation metric used to measure the similarity of the hypothesis to the reference. BLEU measures both adequacy by looking at word precision and fluency by calculating n-gram precision for n =1,2,3,4.
- Meteor: The metric for evaluation of translation with explicit ordering (METEOR) is a metric designed to address the limitations of BLEU, which is a commonly used evaluation metric for machine translation.  For instance, BLEU does not consider the stems and synonyms of words, meaning that it does not match “running” and “runs”, as they are not counted as the same word in the n-gram matching process. Additionally, BLEU does not use recall, which results in short sentences being penalized.
- Bleurt: BLEURT is a pre-trained model with a BERT structure using multi-task loss on synthetic data of a large number of references. It is a sentence-level metric that learns prediction scores that explain the similarity between the hypothesis and references.
- BertScores: BERTscore compares the hypothesis and reference statements of the translator using features extracted by BERT that is trained for the masked language model and next sentence prediction. BERTscore uses token embeddings of the pre-trained BERT.

And create a batch of examples using [DataCollatorForSeq2Seq](https://huggingface.co/docs/transformers/main/en/main_classes/data_collator#transformers.DataCollatorForSeq2Seq). It's more efficient to *dynamically pad* the sentences to the longest length in a batch during collation, instead of padding the whole dataset to the maximum length.
"""

from transformers import AutoModelForSeq2SeqLM, Seq2SeqTrainingArguments, Seq2SeqTrainer
from transformers import DataCollatorForSeq2Seq
import evaluate

# model_path = "/content/drive/MyDrive/Models/T5-small-CC100-SU-JV-02"
model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint)

# Load metrics
sacrebleu_metric = evaluate.load("sacrebleu")
meteor_metric = evaluate.load("meteor")
bertscore_metric = evaluate.load("bertscore")
bluert_metrics = evaluate.load("bleurt", module_type="metric")

data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer_T5pt, model=model)

"""compute metrics function for the metrics we gonna use Bleu, Meteor, Bleurt and BertScore to see the accuracy with various type metrics"""

def postprocess_text(preds, labels):
    preds = [pred.strip() for pred in preds]
    # Flatten the list of lists for labels into a list of strings
    # labels = [label.strip() for sublist in labels for label in sublist]
    labels = [label.strip() for label in labels]
    return preds, labels

def compute_metrics(eval_preds):
    preds, labels = eval_preds
    if isinstance(preds, tuple):
        preds = preds[0]

    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

    decoded_preds, decoded_labels = postprocess_text(decoded_preds, decoded_labels)

    print(f"Decoded preds: {len(decoded_preds)}, Decoded labels: {len(decoded_labels)}")

    # Check if the number of predictions and references match
    if len(decoded_preds) != len(decoded_labels):
        raise ValueError(f"Number of predictions ({len(decoded_preds)}) does not match number of references ({len(decoded_labels)})")

    # Initialize result dictionary
    result = {}

    # Compute sacreBLEU
    bleu_result = sacrebleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
    result["bleu"] = bleu_result["score"]

    # Compute METEOR
    meteor_result = meteor_metric.compute(predictions=decoded_preds, references=decoded_labels)
    result["meteor"] = meteor_result["meteor"]


    # Compute BLEURT
    bleurt_result = bluert_metrics.compute(predictions=decoded_preds, references=decoded_labels)
    # Choose a specific value to log (e.g., mean or median)
    result["Bleurt"] = round(np.mean(bleurt_result['scores']), 4)


    # Compute BERTScore
    bertscore_result = bertscore_metric.compute(predictions=decoded_preds, references=decoded_labels, lang="id")
    result["bertscore_precision"] = np.mean(bertscore_result["precision"])
    result["bertscore_recall"] = np.mean(bertscore_result["recall"])
    result["bertscore_f1"] = np.mean(bertscore_result["f1"])

    prediction_lens = [np.count_nonzero(pred != tokenizer.pad_token_id) for pred in preds]
    result["gen_len"] = np.mean(prediction_lens)
    # result = {k: round(v, 4) for k, v in result.items()}

    # Round specific metrics
    result["bleu"] = round(result["bleu"], 4)
    result["meteor"] = round(result["meteor"], 4)
    result["bertscore_precision"] = round(result["bertscore_precision"], 4)
    result["bertscore_recall"] = round(result["bertscore_recall"], 4)
    result["bertscore_f1"] = round(result["bertscore_f1"], 4)
    result["gen_len"] = round(result["gen_len"], 4)

    return result

training_args = Seq2SeqTrainingArguments(
    output_dir=f"T5-NusaX_checkpoints",
    evaluation_strategy="epoch",
    learning_rate=5e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    weight_decay=0.01,
    save_total_limit=1,
    num_train_epochs=3,
    predict_with_generate=True,
    fp16=True,
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_nusax_train,
    eval_dataset=tokenized_nusax_valid,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

trainer.train()

"""Save the model to drive, or you aslo can push the model to HuggingFace if you want."""

model_name = f"/content/drive/MyDrive/Models/T5-small-NusaX-FULL_model"
trainer.save_model(model_name)

"""## Predict Evaluate

Great, now that you've finetuned a model, you can use it for inference!

Come up with some text you'd like to translate to another language. For T5, you need to prefix your input depending on the task you're working on. For translation from new languge to another new language, you should prefix your input as we when divined the translation task:

First we need to test the model with one sentence to make sure if it realy works
"""

from transformers import pipeline

input = f"Translate Sundanese to Acehnese : Nikmati angsuran 0% dugi ka 12 bulan kanggo mesen tiket pasawat air asia nganggo kartu kiridit BNI!"

translator = pipeline("translation", model=model_name)
output = translator(input)

print(f"""
input  : {input}
output : {output}
""")

def predict_evaluate(data):
    try:
        sources = data['text_1']
        targets = data['text_2']
        predictions = [translator(source)[0]['translation_text'] for source in sources]

        # Initialize lists to store results
        predicts, accuracies, bleus, meteors, bleurts, bertscore_precisions, bertscore_recalls, bertscore_f1s = [], [], [], [], [], [], [], []

        for prediction, target in zip(predictions, targets):
            predicts.append(prediction)

            # Calculate accuracy for each prediction
            accuracies.append(int(prediction == target))

            # Compute sacreBLEU
            bleu_result = sacrebleu_metric.compute(predictions=[prediction], references=[target])
            bleus.append(bleu_result["score"])

            # Compute METEOR
            meteor_result = meteor_metric.compute(predictions=[prediction], references=[target])
            meteors.append(meteor_result["meteor"])

            # Compute Bleurt
            bleurt_result = bluert_metrics.compute(predictions=[prediction], references=[target])
            bleurts.append(bleurt_result['scores'])

            # Compute BERTScore
            bertscore_result = bertscore_metric.compute(predictions=[prediction], references=[target], lang="id")
            bertscore_precisions.append(bertscore_result["precision"])
            bertscore_recalls.append(bertscore_result["recall"])
            bertscore_f1s.append(bertscore_result["f1"])

        # Return a dictionary with lists as values
        return {
            "input": data['text_1'],
            "predict": predicts,
            "target": targets,
            # "accuracy": accuracies,  # Now a list of accuracies
            "bleu": bleus,
            "meteor": meteors,
            "bleurt": bleurts,
            "bertscore_precision": bertscore_precisions,
            "bertscore_recall": bertscore_recalls,
            "bertscore_f1": bertscore_f1s
        }

    except Exception as e:
        print(f"Error during prediction or evaluation: {e}")
        return None

# Assuming test_dataset is correctly defined
data_test_predict_eval = test_dataset.map(predict_evaluate, batched=True)

predict_eval_df = data_test_predict_eval.to_pandas()

display(predict_eval_df.drop(
    [
        'text_1', 'text_2',
        'text_1_lang', 'text_2_lang',
        'text_1_length', 'text_2_length',
    ],
    axis=1)
)

display(predict_eval_df.drop(
    [
        'text_1', 'text_2',
        'text_1_lang', 'text_2_lang',
        'text_1_length', 'text_2_length',
        # 'input',
        # 'bleu',
        # 'meteor',
        # 'bleurt',
        'bertscore_precision',
        'bertscore_recall',
        'bertscore_f1'
    ],
    axis=1)
)

display(predict_eval_df['bleu'].mean())
display(predict_eval_df['meteor'].mean())
display(predict_eval_df['bleurt'].mean())
display(predict_eval_df['bertscore_precision'].mean())
display(predict_eval_df['bertscore_recall'].mean())
display(predict_eval_df['bertscore_f1'].mean())

"""# Datasets
- https://huggingface.co/datasets/indonlp/NusaX-MT
- https://github.com/IndoNLP/nusax
- https://ar5iv.labs.arxiv.org/html/2205.15960

# References

- https://github.com/huggingface/transformers/tree/main/examples/pytorch/translation
- https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/translation.ipynb#scrollTo=X4cRE8IbIrIV
- https://huggingface.co/docs/transformers/tasks/translation
- https://huggingface.co/docs/transformers/model_doc/t5
- https://github.com/EliasK93/transformer-models-for-domain-specific-machine-translation
- https://huggingface.co/docs/transformers/model_doc/marian#old-style-multi-lingual-models
- https://www.mdpi.com/2227-7390/11/4/1006
- https://huggingface.co/spaces/evaluate-metric/bertscore#:~:text=Metric%20description,token%20in%20the%20reference%20sentence
- https://huggingface.co/spaces/evaluate-metric/bleurt
"""


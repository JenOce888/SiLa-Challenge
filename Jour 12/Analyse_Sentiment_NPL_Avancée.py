"""
DAY 12 - Advanced NLP Sentiment Analysis
Two-level system: NLTK (VADER + TF-IDF + Naive Bayes) + Distilled BERT
Dataset: Amazon Book Reviews | Flask API for real-time testing
"""


import warnings
warnings.filterwarnings("ignore")

import nltk
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datasets import load_dataset
from transformers import pipeline as hf_pipeline
import re
import time

#  DOWNLOAD NLTK RESOURCES

nltk.download("vader_lexicon", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)

#  LOAD THE AMAZON BOOK REVIEWS DATASET
print("=" * 60)
print(" Loading Amazon Book Reviews dataset...")
print("=" * 60)

# Load dataset from HuggingFace
dataset = load_dataset("amazon_polarity")

# Use a subset to keep things fast
TRAIN_SIZE = 5000   # number of training examples
TEST_SIZE  = 1000   # number of test examples

train_texts  = dataset["train"]["content"][:TRAIN_SIZE]   # ← "content" for Amazon
train_labels = dataset["train"]["label"][:TRAIN_SIZE]     # 0 = negative, 1 = positive
test_texts   = dataset["test"]["content"][:TEST_SIZE]
test_labels  = dataset["test"]["label"][:TEST_SIZE]

print(f" Train: {len(train_texts)} examples | Test: {len(test_texts)} examples\n")


#  TEXT PREPROCESSING

def clean_text(text: str) -> str:
    """
    Clean raw text:
    - Remove HTML tags (e.g. <br />)
    - Remove special characters and digits
    - Convert to lowercase
    """
    text = re.sub(r"<.*?>", " ", text)          # remove HTML tags
    text = re.sub(r"[^a-zA-Z\s]", " ", text)    # keep only letters
    text = re.sub(r"\s+", " ", text).strip()     # remove extra spaces
    return text.lower()

# Clean all texts
train_clean = [clean_text(t) for t in train_texts]
test_clean  = [clean_text(t) for t in test_texts]


# 4. LEVEL 1 — VADER + TF-IDF + NAIVE BAYES

print("=" * 60)
print(" APPROACH 1: VADER + TF-IDF + Naive Bayes")
print("=" * 60)

#  VADER (rule-based, no training needed) 
# VADER uses a built-in dictionary of words with sentiment scores
# It requires ZERO training — it just reads the words

vader = SentimentIntensityAnalyzer()

def vader_predict(texts):
    """
    Predict sentiment using VADER.
    compound >= 0 → Positive
    compound <  0 → Negative
    """
    predictions = []
    for text in texts:
        scores = vader.polarity_scores(text)
        label  = 1 if scores["compound"] >= 0 else 0
        predictions.append(label)
    return np.array(predictions)

# Measure inference time
start        = time.time()
vader_preds  = vader_predict(test_clean)
vader_time   = time.time() - start

vader_acc = accuracy_score(test_labels, vader_preds)
print(f"\n VADER Accuracy: {vader_acc:.4f}  ({vader_time:.2f}s)")
print(classification_report(test_labels, vader_preds,
                             target_names=["Negative", "Positive"]))

#  TF-IDF + Naive Bayes (supervised learning) 
# TF-IDF converts text to numbers based on word frequency
# Naive Bayes then classifies based on probability

nb_pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=20_000,   # keep the 20,000 most common words
        ngram_range=(1, 2),    # use single words AND pairs of words
        stop_words="english"   # ignore common words like "the", "a", "is"
    )),
    ("clf", MultinomialNB(alpha=0.1)),  # Naive Bayes classifier
])

start     = time.time()
nb_pipeline.fit(train_clean, train_labels)   # train the model
nb_preds  = nb_pipeline.predict(test_clean)  # make predictions
nb_time   = time.time() - start

nb_acc = accuracy_score(test_labels, nb_preds)
print(f"\n TF-IDF + Naive Bayes Accuracy: {nb_acc:.4f}  ({nb_time:.2f}s)")
print(classification_report(test_labels, nb_preds,
                             target_names=["Negative", "Positive"]))


# 5. LEVEL 2 — DISTILBERT (TRANSFORMER MODEL)

print("=" * 60)
print(" APPROACH 2: DistilBERT (fine-tuned on IMDB)")
print("=" * 60)

# Load a pre-trained DistilBERT model from HuggingFace
# This model was already fine-tuned on sentiment analysis — no training needed
bert_clf = hf_pipeline(
    "text-classification",
    model="distilbert-base-uncased-finetuned-sst-2-english",
    truncation=True,   # cut text if it's too long
    max_length=512,    # maximum number of tokens BERT can handle
)

def bert_predict(texts, batch_size=32):
    """
    Predict sentiment using DistilBERT.
    Processes texts in batches for efficiency.
    """
    all_predictions = []
    for i in range(0, len(texts), batch_size):
        batch   = texts[i : i + batch_size]
        results = bert_clf(batch)
        preds   = [1 if r["label"] == "POSITIVE" else 0 for r in results]
        all_predictions.extend(preds)
        if (i // batch_size) % 5 == 0:
            print(f"  → Batch {i // batch_size + 1}/{len(texts) // batch_size + 1}")
    return np.array(all_predictions)

# Evaluate on a smaller subset (BERT is slower than classical ML)
BERT_EVAL_SIZE = 200

start      = time.time()
bert_preds = bert_predict(test_texts[:BERT_EVAL_SIZE])
bert_time  = time.time() - start

bert_acc = accuracy_score(test_labels[:BERT_EVAL_SIZE], bert_preds)
print(f"\n DistilBERT Accuracy: {bert_acc:.4f}  ({bert_time:.2f}s on {BERT_EVAL_SIZE} examples)")
print(classification_report(test_labels[:BERT_EVAL_SIZE], bert_preds,
                             target_names=["Negative", "Positive"]))


#  VISUALIZATIONS — COMPARE THE MODELS

print("\n Generating visualizations...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor("#0F1117")
fig.suptitle("Sentiment Analysis — Book Reviews Model Comparison",
             fontsize=16, fontweight="bold", color="white")

# Dark-themed color palette
colors = {
    "VADER":      "#F72585",   # vivid pink
    "NaiveBayes": "#7209B7",   # deep purple
    "DistilBERT": "#4CC9F0",   # electric cyan
}
models = ["VADER", "NaiveBayes (TF-IDF)", "DistilBERT"]

for ax in axes.flat:
    ax.set_facecolor("#1A1A2E")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333355")

#  Plot 1: Accuracy comparison 
ax   = axes[0, 0]
accs = [vader_acc, nb_acc, bert_acc]
bars = ax.bar(models, accs,
              color=list(colors.values()),
              width=0.5, edgecolor="white", linewidth=1.5)
ax.set_ylim(0.5, 1.0)
ax.set_ylabel("Accuracy")
ax.set_title("Accuracy per Model")
for bar, acc in zip(bars, accs):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.005,
            f"{acc:.3f}", ha="center", va="bottom", fontweight="bold")

#  Plot 2: Inference time comparison
ax    = axes[0, 1]
times = [vader_time, nb_time, bert_time]
ax.bar(models, times,
       color=list(colors.values()),
       width=0.5, edgecolor="white", linewidth=1.5)
ax.set_ylabel("Time (seconds)")
ax.set_title("Inference Time")

#  Plot 3: Confusion matrix — Naive Bayes
ax = axes[1, 0]
cm = confusion_matrix(test_labels, nb_preds)
sns.heatmap(cm, annot=True, fmt="d", cmap="RdPu",
            xticklabels=["Negative", "Positive"],
            yticklabels=["Negative", "Positive"], ax=ax,
            linewidths=0.5, linecolor="#0F1117")
ax.set_title("Confusion Matrix — Naive Bayes")
ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")

#  Plot 4: Confusion matrix — DistilBERT 
ax      = axes[1, 1]
cm_bert = confusion_matrix(test_labels[:BERT_EVAL_SIZE], bert_preds)
sns.heatmap(cm_bert, annot=True, fmt="d", cmap="PuBu",
            xticklabels=["Negative", "Positive"],
            yticklabels=["Negative", "Positive"], ax=ax,
            linewidths=0.5, linecolor="#0F1117")
ax.set_title("Confusion Matrix — DistilBERT")
ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")

plt.tight_layout()
plt.savefig("sentiment_results.png", dpi=150, bbox_inches="tight")
print(" Chart saved: sentiment_results.png\n")


#  VADER SCORE DISTRIBUTION
# Visualize how VADER scores are distributed across reviews
vader_scores = [vader.polarity_scores(t)["compound"] for t in test_clean[:500]]

plt.figure(figsize=(10, 4), facecolor="#0F1117")
ax = plt.gca()
ax.set_facecolor("#1A1A2E")
ax.tick_params(colors="white")
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")
ax.title.set_color("white")
for spine in ax.spines.values():
    spine.set_edgecolor("#333355")

plt.hist(vader_scores, bins=40, color="#F72585", alpha=0.85, edgecolor="#0F1117")
plt.axvline(0, color="#4CC9F0", linestyle="--", linewidth=2, label="Neutral threshold")
plt.xlabel("VADER Compound Score")
plt.ylabel("Frequency")
plt.title("VADER Score Distribution (500 Book Reviews)")
plt.legend(facecolor="#1A1A2E", labelcolor="white")
plt.tight_layout()
plt.savefig("vader_distribution.png", dpi=150, bbox_inches="tight")
print(" Distribution saved: vader_distribution.png\n")


#  FLASK API — SERVE THE MODELS IN REAL TIME
print("=" * 60)
print(" Starting Flask API on http://localhost:5000")
print("=" * 60)

from flask import Flask, request, jsonify

app = Flask(__name__)

# ── Endpoint 1: Single model prediction ──────
@app.route("/predict", methods=["POST"])
def predict():
    """
    POST /predict
    Request body: { "text": "...", "model": "vader" | "naive_bayes" | "bert" }
    Returns the sentiment label and confidence score.
    """
    data  = request.get_json(force=True)
    text  = data.get("text", "")
    model = data.get("model", "naive_bayes").lower()

    if not text:
        return jsonify({"error": "Field 'text' is required"}), 400

    clean = clean_text(text)

    if model == "vader":
        scores = vader.polarity_scores(clean)
        label  = "positive" if scores["compound"] >= 0 else "negative"
        return jsonify({
            "model":  "VADER",
            "label":  label,
            "scores": scores,
        })

    elif model == "naive_bayes":
        pred  = nb_pipeline.predict([clean])[0]
        proba = nb_pipeline.predict_proba([clean])[0]
        return jsonify({
            "model":      "TF-IDF + Naive Bayes",
            "label":      "positive" if pred == 1 else "negative",
            "confidence": round(float(max(proba)), 4),
        })

    elif model == "bert":
        result = bert_clf(text[:512])[0]
        return jsonify({
            "model":      "DistilBERT",
            "label":      "positive" if result["label"] == "POSITIVE" else "negative",
            "confidence": round(float(result["score"]), 4),
        })

    else:
        return jsonify({"error": "Unknown model. Choose: vader, naive_bayes, bert"}), 400


#  Endpoint 2: Compare all 3 models 
@app.route("/compare", methods=["POST"])
def compare():
    """
    POST /compare
    Request body: { "text": "..." }
    Returns predictions from all 3 models side by side.
    """
    data = request.get_json(force=True)
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "Field 'text' is required"}), 400

    clean = clean_text(text)

    # VADER prediction
    scores  = vader.polarity_scores(clean)
    v_label = "positive" if scores["compound"] >= 0 else "negative"

    # Naive Bayes prediction
    nb_pred  = nb_pipeline.predict([clean])[0]
    nb_proba = nb_pipeline.predict_proba([clean])[0]

    # DistilBERT prediction
    bert_res = bert_clf(text[:512])[0]

    return jsonify({
        "text": text[:200],
        "VADER": {
            "label":    v_label,
            "compound": round(scores["compound"], 4)
        },
        "NaiveBayes": {
            "label":      "positive" if nb_pred == 1 else "negative",
            "confidence": round(float(max(nb_proba)), 4)
        },
        "DistilBERT": {
            "label":      "positive" if bert_res["label"] == "POSITIVE" else "negative",
            "confidence": round(float(bert_res["score"]), 4)
        },
    })


#  Endpoint 3: Health check 
@app.route("/health", methods=["GET"])
def health():
    """Simple check to confirm the API is running."""
    return jsonify({"status": "ok", "models": ["vader", "naive_bayes", "bert"]})


#  Start the server
if __name__ == "__main__":
    print("\n Available endpoints:")
    print("  GET  /health")
    print("  POST /predict  → body: { text, model }")
    print("  POST /compare  → body: { text }  (all 3 models)\n")
    print("Example cURL:")
    print('  curl -X POST http://localhost:5000/compare \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"text": "This movie was absolutely fantastic!"}\'\n')
    app.run(debug=True, port=5000)
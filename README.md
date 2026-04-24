README
======
 This project is a decision intelligence assistant built on real Twitter customer support data. It takes a customer complaint, retrieves similar past tickets, generates suggested responses with and without context, and predicts ticket priority using both a trained ML classifier and an LLM — then puts all four outputs side by side so you can compare accuracy, latency, and cost.

Overview
--------
* **Data:** The assistant is trained on real-life Twitter data from various companies receiving and responding to customer support queries.
* **ML:** We train a machine-language model to classify the priority of new user query (customer support) based on the previous data. We also compare the classification to that made by an LLM.
* **RAG:** The LLM should provide two responses to the user query, one with RAG, one without; we compare the two.
* **Embeddings:** For RAG, we need to store the embeddings in a (local) vector store.
* **API:** The query and responses (plus priority predictions) will be submitted and received via APIs.
* **Frontend:** A handy UI will be provided for the user to make the query, see the fetched RAG data and examine the results.

Flow
----
1. User submits query
2. Show similar cases (RAG)
3. Show RAG and non-RAG answers to the query, by the LLM
4. Predict the priority of the (support) query two ways, by the trained ML model and a zero-shot LLM prompt
5. Show four-way comparison

Setup
-----
Install Python virtual environment:
```
uv sync
source .venv/bin/activate
```

To run the FastAPI server:
```
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

To end the session, run `deactivate` or just kill the terminal.

Project structure
-----------------
```
[PROJECT_ROOT]
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Dockerfile                       ← backend Dockerfile (at root)
├── requirements.txt
├── main.py                          ← FastAPI app entry point
├── features.py                      ← shared feature extraction
├── notebook.ipynb
│
├── app/
│   ├── routers/
│   │   ├── query.py                 ← POST /query (orchestrator)
│   │   ├── retrieve.py              ← POST /retrieve
│   │   ├── generate.py              ← POST /generate/rag, /generate/no-rag
│   │   ├── predict.py               ← POST /predict/ml, /predict/llm
│   │   └── health.py                ← GET /health
│   ├── services/
│   │   ├── retrieval.py             ← ChromaDB query logic
│   │   ├── llm.py                   ← Groq API calls
│   │   ├── ml_model.py              ← Load model.pkl, run predict
│   │   └── features.py              ← copied from root features.py
│   ├── schemas/
│   │   └── models.py                ← Pydantic request/response schemas
│   └── utils/
│       └── logger.py                ← JSONL query logging
│
├── ml/
│   └── model.pkl                    ← trained classifier
│
├── chroma_data/                     ← ChromaDB persistent dir (volume-mounted)
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── QueryInput.jsx
│           ├── AnswerPanel.jsx
│           ├── SourcePanel.jsx
│           └── ComparisonTable.jsx
│
└── logs/
```

Data
----
The full dataset, twcs.csv ("Twitter Customer Support"), can be downloaded from Kaggle [here](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter).

### Filtering
We filter the dataset by inbound tweets, which represent messages from users (not company responses). From these, we get the initial customer messages (initial query). We match each query with the initial company response. From the remaining dataset, we extract **20-30k query/response pairs**. These are stored as embeddings for the RAG response. We also create a data frame from just the query messages for training the ML model; classifying priority doesn't need the company response.

Run `filter_dataset.py` from the project root directory to achieve this.

Generated dataset = data/first-brand-reply-pairs.csv

### Embedding
We generate the ChromaDB database of embeddings from the above filtered dataset. Run `embed_dataset.py` to call the embeddings model with the data. The generated collection is called **complaints**.

We can quickly do a sanity check to confirm the database. Start an interactive Python session and run:
```
import chromadb
client = chromadb.PersistentClient("chroma_data")  # data is in the top-level chroma_data/ dir
C = client.get_collection("complaints")
C.count()       # number of records
C.peek(3)       # inspect a few
```

### Labelling function
We need to classify the priority as **urgent** or **normal**. We can come up with a **weak-supervision** labelling function based on:
* keywords (`refund`, `cancel` etc.)
* punctuation (has 2+ exclamation marks)
* ALL-CAPS ratio (e.g. above 30 %)

Feature engineering
-------------------
Define keywords:
```
URGENCY_KEYWORDS = {"refund", "cancel", "broken", "charged", "stolen", "hacked",
                    "urgent", "asap", "immediately", "emergency", "help"}

NEGATIVE_KEYWORDS = {"worst", "terrible", "horrible", "awful", "unacceptable",
                     "disgusting", "scam", "fraud", "pathetic"}
```

Our features:
* Word count
* Char count
* Number of URGENCY keywords
* Number of NEGATIVE keywords
* Number of ALL-CAPS words
* Number of exclamation marks
* Number of question marks
* Sentiment compound score (VADER)
* Number of response tweets (second-last column)

Priority prediction: ML vs LLM
------------------------------
I trained a Gradient Boosting Classifier model, it is saved as `priority_classifier.joblib` under `app/ml`.

It has an accuracy of 98 %, along with the following stats:
```
              precision    recall  f1-score   support

      normal       0.99      1.00      0.99      5561
      urgent       0.98      0.81      0.89       439

    accuracy                           0.98      6000
   macro avg       0.98      0.90      0.94      6000
weighted avg       0.98      0.98      0.98      6000
```

These were evaluated on the test set `data/test_set.csv`, containing about 6k entries.

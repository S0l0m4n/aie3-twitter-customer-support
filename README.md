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

Data
----
The full dataset, twcs.csv ("Twitter Customer Support"), can be downloaded from Kaggle [here](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter).

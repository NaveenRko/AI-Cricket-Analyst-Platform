import joblib

from sentence_transformers import SentenceTransformer

clf = joblib.load("IntentClassifier/intent_classifier.pkl")

encoder = joblib.load("IntentClassifier/intent_encoder.pkl")

embed_model = SentenceTransformer("all-MiniLM-L6-v2")


def predict_intent(question):

    vec = embed_model.encode([question])

    pred = clf.predict(vec)

    return encoder.inverse_transform(pred)[0]

print(predict_intent("Strike rate of Yashasvi Jaiswal"))
  
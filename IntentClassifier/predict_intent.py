import joblib
from sentence_transformers import SentenceTransformer

clf = joblib.load("IntentClassifier/intent_classifier.pkl")
encoder = joblib.load("IntentClassifier/intent_encoder.pkl")

embed_model = SentenceTransformer("all-MiniLM-L6-v2")


def predict_intent(question):

    vec = embed_model.encode([question])

    # Prediction
    pred = clf.predict(vec)

    # Class probabilities
    probs = clf.predict_proba(vec)

    confidence = float(probs.max())

    intent = encoder.inverse_transform(pred)[0]

    return {
        "intent": intent,
        "confidence": confidence
    }


if __name__ == "__main__":

    result = predict_intent(
        "Which team has the best record in must-win playoff games?"
    )

    print(result)
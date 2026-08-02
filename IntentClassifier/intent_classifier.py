# load required libraries
import pandas as pd

from sentence_transformers import SentenceTransformer

from sklearn.preprocessing import LabelEncoder

from xgboost import XGBClassifier

import joblib

#load the intent dataset
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "intent_dataset.csv"

df = pd.read_csv(DATASET_PATH)

print(df.head())

# embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")

X = model.encode(df["question"].tolist())

encoder = LabelEncoder()

y = encoder.fit_transform(df["intent"])

# train
clf = XGBClassifier()

clf.fit(X,y)

joblib.dump(
    clf,
    "intent_classifier.pkl"
)

joblib.dump(
    encoder,
    "intent_encoder.pkl"
)
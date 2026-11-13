import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve, auc
from sklearn.model_selection import train_test_split
import os

def create_graphs():
    print("Loading data...")
    # Map paths
    data_path = "../spam.csv"
    if not os.path.exists(data_path):
        print(f"Cannot find {data_path}")
        return

    df = pd.read_csv(data_path, encoding="latin-1")
    df = df[['v1', 'v2']]
    df.columns = ['label', 'text']
    df['is_spam'] = df['label'].map({'ham': 0, 'spam': 1})
    
    X_train, X_test, y_train, y_test = train_test_split(df['text'], df['is_spam'], test_size=0.2, random_state=42)
    
    print("Training Model...")
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train_vec, y_train)
    
    # 1. Generate ROC Curve
    print("Generating ROC Curve...")
    y_prob = model.predict_proba(X_test_vec)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='#38BDF8', lw=2, label=f'TF-IDF Logistic Regression (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='#F43F5E', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title('Receiver Operating Characteristic (Threat Detection)', fontsize=14)
    plt.legend(loc="lower right")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig("../fig1_roc_curve.png", dpi=300)
    plt.close()
    
    # 2. Generate Prediction Distribution
    print("Generating Probability Distribution...")
    plt.figure(figsize=(10, 6))
    sns.histplot(data=pd.DataFrame({'Phishing Score': y_prob, 'Actual': y_test.map({0: 'Safe Instruction', 1: 'Malicious AI Intercept'})}),
                 x='Phishing Score', hue='Actual', bins=50, kde=True, 
                 palette={'Safe Instruction': '#10B981', 'Malicious AI Intercept': '#F43F5E'})
    plt.axvline(x=0.70, color='yellow', linestyle='--', linewidth=2, label='CryptoGuard Isolation Threshold (0.7)')
    plt.title('NLP Phishing Score Distribution on Robotic Commands', fontsize=14)
    plt.xlabel('Semantic Threat Confidence Score', fontsize=12)
    plt.ylabel('Command Frequency', fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig("../fig2_phishing_distribution.png", dpi=300)
    plt.close()

if __name__ == "__main__":
    create_graphs()
    print("Graphs generated in root folder!")

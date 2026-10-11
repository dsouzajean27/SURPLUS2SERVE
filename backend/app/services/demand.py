import numpy as np
from sklearn.linear_model import LinearRegression

def predict_demand(history):
    """
    history: list of (day_index, quantity)
    Example: [(1, 50), (2, 60), (3, 55)]
    """
    X = np.array([h[0] for h in history]).reshape(-1, 1)
    y = np.array([h[1] for h in history])
    model = LinearRegression()
    model.fit(X, y)

    # Predict next 7 days
    future_days = np.array(range(max(X)[0] + 1, max(X)[0] + 8)).reshape(-1, 1)
    predictions = model.predict(future_days)
    return predictions.tolist()

import pandas as pd
from django.shortcuts import render
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import io, base64

file_path = r'media\traffic.csv'

def get_training_context(custom_input=None):
    df = pd.read_csv(file_path)
    
    # Check if 'DateTime' exists (old dataset), otherwise use new routing dataset
    if 'DateTime' in df.columns:
        from statsmodels.tsa.arima.model import ARIMA
        df['DateTime'] = pd.to_datetime(df['DateTime'], format="%d-%m-%Y %H:%M", errors='coerce')
        df = df.dropna(subset=['DateTime']).sort_values('DateTime')
        df = df[['DateTime', 'Vehicles']].dropna()
        df.set_index('DateTime', inplace=True)
        split_idx = int(len(df) * 0.8)
        train, test = df[:split_idx], df[split_idx:]
        model = ARIMA(train['Vehicles'], order=(5,1,0))
        model_fit = model.fit()
        predictions = model_fit.forecast(steps=len(test))
        y_test = test['Vehicles']
        title1 = "Actual vs Predicted Vehicle Counts (ARIMA)"
        xlabel1 = "Time"
        ylabel1 = "Vehicle Count"
        xlabel2 = "Predicted Vehicle Count"
        custom_prediction = None
    else:
        # New Routing Dataset: Predict congestion_score
        from sklearn.ensemble import RandomForestRegressor
        features = ['source_lat', 'source_lng', 'dest_lat', 'dest_lng', 'distance_km', 'avg_speed_kmph', 'eta_minutes']
        target = 'congestion_score'
        
        # Drop rows with missing values
        df_clean = df[features + [target]].dropna()
        X = df_clean[features]
        y = df_clean[target]
        
        split_idx = int(len(df_clean) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        predictions = pd.Series(model.predict(X_test), index=y_test.index)
        
        title1 = "Actual vs Predicted Congestion Score (RF)"
        xlabel1 = "Test Samples"
        ylabel1 = "Congestion Score"
        xlabel2 = "Predicted Congestion Score"
        
        custom_prediction = None
        if custom_input:
            try:
                pred_df = pd.DataFrame([custom_input], columns=features)
                custom_prediction = round(model.predict(pred_df)[0], 3)
            except Exception as e:
                custom_prediction = f"Error: {e}"

    residuals = y_test - predictions
    mae = float(residuals.abs().mean())
    mse = float((residuals ** 2).mean())
    sse = (residuals ** 2).sum()
    sst = ((y_test - y_test.mean()) ** 2).sum()
    r2 = float(1 - (sse / sst)) if sst != 0 else 0.0

    plt.figure(figsize=(10, 6))
    if 'DateTime' in df.columns:
        sns.lineplot(x=y_test.index, y=y_test.values, label='Actual', color='blue')
        sns.lineplot(x=predictions.index, y=predictions, label='Predicted', color='orange')
        if custom_prediction:
            plt.scatter([predictions.index[-1]], [custom_prediction], color='red', marker='*', s=300, label='Your Route Pred', zorder=5)
    else:
        sns.lineplot(x=range(len(y_test)), y=y_test.values, label='Actual', color='blue')
        sns.lineplot(x=range(len(predictions)), y=predictions.values, label='Predicted', color='orange')
        if custom_prediction:
            plt.scatter([len(predictions)], [custom_prediction], color='red', marker='*', s=300, label='Your Route Pred', zorder=5)
        
    plt.title(title1)
    plt.xlabel(xlabel1)
    plt.ylabel(ylabel1)
    plt.legend()
    plt.tight_layout()
    buf1 = io.BytesIO()
    plt.savefig(buf1, format='png')
    buf1.seek(0)
    graph1_b64 = base64.b64encode(buf1.read()).decode('utf-8')
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=predictions, y=residuals)
    plt.axhline(y=0, color='red', linestyle='--')
    plt.title("Residuals vs Predicted Values")
    plt.xlabel(xlabel2)
    plt.ylabel("Residuals")
    plt.tight_layout()
    buf2 = io.BytesIO()
    plt.savefig(buf2, format='png')
    buf2.seek(0)
    graph2_b64 = base64.b64encode(buf2.read()).decode('utf-8')
    plt.close()

    return {
        'mae': mae,
        'mse': mse,
        'r2': r2,
        'graph1': graph1_b64,
        'graph2': graph2_b64,
        'custom_prediction': custom_prediction,
        'custom_input': custom_input
    }

def train_vehicles_model(request):
    try:
        custom_input = None
        if request.method == 'POST':
            try:
                custom_input = {
                    'source_lat': float(request.POST.get('source_lat', 17.3850)),
                    'source_lng': float(request.POST.get('source_lng', 78.4867)),
                    'dest_lat': float(request.POST.get('dest_lat', 16.5062)),
                    'dest_lng': float(request.POST.get('dest_lng', 80.6480)),
                    'distance_km': float(request.POST.get('distance_km', 300)),
                    'avg_speed_kmph': float(request.POST.get('avg_speed_kmph', 60)),
                    'eta_minutes': float(request.POST.get('eta_minutes', 300))
                }
            except ValueError:
                pass
        else:
            custom_input = request.session.get('last_prediction_inputs')

        context = get_training_context(custom_input)
        return render(request, 'users/task2.html', context)
    except Exception as e:
        return render(request, 'users/task2.html', {'error': str(e)})

def training(request):
    try:
        context = get_training_context()
        print(context)
        return render(request, 'users/task1.html', context)
    except Exception as e:
        print(f"Error in training function: {e}")
        return render(request, 'users/task1.html', {'error': str(e)})

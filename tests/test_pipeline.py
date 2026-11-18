"""Checks Jenkins runs after train.py and before the Docker image is built."""
import json
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app import app

CONFIG = json.loads(Path('config.json').read_text())
METRICS = json.loads(Path('artifacts/metrics.json').read_text())
client = TestClient(app)


def test_artifacts_exist():
    assert Path('artifacts/model.joblib').is_file()
    assert Path('artifacts/metrics.json').is_file()


def test_metrics_fields():
    for key in ('student_id', 'accuracy', 'training_rows', 'model_version', 'git_sha'):
        assert key in METRICS, f'missing {key}'
    assert METRICS['student_id'] == CONFIG['student_id']
    assert len(METRICS['model_version']) == 12


def test_training_rows_match_dataset():
    assert METRICS['training_rows'] == len(pd.read_csv('dataset/train.csv'))


def test_accuracy_better_than_chance():
    assert 0.5 < METRICS['accuracy'] <= 1.0


def test_metrics_endpoint():
    response = client.get('/metrics')
    assert response.status_code == 200
    assert response.json()['model_version'] == METRICS['model_version']


def test_predict_endpoint():
    record = {feature: 0.0 for feature in CONFIG['features']}
    response = client.post('/predict', json={'records': [record, record]})
    assert response.status_code == 200
    body = response.json()
    assert len(body['predictions']) == 2
    assert set(body['predictions']) <= {0, 1}
    assert all(0.0 <= p <= 1.0 for p in body['probabilities'])


def test_predict_rejects_empty_request():
    assert client.post('/predict', json={'records': []}).status_code == 422

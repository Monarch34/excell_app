from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)


def test_health_check():
    """Verify the API is running."""
    response = client.get("/api/v3/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "3.0.0"}


def test_e2e_process_flow():
    """
    Simulate the full frontend flow:
    1. Upload CSV
    2. Detect Columns (Implicit in Upload often, but explicit endpoint exists)
    3. Process Data
    """

    # 1. Mock CSV Upload
    # Parser strict requirements (from src/services/csv_parser.py):
    # Line 0-2: Dimensions
    # Line 3: Empty
    # Line 4: Headers
    # Line 5: Units
    # Line 6+: Data
    csv_content = """Dimension : Length,50,mm
Dimension : Width,12.5,mm
Dimension : Thickness,2.0,mm

Time,Extension,Load,Tensile strain,Tensile stress,Tensile extension
(s),(mm),(N),(%),(MPa),(mm)
0.1,0.01,100,0.001,50,0.001
0.2,0.02,200,0.002,100,0.002
0.3,0.03,300,0.003,150,0.003
0.4,0.04,400,0.004,200,0.004
0.5,0.05,500,0.005,250,0.005
0.6,0.06,600,0.006,300,0.006
0.7,0.07,700,0.007,350,0.007
0.8,0.08,800,0.008,400,0.008
0.9,0.09,900,0.009,450,0.009
1.0,0.10,1000,0.010,500,0.010
"""
    files = {"file": ("test_sample.csv", csv_content, "text/csv")}

    upload_res = client.post("/api/v3/datasets/upload", files=files)
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"

    data = upload_res.json()
    assert "dataset_id" in data
    assert "raw_data" in data
    assert "parameters" in data
    assert len(data["raw_data"]) == 10

    # 2. Prepare Process Payload (generic processing API)
    dataset_id = data["dataset_id"]

    process_payload = {
        "dataset_id": dataset_id,
        "parameters": {"length": 50.0, "width": 12.5, "thickness": 2.0},
        "units": data.get("units", {}),
        "column_mapping": {
            "extension": "Extension",
            "load": "Load",
        },
        "project_name": "Smoke Test",
        "operations": [
            {"type": "find_zero", "config": {"column": "Extension", "result_key": "extension"}},
            {"type": "slice_from_index", "config": {"index_key": "extension_zero_index"}},
            {
                "type": "offset_correction",
                "config": {
                    "columns": [
                        {"source": "Load", "output": "Corrected Load"},
                        {"source": "Extension", "output": "Corrected Extension"},
                    ],
                    "abs_value": False,
                },
            },
        ],
        "user_formulas": [
            {"name": "DoubleLoad", "formula": "[Corrected Load] * 2", "unit": "N"},
        ],
    }

    # 3. Call Process
    process_res = client.post("/api/v3/processing/run", json=process_payload)
    if process_res.status_code != 200:
        print(f"Process Error: {process_res.text}")

    assert process_res.status_code == 200
    results = process_res.json()
    run_id = results.get("run_id")
    assert isinstance(run_id, str) and run_id

    run_data_res = client.get(f"/api/v3/processing/runs/{run_id}/data")
    assert run_data_res.status_code == 200
    processed_rows = run_data_res.json().get("processed_data") or []

    # 4. Verify Results Structure
    assert "results" in results
    assert "extension_zero_index" in results["results"]
    assert len(processed_rows) > 0
    assert "Corrected Load" in processed_rows[0]
    assert "DoubleLoad" in processed_rows[0]

    print("\n Smoke Test Passed!")
    print(f"Results: {results['results']}")

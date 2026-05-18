import pytest
import io
from fastapi.testclient import TestClient
from main import app, videos_db, analyses_db

@pytest.fixture(autouse=True)
def clean_dbs():
    videos_db.clear()
    analyses_db.clear()
    yield

@pytest.fixture
def client():
    return TestClient(app)

class TestAPIEndpoints:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "TRIBE v2" in data["message"]
    
    def test_models_status(self, client):
        response = client.get("/models/status")
        assert response.status_code == 200
        data = response.json()
        assert "tribev2" in data
        assert "mirofish" in data
        assert data["tribev2"]["status"] == "ready"
    
    def test_roi_metadata(self, client):
        response = client.get("/roi/metadata")
        assert response.status_code == 200
        data = response.json()
        assert "A5" in data
        assert "LO" in data
    
    def test_simulate_single_strong(self, client):
        response = client.post("/simulate/single", json={"content_url": "version_a.mp4"})
        assert response.status_code == 200
        data = response.json()
        assert "roi" in data
        assert "W_attn" in data
        assert "stage_gate_passed" in data
    
    def test_simulate_single_weak(self, client):
        response = client.post("/simulate/single", json={"content_url": "version_b.mp4"})
        assert response.status_code == 200
        data = response.json()
        assert data["stage_gate_passed"] is False
        assert data["social"] is None
    
    def test_upload_video(self, client):
        file_content = b"fake mp4 content" * 1000
        response = client.post(
            "/upload",
            files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "analyzed"
        assert "video_id" in data
    
    def test_upload_unsupported_format(self, client):
        response = client.post(
            "/upload",
            files={"file": ("test.txt", io.BytesIO(b"not a video"), "text/plain")}
        )
        assert response.status_code == 400
    
    def test_get_video_not_found(self, client):
        response = client.get("/videos/nonexistent-id")
        assert response.status_code == 404
    
    def test_get_analysis_not_found(self, client):
        response = client.get("/analyses/nonexistent-id")
        assert response.status_code == 404
    
    def test_list_videos_empty(self, client):
        response = client.get("/videos")
        assert response.status_code == 200
        data = response.json()
        assert data["videos"] == []
    
    def test_upload_and_retrieve(self, client):
        file_content = b"fake mp4 content" * 1000
        upload_response = client.post(
            "/upload",
            files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        assert upload_response.status_code == 200
        video_id = upload_response.json()["video_id"]
        
        video_response = client.get(f"/videos/{video_id}")
        assert video_response.status_code == 200
        assert video_response.json()["video"]["id"] == video_id
        
        analysis_response = client.get(f"/analyses/{video_id}")
        assert analysis_response.status_code == 200
        analysis = analysis_response.json()
        assert "hook_score" in analysis
        assert "mirofish_simulation" in analysis
        assert "tribev2_brain_response" in analysis
        assert "stage_gate" in analysis
    
    def test_report_generation(self, client):
        file_content = b"fake mp4 content" * 1000
        upload_response = client.post(
            "/upload",
            files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        video_id = upload_response.json()["video_id"]
        
        report_response = client.get(f"/reports/{video_id}")
        assert report_response.status_code == 200
        report = report_response.json()
        assert "report_id" in report
        assert "analysis" in report
        assert "video" in report
    
    def test_simulation_endpoint(self, client):
        file_content = b"fake mp4 content" * 1000
        upload_response = client.post(
            "/upload",
            files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        video_id = upload_response.json()["video_id"]
        
        sim_response = client.get(f"/simulation/{video_id}")
        assert sim_response.status_code == 200
        sim = sim_response.json()
        assert "final_sentiment" in sim
        assert "persona_distribution" in sim
    
    def test_brain_response_endpoint(self, client):
        file_content = b"fake mp4 content" * 1000
        upload_response = client.post(
            "/upload",
            files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        video_id = upload_response.json()["video_id"]
        
        brain_response = client.get(f"/brain-response/{video_id}")
        assert brain_response.status_code == 200
        brain = brain_response.json()
        assert "cortical_response" in brain
        assert "emotional_impact" in brain
    
    def test_what_if_simulation(self, client):
        file_content = b"fake mp4 content" * 1000
        upload_response = client.post(
            "/upload",
            files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        video_id = upload_response.json()["video_id"]
        
        whatif_response = client.post(
            f"/simulation/what-if/{video_id}",
            json={"modifications": {"emotional_tone": True, "price_decrease": 10}}
        )
        assert whatif_response.status_code == 200
        result = whatif_response.json()
        assert "modifications" in result
        assert "predicted_outcome" in result
        assert "comparison" in result

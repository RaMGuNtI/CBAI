import requests
from typing import Dict, Any, List, Optional
from app.core.config import settings


class APIClient:
    def __init__(self, base_url: str = settings.BACKEND_URL):
        self.base_url = base_url.rstrip("/")
        self.api_prefix = f"{self.base_url}/api"

    def is_backend_online(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.api_prefix}/analytics/dashboard", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return {"total_chatbots": 0, "total_documents": 0, "total_conversations": 0, "total_questions": 0, "recent_chatbots": []}

    def list_chatbots(self) -> List[Dict[str, Any]]:
        try:
            r = requests.get(f"{self.api_prefix}/chatbots", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return []

    def get_chatbot(self, chatbot_id: str) -> Optional[Dict[str, Any]]:
        try:
            r = requests.get(f"{self.api_prefix}/chatbots/{chatbot_id}", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def create_chatbot(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            r = requests.post(f"{self.api_prefix}/chatbots", json=payload, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def update_chatbot(self, chatbot_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            r = requests.put(f"{self.api_prefix}/chatbots/{chatbot_id}", json=payload, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def delete_chatbot(self, chatbot_id: str) -> bool:
        try:
            r = requests.delete(f"{self.api_prefix}/chatbots/{chatbot_id}", timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def set_publish_status(self, chatbot_id: str, is_published: bool) -> bool:
        try:
            r = requests.post(
                f"{self.api_prefix}/chatbots/{chatbot_id}/publish",
                json={"is_published": is_published},
                timeout=5
            )
            return r.status_code == 200
        except Exception:
            return False

    def list_documents(self, chatbot_id: str) -> List[Dict[str, Any]]:
        try:
            r = requests.get(f"{self.api_prefix}/chatbots/{chatbot_id}/documents", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return []

    def upload_files(self, chatbot_id: str, file_tuples: List[tuple], enable_ocr: bool = False) -> List[Dict[str, Any]]:
        try:
            data = {"enable_ocr": "true" if enable_ocr else "false"}
            r = requests.post(
                f"{self.api_prefix}/chatbots/{chatbot_id}/documents/upload",
                files=file_tuples,
                data=data,
                timeout=60
            )
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            return [{"filename": "upload", "status": "error", "message": str(e)}]
        return []

    def delete_document(self, chatbot_id: str, document_id: str) -> bool:
        try:
            r = requests.delete(f"{self.api_prefix}/chatbots/{chatbot_id}/documents/{document_id}", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def send_chat_message(self, chatbot_id: str, message: str, session_id: str = "default_session") -> Optional[Dict[str, Any]]:
        try:
            r = requests.post(
                f"{self.api_prefix}/chatbots/{chatbot_id}/chat",
                json={"message": message, "session_id": session_id},
                timeout=30
            )
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def get_conversation_history(self, chatbot_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            r = requests.get(f"{self.api_prefix}/chatbots/{chatbot_id}/conversations/{session_id}", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def clear_conversation(self, chatbot_id: str, session_id: str) -> bool:
        try:
            r = requests.delete(f"{self.api_prefix}/chatbots/{chatbot_id}/conversations/{session_id}", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def get_share_details(self, chatbot_id: str) -> Optional[Dict[str, Any]]:
        try:
            r = requests.get(f"{self.api_prefix}/chatbots/{chatbot_id}/share", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def run_evaluation(self, chatbot_id: str, test_samples: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, Any]]:
        try:
            payload = {"samples": test_samples} if test_samples else {}
            r = requests.post(f"{self.api_prefix}/chatbots/{chatbot_id}/evaluation", json=payload, timeout=45)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def get_public_chatbot(self, share_token: str) -> Optional[Dict[str, Any]]:
        try:
            r = requests.get(f"{self.api_prefix}/public/chatbots/{share_token}", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def send_public_chat(self, share_token: str, message: str, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            r = requests.post(
                f"{self.api_prefix}/public/chatbots/{share_token}/chat",
                json={"message": message, "session_id": session_id},
                timeout=30
            )
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None


client = APIClient()


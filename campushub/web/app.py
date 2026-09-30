"""
Built-in Zero-Dependency Web Server and REST API for CampusHub.
Powered by Python's native http.server and sqlite3.
"""

import http.server
import json
import os
import urllib.parse
from pathlib import Path
from typing import Dict, Any

from campushub.database.db_manager import get_db
from campushub.services.auth_service import AuthService
from campushub.services.group_service import GroupService
from campushub.services.scheduler_service import SchedulerService
from campushub.services.resource_service import ResourceService
from campushub.services.analytics_service import AnalyticsService
from campushub.services.integrity_service import IntegrityService
from campushub.utils.exceptions import CampusHubException
from campushub.utils.logger import setup_logger

logger = setup_logger("web_server")
STATIC_DIR = Path(__file__).resolve().parent / "static"


class CampusHubRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handles HTTP requests for static dashboard assets and JSON REST APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            self._handle_api_get(path, query)
        else:
            if path == "/" or path == "":
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            payload = json.loads(post_body) if post_body else {}
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON in request body"}, status=400)
            return

        self._handle_api_post(path, payload)

    def _send_json(self, data: Any, status: int = 200):
        response_bytes = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)

    def _handle_api_get(self, path: str, query: Dict[str, Any]):
        db = get_db()
        try:
            if path == "/api/groups":
                course = query.get("course", [None])[0]
                search = query.get("search", [None])[0]
                groups = GroupService(db).list_groups(course_code=course, search_query=search)
                self._send_json([g.to_dict() for g in groups])

            elif path == "/api/sessions":
                group_id = query.get("group_id", [None])[0]
                user_id = query.get("user_id", [None])[0]
                sched = SchedulerService(db)
                if group_id:
                    sessions = sched.list_sessions_for_group(int(group_id))
                elif user_id:
                    sessions = sched.list_upcoming_sessions_for_user(int(user_id))
                else:
                    # Return all upcoming
                    rows = db.execute_query_all(
                        """
                        SELECT s.*, g.name as group_name, u.full_name as host_name,
                               (SELECT COUNT(*) FROM session_attendance sa WHERE sa.session_id = s.id) as attendee_count
                        FROM study_sessions s
                        JOIN study_groups g ON s.group_id = g.id
                        JOIN users u ON s.host_id = u.id
                        ORDER BY s.start_time ASC
                        """
                    )
                    from campushub.models.session import StudySession
                    sessions = [StudySession.from_row(r) for r in rows]
                self._send_json([s.to_dict() for s in sessions])

            elif path == "/api/resources":
                group_id = query.get("group_id", [None])[0]
                tag = query.get("tag", [None])[0]
                search = query.get("search", [None])[0]
                res_list = ResourceService(db).search_resources(
                    group_id=int(group_id) if group_id else None,
                    tag=tag,
                    search_query=search,
                )
                self._send_json([r.to_dict() for r in res_list])

            elif path == "/api/analytics":
                group_id = query.get("group_id", [None])[0]
                if not group_id:
                    self._send_json({"error": "group_id query parameter required"}, status=400)
                    return
                data = AnalyticsService(db).get_group_analytics(int(group_id))
                self._send_json(data)

            elif path == "/api/users":
                users = AuthService(db).list_all_users()
                self._send_json([u.to_dict() for u in users])

            else:
                self._send_json({"error": "Endpoint not found"}, status=404)
        except CampusHubException as e:
            self._send_json({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Internal GET error: {e}")
            self._send_json({"error": "Internal server error"}, status=500)

    def _handle_api_post(self, path: str, payload: Dict[str, Any]):
        db = get_db()
        try:
            if path == "/api/groups":
                grp = GroupService(db).create_group(
                    creator_id=int(payload["creator_id"]),
                    name=payload["name"],
                    course_code=payload["course_code"],
                    description=payload.get("description", ""),
                    max_members=int(payload.get("max_members", 20)),
                    is_private=bool(payload.get("is_private", False)),
                )
                self._send_json(grp.to_dict(), status=201)

            elif path == "/api/sessions":
                sess = SchedulerService(db).schedule_session(
                    group_id=int(payload["group_id"]),
                    host_id=int(payload["host_id"]),
                    title=payload["title"],
                    description=payload.get("description", ""),
                    location_or_link=payload["location_or_link"],
                    start_time_str=payload["start_time"],
                    end_time_str=payload["end_time"],
                )
                self._send_json(sess.to_dict(), status=201)

            elif path == "/api/sessions/rsvp":
                rec = SchedulerService(db).rsvp_session(
                    session_id=int(payload["session_id"]),
                    user_id=int(payload["user_id"]),
                )
                self._send_json(rec.to_dict(), status=200)

            elif path == "/api/sessions/checkin":
                rec = SchedulerService(db).mark_attendance(
                    session_id=int(payload["session_id"]),
                    user_id=int(payload["user_id"]),
                )
                self._send_json(rec.to_dict(), status=200)

            elif path == "/api/resources":
                res = ResourceService(db).upload_resource(
                    group_id=int(payload["group_id"]),
                    uploader_id=int(payload["uploader_id"]),
                    title=payload["title"],
                    resource_type=payload["resource_type"],
                    file_or_url=payload["file_or_url"],
                    description=payload.get("description", ""),
                    tags=payload.get("tags", ""),
                )
                self._send_json(res.to_dict(), status=201)

            elif path == "/api/reviews":
                rev = AnalyticsService(db).submit_review(
                    session_id=int(payload["session_id"]),
                    reviewer_id=int(payload["reviewer_id"]),
                    rating=int(payload["rating"]),
                    comments=payload.get("comments", ""),
                    reviewee_id=int(payload["reviewee_id"]) if payload.get("reviewee_id") else None,
                )
                self._send_json(rev.to_dict(), status=201)

            elif path == "/api/integrity/plagiarism":
                integ = IntegrityService()
                res = integ.calculate_plagiarism(payload["source_text"], payload["target_text"])
                self._send_json(res, status=200)

            elif path == "/api/integrity/ai-detect":
                integ = IntegrityService()
                res = integ.detect_ai_code(payload["code_text"])
                self._send_json(res, status=200)

            elif path == "/api/seed":
                from campushub.cli.menu import CampusHubCLI
                cli = CampusHubCLI(db)
                cli._seed_sample_data()
                self._send_json({"message": "Sample data seeded successfully!"})

            else:
                self._send_json({"error": "Endpoint not found"}, status=404)
        except CampusHubException as e:
            self._send_json({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Internal POST error: {e}")
            self._send_json({"error": str(e)}, status=500)


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Starts the native CampusHub HTTP server."""
    os.makedirs(STATIC_DIR, exist_ok=True)
    server = http.server.HTTPServer((host, port), CampusHubRequestHandler)
    print(f"\n=======================================================")
    print(f" CAMPUSHUB WEB DASHBOARD RUNNING")
    print(f" Access URL: http://{host}:{port}")
    print(f" Press Ctrl+C in this terminal to stop the server.")
    print(f"=======================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down CampusHub Web Server...")
        server.server_close()


if __name__ == "__main__":
    start_server()

import os
import requests
from dotenv import load_dotenv
from parse_files import extract_text_from_files

load_dotenv()

def get_headers(canvas_token: str) -> dict:
    """Get headers for Canvas API requests"""
    if not canvas_token:
        raise ValueError("Canvas token not provided")
    return {
        "Authorization": f"Bearer {canvas_token}"
    }

def get_all_available_canvas_courses(canvas_token: str, school_domain: str) -> list:
    try:
        response = requests.get(f"https://{school_domain}.instructure.com/api/v1/courses?enrollment_state=active", headers=get_headers(canvas_token))
        response.raise_for_status()  

        response_json = response.json()
        if not response_json:
            print("⚠️ No courses returned from API.")
            return []

        cleaned_up_response = []
        for course in response_json:
            cleaned_up_response.append(course)


        return cleaned_up_response

    except requests.exceptions.HTTPError as e:
        print(f" API error while getting courses: {e}")
        return []

def paginate(url):
    results = []
    while url:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()

        if not response.text.strip():
            print("Empty API response received. Returning empty list.")
            return []

        results.extend(response.json())

        url = response.links.get('next', {}).get('url', None)

    return results
    


def get_all_course_materials(canvas_token: str, school_domain: str) -> dict:
    """Get all course materials from Canvas using provided credentials"""
    courses = get_all_available_canvas_courses(canvas_token, school_domain)
    all_materials = {}

    for course in courses:
        if "name" not in course:
            continue  

        course_id = course["id"]
        course_name = course["name"]
        safe_course_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '_')).rstrip()
        course_folder = os.path.join("course_files", safe_course_name)
        os.makedirs(course_folder, exist_ok=True)

        # === Assignments ===
        course_assignments = get_canvas_assignments(canvas_token, school_domain, course_id)
        assignments = []

        for assignment in course_assignments:
            assignment_id = assignment["id"]
            assignment_info = get_canvas_assignment_info(canvas_token, school_domain, course_id, assignment_id)
            if isinstance(assignment_info, dict):
                assignments.append(assignment_info)
            else:
                print("⚠️ Invalid assignment info:", assignment_info)

        # === Files ===
        files_url = f"https://{school_domain}.instructure.com/api/v1/courses/{course_id}/files"
        try:
            while files_url:
                response = requests.get(files_url, headers=get_headers(canvas_token))
                response.raise_for_status()
                data = response.json()

                for file in data:
                    file_name = file['display_name']
                    file_url = file['url']
                    file_path = os.path.join(course_folder, file_name)

                    if os.path.exists(file_path):
                        print(f"✅ Skipping existing file: {file_path}")
                        continue

                    with requests.get(file_url, stream=True) as file_response:
                        file_response.raise_for_status()
                        with open(file_path, 'wb') as f:
                            for chunk in file_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"📥 Downloaded: {file_path}")

                files_url = response.links.get('next', {}).get('url')

        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                print(f"🚫 Skipping course '{course_name}' (ID: {course_id}) due to restricted file access.")
            else:
                print(f"❌ Unexpected error with course '{course_name}': {e}")
            continue  # Skip to the next course

        # === Store collected materials ===
        all_materials[course_name] = {
            "assignments": assignments if assignments else "No assignments available",
            "description": course.get("description", "No description available")
        }

    return all_materials


def get_canvas_assignments(canvas_token: str, school_domain: str, course_id: int):
    try:
        response = requests.get(f"https://{school_domain}.instructure.com/api/v1/courses/{course_id}/assignments", headers=get_headers(canvas_token))
        response_json = response.json()

        print("yahoo", response_json)
    
        return response_json
    except Exception as e:
        print(f"Error getting courses: {e}")
        return []


def get_canvas_assignment_info(canvas_token: str, school_domain: str, course_id: str, assignment_id: str):
    try:
        response = requests.get(f"https://{school_domain}.instructure.com/api/v1/courses/{course_id}/assignments/{assignment_id}", headers=get_headers(canvas_token))
        response.raise_for_status()  # Ensure we handle failed API calls
        response_json = response.json()

        return {
            "id": response_json.get("id", "Unknown ID"),
            "name": response_json.get("name", "Unnamed Assignment"),
            "description": response_json.get("description", "No Description")
        }

    except requests.exceptions.RequestException as e:
        print(f"⚠️ API Request Failed: {e}")
        return {}  
    except KeyError as e:
        print(f"⚠️ Missing Key in API Response: {e}")
        return {}




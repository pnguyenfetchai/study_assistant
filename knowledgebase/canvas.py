from dotenv import load_dotenv
import requests
import os

load_dotenv()

BASE_URL = "https://canvas.instructure.com/api/v1"
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN")


def get_headers():
    return {
        "Authorization": f"Bearer {CANVAS_TOKEN}"
    }

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



def get_all_course_materials():
    courses = get_all_available_canvas_courses()
    all_materials = {}


    for course in courses:
        if "name" not in course:
            continue  

        course_id = course["id"]
        course_name = course["name"]
        course_assignments = get_canvas_assignments(course_id)
        assignments = []

        files_url = f"{BASE_URL}/courses/{course_id}/files"

        if not os.path.exists("course_files"):
            while files_url:
                response = requests.get(files_url, headers=get_headers())
                response.raise_for_status()
                data = response.json()
                for file in data:
                    file_name = file['display_name']
                    file_url = file['url']
                    file_path = os.path.join("course_files", file_name)

                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    with requests.get(file_url, stream=True) as file_response:
                        file_response.raise_for_status()
                        with open(file_path, 'wb') as f:
                            for chunk in file_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                # Check for pagination
                files_url = response.links.get('next', {}).get('url')

        for assignment in course_assignments:
            assignment_id = assignment["id"]
            assignment_info = get_canvas_assignment_info(course_id, assignment_id)
            if isinstance(assignment_info, dict):
                assignments.append(assignment_info)
            else:
                print("drake radindrake", assignment_info)

        all_materials[course_name] = {
            "assignments": assignments if assignments else "No assignments available",
            "description": course.get("description", "No description available")
        }

    return all_materials



def get_all_available_canvas_courses():
    try:
        response = requests.get(f"{BASE_URL}/courses?enrollment_state=active", headers=get_headers())
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



def get_canvas_assignments(course_id: int):
    try:
        response = requests.get(f"{BASE_URL}/courses/{course_id}/assignments", headers=get_headers())
        response_json = response.json()

        print("yahoo", response_json)
    
        return response_json
    except Exception as e:
        print(f"Error getting courses: {e}")
        return []



def get_canvas_assignment_info(course_id: str, assignment_id: str):
    try:
        response = requests.get(f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}", headers=get_headers())
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

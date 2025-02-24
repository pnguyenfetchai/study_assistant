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

        for assignment in course_assignments:
            assignment_id = assignment["id"]
            assignment_info = get_canvas_assignment_info(course_id, assignment_id)
            assignments.append(assignment_info)

        all_materials[course_name] = {
            "assignments": assignments if assignments else "No assignments available",
            "description": course.get("description", "No description available")
        }

    return all_materials



def get_all_available_canvas_courses():
    try:
        response = requests.get(f"{BASE_URL}/courses", headers=get_headers())
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
        response_json = response.json()

        print("response_json", response_json)
        
        cleaned_assignment = []
        cleaned_assignment.append({
            "id": response_json["id"],
            "name": response_json["name"],
            "description": response_json.get("description", "")
        })
    
        return cleaned_assignment[0]
    except Exception as e:
        print(f"Error getting assignment: {e}")
        return {}
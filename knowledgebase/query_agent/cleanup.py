#!/usr/bin/env python3
import os
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_rag_system():
    """Clean up the RAG system by clearing contents of directories"""
    try:
        base_dir = "/app"  # Docker container working directory
        
        # Clean up course_files directory contents
        course_files_dir = os.path.join(base_dir, "course_files")
        subprocess.run(f"find {course_files_dir} -mindepth 1 -delete", shell=True, check=True)
        logger.info("Successfully cleared course_files directory contents")
        
        # Clean up FAISS index files
        faiss_path = os.path.join(base_dir, "faiss_index")
        subprocess.run(f"find {faiss_path} -mindepth 1 -delete", shell=True, check=True)
        logger.info("Successfully cleared FAISS index directory contents")
            
        logger.info("Cleanup completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during cleanup command: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return False

if __name__ == "__main__":
    cleanup_rag_system()

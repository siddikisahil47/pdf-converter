from .config import *

class CleanupOperations:
    @staticmethod
    def cleanup_temp_directory():
        """Clean up the temporary directory and all its contents"""
        try:
            if os.path.exists(TEMP_DIR):
                shutil.rmtree(TEMP_DIR)
                os.makedirs(TEMP_DIR, exist_ok=True)
                logger.info(f"Cleaned up temporary directory: {TEMP_DIR}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory: {str(e)}")

    @staticmethod
    def cleanup_temp_files(files: List[str]):
        """Clean up specific temporary files
        
        Args:
            files: List of file paths to clean up
        """
        for file in files:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    logger.info(f"Cleaned up temporary file: {file}")
            except Exception as e:
                logger.error(f"Error cleaning up {file}: {str(e)}") 